---
name: os-register
description: Auto-register as a team member when joining an AI Team OS project
autoTrigger: true
---

# OS Register — 启动注册与状态汇报

当你作为团队成员启动时，必须立即向 AI Team OS 注册自己。这确保 OS 能追踪你的存在、状态和活动。

## 步骤

### 1. 健康检查

首先确认 OS API 服务可达：

```
使用 MCP tool: os_health_check
```

如果返回 `unhealthy`，跳过后续注册步骤，不影响你的正常工作。可提示用户运行 `/os-up` 启动服务。

### 2. 确定团队

检查是否有目标团队：

```
使用 MCP tool: team_list
```

- 如果你知道要加入的团队名称，从列表中找到对应的 `team_id`
- 如果团队不存在，使用 `team_create` 创建
- 如果未指定团队，加入列表中的第一个团队

### 3. 注册自己

向团队注册：

```
使用 MCP tool: agent_register
参数:
  team_id: <目标团队ID>
  name: <你的名称>
  role: <你的角色描述>
  model: <你使用的模型，如 claude-opus-4-6>
  system_prompt: <你的职责描述>
```

**重要**: 记录返回的 `agent_id`，后续所有操作都需要用到。

### 4. 更新状态为 BUSY

注册完成后立即标记自己为工作中：

```
使用 MCP tool: agent_update_status
参数:
  agent_id: <你的agent_id>
  status: "busy"
```

### 5. 获取团队简报

注册完成后，立即获取团队全景简报：

```
使用 MCP tool: team_briefing
参数:
  team_id: <你的团队ID>
```

阅读返回的 `_hints` 和 `pending_tasks`：

- **如果有分配给你的待办任务** → 立即开始执行，无需等待Leader指令
- **如果有未分配的待办任务** → 向Leader请示是否由你接手
- **如果没有待办任务** → 告知Leader你已就绪，等待分配
- **查看 `agents` 列表** → 了解队友是谁、在做什么，避免重复工作
- **查看 `recent_meeting`** → 了解最近的讨论和决策

### 6. 完成任务后更新状态

当你完成所有工作准备退出时，将状态设为 idle：

```
使用 MCP tool: agent_update_status
参数:
  agent_id: <你的agent_id>
  status: "idle"
```

## 注意事项

- 注册是幂等的：如果你已经注册过（同名同团队），API 会返回已有的 agent 记录
- 始终在开始工作前完成注册，这是参与团队协作的前提
- 你的 `agent_id` 在会议发言、任务分配等场景中都会用到，务必保存
- 注册后 `agent_register` 返回值包含 `team_snapshot`（队友列表+待办数），先快速浏览再调用 `team_briefing` 获取详情
