# 方案A：部门命名约定验证报告

**验证日期**: 2026-03-20
**验证人**: dept-validator
**结论**: **可行** — 命名约定已有天然基础，最小实现成本低

---

## 一、现有 Agent 命名分析

数据库中当前共 **196 个 agents**，其中 **174 个（89%）已使用连字符前缀命名**。

现有典型部门前缀分布：

| 部门前缀 | 代表 agents | 数量 |
|----------|-------------|------|
| `qa-` | qa-observer, qa-tester, qa-reviewer, qa-architect | 5 |
| `frontend-` | frontend-dev, frontend-developer, frontend-engineer, frontend-fixer | 6 |
| `backend-` | backend-dev, backend-hooks, backend-optimizer, backend-reaper | 6 |
| `rd-` | rd-researcher | 1 |
| `ops-` | ops-researcher | 1 |

结论：**命名约定已在实践中自然形成**，无需强制迁移，只需标准化和统一。

---

## 二、Dashboard 分组可行性分析

### 当前渲染逻辑（ProjectDetailPage.tsx:226-229）

```tsx
const agents = (agentsData?.data ?? []).filter((a) => a.role !== 'leader');
const sortedAgents = useMemo(() => {
  const priority: Record<string, number> = { busy: 0, waiting: 1, offline: 2 };
  return [...agents].sort((a, b) => ...);
}, [agents]);
```

**现状**：agents 按状态排序后平铺渲染（`grid gap-3`），无分组结构。

### 实现分组的改动评估

只需在前端加一个 `groupBy` 函数，将 `sortedAgents` 按 `name.split('-')[0]` 分桶，无需后端变更：

```tsx
// 新增：按名称前缀分组
const deptGroups = useMemo(() => {
  const groups: Record<string, Agent[]> = {};
  for (const agent of sortedAgents) {
    const dept = agent.name.includes('-')
      ? agent.name.split('-')[0]
      : 'other';
    (groups[dept] ??= []).push(agent);
  }
  return groups;
}, [sortedAgents]);
```

渲染时改为按分组输出，每组加部门标题。**仅前端 ~30 行改动，零后端变更**。

---

## 三、工作流提醒/任务匹配按部门过滤分析

### 当前 TaskMatcher 逻辑（auto_assign.py:14）

```python
idle_agents = [a for a in agents if a.status in ("waiting", "offline") and a.role != "leader"]
```

**已有 name 字段**，且 `agent.name` 直接可取前缀。扩展为按部门过滤只需：

```python
def get_dept(name: str) -> str:
    return name.split('-')[0] if '-' in name else 'general'

# 按部门分桶查找 idle agents
dept_idle = {get_dept(a.name): a for a in idle_agents}
```

同时，tasks 表已有 `tags` 字段（JSON 数组），可在 tags 中加入部门标签（如 `["qa", "testing"]`），匹配逻辑天然支持。

**评估**：零 schema 变更，仅需扩展现有匹配逻辑 ~10 行。

---

## 四、方案A 最小实现规范

### 4.1 Agent 命名规范

| 部门 | 前缀 | 示例 |
|------|------|------|
| 质量保障 | `qa-` | qa-lead, qa-tester, qa-reviewer |
| 工程前端 | `eng-fe-` | eng-fe-dev, eng-fe-qa |
| 工程后端 | `eng-be-` | eng-be-dev, eng-be-arch |
| 研发 | `rd-` | rd-researcher, rd-prototyper |
| 运营 | `ops-` | ops-monitor, ops-deploy |
| 通用/跨部门 | `gen-` 或无前缀 | gen-coordinator, Leader |

**注意**：现有 `frontend-`/`backend-` 前缀已足够表达工程部门，不强制迁移为 `eng-fe-`/`eng-be-`，保持向后兼容。

### 4.2 Dashboard 分组显示（最小实现）

修改文件：`dashboard/src/pages/ProjectDetailPage.tsx`

改动范围（ActiveTeamContent 组件内）：
1. 新增 `deptGroups` useMemo 计算分组
2. 渲染改为：部门标题 + 该部门 agents grid

### 4.3 工作流按部门过滤（可选扩展）

修改文件：`src/aiteam/loop/auto_assign.py`

改动：在 `find_matches` 中提取 agent 前缀，优先匹配 task tags 包含对应部门名的 agents。

---

## 五、验收标准达成评估

| 验收标准 | 状态 | 说明 |
|----------|------|------|
| Dashboard 能按部门分组显示 agents | **可实现** | 仅需前端 ~30 行，零 schema 变更 |
| Leader 能按部门筛选查看状态 | **可实现** | Dashboard 分组后天然支持，或加 API filter 参数 |
| 工作流提醒能区分部门 | **可实现** | auto_assign.py 扩展 ~10 行 |
| 无需新增数据库表/字段 | **满足** | 复用现有 name 字段提取前缀 |
| 向后兼容现有 agents | **满足** | 无前缀 agents 归入 'other' 组 |

---

## 六、方案A vs 方案B 对比

| 维度 | 方案A（命名约定） | 方案B（department 字段） |
|------|-----------------|------------------------|
| 实现成本 | 极低（前端~30行） | 中（schema迁移+API+UI） |
| 向后兼容 | 完全兼容 | 需数据迁移 |
| 灵活性 | 依赖命名纪律 | 可独立设置，更灵活 |
| 查询效率 | 需字符串解析 | 可索引查询 |
| 推荐场景 | 当前阶段 MVP | 未来正式多部门组织 |

**结论**：方案A 是当前阶段的最优选择，可立即实施，成本极低，且不排除未来升级为方案B。

---

## 七、实施建议

**优先级排序**：
1. **立即可做**：Dashboard 分组显示（高可见度，低风险）
2. **按需实施**：auto_assign 部门过滤（当实际有多部门 agents 并发时）
3. **文档补充**：在 CLAUDE.md 中添加命名约定说明

**不建议做**：
- 强制迁移现有 agents 命名（历史数据太多，收益不大）
- 为命名约定增加 API 验证（过度工程化）
