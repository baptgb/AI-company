# AI Team OS — 接口契约

## 模块间依赖关系

```
cli/ ──→ orchestrator/team_manager.py ──→ memory/store.py
                                     ──→ storage/repository.py
                  ↓
         orchestrator/graphs/*.py ──→ orchestrator/nodes/*.py
                                 ──→ memory/retriever.py
```

## 1. Storage Layer 接口

### StorageRepository (`storage/repository.py`)

所有数据库操作的统一入口。上层模块**只通过此接口**访问数据。

```python
from aiteam.types import Team, Agent, Task, Event, Memory, TaskStatus, AgentStatus

class StorageRepository:
    """数据持久化仓库 — 统一数据访问接口."""

    async def init_db(self) -> None:
        """初始化数据库（创建表/运行迁移）."""

    # === Teams ===
    async def create_team(self, name: str, mode: str, config: dict | None = None) -> Team: ...
    async def get_team(self, team_id: str) -> Team | None: ...
    async def get_team_by_name(self, name: str) -> Team | None: ...
    async def list_teams(self) -> list[Team]: ...
    async def update_team(self, team_id: str, **kwargs) -> Team: ...
    async def delete_team(self, team_id: str) -> bool: ...

    # === Agents ===
    async def create_agent(self, team_id: str, name: str, role: str, **kwargs) -> Agent: ...
    async def get_agent(self, agent_id: str) -> Agent | None: ...
    async def list_agents(self, team_id: str) -> list[Agent]: ...
    async def update_agent(self, agent_id: str, **kwargs) -> Agent: ...
    async def delete_agent(self, agent_id: str) -> bool: ...

    # === Tasks ===
    async def create_task(self, team_id: str, title: str, description: str = "", **kwargs) -> Task: ...
    async def get_task(self, task_id: str) -> Task | None: ...
    async def list_tasks(self, team_id: str, status: TaskStatus | None = None) -> list[Task]: ...
    async def update_task(self, task_id: str, **kwargs) -> Task: ...

    # === Events ===
    async def create_event(self, event_type: str, source: str, data: dict) -> Event: ...
    async def list_events(self, event_type: str | None = None, source: str | None = None, limit: int = 50) -> list[Event]: ...

    # === Memories ===
    async def create_memory(self, scope: str, scope_id: str, content: str, metadata: dict | None = None) -> Memory: ...
    async def get_memory(self, memory_id: str) -> Memory | None: ...
    async def list_memories(self, scope: str, scope_id: str) -> list[Memory]: ...
    async def search_memories(self, scope: str, scope_id: str, query: str, limit: int = 5) -> list[Memory]: ...
    async def delete_memory(self, memory_id: str) -> bool: ...
```

---

## 2. Memory Layer 接口

### MemoryStore (`memory/store.py`)

记忆管理的高级接口，封装三温度逻辑。

```python
class MemoryStore:
    """三温度记忆管理."""

    def __init__(self, repository: StorageRepository) -> None: ...

    async def store(self, scope: str, scope_id: str, content: str, metadata: dict | None = None) -> str:
        """存储记忆，返回memory_id."""

    async def retrieve(self, scope: str, scope_id: str, query: str, limit: int = 5) -> list[Memory]:
        """检索相关记忆（M1: 关键词匹配, M2: 向量搜索）."""

    async def get_context(self, agent_id: str, task: str) -> str:
        """为Agent构建上下文字符串（记忆摘要）."""

    async def list_all(self, scope: str, scope_id: str) -> list[Memory]:
        """列出指定作用域的所有记忆."""

    async def delete(self, memory_id: str) -> bool:
        """删除记忆."""
```

### ContextRecovery (`memory/recovery.py`)

上下文恢复管理。

```python
class ContextRecovery:
    """上下文耗尽时的恢复机制."""

    async def create_checkpoint(self, agent_id: str, state: dict) -> str:
        """创建检查点，返回checkpoint_id."""

    async def restore_checkpoint(self, checkpoint_id: str) -> dict:
        """恢复检查点状态."""

    async def list_checkpoints(self, agent_id: str) -> list[dict]:
        """列出Agent的所有检查点."""
```

---

## 3. Orchestrator Layer 接口

### TeamManager (`orchestrator/team_manager.py`)

团队管理的核心入口，CLI和API都通过此接口操作。

