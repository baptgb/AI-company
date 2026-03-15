# AI Team OS MCP Tools Reference

> 自动生成自 `src/aiteam/mcp/server.py` — 共 31 个工具

## 目录

- [团队管理](#团队管理)
  - [team_create](#team-create)
  - [team_status](#team-status)
  - [team_list](#team-list)
  - [team_briefing](#team-briefing)
  - [team_setup_guide](#team-setup-guide)
- [Agent 管理](#agent-管理)
  - [agent_register](#agent-register)
  - [agent_update_status](#agent-update-status)
  - [agent_list](#agent-list)
- [任务管理](#任务管理)
  - [task_run](#task-run)
  - [task_decompose](#task-decompose)
  - [task_status](#task-status)
  - [taskwall_view](#taskwall-view)
- [循环系统](#循环系统)
  - [loop_start](#loop-start)
  - [loop_status](#loop-status)
  - [loop_next_task](#loop-next-task)
  - [loop_advance](#loop-advance)
  - [loop_pause](#loop-pause)
  - [loop_resume](#loop-resume)
  - [loop_review](#loop-review)
- [会议](#会议)
  - [meeting_create](#meeting-create)
  - [meeting_send_message](#meeting-send-message)
  - [meeting_read_messages](#meeting-read-messages)
  - [meeting_conclude](#meeting-conclude)
- [记忆](#记忆)
  - [memory_search](#memory-search)
- [项目管理](#项目管理)
  - [project_create](#project-create)
  - [phase_create](#phase-create)
  - [phase_list](#phase-list)
- [系统](#系统)
  - [os_health_check](#os-health-check)
  - [event_list](#event-list)
  - [os_report_issue](#os-report-issue)
  - [os_resolve_issue](#os-resolve-issue)

---

## 团队管理

### `team_create`

创建一个新的 AI Agent 团队。  如果指定了 leader_agent_id，会自动完成该 Leader 的旧 active 团队。 一个 Leader 同时只能领导一个 active 团队。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 团队名称 |
| `mode` | `str` | `'coordinate'` | 协作模式，可选 "coordinate"（协调）或 "broadcast"（广播） |
| `project_id` | `str` | `''` | 关联的项目 ID（可选） |
| `leader_agent_id` | `str` | `''` | 领导此团队的 Leader agent ID（可选，用于自动完成旧团队） |

**返回:** 创建的团队信息，包含 team_id

### `team_status`

获取指定团队的详细信息和状态。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或团队名称 |

**返回:** 团队详情，包含名称、模式、成员数等

### `team_list`

列出所有已创建的团队。

**参数:** 无

**返回:** 团队列表，包含每个团队的基本信息

### `team_briefing`

获取团队全景简报 — 一次调用了解团队全部状态。  返回团队信息、成员状态、最近事件、最近会议、待办任务和操作建议。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或团队名称 |

**返回:** 团队全景简报，包含 agents / recent_events / recent_meeting / pending_tasks / _hints

### `team_setup_guide`

根据项目类型获取推荐的团队角色配置。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_type` | `str` | `'web-app'` | 项目类型，可选值：web-app, api-service, data-pipeline, library, refactor, bugfix |

**返回:** 推荐角色列表和组建提示

---

## Agent 管理

### `agent_register`

向团队注册一个新的 AI Agent。  注册成功后状态自动设为busy。 规则：一次性任务完成后Leader应Kill该Agent，可能有后续任务的保留。 工具受限时报告Leader解决。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 目标团队 ID 或名称 |
| `name` | `str` | 必填 | Agent 名称 |
| `role` | `str` | 必填 | Agent 角色描述 |
| `model` | `str` | `'claude-opus-4-6'` | 使用的模型，默认 claude-opus-4-6 |
| `system_prompt` | `str` | `''` | Agent 的系统提示词 |

**返回:** Agent 信息 + teammates 列表 + team_snapshot（含 pending_tasks 和 recent_meeting）

### `agent_update_status`

更新 Agent 的运行状态。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `agent_id` | `str` | 必填 | Agent ID |
| `status` | `str` | 必填 | 新状态，可选 "idle"、"busy"、"offline" |

**返回:** 更新后的 Agent 信息

### `agent_list`

列出团队中所有已注册的 Agent。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** Agent 列表，包含每个 Agent 的状态和角色

---

## 任务管理

### `task_run`

在团队中创建一个任务，等待Agent领取执行。  规则：设置priority(critical/high/medium/low)和horizon(short/mid/long)。 有依赖时设depends_on，系统自动管理BLOCKED状态。统筹并行推进，不等一个完成再开下一个。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `description` | `str` | 必填 | 任务描述 |
| `title` | `str` | `''` | 任务标题（可选） |
| `model` | `str | None` | `None` | 指定使用的模型（可选，仅记录元数据） |
| `depends_on` | `list[str] | None` | `None` | 依赖的任务ID列表（可选，任务将在依赖完成后自动解锁） |

**返回:** 创建的任务信息 + related_tasks（相似任务列表，如有）

### `task_decompose`

将一个大任务拆解为父任务+子任务。  支持两种方式： 1. 使用内置模板（template）自动生成子任务 2. 手动指定子任务列表（subtasks）  可用模板: web-app, api-service, data-pipeline, library, refactor, bugfix

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `title` | `str` | 必填 | 父任务标题 |
| `description` | `str` | `''` | 父任务描述 |
| `template` | `str` | `''` | 内置模板名称（可选） |
| `subtasks` | `list[dict[str, str]] | None` | `None` | 自定义子任务列表，每项含 title 和可选 description（可选） |
| `auto_assign` | `bool` | `False` | 是否自动分配给匹配角色的 Agent（暂未实现） |

**返回:** 父任务 + 子任务列表

### `task_status`

查询任务的当前状态。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `task_id` | `str` | 必填 | 任务 ID |

**返回:** 任务详情，包含状态、结果等

### `taskwall_view`

获取任务墙视图 — 按短/中/长期分类，智能排序。  返回按 score 排序的任务列表，Leader 用此快速了解下一步该做什么。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `horizon` | `str` | `''` | 按时间跨度筛选，可选 "short" / "mid" / "long"（留空=全部） |
| `priority` | `str` | `''` | 按优先级筛选，可选 "critical" / "high" / "medium" / "low"，逗号分隔多选（留空=全部） |

**返回:** 任务墙数据，按 short/mid/long 分组，每组内按 score 降序

---

## 循环系统

### `loop_start`

启动公司循环 — Leader持续工作模式。  启动后循环领取最高优先级任务。每N个任务触发回顾讨论。 任务不足时应组织会议讨论方向，不能没事找事干。  提示: 使用 /continuous-mode 获取完整的持续工作协议， 包括循环领取、暂停恢复、成员管理等详细行为规范。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** 循环状态信息，包含当前阶段和周期数

### `loop_status`

查看公司循环当前状态 — 阶段、周期、已完成任务数。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** 循环状态详情，包含 phase / current_cycle / completed_tasks_count

### `loop_next_task`

获取下一个应执行的任务 — 按优先级×时间跨度×就绪度排序。  优先领取pinned和critical任务。short优先于mid优先于long。 BLOCKED任务等依赖完成后自动解锁，无需手动处理。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `agent_id` | `str` | `''` | 指定 Agent ID，优先返回分配给该 Agent 的任务（可选） |

**返回:** 下一个待执行的任务信息，无任务时返回空

### `loop_advance`

推进循环到下一阶段。  可用 trigger: - tasks_planned: 规划完成 → 执行 - batch_completed: 一批任务完成 → 监控 - all_tasks_done: 全部完成 → 回顾 - issues_found: 发现问题 → 返回执行 - all_clear: 一切正常 → 回顾 - new_tasks_added: 有新任务 → 重新规划 - no_more_tasks: 无更多任务 → 空闲

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `trigger` | `str` | 必填 | 触发器名称 |

**返回:** 更新后的循环状态

### `loop_pause`

暂停循环 — 保留当前状态，随时可恢复。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** 暂停后的循环状态

### `loop_resume`

恢复循环 — 从暂停处继续。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** 恢复后的循环状态

### `loop_review`

触发公司循环回顾 — 自动创建回顾会议并生成统计报告。  回顾会议包含：本轮完成的任务汇总、失败任务分析、下一步建议。 Leader和团队可在会议中讨论并产出新的待办任务。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |

**返回:** 回顾会议信息，包含 meeting_id / stats / topic

---

## 会议

### `meeting_create`

创建团队会议，用于多 Agent 协作讨论。  规则：根据议题动态添加合适参与者，讨论中发现新方向时随时招募专家。 讨论结论应转为任务放入任务墙。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `topic` | `str` | 必填 | 会议讨论主题 |
| `participants` | `list[str] | None` | `None` | 参会 Agent ID 列表，为空则全员参与 |

**返回:** 会议信息，包含 meeting_id 和操作指引

### `meeting_send_message`

在会议中发送讨论消息。  讨论规则： - Round 1: 各自提出观点 - Round 2+: 必须先读取前人发言，引用并回应具体观点 - 最后一轮: 汇总共识和分歧

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `meeting_id` | `str` | 必填 | 会议 ID |
| `agent_id` | `str` | 必填 | 发言 Agent 的 ID |
| `agent_name` | `str` | 必填 | 发言 Agent 的名称 |
| `content` | `str` | 必填 | 消息内容 |
| `round_number` | `int` | `1` | 讨论轮次，默认 1 |

**返回:** 发送成功的消息信息

### `meeting_read_messages`

读取会议中的所有讨论消息。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `meeting_id` | `str` | 必填 | 会议 ID |
| `limit` | `int` | `100` | 返回消息数量上限，默认 100 |

**返回:** 消息列表，按时间顺序排列

### `meeting_conclude`

结束会议，标记为已完成。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `meeting_id` | `str` | 必填 | 会议 ID |

**返回:** 更新后的会议信息

---

## 记忆

### `memory_search`

搜索 AI Team OS 中的记忆存储。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | `str` | `''` | 搜索关键词 |
| `scope` | `str` | `'global'` | 记忆作用域，默认 "global" |
| `scope_id` | `str` | `'system'` | 作用域 ID，默认 "system" |
| `limit` | `int` | `10` | 返回数量上限，默认 10 |

**返回:** 匹配的记忆列表

---

## 项目管理

### `project_create`

创建一个新项目，自动创建默认 Phase。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 项目名称 |
| `description` | `str` | `''` | 项目描述 |
| `root_path` | `str` | `''` | 项目根目录路径（可选，UNIQUE） |

**返回:** 创建的项目信息，包含 project_id

### `phase_create`

在项目中创建一个新的开发阶段。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_id` | `str` | 必填 | 项目 ID |
| `name` | `str` | 必填 | 阶段名称 |
| `description` | `str` | `''` | 阶段描述 |
| `order` | `int` | `0` | 排序序号，默认 0 |

**返回:** 创建的阶段信息，包含 phase_id

### `phase_list`

列出项目的所有 Phase 及其状态。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_id` | `str` | 必填 | 项目 ID |

**返回:** Phase 列表，包含每个 Phase 的名称、状态和排序

---

## 系统

### `os_health_check`

检查 AI Team OS API 服务的健康状态。  通过访问团队列表端点验证 API 服务是否正常运行。

**参数:** 无

**返回:** 健康状态信息，包含 API 可达性和团队数量

### `event_list`

列出系统中的最近事件。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | `int` | `50` | 返回事件数量上限，默认 50 |

**返回:** 事件列表，包含事件类型、来源和时间

### `os_report_issue`

上报问题到团队。问题作为高优先级任务创建，自动标记为issue类型。  severity 会映射为任务优先级：critical→critical, high→high, medium→high, low→medium。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team_id` | `str` | 必填 | 团队 ID 或名称 |
| `title` | `str` | 必填 | 问题标题 |
| `description` | `str` | `''` | 问题详细描述 |
| `severity` | `str` | `'medium'` | 严重程度，可选 "critical" / "high" / "medium" / "low" |
| `category` | `str` | `'bug'` | 问题分类，如 "bug" / "performance" / "security" / "ux" |

**返回:** 创建的 Issue 任务信息

### `os_resolve_issue`

标记Issue为已解决，附带解决方案描述。  将Issue状态更新为 resolved，同时记录解决方案。 Issue对应的任务也会被标记为 completed。

**参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `issue_id` | `str` | 必填 | Issue（任务）ID |
| `resolution` | `str` | 必填 | 解决方案描述 |

**返回:** 更新后的 Issue 信息
