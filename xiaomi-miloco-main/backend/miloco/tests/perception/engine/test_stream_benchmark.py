"""流式 vs 非流式 Benchmark — 对比 3s/5s 窗口 × stream/non-stream 的指令响应速度。

捕获 TTFT（首 token 时间）来分离排队+prefill vs decode，排除排队干扰。

用法：
    cd server/packages/perception-engine/src

    # 跑单个视频
    MILOCO_MODEL__OMNI__API_KEY=... uv run python -m engine.tests.test_stream_benchmark /path/to/video.mp4

    # 跑整个目录
    MILOCO_MODEL__OMNI__API_KEY=... uv run python -m engine.tests.test_stream_benchmark /path/to/录制事件/

    # 只跑流式
    MILOCO_MODEL__OMNI__API_KEY=... uv run python -m engine.tests.test_stream_benchmark video.mp4 --stream-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from miloco.perception.engine.config import OmniConfig
from miloco.perception.engine.omni.omni_client import call_omni, call_omni_stream
from miloco.perception.engine.omni.prompt_builder import (
    build_prompt,
    build_stream_prompt,
)
from miloco.perception.engine.omni.response_parser import (
    parse_omni_response,
    parse_omni_response_from_text,
    try_extract_matched_rules,
    try_extract_speeches,
    try_extract_suggestions,
)
from miloco.perception.engine.types import (
    AudioAnalysis,
    AudioType,
    FrameInfo,
    IdentityPacket,
    MotionState,
    OmniContext,
)

from .run_stream_test import simulate_stream


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
@dataclass
class BenchmarkResult:
    """Result of a single benchmark run (one window, one config)."""

    video: str
    window_idx: int
    window_start_sec: float
    period_sec: int
    stream: bool
    # Timing (seconds)
    e2e: float = 0.0  # total time
    ttft: float = 0.0  # time to first token (stream only; = e2e for non-stream)
    tti: float = (
        0.0  # time to speeches extracted (stream only; = e2e for non-stream)
    )
    ttr: float = (
        0.0  # time to matched_rules extracted (stream only; = e2e for non-stream)
    )
    tts: float = (
        0.0  # time to suggestions extracted (stream only; = e2e for non-stream)
    )
    # Derived (seconds)
    queue_prefill: float = 0.0  # ≈ ttft (排队+prefill)
    decode_total: float = 0.0  # ≈ e2e - ttft (全部 decode)
    decode_to_speeches: float = 0.0  # ≈ tti - ttft (decode 到 speeches 完成)
    decode_to_matched_rules: float = 0.0  # ≈ ttr - ttft
    decode_to_suggestions: float = 0.0  # ≈ tts - ttft
    decode_after_speeches: float = 0.0  # ≈ e2e - tti (speeches 之后的 decode)
    # Tokens
    input_tokens: int = 0
    output_tokens: int = 0
    # Content
    speeches_count: int = 0
    speeches_content: list[str] = field(default_factory=list)
    speeches_types: list[str] = field(default_factory=list)
    speeches_statuses: list[str] = field(default_factory=list)
    speeches_speakers: list[str] = field(default_factory=list)
    has_command: bool = False
    has_complete_command: bool = False
    # matched_rules content
    matched_rules_count: int = 0
    matched_rules_content: list[str] = field(default_factory=list)
    # suggestions content
    suggestions_count: int = 0
    suggestions_content: list[str] = field(default_factory=list)
    # caption content
    caption_content: list[str] = field(default_factory=list)
    error: str | None = None
    # Raw content for JSON export
    raw_response_text: str = ""
    user_content: str = ""
    pending_speech_input: list[dict] | None = None

    @property
    def config_label(self) -> str:
        mode = "stream" if self.stream else "non-stream"
        return f"{self.period_sec}s-{mode}"

    def compute_derived(self):
        self.queue_prefill = self.ttft
        self.decode_total = max(0, self.e2e - self.ttft)
        self.decode_to_speeches = max(0, self.tti - self.ttft)
        self.decode_to_matched_rules = max(0, self.ttr - self.ttft)
        self.decode_to_suggestions = max(0, self.tts - self.ttft)
        self.decode_after_speeches = max(0, self.e2e - self.tti)


# ---------------------------------------------------------------------------
# Core benchmark logic
# ---------------------------------------------------------------------------
async def run_non_stream_benchmark(
    payload: dict, config: OmniConfig
) -> BenchmarkResult:
    """Run non-streaming omni call."""
    r = BenchmarkResult(
        video="", window_idx=0, window_start_sec=0, period_sec=0, stream=False
    )
    t_start = time.monotonic()
    try:
        raw_resp = await call_omni(payload, config)
    except Exception as e:
        r.error = str(e)
        return r

    elapsed = time.monotonic() - t_start
    r.e2e = elapsed
    r.ttft = elapsed  # non-stream: no TTFT, treat as e2e
    r.tti = elapsed

    usage = raw_resp.get("usage", {})
    r.input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
    r.output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))

    # Capture raw response text
    choices = raw_resp.get("choices", [])
    if choices:
        r.raw_response_text = choices[0].get("message", {}).get("content", "")

    omni_output = parse_omni_response(raw_resp)
    r.speeches_count = len(omni_output.speeches)
    r.speeches_content = [i.content for i in omni_output.speeches]
    r.speeches_types = ["✓" if i.needs_response else "-" for i in omni_output.speeches]
    r.speeches_statuses = ["complete" if i.is_complete else "incomplete" for i in omni_output.speeches]
    r.speeches_speakers = [i.speaker for i in omni_output.speeches]
    r.has_command = any(i.needs_response for i in omni_output.speeches)
    r.has_complete_command = any(
        i.needs_response and i.is_complete
        for i in omni_output.speeches
    )
    r.matched_rules_count = len(omni_output.matched_rules)
    r.matched_rules_content = [
        f"{m.rule_id}:{m.reason}" for m in omni_output.matched_rules
    ]
    r.suggestions_count = len(omni_output.suggestions)
    r.suggestions_content = [f"{s.event}:{s.action}" for s in omni_output.suggestions]
    r.caption_content = [f"{e.room_name}:{e.description}" for e in omni_output.caption]

    r.compute_derived()
    return r


async def run_stream_benchmark(payload: dict, config: OmniConfig) -> BenchmarkResult:
    """Run streaming omni call with TTFT and early extraction of all 3 layers."""
    r = BenchmarkResult(
        video="", window_idx=0, window_start_sec=0, period_sec=0, stream=True
    )
    t_start = time.monotonic()
    buffer = ""
    first_token = False
    speeches_extracted = False
    matched_rules_extracted = False
    suggestions_extracted = False

    try:
        async for delta in call_omni_stream(payload, config):
            if not first_token:
                first_token = True
                r.ttft = time.monotonic() - t_start

            buffer += delta

            if (
                speeches_extracted
                and matched_rules_extracted
                and suggestions_extracted
            ):
                continue

            if not speeches_extracted:
                speeches = try_extract_speeches(buffer)
                if speeches is not None:
                    speeches_extracted = True
                    r.tti = time.monotonic() - t_start

            if not matched_rules_extracted:
                matched_rules = try_extract_matched_rules(buffer)
                if matched_rules is not None:
                    matched_rules_extracted = True
                    r.ttr = time.monotonic() - t_start

            if not suggestions_extracted:
                suggestions = try_extract_suggestions(buffer)
                if suggestions is not None:
                    suggestions_extracted = True
                    r.tts = time.monotonic() - t_start
    except Exception as e:
        r.error = str(e)
        return r

    r.e2e = time.monotonic() - t_start

    if not first_token:
        r.ttft = r.e2e
    if not speeches_extracted:
        r.tti = r.e2e
    if not matched_rules_extracted:
        r.ttr = r.e2e
    if not suggestions_extracted:
        r.tts = r.e2e

    r.raw_response_text = buffer
    omni_output = parse_omni_response_from_text(buffer)
    r.speeches_count = len(omni_output.speeches)
    r.speeches_content = [i.content for i in omni_output.speeches]
    r.speeches_types = ["✓" if i.needs_response else "-" for i in omni_output.speeches]
    r.speeches_statuses = ["complete" if i.is_complete else "incomplete" for i in omni_output.speeches]
    r.speeches_speakers = [i.speaker for i in omni_output.speeches]
    r.has_command = any(i.needs_response for i in omni_output.speeches)
    r.has_complete_command = any(
        i.needs_response and i.is_complete
        for i in omni_output.speeches
    )
    r.matched_rules_count = len(omni_output.matched_rules)
    r.matched_rules_content = [
        f"{m.rule_id}:{m.reason}" for m in omni_output.matched_rules
    ]
    r.suggestions_count = len(omni_output.suggestions)
    r.suggestions_content = [f"{s.event}:{s.action}" for s in omni_output.suggestions]
    r.caption_content = [f"{e.room_name}:{e.description}" for e in omni_output.caption]
    r.output_tokens = len(buffer) // 4  # rough estimate

    r.compute_derived()
    return r


# ---------------------------------------------------------------------------
# Window runner
# ---------------------------------------------------------------------------
async def benchmark_window(
    identity_packet: IdentityPacket,
    context: OmniContext,
    config: OmniConfig,
    video_name: str,
    window_idx: int,
    window_start_sec: float,
    period_sec: int,
    stream: bool,
) -> BenchmarkResult:
    if stream:
        payload = build_stream_prompt(identity_packet, context)
        result = await run_stream_benchmark(payload, config)
    else:
        payload = build_prompt(identity_packet, context)
        result = await run_non_stream_benchmark(payload, config)

    result.video = video_name
    result.window_idx = window_idx
    result.window_start_sec = window_start_sec
    result.period_sec = period_sec
    result.stream = stream
    result.user_content = payload.get("user_content", "")
    result.pending_speech_input = context.pending_speech
    return result


# ---------------------------------------------------------------------------
# Video runner
# ---------------------------------------------------------------------------
async def benchmark_video(
    video_path: str,
    periods: list[int],
    run_stream: bool = True,
    run_non_stream: bool = True,
    fps: int = 1,
) -> list[BenchmarkResult]:
    video_name = Path(video_path).stem
    results: list[BenchmarkResult] = []

    omni_config = OmniConfig(
        api_key=os.environ.get("MILOCO_MODEL__OMNI__API_KEY", ""),
        timeout=60.0,
    )

    for period_sec in periods:
        print(f"\n  [{video_name}] 切分 {period_sec}s 窗口...")
        windows = simulate_stream(video_path, fps=fps, period_sec=period_sec)
        print(f"  共 {len(windows)} 个窗口")

        # Maintain per-config persistent context for cross-window continuation
        # (pending_speech). Each config (stream/non-stream) gets
        # its own context so they don't interfere with each other.
        persistent_contexts: dict[str, OmniContext] = {}

        for win_idx, (input_slice, win_start) in enumerate(windows):
            identity_packet = IdentityPacket(
                packet_id=str(uuid.uuid4()),
                room_name="test-room",
                timestamp=input_slice.end_timestamp,
                frame_info=FrameInfo(
                    start_timestamp=input_slice.start_timestamp,
                    end_timestamp=input_slice.end_timestamp,
                    fps=fps,
                ),
                targets=[],
                scene_motion=MotionState.STATIC,
                frames=[],
                all_frames=input_slice.frames,
                audio_clip=input_slice.audio_clip,
                audio_analysis=AudioAnalysis(
                    type=AudioType.SILENCE, is_urgent=False, energy_level=0.0
                ),
                sample_rate=input_slice.sample_rate,
            )

            configs_to_run: list[tuple[bool, str]] = []
            if run_non_stream:
                configs_to_run.append((False, "non-stream"))
            if run_stream:
                configs_to_run.append((True, "stream"))

            for stream, label in configs_to_run:
                # Get or create persistent context for this config
                if label not in persistent_contexts:
                    persistent_contexts[label] = OmniContext()
                context = persistent_contexts[label]
                tag = f"{period_sec}s-{label}"
                ps_note = ""
                if context.pending_speech:
                    ps_note = f" (pending: {', '.join(p['content'] for p in context.pending_speech)})"
                print(
                    f"    窗口 #{win_idx} ({win_start:.1f}s) [{tag}]{ps_note} ...",
                    end=" ",
                    flush=True,
                )

                result = await benchmark_window(
                    identity_packet=identity_packet,
                    context=context,
                    config=omni_config,
                    video_name=video_name,
                    window_idx=win_idx,
                    window_start_sec=win_start,
                    period_sec=period_sec,
                    stream=stream,
                )

                if result.error:
                    print(f"ERROR: {result.error}")
                else:
                    cmd_tag = ""
                    if result.has_complete_command:
                        cmd_tag = " [CMD:complete]"
                    elif result.has_command:
                        cmd_tag = " [CMD:incomplete]"
                    # Show interaction summary
                    int_summary = ""
                    if result.speeches_content:
                        parts = []
                        for tp, ct, st in zip(
                            result.speeches_types,
                            result.speeches_content,
                            result.speeches_statuses,
                        ):
                            parts.append(f"{tp}/{st}:{ct}")
                        int_summary = f"  speeches=[{', '.join(parts[:2])}]"
                    if stream:
                        print(
                            f"e2e={result.e2e:.2f}s  ttft={result.ttft:.2f}s  "
                            f"tti={result.tti:.2f}s  decode={result.decode_total:.2f}s{cmd_tag}{int_summary}"
                        )
                    else:
                        print(
                            f"e2e={result.e2e:.2f}s  tokens={result.output_tokens}{cmd_tag}{int_summary}"
                        )

                results.append(result)

                # Update persistent context for cross-window continuation
                if not result.error:
                    # Carry over incomplete speeches as pending_speech
                    incomplete = [
                        {"speaker": sp, "content": ct}
                        for tp, ct, st, sp in zip(
                            result.speeches_types,
                            result.speeches_content,
                            result.speeches_statuses,
                            result.speeches_speakers,
                        )
                        if st == "incomplete"
                    ]
                    context.pending_speech = incomplete if incomplete else None

                    # Show pending_speech state if set
                    if context.pending_speech:
                        ps_summary = ", ".join(
                            f"{p['content']}" for p in context.pending_speech
                        )
                        print(f"      → pending_speech for next window: [{ps_summary}]")

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def print_video_table(results: list[BenchmarkResult], title: str):
    """Print analysis for one video or overall."""
    print(f"\n{'=' * 95}")
    print(f"  {title}")
    print(f"{'=' * 95}")

    # 1. 总体延迟对比（排除排队）
    configs: dict[str, list[BenchmarkResult]] = {}
    for r in results:
        if r.error is None:
            configs.setdefault(r.config_label, []).append(r)

    print("\n  总体延迟对比（秒）")
    print(
        f"  {'配置':<18} {'E2E':<8} {'排队+PF':<10} {'Decode':<9} {'→TTI':<8} {'→剩余':<8} {'窗口数':<6}"
    )
    print(f"  {'-' * 70}")

    for label in sorted(configs.keys()):
        rs = configs[label]
        print(
            f"  {label:<18} "
            f"{_avg([r.e2e for r in rs]):<8.2f} "
            f"{_avg([r.queue_prefill for r in rs]):<10.2f} "
            f"{_avg([r.decode_total for r in rs]):<9.2f} "
            f"{_avg([r.decode_to_speeches for r in rs]):<8.2f} "
            f"{_avg([r.decode_after_speeches for r in rs]):<8.2f} "
            f"{len(rs):<6}"
        )

    # 2. 流式 vs 非流式对比（纯 decode 部分）
    stream_results = [r for r in results if r.stream and r.error is None]
    if stream_results:
        print("\n  流式三层早提取 Decode 分解（排除排队+prefill，秒）")
        print(
            f"  {'配置':<18} {'Decode总':<9} {'→interact':<10} {'→rules':<9} {'→suggest':<10} {'→env完成':<9} {'interact节省'}"
        )
        print(f"  {'-' * 80}")

        for label in sorted(set(r.config_label for r in stream_results)):
            rs = [r for r in stream_results if r.config_label == label]
            decode = _avg([r.decode_total for r in rs])
            to_int = _avg([r.decode_to_speeches for r in rs])
            to_rules = _avg([r.decode_to_matched_rules for r in rs])
            to_sugg = _avg([r.decode_to_suggestions for r in rs])
            after = _avg([r.decode_after_speeches for r in rs])
            pct = (after / decode * 100) if decode > 0 else 0
            print(
                f"  {label:<18} {decode:<9.2f} {to_int:<10.2f} {to_rules:<9.2f} {to_sugg:<10.2f} {after:<9.2f} {pct:.0f}%"
            )

    # 3. Command 指令响应分析
    cmd_results = [r for r in results if r.has_command and r.error is None]
    if cmd_results:
        print("\n  Command 指令响应时间（秒）")
        print(
            f"  {'视频':<12} {'窗口':<8} {'配置':<18} {'E2E':<8} {'排队+PF':<10} {'→CMD可用':<10} {'status':<12} {'指令内容'}"
        )
        print(f"  {'-' * 95}")

        for r in cmd_results:
            cmd_avail = r.tti if r.stream else r.e2e
            # Build content with status for each command interaction
            cmd_details = []
            for j, (tp, ct, st) in enumerate(
                zip(
                    r.speeches_types,
                    r.speeches_content,
                    r.speeches_statuses,
                )
            ):
                if tp.lower() == "command":
                    cmd_details.append(f"{ct}({st})")
            content = (
                ", ".join(cmd_details[:3])
                if cmd_details
                else ", ".join(r.speeches_content[:2])
            )
            status_summary = "complete" if r.has_complete_command else "incomplete"
            print(
                f"  {r.video[:11]:<12} #{r.window_idx:<6} {r.config_label:<18} "
                f"{r.e2e:<8.2f} {r.queue_prefill:<10.2f} {cmd_avail:<10.2f} {status_summary:<12} {content}"
            )

        # Command 指令汇总
        print("\n  Command 指令平均响应时间（秒）")
        cmd_by_config: dict[str, list[BenchmarkResult]] = {}
        for r in cmd_results:
            cmd_by_config.setdefault(r.config_label, []).append(r)

        print(
            f"  {'配置':<18} {'Avg E2E':<10} {'Avg CMD可用':<13} {'Avg 排队+PF':<13} {'Avg 纯Decode→CMD':<16} {'数量'}"
        )
        print(f"  {'-' * 72}")
        for label in sorted(cmd_by_config.keys()):
            rs = cmd_by_config[label]
            avg_e2e = _avg([r.e2e for r in rs])
            avg_cmd = _avg([r.tti if r.stream else r.e2e for r in rs])
            avg_qp = _avg([r.queue_prefill for r in rs])
            avg_decode_cmd = _avg([r.decode_to_speeches for r in rs])
            print(
                f"  {label:<18} {avg_e2e:<10.2f} {avg_cmd:<13.2f} {avg_qp:<13.2f} {avg_decode_cmd:<16.2f} {len(rs)}"
            )

    # 4. 每窗口详细
    print("\n  每窗口详细（秒）")
    print(
        f"  {'视频':<10} {'#':<4} {'配置':<18} {'E2E':<7} {'TTFT':<7} {'TTI':<7} {'TTR':<7} {'TTS':<7} {'Decode':<7} {'CMD':<5} {'speeches'}"
    )
    print(f"  {'-' * 115}")

    for r in results:
        if r.error:
            print(
                f"  {r.video[:9]:<10} {r.window_idx:<4} {r.config_label:<18} ERROR: {r.error[:30]}"
            )
        else:
            cmd = "Y" if r.has_complete_command else ("y" if r.has_command else "")
            # Build detailed speeches string: type/status/content
            if r.speeches_content:
                int_details = []
                for tp, ct, st in zip(
                    r.speeches_types,
                    r.speeches_content,
                    r.speeches_statuses,
                ):
                    int_details.append(f"{tp}/{st}: {ct}")
                utt_str = " | ".join(int_details[:3])
            else:
                utt_str = "-"
            ttft_s = f"{r.ttft:.2f}" if r.stream else "-"
            tti_s = f"{r.tti:.2f}" if r.stream else "-"
            ttr_s = f"{r.ttr:.2f}" if r.stream else "-"
            tts_s = f"{r.tts:.2f}" if r.stream else "-"
            decode_s = f"{r.decode_total:.2f}" if r.stream else "-"
            print(
                f"  {r.video[:9]:<10} {r.window_idx:<4} {r.config_label:<18} "
                f"{r.e2e:<7.2f} {ttft_s:<7} {tti_s:<7} {ttr_s:<7} {tts_s:<7} {decode_s:<7} {cmd:<5} {utt_str}"
            )

    # 5. 流式 vs 非流式输出内容对比
    print("\n  流式 vs 非流式输出内容对比")
    print(f"  {'-' * 115}")
    # Group by (video, window_idx)
    from collections import defaultdict

    window_groups: dict[tuple[str, int], dict[str, BenchmarkResult]] = defaultdict(dict)
    for r in results:
        if r.error is None:
            mode = "stream" if r.stream else "non-stream"
            window_groups[(r.video, r.window_idx)][mode] = r

    for (video, win_idx), modes in sorted(window_groups.items()):
        ns = modes.get("non-stream")
        st = modes.get("stream")
        if not ns or not st:
            continue
        print(f"\n  [{video}] 窗口 #{win_idx}")
        # caption
        ns_env = " | ".join(ns.caption_content) if ns.caption_content else "[]"
        st_env = " | ".join(st.caption_content) if st.caption_content else "[]"
        env_match = "✓" if ns_env == st_env else "✗"
        print(f"    caption {env_match}:")
        print(f"      non-stream: {ns_env}")
        print(f"      stream:     {st_env}")
        # speeches
        ns_int = (
            " | ".join(
                f"{t}/{s}:{c}"
                for t, c, s in zip(
                    ns.speeches_types,
                    ns.speeches_content,
                    ns.speeches_statuses,
                )
            )
            if ns.speeches_content
            else "[]"
        )
        st_int = (
            " | ".join(
                f"{t}/{s}:{c}"
                for t, c, s in zip(
                    st.speeches_types,
                    st.speeches_content,
                    st.speeches_statuses,
                )
            )
            if st.speeches_content
            else "[]"
        )
        int_match = "✓" if ns_int == st_int else "✗"
        print(f"    speeches  {int_match}:")
        print(f"      non-stream: {ns_int}")
        print(f"      stream:     {st_int}")
        # matched_rules
        ns_rules = (
            " | ".join(ns.matched_rules_content) if ns.matched_rules_content else "[]"
        )
        st_rules = (
            " | ".join(st.matched_rules_content) if st.matched_rules_content else "[]"
        )
        rules_match = "✓" if ns_rules == st_rules else "✗"
        print(f"    matched_rules {rules_match}:")
        print(f"      non-stream: {ns_rules}")
        print(f"      stream:     {st_rules}")
        # suggestions
        ns_sugg = " | ".join(ns.suggestions_content) if ns.suggestions_content else "[]"
        st_sugg = " | ".join(st.suggestions_content) if st.suggestions_content else "[]"
        sugg_match = "✓" if ns_sugg == st_sugg else "✗"
        print(f"    suggestions   {sugg_match}:")
        print(f"      non-stream: {ns_sugg}")
        print(f"      stream:     {st_sugg}")


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------
def _result_to_dict(r: BenchmarkResult) -> dict:
    """Convert a BenchmarkResult to a JSON-serializable dict."""
    return {
        "video": r.video,
        "window_idx": r.window_idx,
        "window_start_sec": round(r.window_start_sec, 1),
        "period_sec": r.period_sec,
        "mode": "stream" if r.stream else "non-stream",
        "config_label": r.config_label,
        "timing": {
            "e2e": round(r.e2e, 3),
            "ttft": round(r.ttft, 3),
            "tti": round(r.tti, 3),
            "ttr": round(r.ttr, 3),
            "tts": round(r.tts, 3),
            "queue_prefill": round(r.queue_prefill, 3),
            "decode_total": round(r.decode_total, 3),
            "decode_to_speeches": round(r.decode_to_speeches, 3),
            "decode_to_matched_rules": round(r.decode_to_matched_rules, 3),
            "decode_to_suggestions": round(r.decode_to_suggestions, 3),
            "decode_after_speeches": round(r.decode_after_speeches, 3),
        },
        "tokens": {
            "input": r.input_tokens,
            "output": r.output_tokens,
        },
        "speeches": [
            {
                "type": tp,
                "content": ct,
                "status": st,
                "speaker": sp,
            }
            for tp, ct, st, sp in zip(
                r.speeches_types,
                r.speeches_content,
                r.speeches_statuses,
                r.speeches_speakers,
            )
        ],
        "has_command": r.has_command,
        "has_complete_command": r.has_complete_command,
        "matched_rules": r.matched_rules_content,
        "suggestions": r.suggestions_content,
        "caption": r.caption_content,
        "pending_speech_input": r.pending_speech_input,
        "user_content": r.user_content,
        "raw_response": r.raw_response_text,
        "error": r.error,
    }


def export_results_json(results: list[BenchmarkResult], output_path: str):
    """Export all results to a JSON file, grouped by mode (stream/non-stream)."""
    stream_results = [_result_to_dict(r) for r in results if r.stream]
    non_stream_results = [_result_to_dict(r) for r in results if not r.stream]

    data = {
        "stream": stream_results,
        "non_stream": non_stream_results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  📄 JSON 导出: {output_path}")
    print(
        f"     stream: {len(stream_results)} 条, non_stream: {len(non_stream_results)} 条"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="流式 vs 非流式 Benchmark")
    parser.add_argument("path", help="视频文件或目录路径")
    parser.add_argument("--periods", default="3,5", help="窗口大小列表 (默认 3,5)")
    parser.add_argument("--fps", type=int, default=1, help="采样 FPS (默认 1)")
    parser.add_argument("--stream-only", action="store_true", help="只跑流式")
    parser.add_argument("--non-stream-only", action="store_true", help="只跑非流式")
    parser.add_argument(
        "--json-output", type=str, default=None, help="导出每次调用详情到 JSON 文件"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    periods = [int(p) for p in args.periods.split(",")]
    run_stream = not args.non_stream_only
    run_non_stream = not args.stream_only

    path = Path(args.path)
    if path.is_dir():
        videos = sorted(str(f) for f in path.glob("*.mp4"))
    elif path.is_file():
        videos = [str(path)]
    else:
        print(f"[ERROR] 路径不存在: {path}")
        return

    if not videos:
        print(f"[ERROR] 未找到 mp4 文件: {path}")
        return

    api_key = os.environ.get("MILOCO_MODEL__OMNI__API_KEY", "")
    if not api_key:
        print("[ERROR] MILOCO_MODEL__OMNI__API_KEY 未设置")
        return

    print("\n  流式 vs 非流式 Benchmark（排除排队）")
    print(f"  {'=' * 50}")
    print(f"  视频: {len(videos)} 个")
    print(f"  窗口大小: {periods}")
    print(f"  FPS: {args.fps}")
    print(
        f"  模式: {'stream' if args.stream_only else 'non-stream' if args.non_stream_only else 'both'}"
    )

    all_results: list[BenchmarkResult] = []

    for video_path in videos:
        video_name = Path(video_path).stem
        print(f"\n{'#' * 70}")
        print(f"  视频: {video_name}")
        print(f"{'#' * 70}")

        results = await benchmark_video(
            video_path,
            periods=periods,
            run_stream=run_stream,
            run_non_stream=run_non_stream,
            fps=args.fps,
        )
        all_results.extend(results)

        # Per-video table
        print_video_table(results, f"分析: {video_name}")

    # Cross-video summary
    if len(videos) > 1:
        print_video_table(all_results, "跨视频汇总")

    # JSON export
    json_out = args.json_output
    if json_out is None:
        # Auto-generate default path
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_out = f"/tmp/benchmark_{ts}.json"

    export_results_json(all_results, json_out)


if __name__ == "__main__":
    asyncio.run(main())