```python
from aiteam.types import Team, Agent, Task, TaskResult, TeamStatus

class TeamManager:
    """团队管理器 — 所有团队操作的统一入口."""

    def __init__(self, repository: StorageRepository, memory: MemoryStore) -> None: ...

    # === 团队管理 ===
    async def create_team(self, name: str, mode: str = "coordinate", config: dict | None = None) -> Team: ...
    async def get_team(self, name_or_id: str) -> Team: ...
    async def list_teams(self) -> list[Team]: ...
    async def delete_team(self, name_or_id: str) -> bool: ...
    async def set_mode(self, name_or_id: str, mode: str) -> Team: ...

    # === Agent管理 ===
    async def add_agent(self, team_name: str, name: str, role: str,
                        system_prompt: str = "", model: str = "claude-opus-4-6") -> Agent: ...
    async def remove_agent(self, team_name: str, agent_name: str) -> bool: ...
    async def list_agents(self, team_name: str) -> list[Agent]: ...

    # === 任务执行 ===
    async def run_task(self, team_name: str, task_description: str, **kwargs) -> TaskResult: ...
    async def get_task_status(self, task_id: str) -> Task: ...
    async def list_tasks(self, team_name: str) -> list[Task]: ...

    # === 状态 ===
    async def get_status(self, team_name: str | None = None) -> TeamStatus: ...
```

### Graph接口 (`orchestrator/graphs/*.py`)

每种编排模式实现同一接口：

```python
from langgraph.graph import StateGraph

def build_coordinate_graph(agents: list[Agent], memory: MemoryStore) -> StateGraph:
    """构建Coordinate模式的StateGraph."""

def build_broadcast_graph(agents: list[Agent], memory: MemoryStore) -> StateGraph:
    """构建Broadcast模式的StateGraph. [M2]"""
```

### Node接口 (`orchestrator/nodes/*.py`)

```python
from aiteam.types import TeamState

async def leader_plan_node(state: TeamState) -> dict:
    """Leader分析任务并制定执行计划."""

async def agent_execute_node(state: TeamState, config: dict) -> dict:
    """Agent执行分配的子任务."""

async def leader_synthesize_node(state: TeamState) -> dict:
    """Leader综合各Agent输出，生成最终结果."""
```

---

## 4. CLI Layer 接口

### CLI命令 → TeamManager 映射

| CLI命令 | TeamManager方法 |
|---------|----------------|
| `aiteam init` | 生成aiteam.yaml（不调用TeamManager） |
| `aiteam team create --name X --mode Y` | `create_team(name, mode)` |
| `aiteam team list` | `list_teams()` |
| `aiteam team show X` | `get_team(X)` |
| `aiteam team delete X` | `delete_team(X)` |
| `aiteam agent create --team X --name Y --role Z` | `add_agent(X, Y, Z)` |
| `aiteam agent list --team X` | `list_agents(X)` |
| `aiteam task run --team X --task "..."` | `run_task(X, "...")` |
| `aiteam task status ID` | `get_task_status(ID)` |
| `aiteam status` | `get_status()` |

---

## 5. 配置模型

### ProjectConfig (`config/settings.py`)

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class InfrastructureConfig(BaseModel):
    storage_backend: Literal["sqlite", "postgresql"] = "sqlite"
    memory_backend: Literal["file", "mem0"] = "file"
    dashboard_port: int = 3000
    api_port: int = 8000
    db_url: str = "sqlite+aiosqlite:///aiteam.db"

class DefaultsConfig(BaseModel):
    model: str = "claude-opus-4-6"
    max_context_ratio: float = 0.8

class AgentConfig(BaseModel):
    name: str
    role: str
    system_prompt: str = ""
    model: str | None = None  # 继承defaults

class LeaderConfig(AgentConfig):
    pass

class TeamConfig(BaseModel):
    name: str
    mode: Literal["coordinate", "broadcast", "route", "meet"] = "coordinate"
    leader: LeaderConfig | None = None
    members: list[AgentConfig] = []

class ProjectConfig(BaseModel):
    """aiteam.yaml 的完整配置模型."""
    project: dict[str, str] = {"name": "", "description": "", "language": "zh"}
    defaults: DefaultsConfig = DefaultsConfig()
    infrastructure: InfrastructureConfig = InfrastructureConfig()
    team: TeamConfig | None = None
```

---

## 6. 共享类型索引

所有类型定义在 `src/aiteam/types.py`，各模块**只引用不定义**：
- `Team`, `Agent`, `Task`, `Memory`, `Event` — 数据模型
- `TeamState` — LangGraph状态
- `TaskResult`, `TeamStatus` — 结果类型
- `TaskStatus`, `AgentStatus` — 枚举
- `OrchestrationMode` — 编排模式枚举
