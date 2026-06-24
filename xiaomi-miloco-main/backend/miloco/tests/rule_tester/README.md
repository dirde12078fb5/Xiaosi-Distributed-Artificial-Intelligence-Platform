# Rule Tester

V3 Rule 模块的开发验证工具。提供一个浏览器页面：

1. **创建任务**：输入自然语言（"每天喝 8 杯水"），通过 LLM 跑 `miloco-create-task`
   skill SOP，最终调用 `miloco-cli rule create` 真实落地规则。
2. **mock 感知触发**：直接 import `miloco.rule.runner.RuleRunner`，调
   `update_state(rule_id, source_did, current_bool, context)`。可以通过
   反复 `true / false` 切换观察 state mode 的差分 + 60s 防抖行为。
3. **调试触发**：调 `runner.trigger_rule(...)`，跳过差分合成一次 ENTERED。
4. **观察日志 / Mock MIoT 调用**：右栏列最近 30 条 `rule_log` + Mock
   MIoT 调用历史（实际不发到设备，只记 payload）。

## 架构

```
浏览器 ─HTTP─▶ rule-tester (FastAPI 8090)
                │
                ├─ POST /api/create-task
                │     └─ LLM (OpenAI 兼容) 跑 miloco-create-task SOP
                │     └─ subprocess miloco-cli rule create  ─HTTP─▶ miloco backend (1810)
                │     └─ 从 SQLite 重新加载规则到本地 runner
                │
                ├─ POST /api/rules/{id}/update-state
                │     └─ runner.update_state(...)            (in-process)
                │
                ├─ POST /api/rules/{id}/trigger
                │     └─ runner.trigger_rule(...)            (in-process)
                │
                └─ GET / : Jinja2 渲染 rules + logs + miot 调用
```

- **生产代码改动：零**。tester 只读 SQLite + 调用 cli + import runner。
- **MIoT 是 mock 的**（`mock_miot.py`），不会真的开关设备。

## 启动

### 1. miloco backend

确保 backend 已经跑起来（`miloco-cli rule create` 走 HTTP 调它）：

```
cd backend/miloco
uv run miloco_server   # 或 install.sh 脚本
```

backend 默认监听 `http://127.0.0.1:1810`。

### 2. 配置 LLM

任选其一：

**环境变量**（推荐）：

```
export MILOCO_TESTER_LLM_BASE_URL="https://api.openai.com/v1"
export MILOCO_TESTER_LLM_API_KEY="sk-..."
export MILOCO_TESTER_LLM_MODEL="gpt-4o-mini"
```

**配置文件**：

```
cd backend/miloco/tests/rule_tester
cp config.example.toml config.toml
# 编辑 config.toml 填 api_key
```

### 3. 启动 tester

```
cd backend/miloco
uv run python tests/rule_tester/server.py --port 8090
```

浏览器打开 <http://localhost:8090>。

## 注意事项

- **共享 SQLite**：tester 和 backend 同时运行，访问同一个数据库文件。SQLite
  默认 journal_mode 支持多进程，写并发概率低（perception 没切 V3 时 backend
  自己几乎不写 rule_log）。
- **runner 状态独立**：tester 持有自己的 RuleRunner 实例，`_last_source_state`
  / `_pending_exit` 跟 backend 的 runner 互相不通。验证 state mode 防抖时
  请在 tester 这一侧连续操作。
- **memory_write / cron_add 仅记录**：V3 还有阶段 A（memory）和阶段 B
  （cron），它们由 OpenClaw plugin 实现，不在本仓范围。tester 把 LLM
  emit 的这两类调用记到 trace 里展示，但不真实执行。
- **skill 文档**：直接读仓内生产 SKILL（`plugins/skills/miloco-create-task/SKILL.md`），
  跟 OpenClaw 实际加载的是同一份，无需手动同步。

## 配置参考

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `MILOCO_TESTER_LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容 endpoint |
| `MILOCO_TESTER_LLM_API_KEY` | （必填） | API Key |
| `MILOCO_TESTER_LLM_MODEL` | `gpt-4o-mini` | model id |
| `MILOCO_TESTER_CLI_BIN` | `miloco-cli` | cli 可执行文件路径 |
| `MILOCO_TESTER_MAX_ITERS` | `8` | 单次 query 最多 LLM 轮次 |

`config.toml` 字段对照见 `config.example.toml`。

## 已知限制

- 不验证阶段 A / 阶段 B 的真实落地（memory / cron）
- 不会自动停止 backend / tester（手动 Ctrl-C）
- update-state / trigger 后页面 200ms 自动刷新，规则列表里的 `_last_rule_state`
  反映 tester 自己的 runner，不是 backend 的
- LLM 输出 cli args 时会把含空格的中文字符串作为整体一个 token；如果
  LLM 拼错（例如把 `--name "[xxx] yyy"` 拆成多个），可能导致 cli 解析失败。
  这种情况打开 trace 里的 stderr 看具体报错。
