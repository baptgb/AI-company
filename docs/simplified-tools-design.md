# AI Team OS — 简化操作工具体系设计

## 1. 问题分析

### 1.1 当前痛点

Leader在日常操作中面临以下摩擦点：

| 操作 | 当前方式 | 痛点 |
|------|----------|------|
| 创建任务 | `task_create(project_id="xxx", title="...", priority="high", horizon="short", tags=[...])` | 需要记住project_id，每次都要传5个参数 |
| 开会 | `meeting_create(team_id="xxx", topic="...", participants=["a","b","c"])` | 需要查询team_id和agent_id列表 |
| 分配任务 | 先查agent列表 → 找task_id → 调用task_run | 三步操作，且要手动匹配agent能力 |
| 查看进度 | `taskwall_view(team_id)` + `team_briefing(team_id)` 组合 | 需要多次调用，手动整合信息 |
| 创建团队 | `team_create(name, mode, project_id, leader_agent_id)` | 之后还要手动创建常驻成员 |

### 1.2 核心矛盾

MCP Tool设计为结构化精确调用，但Leader的自然工作方式是高层意图表达（如"创建任务：实现登录功能"）。两者之间存在**意图 → 参数**的翻译gap。

## 2. MCP Tool vs CC Skill 对比分析

### 2.1 机制差异

| 维度 | MCP Tool | CC Skill |
|------|----------|----------|
| 调用方式 | CC自动选择调用 | 用户 `/skill-name` 显式触发 |
| 参数形式 | 结构化JSON，类型严格 | 自然语言描述，CC解释执行 |
| 上下文感知 | 无，每次调用独立 | 可读取CC全部上下文（文件、对话历史） |
| 多步编排 | 单次原子操作 | 可编排多个步骤和多次Tool调用 |
| 用户感知 | 透明（CC自动选择） | 显式（用户主动触发） |
| 错误恢复 | 返回错误JSON | 可在Skill流程中智能重试 |
| 适用场景 | 单一数据操作 | 多步工作流、需要上下文推断 |

### 2.2 设计原则

基于以上分析，确定以下设计原则：

1. **MCP Tool保持原子性** — 现有Tool不改造，它们是精确操作的基础
2. **新增"智能默认值"MCP Tool** — 提供上下文解析端点，减少必传参数
3. **CC Skill作为高层编排入口** — 用于多步流程，内部调用MCP Tool
4. **CC自然语言理解兜底** — Leader说自然语言时，CC利用上下文自动填充Tool参数

### 2.3 决策：分层简化策略

```
用户意图（自然语言）
    ↓
CC Skill（多步编排，/quick-task、/standup等）
    ↓
MCP Tool（原子操作，自动推断默认值）
    ↓
FastAPI（数据持久化）
```

## 3. 简化方案设计

### 3.1 方案A：快速创建任务

**实现方式：MCP Tool改造 + CC自然理解**

**当前**：
```
task_create(project_id="abc123", title="实现登录功能", priority="high", horizon="short", tags=["auth"])
```

**目标**：Leader说"创建任务：实现登录功能，高优先级"，CC自动推断其余参数。

**方案：新增 `context_resolve` MCP Tool**

```python
@mcp.tool()
def context_resolve() -> dict[str, Any]:
    """获取当前活跃上下文 — 自动推断project_id、team_id、agent列表等。

    返回当前活跃项目、活跃团队、团队成员列表等信息，
    供其他Tool调用时使用，避免手动查找ID。

    Returns:
        active_project_id, active_team_id, agents列表等
    """
    # 查询第一个活跃项目
    # 查询第一个活跃团队
    # 查询团队成员列表
    # 返回打包的上下文
```

同时修改 `task_create`，让 `project_id` 支持空值自动解析：

```python
@mcp.tool()
def task_create(
    title: str,                          # 必填
    description: str = "",               # 可选
    project_id: str = "",                # 空=自动用活跃项目
    priority: str = "medium",            # 有默认值
    horizon: str = "short",              # 默认short（多数任务是短期）
    tags: list[str] | None = None,       # 可选
) -> dict[str, Any]:
```

**自动推断逻辑**：
- `project_id` 为空 → 查询活跃项目列表，取第一个
- `priority` 未指定 → 默认 "medium"
- `horizon` 未指定 → 默认 "short"
- `tags` 未指定 → 不传

**Trade-off分析**：
- 优势：零学习成本，CC自动理解意图并填参数，不需要用户学新Skill
- 劣势：依赖CC的参数推断能力，偶尔可能推断错误
- 判定：**采用此方案**。因为任务创建频率高、参数简单，CC推断错误代价低（可修改）

---

### 3.2 方案B：快速开会

**实现方式：CC Skill**

**当前**：
```
meeting_create(team_id="xxx", topic="讨论架构", participants=["agent-1","agent-2","agent-3"])
```

