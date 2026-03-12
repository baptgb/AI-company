# AI Team OS — 架构设计文档

## 1. 系统概览

AI Team OS 是一个通用可复用的AI Agent团队操作系统框架，支持动态创建/管理AI Agent团队，具有长期记忆、多种编排模式和Web管理界面。

### 1.1 五层架构

```
┌──────────────────────────────────────────────────────────┐
│  Layer 5: Web Dashboard (React + TypeScript)   [M2引入]  │
├──────────────────────────────────────────────────────────┤
│  Layer 4: CLI (Typer) + REST API (FastAPI)               │
├──────────────────────────────────────────────────────────┤
│  Layer 3: Team Orchestrator (LangGraph StateGraph)       │
├──────────────────────────────────────────────────────────┤
│  Layer 2: Memory Manager (Mem0 / File fallback)          │
├──────────────────────────────────────────────────────────┤
│  Layer 1: Storage (PostgreSQL/SQLite + Redis/Memory)     │
└──────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
用户 → CLI命令 → TeamManager → LangGraph StateGraph → Agent节点
                                    ↕                      ↕
                              MemoryManager          LLM Provider
                                    ↕                 (LangChain)
                              StorageRepository
                              (SQLite/PostgreSQL)
```

---

## 2. Layer 1: Storage — 数据持久化

### 2.1 存储后端策略

| 阶段 | 后端 | 依赖 |
|------|------|------|
| M1 | SQLite | 零依赖，内置Python |
| M2+ | PostgreSQL + pgvector | Docker |

通过 `StorageBackend` 抽象接口切换，上层无感知。

### 2.2 数据模型

#### teams 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | str | 团队名称（唯一） |
| mode | str | 编排模式: coordinate/broadcast/route/meet |
| config | JSON | 团队配置（yaml解析后） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

#### agents 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| team_id | UUID | 所属团队（外键） |
| name | str | Agent名称 |
| role | str | 角色描述 |
| system_prompt | text | 系统提示词 |
| model | str | 使用的模型ID |
| status | str | idle/busy/error/offline |
| config | JSON | Agent配置 |
| created_at | datetime | 创建时间 |

#### tasks 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| team_id | UUID | 所属团队 |
| title | str | 任务标题 |
| description | text | 任务描述 |
| status | str | pending/running/completed/failed |
| assigned_to | UUID | 分配给的Agent（可选） |
| result | text | 任务结果 |
| parent_id | UUID | 父任务（支持子任务） |
| created_at | datetime | 创建时间 |
| started_at | datetime | 开始时间 |
| completed_at | datetime | 完成时间 |

#### memories 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| scope | str | global/team/agent/user |
| scope_id | str | 作用域ID |
| content | text | 记忆内容 |
| metadata | JSON | 元数据（来源、标签等） |
| created_at | datetime | 创建时间 |
| accessed_at | datetime | 最后访问时间 |

#### events 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| type | str | 事件类型（见事件类型列表） |
| source | str | 事件来源（agent_id/team_id/system） |
| data | JSON | 事件数据 |
| timestamp | datetime | 事件时间 |

### 2.3 事件类型

```
team.created / team.deleted / team.mode_changed
agent.created / agent.removed / agent.status_changed
task.created / task.started / task.completed / task.failed
memory.created / memory.updated / memory.accessed
meeting.started / meeting.round_completed / meeting.concluded
system.started / system.stopped / system.error
```

---

## 3. Layer 2: Memory Manager — 记忆管理

### 3.1 三温度记忆

| 温度 | M1实现 | M2实现 | 用途 |
|------|--------|--------|------|
| Hot | Python dict | Redis | 当前会话上下文，<1ms |
| Warm | SQLite memories表 | PostgreSQL + Mem0 | 跨会话持久记忆，<50ms |
| Cold | JSON文件归档 | JSON文件归档 | 历史归档，<500ms |

### 3.2 四级记忆隔离（Mem0模式）

| 级别 | scope | 说明 |
|------|-------|------|
| Global | global | 全系统共享知识 |
| Team | team:{team_id} | 团队内共享 |
| Agent | agent:{agent_id} | Agent私有记忆 |
| User | user:{user_id} | 用户偏好 |

### 3.3 上下文恢复流程

```
Agent上下文耗尽 → 触发checkpoint保存
  → 保存: LangGraph Checkpoint + 当前记忆快照 + 任务进度
  → 恢复: 新Agent实例 + 加载Checkpoint + 注入记忆摘要 + 从断点继续
```

### 3.4 Memory Manager 接口

```python
class MemoryManager(Protocol):
    async def store(self, scope: str, scope_id: str, content: str, metadata: dict) -> str: ...
    async def retrieve(self, scope: str, scope_id: str, query: str, limit: int = 5) -> list[Memory]: ...
    async def list_memories(self, scope: str, scope_id: str) -> list[Memory]: ...
    async def delete(self, memory_id: str) -> bool: ...
    async def create_snapshot(self, agent_id: str) -> dict: ...
    async def restore_from_snapshot(self, snapshot: dict) -> None: ...
```

---

## 4. Layer 3: Team Orchestrator — 团队编排

### 4.1 LangGraph StateGraph 核心

每种编排模式对应一个独立的 StateGraph：

#### Coordinate模式（M1）
```
START → leader_plan → [agent_1, agent_2, ...] → leader_synthesize → END
        (Leader分析    (顺序执行各Agent)         (Leader综合结果)
         并制定计划)
```

#### Broadcast模式（M2）
```
START → broadcast → [agent_1 ∥ agent_2 ∥ ...] → reducer → END
        (广播任务)   (并行执行)                   (合并结果)
```

