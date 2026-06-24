# 身份识别

## 背景与目标

感知流水线能描述"画面中有人"，但无法回答"是谁"。身份识别模块解决这个问题：通过 face / body_appearance 两类视觉特征，把摄像头看到的人与家庭成员档案对应起来。

准确的身份识别让整个系统从"有人触发"升级为"谁触发"——规则可以精确到人，场景描述更自然，家庭记忆能正确归属。

---

## 产品面

### 能做什么

- **家庭成员管理**：增删改查成员（姓名/角色），每个成员持有独立的样本库
- **主动注册（两条路径）**：用户上传照片/视频直接进入 tier_a；或从系统自动积累的陌生人池（tier_u）中选取 crop 升级
- **实时识别**：随感知流水线运行，track 稳定后自动识别并写回 person_id，caption 中出现成员名
- **陌生人分配**：未能识别的 track 自动分配唯一编号（`unknown_<n>`），同一个人跨不同 track 用 ReID embedding 聚类合并

### 典型场景

**场景 1 — 新成员注册**：家里来了新保姆，需要让系统认识她。用户通过 Agent 触发 `miloco-miot-identity-register` Skill，上传视频或照片。系统展示候选 crop 拼图等待用户确认，确认后写入 tier_a。之后感知流水线识别到她时，caption 会用"保姆"而非"陌生人 #3"称呼。

**场景 2 — 从陌生人池升级**：系统在近期感知中多次看到一位陌生人，自动积累了多张高质量 crop 并归入陌生人池。用户通过 Skill 取出候选拼图，认出是经常来访的朋友，确认后从陌生人池选取 crop 写入 tier_a，跳过手动上传照片。

### 能力边界

- 识别精度取决于样本质量（图像清晰度、角度多样性）和模型能力
- 实时识别依赖感知流水线运行；流水线未启动时识别不工作，但成员管理 API 仍可用
- 陌生人池（tier_u）全内存，重启即清
- 每个摄像头持有独立的 IdentityEngine 实例，身份库全局共享；不支持"两台摄像头实时合并同一 track"
- 成员名重复时创建/更新返回 `code=2002`（`ConflictException`）

---

## 研发面

### 架构概览（数据流图）

#### 成员 CRUD 调用链

```
CLI / Agent（miloco-miot-identity Skill）
  → /api/identity/persons（person/router.py）
  → PersonService（person/service.py）
  → PersonRepo（database/person_repo.py）
  → miloco.db（person 表）
```

成员删除时，删除端点（`person/router.py` 的 delete 路由）编排两路级联：`PersonService.delete_person` 删 DB 行后，再经 `IdentityLibrary` 删除文件系统样本目录、经 `HomeProfileService.remove_subject` 清理家庭档案中绑定该成员的条目。

#### 实时识别链路（person_id 生成与消费）

```
TrackingService（DeepSORT 跟踪）
  → active tracks（track_id + bbox + ReID embedding）
  ↓
IdentityEngine（perception/engine/identity/engine.py）
  ├─ 未识别 track → 派发识别请求（Fused 路径）
  │    → gallery composite 注入 Omni fused 主调用
  │    → Omni 返回 identity_assignments → 写回 IdentityEngine 状态机
  ├─ confirmed track → 周期性重审
  ├─ unknown track → 累积 crop 到 TierUPool（陌生人池）
  └─ 返回 {track_id → person_id} 映射
  ↓
Omni 层（person_id 注入 prompt → caption 中出现成员名）
```

#### 陌生人→成员注册流程

```
IdentityEngine（识别失败 → unknown）
  → TierUPool（ReID embedding 聚类，合并同一人不同 track 的 crop）
  ↓
miloco-miot-identity-register Skill
  → 取候选拼图 → 用户确认选号 → commit 写 tier_a
  ↓
IdentityLibrary 写入样本文件
  → $MILOCO_HOME/data/identity_lib/persons/<id>/tier_a/
  ↓
下次感知时 IdentityEngine 检测 tier_a 指纹变化 → 重新识别
```

### 核心模块

**IdentityLibrary**（`perception/engine/identity/library.py`）