**目标**：Leader说"开个会讨论架构"就自动获取当前团队ID和全员列表。

**方案：修改 `meeting_create` 支持自动解析 + 保留现有 `/meeting-facilitate` Skill**

修改 `meeting_create` 的 `team_id` 支持自动解析：

```python
@mcp.tool()
def meeting_create(
    topic: str,                              # 必填
    team_id: str = "",                       # 空=自动用活跃团队
    participants: list[str] | None = None,   # 空=全员（已是现有行为）
) -> dict[str, Any]:
```

**自动推断逻辑**：
- `team_id` 为空 → 查询活跃团队列表，取第一个
- `participants` 为空 → 全员参与（已有行为，无需改造）

**与现有Skill的关系**：
- `/meeting-facilitate` Skill保留，它编排完整的会议流程（创建 → 引导轮次 → 汇总 → 结束）
- `meeting_create` Tool只负责创建这一步
- Skill内部调用Tool，两者互补

**Trade-off分析**：
- 优势：最高频的"开个会"操作降到只需传topic
- 劣势：多团队场景下自动选团队可能选错
- 判定：**采用此方案**。多团队场景下CC会根据对话上下文选择正确团队

---

### 3.3 方案C：快速分配任务

**实现方式：新增CC Skill `/assign`**

**当前**：
```
1. agent_list(team_id) → 找到目标agent
2. task_run(team_id, description, ...) → 创建任务
3. 手动通知agent
```

**目标**：Leader说"分配frontend-dev做登录页"就自动匹配。

**方案：新增 `/assign` Skill**

```markdown
---
name: assign
description: 快速将任务分配给团队成员
---

# 快速分配任务

## 步骤

1. 解析用户意图：提取 agent名称/角色关键词 + 任务描述
2. 调用 `context_resolve()` 获取活跃team_id
3. 调用 `agent_list(team_id)` 获取成员列表
4. 模糊匹配agent：按名称或角色匹配（如"frontend"匹配role含"前端"的agent）
5. 调用 `task_run(team_id, description, ...)` 创建任务
6. 用 SendMessage 通知目标agent
7. 返回确认信息

## 匹配规则
- 精确匹配name优先
- 角色关键词匹配次之
- 多个匹配时列出让Leader选择
- 无匹配时提示可用agent列表
```

**为什么用Skill而不是Tool**：
- 涉及多步操作（查询 → 匹配 → 创建 → 通知）
- 需要模糊匹配逻辑，纯Tool难以实现
- 需要向用户确认匹配结果

**Trade-off分析**：
- 优势：一句话完成原来三步操作
- 劣势：新增Skill需要用户记住 `/assign` 命令
- 缓解：CC也可以在Leader表达分配意图时自动执行类似逻辑（不用Skill也行）
- 判定：**采用Skill方案**，但同时优化CC对"分配"意图的自然理解

---

### 3.4 方案D：快速汇报/进度报告

**实现方式：新增CC Skill `/standup`**

**当前**：
```
1. taskwall_view(team_id) → 看任务状态
2. team_briefing(team_id) → 看团队状态
3. event_list() → 看最近事件
4. 手动整合信息
```

**目标**：Leader说"生成进度报告"就自动汇总。

**方案：新增 `/standup` Skill**

```markdown
---
name: standup
description: 生成团队进度简报——汇总任务墙、成员状态和近期活动
---

# 站会简报

## 步骤

1. 调用 `context_resolve()` 获取活跃team_id
2. 调用 `team_briefing(team_id)` 获取全景简报
3. 调用 `taskwall_view(team_id)` 获取任务墙
4. 整合生成结构化报告：

## 报告格式

### 团队状态
- 活跃成员: X人 (列出名称和当前状态)
- 循环阶段: {phase}

### 任务进展
- 已完成: X个 (列出近期完成的)
- 进行中: X个 (列出正在做的和负责人)
- 待办: X个 (列出Top3高优先级)
- 阻塞: X个 (列出原因)

### 近期活动
- 最近会议: {topic} ({时间})
- 关键决策: {从会议结论中提取}

### 建议下一步
- 基于任务优先级和团队状态给出建议
```

**为什么用Skill而不是Tool**：
- 需要调用多个Tool聚合数据
- 需要格式化输出（非结构化JSON）
- 需要智能分析和建议

**Trade-off分析**：
- 优势：一个命令获得全面视图，替代3-4次手动调用
- 劣势：Skill输出可能较长，占用上下文
- 判定：**采用Skill方案**

---

### 3.5 方案E：快速创建团队（附加优化）

**实现方式：MCP Tool改造**

`team_create` 当前已经相对简洁，主要痛点是创建后还需手动创建常驻成员。