#### Route模式（M3）
```
START → router → agent_X → END
        (根据任务类型路由到对应专家Agent)
```

#### Meet模式（M3）
```
START → facilitator_intro → [round_1: all agents ∥] → check_consensus
         ↑                                                    ↓
         └──── next_round (if no consensus) ←─────────────────┘
                                                              ↓
                                                     facilitator_conclude → END
```

### 4.2 TeamManager 接口

```python
class TeamManager:
    async def create_team(self, name: str, mode: str, config: dict) -> Team: ...
    async def add_agent(self, team_id: str, name: str, role: str, **kwargs) -> Agent: ...
    async def remove_agent(self, team_id: str, agent_id: str) -> bool: ...
    async def run_task(self, team_id: str, task: str, **kwargs) -> TaskResult: ...
    async def get_status(self, team_id: str) -> TeamStatus: ...
    async def set_mode(self, team_id: str, mode: str) -> None: ...
```

### 4.3 Agent节点

每个Agent在LangGraph中是一个节点，接收状态、调用LLM、返回更新：

```python
async def agent_node(state: TeamState, config: RunnableConfig) -> dict:
    agent_config = state["agents"][config["agent_id"]]
    llm = ChatAnthropic(model=agent_config.model)
    # 注入记忆上下文
    memories = await memory_manager.retrieve("agent", agent_config.id, state["current_task"])
    # 调用LLM
    response = await llm.ainvoke([system_prompt + memories, state["current_task"]])
    return {"messages": [response], "agent_outputs": {agent_config.id: response.content}}
```

### 4.4 TeamState 定义

```python
class TeamState(TypedDict):
    team_id: str
    current_task: str
    messages: Annotated[list[BaseMessage], add_messages]
    agent_outputs: dict[str, str]        # agent_id → output
    leader_plan: str | None
    consensus_reached: bool
    round_number: int
    final_result: str | None
```

---

## 5. Layer 4: CLI + REST API

### 5.1 CLI命令（Typer）

```
aiteam init [--template research|development|analysis]
aiteam team create/list/show/set-mode/delete
aiteam agent create/list/show/update/remove
aiteam task create/run/status/output
aiteam meet --team <team> --topic <topic>
aiteam memory search/list/add
aiteam status
aiteam up / down                    # M2: 启动/停止全栈
aiteam config / doctor              # 系统诊断
```

### 5.2 REST API（FastAPI，M2引入）

```
GET    /api/teams                   # 团队列表
POST   /api/teams                   # 创建团队
GET    /api/teams/{id}              # 团队详情
PUT    /api/teams/{id}              # 更新团队
DELETE /api/teams/{id}              # 删除团队

GET    /api/teams/{id}/agents       # Agent列表
POST   /api/teams/{id}/agents       # 添加Agent
GET    /api/agents/{id}             # Agent详情

POST   /api/tasks                   # 创建任务
GET    /api/tasks/{id}              # 任务详情
POST   /api/tasks/{id}/run          # 执行任务

GET    /api/events                  # 事件列表（支持过滤）
GET    /api/memory?scope=&query=    # 记忆搜索

WS     /ws/events                   # WebSocket事件实时推送
WS     /ws/agents/{id}/status       # Agent状态实时推送
```

---

## 6. Layer 5: Web Dashboard（M2引入）

### 6.1 页面规划

| 优先级 | 页面 | 路由 | M2/M3 |
|--------|------|------|-------|
| P0 | 总览 | `/` | M2 |
| P0 | 团队/成员 | `/teams` | M2 |
| P0 | 任务看板 | `/tasks` | M2 |
| P0 | 事件日志 | `/events` | M2 |
| P1 | 设置 | `/settings` | M2 |
| P2 | 会议纪要 | `/meetings` | M3 |
| P2 | 记忆浏览 | `/memory` | M3 |
| P2 | 成本追踪 | `/costs` | M3 |
| P3 | 调试面板 | `/debug` | M3 |

### 6.2 实时通信

- WebSocket连接到 `/ws/events`
- 自动重连（断连后指数退避）
- 事件类型过滤（客户端侧）

---

## 7. 配置系统

### 7.1 aiteam.yaml

```yaml
project:
  name: "my-project"
  description: "项目描述"
  language: "zh"

defaults:
  model: "claude-opus-4-6"
  max_context_ratio: 0.8

infrastructure:
  storage_backend: "sqlite"      # sqlite | postgresql
  memory_backend: "file"         # file | mem0
  dashboard_port: 3000
  api_port: 8000

team:
  name: "dev-team"
  mode: "coordinate"
  leader:
    name: "lead"
    role: "技术总监"
    system_prompt: "你是一位技术总监..."
  members:
    - name: "dev-1"
      role: "后端开发"
    - name: "dev-2"
      role: "前端开发"
```

### 7.2 配置验证

使用Pydantic模型验证aiteam.yaml，提供：
- 字段类型检查
- 必填字段验证
- 枚举值约束（mode: coordinate|broadcast|route|meet）
- 友好的中文错误提示

---

## 8. 错误处理

### 8.1 Agent执行失败

```
失败 → 记录错误事件 → 检查重试次数
  → 未超限: 重试（指数退避）
  → 已超限: 标记任务failed → 通知Leader → Leader决定是否重新分配
```

### 8.2 上下文耗尽

```
上下文使用率 > max_context_ratio → 触发checkpoint → 保存状态
  → 创建新Agent实例 → 恢复checkpoint → 继续执行
```

### 8.3 LLM调用失败

```
API错误 → 分类处理:
  - RateLimit: 等待重试
  - InvalidRequest: 截断输入重试
  - AuthError: 终止并提示用户检查API Key
  - NetworkError: 重试3次后终止
```