磁盘身份库的读写封装，负责 tier_a / tier_c 样本的加载、写入、FIFO 管理。进程内所有 per-camera IdentityEngine 共享同一份实例。样本库默认在 `$MILOCO_HOME/data/identity_lib/persons/`。

**TierUPool**（`perception/engine/identity/tier_u.py`）

陌生人池，全内存、重启即清。内部用 ReID embedding 聚类，把同一个人不同 track 的 crop 归到同一 cluster。embedding 从跟踪侧 Track 的 ReID 特征快照获取，零额外推理。

**RegistrationSessionManager**（`perception/engine/identity/registration_session.py`）

管理注册会话生命周期（创建、pending 累积、commit、rollback）。进程内单例，由 `Manager` 懒加载持有。两条注册路径（照片/视频上传 vs 陌生人池升级）都必须经过"预览确认 → commit"两步，不允许跳过用户确认直接写盘。

**IdentityEngine**（`perception/engine/identity/engine.py`）

per-camera 识别管线总编排，维护每个 track 的四态识别状态机（none/pending/confirmed/unknown）。决定何时派发识别请求，回流结果后更新 person_id 映射，以及何时将高置信结果异步写入 tier_c。每窗口比对 tier_a 指纹快照，发现变化时将所有 track 推回 pending 强制重判。

### 关键设计决策

#### tier_a / tier_c / tier_u 三层样本设计意图

- **tier_a**（`persons/<id>/tier_a/`）：用户主动登记，永久保留，代表最可靠的参照样本
- **tier_c**（`persons/<id>/tier_c/`）：系统在线推理中自动积累，FIFO 滚动更新。让身份参照跟上人物外观自然变化（换衣、不同光照），避免只靠注册时的老照片导致长期识别漂移。tier_c 写盘有严格门控条件，且在独立异步任务中执行，不阻塞每窗推理
- **tier_u**（TierUPool）：识别失败的未知 track 的临时 crop 缓冲，全内存、重启即清。为主动注册提供候选素材，用户可从中选取系统已积累的近期 crop，无需手动上传照片

**IdentityEngine 状态机**：每个 track 的识别结果需经多次 Omni 识别一致后才晋升为已提交状态（confirmed 或 unknown），避免单帧误识。tier_a 指纹改变时强制所有 track 重新走识别流程，确保新增/更新参照样本立即生效；tier_c 变化不触发重判（避免自喂环）。

**启动补齐**：服务启动时异步补齐历史 tier_a 样本缺失的 ReID 嵌入向量（幂等），确保旧版本迁移后不影响识别质量。

### 如果我要修改身份识别相关功能

| 修改目标                            | 去看哪个文件                                               |
| ----------------------------------- | ---------------------------------------------------------- |
| 修改识别状态机逻辑（何时触发/确认） | `perception/engine/identity/engine.py`（IdentityEngine）   |
| 修改陌生人池聚类逻辑                | `perception/engine/identity/tier_u.py`（TierUPool）        |
| 修改样本库读写逻辑                  | `perception/engine/identity/library.py`（IdentityLibrary） |
| 修改注册流程（预览/commit 逻辑）    | `perception/engine/identity/registration_session.py`       |
| 修改成员 CRUD API                   | `person/router.py`、`person/service.py`                    |

### 身份识别相关 API 路径

成员管理：`/api/identity/persons` 前缀（CRUD）；注册流程：`/api/identity/register/preview`（预览）→ `/api/identity/register/commit`（确认写入）；陌生人池：`/api/identity/pool/fetch`。完整端点见 `person/router.py`。

### 与其他模块的关系

**上游**：身份识别嵌入在 Identity 层，每次感知周期由 Identity 编排器（`engine/identity/identity.py`）调用，`{track_id → person_id}` 映射写回 `IdentityPacket` 后交给 Omni 层。

**下游**：`person_id` 注入 Omni prompt，VLM 在 caption 中以成员名代替匿名编号。成员删除时 `HomeProfileService.remove_subject` 联动清理档案中绑定该成员的条目。

**共享**：所有 per-camera IdentityEngine 共享同一份 IdentityLibrary，注册流程和实时引擎都通过它读写样本。