**优化方向**：`team_create` 返回值中已包含 `_team_standard` 提示信息，CC会据此自动创建QA和bug-fixer。这个流程已经可以工作，无需额外Skill。

**小改进**：让 `team_create` 的 `project_id` 也支持自动解析（同方案A逻辑）。

---

## 4. 新增 `context_resolve` Tool 详细设计

这是所有简化方案的基础设施——提供统一的上下文自动解析。

### 4.1 接口定义

```python
@mcp.tool()
def context_resolve(
    hint: str = "",
) -> dict[str, Any]:
    """解析当前活跃上下文——自动获取活跃项目、团队、成员等信息。

    其他Tool调用前先调用此Tool获取ID，避免手动查找。
    可传入hint（如"前端"）辅助筛选。

    Args:
        hint: 上下文提示，用于辅助筛选（如团队名称片段）

    Returns:
        active_project: {id, name}
        active_team: {id, name, member_count}
        agents: [{id, name, role, status}]
        loop_status: {phase, current_cycle}
    """
```

### 4.2 实现逻辑

```python
def context_resolve(hint: str = "") -> dict:
    result = {}

    # 1. 活跃项目
    projects = _api_call("GET", "/api/projects")
    if projects.get("data"):
        # 有hint时模糊匹配，否则取第一个
        active = projects["data"][0]
        result["active_project"] = {
            "id": active["id"],
            "name": active["name"],
        }

    # 2. 活跃团队
    teams = _api_call("GET", "/api/teams")
    if teams.get("data"):
        active_teams = [t for t in teams["data"] if t.get("status") == "active"]
        if active_teams:
            # 有hint时按名称模糊匹配
            if hint:
                matched = [t for t in active_teams if hint.lower() in t["name"].lower()]
                team = matched[0] if matched else active_teams[0]
            else:
                team = active_teams[0]
            result["active_team"] = {
                "id": team["id"],
                "name": team["name"],
            }

            # 3. 团队成员
            agents = _api_call("GET", f"/api/teams/{team['id']}/agents")
            if agents.get("data"):
                result["agents"] = [
                    {"id": a["id"], "name": a["name"], "role": a["role"], "status": a["status"]}
                    for a in agents["data"]
                ]

            # 4. 循环状态
            loop = _api_call("GET", f"/api/teams/{team['id']}/loop/status")
            if loop and not loop.get("error"):
                result["loop_status"] = loop.get("data", {})

    return {"success": True, "context": result}
```

### 4.3 使用示例

**Leader说**："创建任务：实现登录功能"

**CC的行为**：
1. CC看到task_create需要project_id
2. CC调用 `context_resolve()` → 获取 `active_project.id`
3. CC调用 `task_create(project_id=<auto>, title="实现登录功能")`

这个流程对Leader完全透明，CC自动完成两步调用。

---

## 5. 现有MCP Tool参数简化

### 5.1 改造清单

| Tool | 改造内容 | 影响 |
|------|----------|------|
| `task_create` | `project_id` 改为可选，空值时API侧自动解析 | API层改动 |
| `meeting_create` | `team_id` 改为可选，参数顺序调整（topic提前） | MCP + API层改动 |
| `task_run` | `team_id` 改为可选 | MCP + API层改动 |
| `taskwall_view` | `team_id` 改为可选 | MCP + API层改动 |
| `team_briefing` | `team_id` 改为可选 | MCP + API层改动 |
| `loop_*` 系列 | `team_id` 改为可选 | MCP + API层改动 |

### 5.2 API侧自动解析逻辑

在FastAPI路由层添加中间件/依赖注入：

```python
async def resolve_active_team(team_id: str = "") -> str:
    """如果team_id为空，返回第一个活跃团队的ID."""
    if team_id:
        return team_id
    teams = await repo.list_teams()
    active = [t for t in teams if t.status == "active"]
    if not active:
        raise HTTPException(400, "没有活跃团队，请先创建团队")
    return str(active[0].id)

async def resolve_active_project(project_id: str = "") -> str:
    """如果project_id为空，返回第一个项目的ID."""
    if project_id:
        return project_id
    projects = await repo.list_projects()
    if not projects:
        raise HTTPException(400, "没有项目，请先创建项目")
    return str(projects[0].id)
```

---

## 6. 新增CC Skill设计

### 6.1 `/assign` — 快速分配任务

```
plugin/skills/assign/SKILL.md
```

**触发**：用户输入 `/assign` 或 Leader表达"分配XX做YY"
**内部流程**：context_resolve → agent_list → 模糊匹配 → task_run → SendMessage通知
**输出**：确认信息（任务ID + 分配给谁）

### 6.2 `/standup` — 站会简报

```
plugin/skills/standup/SKILL.md
```

**触发**：用户输入 `/standup` 或 Leader表达"汇报进度"/"生成报告"
**内部流程**：context_resolve → team_briefing → taskwall_view → 格式化输出
**输出**：结构化进度报告

