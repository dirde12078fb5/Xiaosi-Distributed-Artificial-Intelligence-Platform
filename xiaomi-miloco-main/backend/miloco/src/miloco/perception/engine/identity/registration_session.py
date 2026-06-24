"""注册会话管理 — pending session + commit + 历史批次。

支持 v4 §3 的"两步走"注册流程(Web 用):
    preview → 返回 register_session_id_pending + candidates + auto_selected_indices
            → 用户改勾选 → commit(用 indices 真正入库)

也支持"一气呵成"路径(agent 用):直接 commit 不经 preview,内部自动跑 select_topk
全部选中。

pending session 持久化决策(v1.2 §9.4.3):
    **纯内存 + 10 min TTL**,不引入 sqlite。重启即丢——用户半小时不操作本来就
    该重来;引入持久化反而要管一致性 / 清理 / 迁移。

historic sessions 来源:
    扫 ``data/identity_lib/persons/*/tier_a/*.json`` 聚合 register_session_id
    字段,**无独立 DB 表**——避免一致性维护成本。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from miloco.perception.engine.identity.extractor import ScoredCandidate
from miloco.perception.engine.identity.library import (
    BodySample,
    IdentityLibrary,
)
from miloco.perception.engine.identity.registration_filter import (
    SelectionResult,
    select_topk,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 配置常量
# =============================================================================

DEFAULT_PENDING_TTL_SEC = 600.0      # 10 min,与 v1.2 §9.4.3 一致
SESSION_ID_PREFIX = "rs-"            # commit 后写入 sidecar 的稳定 id 前缀
PENDING_ID_PREFIX = "rsp-"           # preview 阶段的临时 pending id 前缀


# =============================================================================
# 数据结构
# =============================================================================


@dataclass
class PendingSession:
    """preview 后、commit 前的中间状态(内存)。

    candidates 是 select_topk 跑过的全量打分候选(主路径 + 备路径都用过的输入);
    auto_selected_indices 是系统挑出来的 topk 索引;用户在 web 上可改选,commit
    时按用户传的 indices 真正入库。
    """

    pending_id: str
    member_id: str | None             # 已有 member 时给;新建走 commit 时传 name+role
    candidates: list[ScoredCandidate]
    auto_selected_indices: list[int]
    expires_at: float
    source: str                       # "from_pool" / "from_media" / "from_cluster"
    metadata: dict = field(default_factory=dict)


@dataclass
class CommitResult:
    """commit 后的返回结果。"""

    person_id: str
    register_session_id: str
    written_samples: list[str]        # 写入的 body 文件名
    selection_status: str             # ok / user_reduced / no_valid_subject
                                       # - ok:实际入库数 ≥ auto_selected 数
                                       # - user_reduced:用户在 web 上勾掉部分样本,实际入库 < auto_selected
                                       # - no_valid_subject:0 张入库
                                       # 跟 select_topk 的 "weak_diversity" 状态语义不同(后者是
                                       # 算法挡 pHash 阈值挑不到 topk),刻意不同名避免混淆。


@dataclass
class HistorySession:
    """register sessions 列表的单条。"""

    register_session_id: str
    member_id: str
    member_name: str | None
    created_at: float
    written_count: int                # 该 session 写入身份库的 body 文件数
    source: str | None
    cluster_id: str | None


# =============================================================================
# 主类
# =============================================================================


class RegistrationSessionManager:
    """注册会话管理器:管理 pending dict + 提供 commit / sessions / rollback。

    实例**进程内单例**(由调用方 / FastAPI app 持有);不跨进程共享,不持久化。
    """

    def __init__(
        self,
        library: IdentityLibrary,
        *,
        pending_ttl_sec: float = DEFAULT_PENDING_TTL_SEC,
        now_fn=time.time,
    ) -> None:
        self.library = library
        self.pending_ttl_sec = pending_ttl_sec
        self._now = now_fn
        self._pending: dict[str, PendingSession] = {}

    # ----- preview / commit -----

    def create_pending(
        self,
        candidates: list[ScoredCandidate],
        *,
        source: str,
        member_id: str | None = None,
        select_topk_kwargs: dict[str, Any] | None = None,
        select_fn: Callable[..., SelectionResult] = select_topk,
        metadata: dict | None = None,
    ) -> tuple[str, SelectionResult, PendingSession]:
        """preview 入口:跑 select_fn + 落 pending dict + 返回。

        Args:
            select_fn: 筛选函数。默认 ``select_topk`` 兼容老路径;视频附件路径传
                ``select_topk_with_frontal_seed`` 走"正脸优先 + face cand 优先 +
                凑满 topk"策略。函数签名: ``(candidates, **kwargs) -> SelectionResult``。
            select_topk_kwargs: 透传给 select_fn 的 kwargs (topk / min_k 等)。

        Returns:
            (pending_id, selection_result, pending_session)
        """
        self._gc_expired()
        sr = select_fn(candidates, **(select_topk_kwargs or {}))
        # 按 sr.samples 顺序映射回 candidates 原索引, 保留 select 输出的顺序
        # (正脸 seed 在 sr.samples[0], 拼图按本顺序展示 → 正脸排第一位)。
        # ScoredCandidate 含 ndarray, 不能用 == / index, 用 id() 反查。
        cand_id_to_idx = {id(c): i for i, c in enumerate(candidates)}
        auto_indices = [
            cand_id_to_idx[id(s)] for s in sr.samples
            if id(s) in cand_id_to_idx
        ]
        pending_id = PENDING_ID_PREFIX + uuid.uuid4().hex
        sess = PendingSession(
            pending_id=pending_id,
            member_id=member_id,
            candidates=candidates,
            auto_selected_indices=auto_indices,
            expires_at=self._now() + self.pending_ttl_sec,
            source=source,
            metadata=metadata or {},
        )
        self._pending[pending_id] = sess
        return pending_id, sr, sess

    def commit_pending(
        self,
        pending_id: str,
        *,
        indices: list[int],
        member_name: str | None = None,
        member_role: str | None = None,
        member_resolver: "Any | None" = None,   # callable(member_id, name, role)->member_id|None
        reid_extractor: "Any | None" = None,
    ) -> CommitResult | None:
        """commit 入口:按 indices 把指定 candidates 写入身份库。

        - pending 已过期 / 不存在 → 返 None。
        - indices 含越界值 → 静默过滤(忽略)。
        - member_resolver 统一解析目标身份:member_id 绑定既有(带 role 则补写 SQL)、member_name 新建/复用。
        - member_id / member_name 都缺 → 报错(没有目标身份)。
        """
        self._gc_expired()
        sess = self._pending.get(pending_id)
        if sess is None:
            logger.warning("commit_pending: pending_id=%s 不存在或已过期", pending_id)
            return None

        # 解析目标 member_id:统一走 resolver——按 id 绑定既有成员时也把 role 落 SQL,按 name
        # 新建/复用。两条路径都保证 SQL(name/role 单一事实源)被写,避免只写文件层 meta、
        # 重启被 sync_person_meta_from_sql 反向覆盖。
        if member_resolver is not None:
            person_id = member_resolver(sess.member_id, member_name, member_role)
        else:
            person_id = sess.member_id
        if person_id is None:
            logger.warning(
                "commit_pending: 无法解析目标 member(member_id/name 都缺) pending_id=%s",
                pending_id,
            )
            return None

        # 文件层 meta.json 的 name 是 omni 渲染 prompt 的"姓名"来源。真名(member_name)
        # 与家庭角色(member_role)两路独立落盘、各归各位——不再像旧逻辑那样"role 缺省就
        # 拿 name 顶上"灌成镜像。member_resolver 已先把 name/role 落 SQL(按 id 绑定既有成员、
        # 带 role 也补写),这里写的 meta 与 SQL 同源；member_name/member_role 为 None 时
        # add_tier_a_samples_batch 对该字段不覆盖、meta 原值保留。

        # 按 indices 收 candidates → BodySample
        valid_idx = [i for i in indices if 0 <= i < len(sess.candidates)]
        chosen = [sess.candidates[i] for i in valid_idx]
        register_session_id = SESSION_ID_PREFIX + uuid.uuid4().hex

        bodies: list[BodySample] = []
        for c in chosen:
            meta = {
                "score": c.score,
                "phash": format(c.phash, "x"),
                "track_id": c.track_id,
                "camera_id": c.cam_id,
                "cluster_id": c.cluster_id,
                "captured_at": c.captured_at,
                "bbox": list(c.bbox_xyxy),
                "detector_conf": c.detector_conf,
                "sharpness": c.sharpness,
            }
            bodies.append(BodySample(
                body_crop=c.body_crop,
                face_crop=c.face_crop,
                source=sess.source,
                captured_at=c.captured_at,
                metadata=meta,
                reid_embedding=c.reid_embedding,
            ))

        written = self.library.add_tier_a_samples_batch(
            person_id, bodies, register_session_id,
            name=member_name, role=member_role,
            reid_extractor=reid_extractor,
        )

        # commit 后清掉 pending
        self._pending.pop(pending_id, None)

        # 判定 selection_status:实际入库数 vs auto_selected 比较。注意"用户少选"
        # 不复用 select_topk 的 ``weak_diversity``——后者是算法挡 pHash 阈值挑不到
        # topk 的语义,跟"用户手动勾掉一张"是两件事,前端 / SKILL 拿到 status 后做
        # 不同 UX 应答(weak_diversity 提示"差异化不够,要补素材";user_reduced 不
        # 提示,因为用户明确表达了"只要这些")。
        if len(written) == 0:
            status = "no_valid_subject"
        elif len(written) >= len(sess.auto_selected_indices):
            status = "ok"
        else:
            status = "user_reduced"

        logger.info(
            "commit_pending pending=%s person=%s session=%s written=%d",
            pending_id, person_id, register_session_id, len(written),
        )
        return CommitResult(
            person_id=person_id,
            register_session_id=register_session_id,
            written_samples=written,
            selection_status=status,
        )

    def commit_oneshot(
        self,
        candidates: list[ScoredCandidate],
        *,
        member_id: str | None = None,
        member_name: str | None = None,
        member_role: str | None = None,
        source: str,
        select_topk_kwargs: dict[str, Any] | None = None,
        member_resolver: "Any | None" = None,
        reid_extractor: "Any | None" = None,
    ) -> CommitResult | None:
        """一气呵成入库(agent 用):内部 preview + 自动全选 auto_indices + commit。

        给 agent skill / from-pool / from-cluster / from-media CLI 等"无需用户调勾选"
        的场景使用。
        """
        pending_id, _sr, sess = self.create_pending(
            candidates, source=source, member_id=member_id,
            select_topk_kwargs=select_topk_kwargs,
        )
        return self.commit_pending(
            pending_id,
            indices=sess.auto_selected_indices,
            member_name=member_name,
            member_role=member_role,
            member_resolver=member_resolver,
            reid_extractor=reid_extractor,
        )

    # ----- pending GC -----

    def _gc_expired(self) -> None:
        now = self._now()
        expired = [pid for pid, s in self._pending.items() if s.expires_at < now]
        for pid in expired:
            self._pending.pop(pid, None)

    def pending_count(self) -> int:
        """对外只读:当前内存里 pending 数(给 status / metrics 用)。"""
        self._gc_expired()
        return len(self._pending)

    # ----- 历史批次 + rollback -----

    def list_sessions(
        self, *, member_id: str | None = None, limit: int = 20,
    ) -> list[HistorySession]:
        """扫 sidecar 聚合 register_session_id 历史。

        member_id 给定时只看该成员;否则全库扫(成本 = 所有 tier_a sidecar 数,
        20 人 × 5 张 = 100 个 json,毫秒级)。
        """
        per_session: dict[str, dict] = {}
        persons_dir = self.library.persons_dir
        if not persons_dir.is_dir():
            return []
        person_iter = ([persons_dir / member_id]
                       if member_id else persons_dir.iterdir())
        for p in person_iter:
            if not p.is_dir():
                continue
            tier_a = p / "tier_a"
            if not tier_a.is_dir():
                continue
            pid = p.name
            name = self.library.get_name(pid)
            for sidecar in tier_a.glob("body_*.json"):
                try:
                    meta = json.loads(sidecar.read_text(encoding="utf-8"))
                except Exception:
                    continue
                rsid = meta.get("register_session_id")
                if not rsid:
                    continue
                bucket = per_session.setdefault(rsid, {
                    "register_session_id": rsid,
                    "member_id": pid,
                    "member_name": name,
                    "created_at": meta.get("captured_at", 0.0),
                    "written_count": 0,
                    "source": meta.get("source"),
                    "cluster_id": meta.get("cluster_id"),
                })
                bucket["written_count"] += 1
                # created_at 取 session 内最早一张的时间
                if meta.get("captured_at", 0.0) < bucket["created_at"]:
                    bucket["created_at"] = meta["captured_at"]

        sessions = sorted(
            per_session.values(),
            key=lambda d: d["created_at"], reverse=True,
        )[:limit]
        return [HistorySession(**d) for d in sessions]

    def rollback_session(
        self, register_session_id: str, *, member_id: str | None = None,
    ) -> int:
        """删该 register_session_id 写入身份库的所有 tier_a sample。

        member_id 给定时只对该 person 操作(快);否则全库扫(慢但兜底)。
        """
        if member_id:
            return self.library.delete_by_register_session(member_id, register_session_id)
        # 全库扫:遍历每个 person 调 delete_by_register_session
        deleted = 0
        for p in self.library.persons_dir.iterdir():
            if not p.is_dir():
                continue
            deleted += self.library.delete_by_register_session(
                p.name, register_session_id,
            )
        return deleted
