"""注册图片筛选算法 — v4 全景图第 2 个黄色块。

从用户确认的 cluster 全量候选(已 §7 抽取算法打完分降序排列)选出 topk 张
"高分 + 彼此差异化"样本入身份库,不是简单挑最高分前 N 张。

筛选维度(v4 §4.1):
    主选 · pHash 指纹距离 ≥ 28   视觉差异(避免几乎重复的帧),复用 TierC G 兜底阈值
    备选 · ReID 特征相似度 < 0.9  语义/姿态差异(同人不同姿态时比 pHash 更稳)
    时间间隔 · ≥ 1 秒           时序差异(1 fps 主流程下即相邻帧)

主路径走 pHash + 时间间隔(与);pHash 拒了过多导致凑不齐 topk 时,**回退 ReID
阈值**再筛一次("同人不同姿态"在 ReID 下更宽容)。

输出 ``SelectionResult``:含 status 状态码 + 入选样本 + 拒绝原因列表;
status 直接对接 v4 §4.2 agent 反馈话术表。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from miloco.perception.engine.identity._image_utils import hamming as _hamming
from miloco.perception.engine.identity.extractor import ScoredCandidate

logger = logging.getLogger(__name__)


# =============================================================================
# 阈值常量(代码默认,本期不暴露 yaml;v4 §4.1)
# =============================================================================

DEFAULT_TOPK = 3
DEFAULT_MIN_K = 1
DEFAULT_PHASH_DISTANCE_MIN = 28          # 复用 TierC G 兜底阈值
DEFAULT_TIME_GAP_SEC_MIN = 1.0           # 1 fps 下即相邻帧
DEFAULT_REID_SIM_MAX = 0.9               # 备选回退,同人不同姿态在 ReID 下更宽容


# =============================================================================
# 数据结构
# =============================================================================


SelectionStatus = Literal[
    "ok",                       # topk 已选齐
    "weak_diversity",           # 选不到 topk 但 ≥ min_k
    "no_valid_subject",         # 候选 0 张
    "ambiguous_multiperson",    # 多人歧义(本算法不直接产出,留给上层 §3)
    "decode_failed",            # 视频 / 图像解码失败(本算法不直接产出)
]


@dataclass
class SelectionResult:
    """筛选输出。

    ``status`` 与 v4 §4.2 反馈话术表直接对应,上层 agent / web 据此渲染。
    ``rejected`` 记录每张被拒候选 + 原因,debug 用。
    """

    samples: list[ScoredCandidate] = field(default_factory=list)
    status: SelectionStatus = "no_valid_subject"
    rejected: list[tuple[ScoredCandidate, str]] = field(default_factory=list)


# =============================================================================
# pHash 汉明距离 — 实现在 _image_utils.py(已在顶部 import)
# =============================================================================


# =============================================================================
# ReID 余弦相似度(两侧默认 L2-normalized)
# =============================================================================


def _cosine(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    dot = float(np.dot(a, b))
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if abs(na - 1.0) < 1e-3 and abs(nb - 1.0) < 1e-3:
        return dot
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


# =============================================================================
# 主算法
# =============================================================================


def select_topk(
    candidates: list[ScoredCandidate],
    *,
    topk: int = DEFAULT_TOPK,
    min_k: int = DEFAULT_MIN_K,
    phash_distance_min: int = DEFAULT_PHASH_DISTANCE_MIN,
    time_gap_sec_min: float = DEFAULT_TIME_GAP_SEC_MIN,
    reid_sim_max: float = DEFAULT_REID_SIM_MAX,
    skip_phash_dedup: bool = False,
    preseeded: list[ScoredCandidate] | None = None,
    ensure_topk: bool = False,
) -> SelectionResult:
    """选 topk 张"高分 + 彼此差异化"样本。

    主路径:按 ``candidates`` 的既有顺序遍历,与已入选样本检查 pHash 距离 +
    时间差;都过则入选,任一不过则记入 rejected。顺序由调用方决定——单图 / 陌生人
    池路径按 score 降序传入,extract_samples 视频路径则按帧时间序传入(未做全局
    score 排序),因此"高分优先"仅在调用方已排序时成立。

    备路径:主路径选不齐 topk 但 ≥ min_k 时,**回退 ReID 阈值**再扫被拒候选,
    用余弦 < reid_sim_max(0.9)二次入选。同人不同姿态在 ReID 下比 pHash 更宽容,
    弥补 pHash 过严的漏选。

    Args:
        skip_phash_dedup: True 时主路径跳过 pHash hamming 检查,只保留时间间隔
            +(备路径)ReID 余弦判定。专给"用户多图批量"路径用——用户手挑的图
            场景接近时 pHash 经常 < 28 导致 4 张被收敛到 1,违反用户预期。
            视频帧 / 陌生人池路径保持默认 False(那两条天然冗余高,需 pHash 去重)。
        preseeded: 调用方预先决定的"必入选"样本列表。这些样本无条件进 selected,
            主路径扫剩余 candidates 时跟它们做 pHash/time 互检差异化。给"种子选取
            策略"(如 select_topk_with_frontal_seed 的正脸 seed)用,避免 helper
            自己模拟 _check_against_selected 逻辑导致漂移。
            None 时行为完全等同现状。注:preseeded 里的 cand 仍要按 score 顺序排,
            主路径用 ``s is cand`` identity 跳过避免重复入选。
        ensure_topk: True 时,在主路径 + ReID 备路径都跑完后若 len(selected) < topk,
            **从 rejected 按 score 顺序补足到 topk**(不再 dedup)。给"单人注册视频"
            场景兜底:同人 ReID 必然 >= 0.9 + 同人同衣 pHash 经常 < 28,两条 dedup
            一起把 selected 卡得只剩 1-2 张。需要保证 topk 张样本数时打开。
            False(默认)保留"差异化优先,凑不齐就 weak_diversity"语义。
            注:ensure_topk 兜底入选的 cand 不再过滤,status 仍按差异化阶段计算
            (差异化不够时 status='weak_diversity' 但 selected 已被补满)。
    """
    if not candidates and not (preseeded or []):
        return SelectionResult(status="no_valid_subject")

    # 主路径:pHash + 时间间隔(skip_phash_dedup=True 时跳过 pHash)
    # preseeded 直接进 selected, 主路径扫剩余 candidates 时跟它们互检
    selected: list[ScoredCandidate] = list(preseeded or [])
    rejected: list[tuple[ScoredCandidate, str]] = []
    effective_phash_min = 0 if skip_phash_dedup else phash_distance_min
    for cand in candidates:
        if len(selected) >= topk:
            # 已够 topk,剩余的视为"未入选"不算 rejected
            break
        # preseeded 的 cand 可能同时出现在 candidates 里, identity 跳过避免重复
        if any(s is cand for s in selected):
            continue
        reason = _check_against_selected(
            cand, selected,
            phash_distance_min=effective_phash_min,
            time_gap_sec_min=time_gap_sec_min,
        )
        if reason is None:
            selected.append(cand)
        else:
            rejected.append((cand, reason))

    # 主路径选齐 → ok
    if len(selected) >= topk:
        return SelectionResult(samples=selected, status="ok", rejected=rejected)

    # 主路径不齐 → 备路径:回退 ReID 阈值再扫 rejected
    # 注:只有 rejected 候选带 reid_embedding 才有意义
    if (
        len(selected) < topk
        and any(r[0].reid_embedding is not None for r in rejected)
    ):
        remaining_rejected: list[tuple[ScoredCandidate, str]] = []
        for cand, orig_reason in rejected:
            if len(selected) >= topk or cand.reid_embedding is None:
                remaining_rejected.append((cand, orig_reason))
                continue
            # ReID 维度:跟已入选样本余弦 < reid_sim_max 才视为"姿态差异足够"
            ok_reid = True
            for s in selected:
                if s.reid_embedding is None:
                    continue
                sim = _cosine(cand.reid_embedding, s.reid_embedding)
                if sim >= reid_sim_max:
                    ok_reid = False
                    break
            # 仍要满足时间间隔(防同一秒重复)
            ok_time = all(
                abs(cand.captured_at - s.captured_at) >= time_gap_sec_min
                for s in selected
            )
            if ok_reid and ok_time:
                selected.append(cand)
                logger.debug("ReID 备路径补选 1 张 score=%.3f", cand.score)
            else:
                remaining_rejected.append((cand, "reid_backup_failed"))
        rejected = remaining_rejected

    # 状态判定(基于差异化阶段的 selected 数量, ensure_topk 兜底不改 status)
    if len(selected) >= topk:
        status: SelectionStatus = "ok"
    elif len(selected) >= min_k:
        status = "weak_diversity"
    else:
        status = "no_valid_subject"

    # ensure_topk 兜底: 差异化不够 topk 时按 rejected score 顺序无条件补满
    # rejected 是主路径按 candidates score 降序遍历时追加的, 自身已是 score 降序
    if ensure_topk and len(selected) < topk:
        for cand, _ in rejected:
            if len(selected) >= topk:
                break
            if any(s is cand for s in selected):
                continue
            selected.append(cand)

    return SelectionResult(samples=selected, status=status, rejected=rejected)


def _check_against_selected(
    cand: ScoredCandidate,
    selected: list[ScoredCandidate],
    *,
    phash_distance_min: int,
    time_gap_sec_min: float,
) -> str | None:
    """主路径筛选:检查 cand 与已入选样本的 pHash + 时间差。返回拒绝原因,通过返 None。"""
    for s in selected:
        if _hamming(cand.phash, s.phash) < phash_distance_min:
            return "phash_too_close"
        if abs(cand.captured_at - s.captured_at) < time_gap_sec_min:
            return "time_gap_too_short"
    return None


# =============================================================================
# 视频附件注册路径专用: 正脸优先 + face cand 优先 + 选满 topk 三件套
# =============================================================================

# face bbox 宽/高 ∈ [DEFAULT_FRONTAL_WH_MIN, DEFAULT_FRONTAL_WH_MAX) 视为"正脸候选":
# 下限 0.70 排除侧脸 (w/h < 0.65 是大侧脸, 0.65-0.70 是半侧脸, 不算"端正正脸");
# 上限 0.80 排除"抬头瞬间"屠榜 (转头到顶时 sharpness 飙升但 face 是仰视, 不适合
# 当注册首图主脸样本)。详细分布验证见 .wsh_cc 下 sim 4 个视频实测。
DEFAULT_FRONTAL_WH_MIN = 0.70
DEFAULT_FRONTAL_WH_MAX = 0.80


def _face_wh_ratio(c: ScoredCandidate) -> float:
    """face_crop bbox 宽/高比。无 face_crop 返 0.0。"""
    if c.face_crop is None:
        return 0.0
    h, w = c.face_crop.shape[:2]
    return float(w) / max(1, h)


def _same_frame_face_wh_ratio(c: ScoredCandidate) -> float:
    """同帧 face crop (body 那一帧关联到的 face_det) 的宽/高比。

    用于 select_topk_with_frontal_seed 判 frontal seed: video 路径 cand.face_crop
    可能是 extract_from_video 末尾跨帧分发后**借自其他帧最锐的 face**, 用它判
    "body 那一帧朝向"会失真; 用 same_frame_face_crop 直接看 body 帧的脸朝向。
    image / pool 路径 same_frame_face_crop 为 None (没经过跨帧分发), 退回看
    face_crop 本身。
    """
    sf = getattr(c, "same_frame_face_crop", None)
    if sf is None:
        # 没记同帧 face (image / pool 路径) → 退回看 face_crop 本身
        # (这两条路径的 face_crop 就是同帧, 不存在被跨帧覆盖的情况)
        return _face_wh_ratio(c)
    h, w = sf.shape[:2]
    return float(w) / max(1, h)


# V_combined ReID-driven farthest-first 阈值 (跟 select_topk reid_sim_max=0.9 同一个 ReID
# 余弦量纲, 但本块比 0.9 严一档到 0.85): cand 跟已选集合的最大余弦 < 0.85 才算"差异化够",
# 否则进放宽阶段取最远点。0.85 是 sim 实测在 4 个视频上让 body / face 都明显拉开的阈值;
# 取更高 (0.90) 会让 farthest-first 几乎都走"严阈值通过"路径退化为按 score 选, 取更低
# (0.80) 严阈值常常零命中, 大量样本走放宽路径。
DEFAULT_V_COMBINED_SIM_THRESHOLD = 0.85


def select_topk_with_frontal_seed(
    candidates: list[ScoredCandidate],
    *,
    topk: int = DEFAULT_TOPK,
    frontal_wh_min: float = DEFAULT_FRONTAL_WH_MIN,
    frontal_wh_max: float = DEFAULT_FRONTAL_WH_MAX,
    reid_extractor: "Any | None" = None,
    body_sim_threshold: float = DEFAULT_V_COMBINED_SIM_THRESHOLD,
    face_sim_threshold: float = DEFAULT_V_COMBINED_SIM_THRESHOLD,
    **select_topk_kwargs,
) -> SelectionResult:
    """视频附件注册路径专用:正脸优先 + face cand 优先 + 选满 topk。

    解决 ``select_topk`` 在"单人 × 短时段 × 同摄像头"场景下的 3 个问题:

    1. **侧脸 / 抬头屠榜 score 排序**:转头到极限位置时 motion blur 最低、
       sharpness 飙升 → score 公式被 sharpness 主导 → 选出来 top-3 全是
       侧脸 / 抬头, 看不到端正正脸。
       → 解法: 在 ``face_w/h ∈ [frontal_wh_min, frontal_wh_max)`` 区间里
         选 score 最高那张 **强制种子入选 #1**, 保证主图一定是正脸。
         w/h < 0.70 是侧脸、w/h >= 0.80 是抬头, 中间区间是端正正脸 + 轻微低头。

    2. **无脸 body 抢有脸样本名额**:select_topk 主路径按 score 降序扫全集,
       无脸 body 跟有脸 cand 的 pHash 距离往往更大 (背身 vs 正脸轮廓差异大),
       反而比有脸 cand 更容易通过 dedup, 挤掉真正"有 face_id 价值"的样本。
       → 解法: 只在 ``face_cands = [c for c in candidates if c.face_crop is
         not None]`` 集合上跑 select_topk。face_cands < topk 时**不**用无脸
         cand 兜底, 直接返回 face_cands 数量 + status='weak_diversity' 让
         前端给出"质量警告"。face_cands == 0 时返 'no_valid_subject'。

    3. **同人 dedup 阈值过严选不满 topk**:pHash >= 28 / ReID < 0.9 是给陌生人池
       场景定的, 单人注册视频里同人 cand 必然 pHash < 28 且 ReID >= 0.9, 主路径
       和 ReID 备路径双双卡死, selected 经常只有 1-2 张, 用户挑号样本不够。
       → 解法: ``select_topk(ensure_topk=True)`` 在 dedup 跑完仍 < topk 时,
         按 score 顺序从 rejected 补足到 topk(不再 dedup)。"差异化优先,
         不够再放宽"。

    Args:
        candidates: 已按 score 降序的候选列表。
        topk: 目标样本数。
        frontal_wh_min/frontal_wh_max: 正脸 face_w/h 区间。默认 [0.70, 0.80),
            实测 4 个视频 端正正脸都落这。
        reid_extractor: HumanReID 实例 (或任何提供 ``extract_feature(crop) ->
            ndarray[128]``)。**给了就启用 V_combined 路径** (body ReID-driven +
            face 独立 ReID-driven, 见下"V_combined 路径"), **None 走当前 V0 路径**
            (select_topk + ensure_topk 兜底)。视频附件注册路径透传, 其他路径
            (image / pool) 传 None。
        body_sim_threshold / face_sim_threshold: V_combined 路径下 farthest-first
            的严阈值 (cand 跟已选集合最大余弦 < 阈值才算差异化合格)。两阶段独立。
            默认 0.85, 跟 sim 在 4 个视频上验证一致。
        **select_topk_kwargs: 透传给 select_topk 的其余参数 (min_k /
            phash_distance_min / time_gap_sec_min / reid_sim_max / skip_phash_dedup)。
            不要传 ``preseeded`` / ``ensure_topk``, 由本函数内部控制。
            V_combined 路径 (reid_extractor 不为 None) 不读取这些参数。

    V_combined 路径 (reid_extractor 给定时):
      1. body 选样: body emb (DeepSORT 关联阶段算好的, cand.reid_embedding)
         farthest-first 选 ``topk`` 个 cand, 严阈值 ``body_sim_threshold``,
         不达放宽到最远点。base = V6b frontal seed (其 face_crop 覆盖为同帧)。
      2. face 选样: 把每个 cand 的 ``same_frame_face_crop`` 喂 ``reid_extractor``
         抽 128-dim "face 视觉外观 emb" (用 body ReID 模型抽 face crop, 实测
         有区分度, 不是严格 face identity), 再按 face emb farthest-first 选
         ``topk`` 张, base = seed.same_frame_face_crop (正脸硬约束)。
      3. face 重分配回 body cand: body_picks[i].face_crop = face_picks[i].
         same_frame_face_crop。结果: #0 body+face 同帧正脸; #1-#4 body 来自
         body ReID 选定帧, face 来自 face ReID 选定帧 (可能跨帧)。
      解决 V_reid 单 ReID 让 face 多样性退化 (sim 实测 mean cos > 0.90, 等于
      5 张 face 几乎相同) 的问题。代价: ``topk`` 张 face crop 现场抽 emb 推理
      (~5-10ms/张, 总开销 ~50ms, 注册路径非热路径可接受)。

    Returns:
        ``SelectionResult``:
          - face_cands >= topk: 选满 topk 张 face cand (含 1 张 frontal seed,
            其余按 select_topk 差异化逻辑选; ensure_topk 兜底防"全被 dedup 拒")
          - 0 < face_cands < topk: 返 face_cands 数量, status 取决于差异化结果
            —— 默认 min_k=1 时为 'weak_diversity'; 调用方透传 min_k>1 且差异化
            后 selected < min_k 时, select_topk 会返 'no_valid_subject'
            (video 路径不传 min_k, 默认 1, 不触发)
          - face_cands == 0: status='no_valid_subject' (face 检测全失败,
            注册视频质量不达标, 不用无脸 body 兜底)
    """
    face_cands = [c for c in candidates if c.face_crop is not None]

    # face 检测全 fail → 不用无脸 body 凑数, 直接报告"无效"
    # (用户视频注册场景: 没人脸的样本对 face_id 识别无用, 重拍)
    if not face_cands:
        return SelectionResult(status="no_valid_subject")

    # face_cands 内部找 frontal seed (同帧 face_w/h ∈ [min, max) 区间 score 最高)
    # 关键: 用 _same_frame_face_wh_ratio (而非 _face_wh_ratio) — video 路径 cand.face_crop
    # 是 extract_from_video 末尾跨帧分发借来的最锐 face, 它的 w/h 反映的是"借来那张
    # 的朝向", 不一定跟 body frame 同朝向; 这里要按 body 帧自己关联到的同帧 face
    # 判 frontal, 保证 seed.body 跟"算法判定为正脸"的同帧 face 朝向一致 (即用户诉求:
    # body 中至少有一个跟正脸 face 同瞬间的样本)。
    frontal = [c for c in face_cands
               if frontal_wh_min <= _same_frame_face_wh_ratio(c) < frontal_wh_max]
    seed: ScoredCandidate | None = None
    if frontal:
        seed = max(frontal, key=lambda c: c.score)
        # video 路径 seed 选定后, 把 face_crop 覆盖回同帧 face_crop, 让号码图首位
        # cand 的 body / face 来自同一帧 → 朝向一致 (用户诉求"正脸 face 对应正脸 body")。
        # image / pool 路径 same_frame_face_crop 为 None, 不覆盖, 保持原 face_crop。
        sf = getattr(seed, "same_frame_face_crop", None)
        if sf is not None:
            seed.face_crop = sf

    # ============================================================
    # V_combined 路径 (reid_extractor 给定 = video 附件注册路径)
    # ============================================================
    if reid_extractor is not None:
        return _select_v_combined(
            face_cands, seed,
            topk=topk,
            reid_extractor=reid_extractor,
            body_sim_threshold=body_sim_threshold,
            face_sim_threshold=face_sim_threshold,
        )

    # ============================================================
    # V0 路径 (默认, image / pool 走这条)
    # ============================================================
    preseeded = [seed] if seed is not None else None
    # 只在 face_cands 上跑 select_topk, ensure_topk=True 保证内部凑满
    # 不用 candidates 全集 → 无脸 body 不参与, 不会抢有脸名额
    return select_topk(
        face_cands,
        topk=topk,
        preseeded=preseeded,
        ensure_topk=True,
        **select_topk_kwargs,
    )


def _max_sim_to_selected(
    cand_emb: "NDArray[np.float32]",
    selected: list[ScoredCandidate],
    cand_to_emb: dict[int, "NDArray[np.float32] | None"],
) -> float:
    """cand_emb 跟 selected 中所有有 emb 成员的最大余弦。

    selected 全无 emb → 0.0 (= 跟空集距离最远)。default=0.0 兼防 selected 全
    None emb 时空 generator 抛 ValueError —— 当前调用方保证 seed 有 emb, 实际
    触发概率近 0, 但未来若传入 emb=None 的 seed, 兜底为 0.0 让 farthest-first
    正常选远点而不是异常。
    """
    return max(
        (_cosine(cand_emb, s_emb)
         for s in selected
         if (s_emb := cand_to_emb.get(id(s))) is not None),
        default=0.0,
    )


def _farthest_first_pick(
    cands: list[ScoredCandidate],
    *,
    topk: int,
    sim_threshold: float,
    seed: ScoredCandidate,
    cand_to_emb: dict[int, "NDArray[np.float32] | None"],
) -> list[ScoredCandidate]:
    """ReID-driven farthest-first 选 topk 个 cand, base = seed。

    阶段 1 (严阈值): 按 cand.score 降序扫剩余, 取第一个跟已选集合余弦最大值
    < sim_threshold 的 cand。差异化"够远"就接受。
    阶段 2 (放宽到最远点): 严阈值全拒 → 选「跟 selected 余弦最大值最小」的 cand
    (k-center 启发式的最远点)。

    cand_to_emb: id(cand) → emb 映射, None 表示该 cand 无 emb 不参与 farthest-first。
    seed 必须有 emb (调用方保证 / 兜底降级)。
    """
    selected: list[ScoredCandidate] = [seed]
    selected_ids = {id(seed)}
    score_desc = sorted(cands, key=lambda c: c.score, reverse=True)
    while len(selected) < topk:
        # 阶段 1: 严阈值
        chosen: ScoredCandidate | None = None
        for cand in score_desc:
            if id(cand) in selected_ids:
                continue
            cand_emb = cand_to_emb.get(id(cand))
            if cand_emb is None:
                continue
            if _max_sim_to_selected(cand_emb, selected, cand_to_emb) < sim_threshold:
                chosen = cand
                break
        if chosen is not None:
            selected.append(chosen)
            selected_ids.add(id(chosen))
            continue
        # 阶段 2: 放宽 — 最远点
        remaining = [
            c for c in score_desc
            if id(c) not in selected_ids and cand_to_emb.get(id(c)) is not None
        ]
        if not remaining:
            # emb 都没了, fallback 按 score 取剩余
            for c in score_desc:
                if len(selected) >= topk:
                    break
                if id(c) not in selected_ids:
                    selected.append(c)
                    selected_ids.add(id(c))
            break
        # 最远点 = 跟已选集合最大余弦最小的那个 (k-center 启发式)
        chosen = min(
            remaining,
            key=lambda c: _max_sim_to_selected(cand_to_emb[id(c)], selected, cand_to_emb),
        )
        selected.append(chosen)
        selected_ids.add(id(chosen))
    return selected[:topk]


def _select_v_combined(
    face_cands: list[ScoredCandidate],
    seed: "ScoredCandidate | None",
    *,
    topk: int,
    reid_extractor: "Any",
    body_sim_threshold: float,
    face_sim_threshold: float,
) -> SelectionResult:
    """V_combined: body 选 cand (按 body ReID emb farthest-first) + face 重分配
    (按 face emb farthest-first), 首位 face/body 同帧正脸。

    详见 ``select_topk_with_frontal_seed`` docstring 的 "V_combined 路径" 段。
    """
    # 阶段 1: body 选样 — body ReID emb farthest-first
    # 无 frontal seed (face_w/h 全部在 [0.70, 0.80) 之外, 罕见) → 退化用 score 最高
    base_body = seed if seed is not None else max(face_cands, key=lambda c: c.score)
    body_emb_map = {id(c): c.reid_embedding for c in face_cands}
    # base_body 必须有 emb 才能跑 farthest-first; 若没 (DeepSORT fast mode 偶发) → 降级
    # 退回 V0: 把 base_body 当 preseed 给 select_topk
    if body_emb_map.get(id(base_body)) is None:
        return select_topk(
            face_cands,
            topk=topk,
            preseeded=[base_body] if base_body is not None else None,
            ensure_topk=True,
        )
    body_picks = _farthest_first_pick(
        face_cands,
        topk=topk,
        sim_threshold=body_sim_threshold,
        seed=base_body,
        cand_to_emb=body_emb_map,
    )

    # 阶段 2: 抽 face emb — 用 reid_extractor 在 same_frame_face_crop 上抽 128-dim
    # (body ReID 模型应用在 face crop, 实测有区分度, 见 docstring)
    face_emb_map: dict[int, "NDArray[np.float32] | None"] = {}
    for c in face_cands:
        sf = getattr(c, "same_frame_face_crop", None)
        if sf is None:
            face_emb_map[id(c)] = None
            continue
        try:
            face_emb_map[id(c)] = reid_extractor.extract_feature(sf)
        except Exception:  # noqa: BLE001
            logger.warning("V_combined face emb 抽取失败, 该 cand 不参与 face farthest-first",
                           exc_info=True)
            face_emb_map[id(c)] = None

    # 阶段 3: face 选样 — face emb farthest-first
    # base_face_cand = seed (有 same_frame_face_crop 且抽 emb 成功), 兜底用 base_body 自己
    base_face = base_body
    if face_emb_map.get(id(base_face)) is None:
        # 找一个有 face emb 的 cand 当 base
        base_face = next(
            (c for c in face_cands if face_emb_map.get(id(c)) is not None),
            base_body,
        )
    if face_emb_map.get(id(base_face)) is None:
        # face_pool 全无 emb → 退化, face 不重新分配, 直接返 body_picks。
        # status 跟末尾分支同款判 body_picks 数量, 防 face 池失效时调用方
        # (前端) 拿到 status='ok' 跳过"质量警告"导致用户以为入库 topk 实际 < topk。
        status = "ok" if len(body_picks) >= topk else "weak_diversity"
        return SelectionResult(samples=body_picks, status=status, rejected=[])
    face_picks = _farthest_first_pick(
        face_cands,
        topk=topk,
        sim_threshold=face_sim_threshold,
        seed=base_face,
        cand_to_emb=face_emb_map,
    )

    # 阶段 4: face 重分配回 body_picks (顺序绑定, 首位是 seed face/body 同帧)
    for i in range(min(topk, len(body_picks))):
        if i >= len(face_picks):
            break
        sf = getattr(face_picks[i], "same_frame_face_crop", None)
        if sf is not None:
            body_picks[i].face_crop = sf

    status = "ok" if len(body_picks) >= topk else "weak_diversity"
    return SelectionResult(samples=body_picks, status=status, rejected=[])