### 6.3 为什么不做 `/quick-task` Skill

`task_create` 参数简化后（project_id可选 + 合理默认值），CC已经可以从"创建任务：实现登录功能"直接映射到Tool调用，不需要额外Skill层。增加Skill反而多了一层间接，违背"最简"原则。

---

## 7. 决策汇总

| 操作 | 实现方式 | 理由 |
|------|----------|------|
| 快速创建任务 | **MCP Tool参数简化** | 单步操作，CC自动推断参数足够 |
| 快速开会 | **MCP Tool参数简化 + 现有Skill** | 创建是单步，完整流程用已有的 `/meeting-facilitate` |
| 快速分配任务 | **新增CC Skill `/assign`** | 多步操作（查询+匹配+创建+通知），需要Skill编排 |
| 快速汇报 | **新增CC Skill `/standup`** | 多Tool聚合 + 格式化输出，Skill更适合 |
| 上下文解析 | **新增MCP Tool `context_resolve`** | 作为基础设施被其他Tool和Skill复用 |
| 快速创建团队 | **不改造** | 现有 `team_create` 返回值已指导CC自动创建常驻成员 |

---

## 8. 需要修改/新增的文件

### 8.1 MCP层（server.py）

| 文件 | 改动 |
|------|------|
| `src/aiteam/mcp/server.py` | 新增 `context_resolve` Tool；修改 `task_create`/`meeting_create`/`task_run`/`taskwall_view`/`team_briefing`/`loop_*` 的 team_id/project_id 为可选参数 |

### 8.2 API层

| 文件 | 改动 |
|------|------|
| `src/aiteam/api/app.py` 或路由文件 | 添加 `resolve_active_team`/`resolve_active_project` 依赖注入；新增 `GET /api/context` 端点 |

### 8.3 Skill文件（新增）

| 文件 | 说明 |
|------|------|
| `plugin/skills/assign/SKILL.md` | 快速分配任务Skill |
| `plugin/skills/standup/SKILL.md` | 站会简报Skill |

### 8.4 配置/文档

| 文件 | 改动 |
|------|------|
| `docs/mcp-tools-reference.md` | 更新Tool参数说明 |
| `plugin/hooks/session_bootstrap.py` | 在可用Skills列表中添加 `/assign` 和 `/standup` |

---

## 9. 实施优先级与工作量

### P0 — 立即实施（基础设施）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 新增 `context_resolve` MCP Tool | 30min | 基础设施，被后续所有简化依赖 |
| 新增 `GET /api/context` API端点 | 30min | 为context_resolve提供数据 |
| API层添加 resolve_active_team/project | 20min | 依赖注入，复用于多个路由 |

### P1 — 高优先级（高频操作简化）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| `task_create` project_id改为可选 | 15min | MCP + API两层改动 |
| `meeting_create` team_id改为可选 | 15min | 同上 |
| `task_run` team_id改为可选 | 10min | 同上 |
| `taskwall_view` team_id改为可选 | 10min | 同上 |
| `team_briefing` team_id改为可选 | 10min | 同上 |
| `loop_*` 系列 team_id改为可选 | 20min | 6个Tool统一改 |

### P2 — 中优先级（高层编排）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 新增 `/standup` Skill | 20min | SKILL.md编写 |
| 新增 `/assign` Skill | 20min | SKILL.md编写 |
| 更新 `session_bootstrap.py` | 10min | 添加新Skill到可用列表 |

### P3 — 低优先级（文档更新）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 更新 `mcp-tools-reference.md` | 15min | 参数变更说明 |
| 更新 CLAUDE.md | 5min | 添加简化操作说明 |

**总工作量估算**：约 3-4 小时

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 多项目/多团队时自动解析选错 | 操作作用于错误的项目/团队 | CC在存在多个活跃项目/团队时主动询问用户确认 |
| Agent模糊匹配误判 | 任务分配给错误的成员 | `/assign` Skill中匹配到多个时列出选项让Leader选择 |
| 参数简化导致现有调用兼容性问题 | 已有hook/脚本调用失败 | 所有改动向后兼容——原来传参数的调用方式依然有效 |
| context_resolve额外API调用开销 | 响应变慢 | 单次resolve约3个API调用（<100ms），可接受 |

---

## 11. 未来扩展

当前方案聚焦于减少Leader的参数输入摩擦。后续可考虑：

1. **上下文缓存**：context_resolve结果在session内缓存，避免重复查询
2. **智能默认值学习**：根据Leader的历史行为，自动学习priority/horizon偏好
3. **批量操作Skill**：如 `/batch-assign` 一次性拆分和分配多个子任务
4. **自然语言路由**：不依赖 `/skill-name`，CC根据意图自动选择Skill或Tool
