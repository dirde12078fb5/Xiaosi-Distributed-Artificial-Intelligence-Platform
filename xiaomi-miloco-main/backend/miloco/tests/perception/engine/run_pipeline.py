"""批量测试脚本：对 fixtures/ 下的视频文件跑完整 pipeline 并输出结果。

用法：
    # 使用 mock tracking + 真实 omni（使用内置 API key）
    python -m tests.run_pipeline fixtures/

    # 使用 mock omni（不调用 API）
    python -m tests.run_pipeline fixtures/ --mock-omni

    # 指定单个视频
    python -m tests.run_pipeline fixtures/2.mp4

    # 自定义规则条件
    python -m tests.run_pipeline fixtures/ --rule "reading_light:读书开灯:当前是否有人在读书"

    # 指定 API key（覆盖内置）
    OPENROUTER_API_KEY=xxx python -m tests.run_pipeline fixtures/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock

from miloco.perception.engine.config import PerceptionConfig
from miloco.perception.engine.identity.tracking_service import (
    MockTrackingService,
    create_default_mock_response,
)
from miloco.perception.engine.input.video_splitter import split_video
from miloco.perception.engine.pipeline import run_pipeline
from miloco.perception.engine.types import OmniContext, RuleCondition

# mock omni 的默认响应
MOCK_OMNI_RESPONSE = {
    "id": "mock",
    "choices": [
        {
            "message": {
                "content": json.dumps(
                    {
                        "caption": {"scene": "[MOCK] 场景描述占位", "delta": None},
                        "evaluation": {"ruleResults": [], "commonSenseFlags": []},
                        "speech": None,
                    }
                ),
            },
        }
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MVP pipeline batch test")
    parser.add_argument("input", help="视频文件或 fixtures 目录路径")
    parser.add_argument(
        "--mock-omni", action="store_true", help="使用 mock omni（不调用 API）"
    )
    parser.add_argument(
        "--rule",
        action="append",
        default=[],
        help="规则条件，格式: rule_id:name:conditions",
    )
    parser.add_argument("--room", default="study-room", help="房间 ID")
    return parser.parse_args()


def collect_videos(input_path: str) -> list[Path]:
    p = Path(input_path)
    if p.is_file():
        return [p]
    if p.is_dir():
        exts = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
        videos = sorted(f for f in p.iterdir() if f.suffix.lower() in exts)
        if not videos:
            print(f"[WARN] 目录 {p} 下没有视频文件")
        return videos
    print(f"[ERROR] 路径不存在: {input_path}")
    sys.exit(1)


def parse_rules(raw_rules: list[str]) -> list[RuleCondition]:
    rules = []
    for r in raw_rules:
        parts = r.split(":", 2)
        if len(parts) != 3:
            print(f"[WARN] 规则格式错误（应为 id:name:conditions）: {r}")
            continue
        rules.append(
            RuleCondition(rule_id=parts[0], rule_name=parts[1], query=parts[2])
        )
    if not rules:
        rules.append(
            RuleCondition(
                rule_id="reading_light",
                rule_name="读书开灯",
                query="当前是否有人在读书",
            )
        )
    return rules


def print_divider(char: str = "=", width: int = 70):
    print(char * width)


def print_result(video_path: Path, result, elapsed_ms: float):
    print_divider()
    print(f"视频: {video_path.name}")
    print_divider("-")

    # Input
    s = result.input_slice
    print("\n[数据输入层]")
    print(f"  房间: {s.room_name}")
    print(f"  帧数: {len(s.frames)}")
    if s.frames:
        print(f"  帧尺寸: {s.frames[0].shape[1]}x{s.frames[0].shape[0]}")
    print(
        f"  音频样本: {len(s.audio_clip)} ({'有' if len(s.audio_clip) > 0 else '无'}音频)"
    )

    # Gate
    print("\n[Gate 层]")
    if result.skipped:
        print("  结果: SKIPPED（无变化，未触发下游）")
        print(f"\n总耗时: {elapsed_ms:.0f}ms")
        return

    gt = result.gate_packet.trigger
    print("  结果: TRIGGERED")
    print(
        f"  视觉变化: {'YES' if gt.visual_changed else 'NO'} (score={gt.visual_change_score:.6f})"
    )
    print(
        f"  音频活跃: {'YES' if gt.audio_active else 'NO'} (energy={gt.audio_energy_level:.6f})"
    )
    print(f"  输出帧数: {len(result.gate_packet.frames)}")

    # Edge
    ep = result.identity_packet
    if ep:
        print("\n[Edge 层]")
        print(f"  场景状态: {ep.scene_motion.value}")
        print(f"  检测目标: {len(ep.targets)} 个")
        for t in ep.targets:
            verify_tag = " [需Omni验证]" if t.needs_omni_verify else ""
            print(
                f"    - type={t.type.value}, id={t.person_id}{verify_tag}"
            )
            print(f"      bbox 帧数: {len(t.box_info)}")
        print(
            f"  抽帧结果: {len(ep.frames)} 帧 ({ep.frames[0].resolution.value if ep.frames else 'N/A'})"
        )
        for f in ep.frames:
            print(
                f"    frame[{f.frame_index}]: {f.image.shape[1]}x{f.image.shape[0]}, crops={len(f.crops)}"
            )
            for c in f.crops:
                print(
                    f"      crop[track={c.track_id}]: {c.image.shape[1]}x{c.image.shape[0]}"
                )
        print("  音频分析:")
        print(f"    type={ep.audio_analysis.type.value}")
        print(f"    energy={ep.audio_analysis.energy_level:.6f}")
        print(f"    urgent={ep.audio_analysis.is_urgent}")

    # Omni
    oo = result.omni_output
    if oo:
        print("\n[Omni 层]")
        print(f"  场景描述: {oo.caption.scene}")
        # caption.audio removed — scene now includes audio description
        if oo.caption.delta:
            print(f"  场景变化: {oo.caption.delta}")

        if oo.evaluation.rule_results:
            print("  规则判断:")
            for rr in oo.evaluation.rule_results:
                status = "MATCHED" if rr.matched else "NOT MATCHED"
                print(f"    [{status}] {rr.rule_id} (confidence={rr.confidence:.2f})")
                print(f"      reasoning: {rr.reasoning}")
        else:
            print("  规则判断: 无")

        if oo.evaluation.common_sense_flags:
            print("  常识标注:")
            for cs in oo.evaluation.common_sense_flags:
                print(
                    f"    [{cs.severity.value}] {cs.category.value}: {cs.observation}"
                )
                if cs.suggested_action:
                    print(f"      建议: {cs.suggested_action}")
        else:
            print("  常识标注: 无")

        if oo.speech:
            print("  语音检测:")
            print(f"    type={oo.speech.type.value}")
            print(f"    speaker={oo.speech.speaker}")
            print(f'    transcript="{oo.speech.transcript}"')
        else:
            print("  语音检测: 无")

    print(f"\n总耗时: {elapsed_ms:.0f}ms")


async def run_single(
    video_path: Path,
    config: PerceptionConfig,
    context: OmniContext,
    mock_omni: bool,
):
    # 拆帧
    try:
        input_slice = split_video(str(video_path), "study-room", config.input)
    except Exception as e:
        print_divider()
        print(f"视频: {video_path.name}")
        print(f"[ERROR] 拆帧失败: {e}")
        return

    tracking = MockTrackingService(create_default_mock_response())

    start = time.monotonic()

    if mock_omni:
        import engine.omni.omni as omni_mod

        original = omni_mod.call_omni
        omni_mod.call_omni = AsyncMock(return_value=MOCK_OMNI_RESPONSE)
        try:
            result = await run_pipeline(
                input_slice, context, config, tracking_service=tracking
            )
        finally:
            omni_mod.call_omni = original
    else:
        result = await run_pipeline(
            input_slice, context, config, tracking_service=tracking
        )

    elapsed = (time.monotonic() - start) * 1000
    print_result(video_path, result, elapsed)


async def main():
    args = parse_args()
    videos = collect_videos(args.input)
    if not videos:
        return

    config = PerceptionConfig()

    # API key: 环境变量 MILOCO_MODEL__OMNI__API_KEY，omni_client 内部也会自动读取
    api_key = os.environ.get("MILOCO_MODEL__OMNI__API_KEY", "")
    if not api_key and not args.mock_omni:
        print("[WARN] MILOCO_MODEL__OMNI__API_KEY 未设置，将无法调用 MiMo API")
    config.omni.api_key = api_key

    mock_omni = args.mock_omni

    rules = parse_rules(args.rule)
    context = OmniContext(rule_conditions=rules)

    mode_str = "MOCK OMNI" if mock_omni else f"LIVE OMNI ({config.omni.model})"
    print("\n MVP Pipeline Test")
    print(f"视频数: {len(videos)}")
    print(f"模式: {mode_str}")
    print(f"规则: {[r.rule_id + ': ' + r.conditions for r in rules]}")

    for video in videos:
        await run_single(video, config, context, mock_omni)

    print_divider()
    print(f"\n完成，共测试 {len(videos)} 个视频")


if __name__ == "__main__":
    asyncio.run(main())
