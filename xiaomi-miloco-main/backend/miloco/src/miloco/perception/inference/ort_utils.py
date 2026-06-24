"""ONNX Runtime session utilities — centralised thread control."""

from __future__ import annotations

import logging
import platform

import onnxruntime as ort

_LOGGER = logging.getLogger(__name__)

# Empirically tested: 4 threads gives the best balance of throughput and
# tail-latency stability on real workloads.  Higher counts look faster on
# synthetic benchmarks but suffer from scheduling jitter on real frames
# (e.g. 8 threads: avg 62ms but max 410ms vs 4 threads: avg 48ms, max 58ms).
_DEFAULT_NUM_THREADS = 4

# Apple Silicon 上 CPU EP 默认走 ArmKleidiAI::MlasConv,每次 Conv 推理分配
# native workspace 不归还,长跑 RSS 单调上涨。CoreML EP 走 ANE/GPU 绕开此路径。
# Intel Mac 上 CoreML EP 反而更慢,需要按 arch 区分。
_IS_APPLE_SILICON = (
    platform.system() == "Darwin" and platform.machine() == "arm64"
)


def _ort_version_ge(major: int, minor: int) -> bool:
    try:
        parts = ort.__version__.split(".")
        return (int(parts[0]), int(parts[1])) >= (major, minor)
    except (ValueError, IndexError):
        return False


def make_session(
    model_path: str,
    *,
    use_gpu: bool = False,
    num_threads: int | None = None,
) -> ort.InferenceSession:
    """Create an InferenceSession with thread-count control.

    Args:
        model_path: Path to the ONNX model file.
        use_gpu: Whether to prefer CUDA execution provider.
        num_threads: Number of intra/inter-op threads. ``None`` uses the
            module default (4).
    """
    providers = ["CPUExecutionProvider"]
    available = ort.get_available_providers()
    if use_gpu and "CUDAExecutionProvider" in available:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    # Apple Silicon 即使 use_gpu=False 也走 CoreML — 主要目的是绕开 CPU EP
    # 上 ArmKleidiAI 的 workspace 内存泄漏 (不是为性能,顺带也快)。
    #
    # CoreML EP (FP16) vs CPU EP (FP32) 的数值漂移在本仓库的 detector / reid
    # 模型上实测业务阈值内可忽略 — detector top conf |Δ| ≤ 1.3e-4 远小于
    # 0.5 阈值;reid same-input cosine ≥ 0.999998,cross-pair cosine drift
    # p95 = 4e-4 — 故未加 provider_options 钉死 MLComputeUnits。
    elif _IS_APPLE_SILICON and "CoreMLExecutionProvider" in available:
        providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    elif _IS_APPLE_SILICON:
        # 自构 / 精简版 wheel 可能不带 CoreML EP,此时静默退回 CPU EP 会让本
        # 模块的内存修复彻底失效。WARNING 级别醒目,避免长跑几小时才发现 RSS
        # 还在涨,人却以为"在 Mac 上就一定走 CoreML"。
        _LOGGER.warning(
            "Apple Silicon detected but CoreMLExecutionProvider not in %s; "
            "falling back to CPU EP — KleidiAI workspace leak will reappear. "
            "Check onnxruntime wheel build options.",
            available,
        )

    opts = ort.SessionOptions()
    threads = num_threads if num_threads is not None else _DEFAULT_NUM_THREADS
    opts.intra_op_num_threads = threads
    opts.inter_op_num_threads = threads

    # 兜底层: onnxruntime >= 1.25 加 PR #27136 引入的 opt-out。CoreML 不支持
    # 的算子会 fallback 到 CPU EP,默认仍走 ArmKleidiAI 继续小幅泄漏;另外覆盖
    # 非 Apple Silicon ARM 平台 (如 Linux ARM 部署)。
    if _ort_version_ge(1, 25):
        opts.add_session_config_entry("mlas.disable_kleidiai", "1")

    _LOGGER.info("ORT session providers=%s for %s", providers, model_path)
    return ort.InferenceSession(model_path, sess_options=opts, providers=providers)
