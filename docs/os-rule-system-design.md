# AI Team OS 规则体系与行为绑定设计文档

> 基于 2026-03-20 架构讨论会议 (ID: 203df3e4) 的结论
> 参与者: rule-architect, deployment-designer, enforcement-designer
> 状态: Accepted

---

## 1. 设计原则

### 1.1 核心理念：纵深防御（Defense in Depth）

不依赖任何单一机制确保规则遵守。四层防线各有侧重，任何一层失效时其他层仍能提供保护。

### 1.2 五条设计原则

1. **按工具类型选择执行方式** — deny/exit(2) 只用于可靠阻断的工具类型（Bash/Agent），对 Write/Edit 使用替代方案
2. **MCP 端验证是最可靠的强制机制** — OS 自己的 MCP 工具在 handler 中做前置校验，100% 不可绕过
3. **信息不重复维护** — 规则的权威来源是 `GET /api/system/rules`，其他层引用或注入，不独立维护副本
4. **子 agent 规则通过冗余覆盖** — 模板 + SubagentStart 双重注入，容忍其中一个被上下文压缩丢失
5. **引导优先于阻断** — 大多数规则通过引导（warn/remind）实现，只有安全类和架构完整性类规则使用硬阻断

### 1.3 关键约束

- CC 子 agent **不继承**父 agent 的 hooks 和 MCP 工具（已确认的平台限制）
- `permissionDecision: "deny"` 对 Bash/Agent 工具可靠，对 Write/Edit 存在漏洞
- Hook 脚本必须在 100ms 内完成（CC 超时限制），复杂逻辑应放在 MCP server 端

---

## 2. 四层防线架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: CLAUDE.md（意识层）                                    │
│  CC 启动时读取，建立"这是 OS 管理项目"的认知                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: SessionStart Hook（引导层）                             │
│  会话开始注入完整规则集 + 任务墙 + 团队状态                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: PreToolUse Hook（执法层）                               │
│  运行时拦截工具调用，deny 危险操作 / warn 不合规行为                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: MCP Tool 内置校验（契约层）                              │
│  OS 工具在 handler 中验证前置条件，100% 不可绕过                    │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1: CLAUDE.md — 意识层

**职责**：让 CC 知道"这是一个 OS 管理的项目"，建立基本认知框架

**实现方式**：
- 项目级 `CLAUDE.md` 中用 HTML marker 包裹 OS section
- 内容极简（5-8 行），不写完整规则
- 安装时通过 `install.py` 写入/更新，不破坏用户已有内容

**CLAUDE.md OS Section 标准内容**：
```markdown
<!-- AI-TEAM-OS-START -->
## AI Team OS
**技术栈**: Python 3.12 + FastAPI | React 19 + Vite | SQLite
**架构**: Storage -> API -> Dashboard (docs/architecture.md)

## 核心约束
- 所有输出使用中文
- 共享类型只引用 `src/aiteam/types.py`
- 代码风格: PEP 8, 类型注解, async 优先

## Leader 核心行为
- 专注统筹，实施工作委派团队成员
- 新需求先加入任务墙，系统级功能先写设计文档
- 完整规则通过 SessionStart 自动注入，也可查询 GET /api/system/rules
<!-- AI-TEAM-OS-END -->
```

**覆盖的规则**：无具体规则强制——仅建立认知
**强度**：最弱（CC 可能忽略或在长对话中遗忘）
**优势**：CC 原生机制，零延迟，每次对话都加载

### Layer 2: SessionStart Hook — 引导层

**职责**：会话开始时注入完整上下文，为 CC 提供全面的行为指引

**实现方式**：
- `session_bootstrap.py` 在 SessionStart 时执行
- 从 API 动态获取规则集、任务墙、团队状态
- 输出到 stdout 作为 system-level context 注入

**注入内容**：
1. 完整 Leader 行为规则（所有 B 类规则）
2. 任务墙 Top5 + 进行中任务
3. 团队状态（活跃团队、成员数）
4. 可用 Agent 模板列表
5. 可用 Skills 列表

**覆盖的规则**：所有 B 类（advisory）规则
**强度**：中等（作为 system context 注入，CC 高度重视）
**劣势**：一次性注入，长对话后可能被 compact 压缩

### Layer 3: PreToolUse Hook — 执法层

**职责**：运行时拦截每一次工具调用，对危险操作硬阻断，对不合规行为软警告

**实现方式**：
- `workflow_reminder.py` 在 PreToolUse 时执行
- 根据规则分级返回 `permissionDecision: "deny"` 或 `additionalContext` 警告
- matcher 配置：`Agent|Bash|Edit|Write|Read`

**三级执法策略**：

```python
ENFORCEMENT_LEVELS = {
    # Level 3a: 硬阻断 — permissionDecision: "deny"
    # 仅用于 Bash 和 Agent 工具（deny 可靠的场景）
    "hard_block": {
        "triggers": ["Bash", "Agent"],
        "rules": [
            "S1_dangerous_rm",          # rm -rf / 或 ~/
            "S1_db_destructive",        # DROP TABLE / TRUNCATE
            "S1_force_push",            # git push --force
            "S3_sensitive_git_add",     # git add .env / .pem / credentials
            "B04_agent_no_team_name",   # Agent() 不带 team_name
        ]
    },
    # Level 3b: 软警告 — additionalContext 注入警告文本
    "soft_warn": {
        "triggers": ["Bash", "Edit", "Write", "Agent"],
        "rules": [
            "S2_hardcoded_secrets",     # Write/Edit 中硬编码密钥
            "S2_env_file_write",        # 写入 .env 文件
            "S2_chmod_777",             # 过度开放权限
            "B09_leader_too_many",      # Leader 连续执行过多工具调用
            "B010_missing_permanent",   # 缺少常驻成员
            "TASKWALL_stale",           # 长时间未查看任务墙
        ]
    },
    # Level 3c: 信息提示 — additionalContext 注入提示
    "info": {
        "triggers": ["Agent", "SendMessage"],
        "rules": [
            "MEMO_reminder",            # 提醒读取历史 memo
            "PARALLEL_suggestion",      # 建议并行分配空闲 Agent
            "HANDOFF_reminder",         # Agent 完成后提醒分配后续
            "MEETING_notify",           # 会议创建后提醒通知参与者
        ]
    }
}
```

**覆盖的规则**：安全类（S1-S3）+ 部分 B 类规则的运行时提醒
**强度**：对 Bash/Agent 最强（可硬阻断），对 Write/Edit 中等（仅警告）
**当前改进重点**：启用 `permissionDecision: "deny"`（当前从未使用）

### Layer 4: MCP Tool 内置校验 — 契约层

**职责**：OS 自己的 MCP 工具在执行时验证前置条件，拒绝不合规操作

**实现方式**：
- 在各 MCP tool handler 中添加前置校验逻辑
- 校验失败返回明确错误信息，指导 CC 如何修正

**校验清单**：

| MCP Tool | 校验规则 | 失败响应 |
|----------|---------|---------|
| `task_status(completed)` | 必须有 summary memo | "请先 task_memo_add(type=summary) 记录完成总结" |
| `task_create` | 必须有 title 和 description | "任务必须有标题和描述" |
| `meeting_conclude` | 必须有至少 1 条 action_item | "请先确认会议行动项" |
| `agent_register` | 必须有活跃团队 | "请先 team_create 创建团队" |
| `loop_start` | 必须有 pending 任务 | "任务墙无待办任务，请先创建任务" |

**覆盖的规则**：所有 OS 流程规则（任务管理、会议流程、Agent 生命周期）
**强度**：最强——100% 不可绕过
**劣势**：只能约束 OS 工具的使用，无法约束 CC 原生工具

---

## 3. 规则到执行方式映射表

### 3.1 A 类规则（代码自动执行）

| 规则 ID | 规则名称 | 执行层 | 执行方式 |
|---------|---------|--------|---------|
| A1 | Agent 主动注册 | Layer 4 | MCP handler 自动处理 |
| A2 | Hook 自动兜底 | Layer 3 | hook_translator 自动处理 |
| A3 | SubagentStop->等待 | Layer 3 | hook_translator 自动处理 |
| A4 | SessionEnd->关闭 | Layer 3 | hook_translator 自动处理 |
| A5 | Stop->关闭 | Layer 3 | hook_translator 自动处理 |
| A6 | 状态自愈 | Layer 3 | hook_translator 自动处理 |
| A7 | 注册即工作 | Layer 4 | MCP handler 默认 busy |
| A8 | Session-Leader 复用 | Layer 3 | hook_translator 自动处理 |
| A9 | 自动创建项目 | Layer 3 | hook_translator 自动处理 |
| A10 | 文件编辑冲突检测 | Layer 3 | hook_translator 自动处理 |
| A11 | 热点文件追踪 | Layer 3 | hook_translator 内存追踪 |
| A12 | 工具使用记录 | Layer 3 | hook_translator 自动处理 |
| A13 | current_task 自动提取 | Layer 3+4 | hook_translator + handler |
| A14 | last_active_at 更新 | Layer 3 | hook_translator 自动处理 |
| A15 | 事件总线广播 | Layer 4 | EventBus 自动处理 |
| A16 | 共享类型定义 | Layer 1 | CLAUDE.md 声明 |
| A17 | 任务依赖自动阻塞 | Layer 4 | MCP handler 自动处理 |
| A18 | Hook 统一入口 | Layer 3 | send_event.py 自动处理 |

### 3.2 B 类规则（需人工判断）

| 规则 ID | 规则名称 | 执行层 | 执行方式 |
|---------|---------|--------|---------|
| B0 | Leader 统筹全局 | Layer 2 | SessionStart 注入 |
| B0.1 | 瓶颈时组织讨论 | Layer 2+3c | SessionStart + info 提示 |
| B0.2 | 会议动态成员 | Layer 2 | SessionStart 注入 |
| B0.3 | 成员工具限制上报 | Layer 2 | SessionStart 注入 |
| B0.4 | 添加成员必须用 team_name | Layer 3a | **hard_block (deny)** |
| B0.5 | 任务墙灵活领取 | Layer 2 | SessionStart 注入 |
| B0.6 | 项目记忆维护 | Layer 2+3c | SessionStart + info 提示 |
| B0.7 | 不空等 | Layer 2+3b | SessionStart + soft_warn |
| B0.8 | 新功能同步 QA | Layer 3c | info 提示（task_status completed 时） |
| B0.9 | Leader 专注统筹 | Layer 3b | soft_warn（递增强度） |
| B0.10 | 创建团队含常驻成员 | Layer 3b | soft_warn（周期检查） |
| B0.11 | Leader 设定 agent 当前任务 | Layer 2 | SessionStart 注入 |
| B0.12 | 任务 Memo 追踪 | Layer 3c+4 | info 提示 + MCP 校验 |
| B0.13 | Agent 标准化汇报 | Layer 2 | Agent 模板注入 |
| B0.14 | 行动项必须上墙 | Layer 3c | info 提示（meeting_conclude 后） |
| B1 | 文件驱动协调 | Layer 2 | SessionStart + SubagentStart |
| B2 | Kill vs 保留 Agent | Layer 2 | SessionStart 注入 |
| B3 | 记忆权威层级 | Layer 1+2 | CLAUDE.md + SessionStart |
| B4 | 上下文管理-WARNING | Layer 3b | UserPromptSubmit hook |
| B5 | 上下文管理-CRITICAL | Layer 3b | UserPromptSubmit hook |
| B6 | 会议讨论规则 | Layer 2 | SessionStart + 模板 |
| B6.1 | 会议触发时机 | Layer 2 | SessionStart 注入 |
| B6.2 | 会议参与者通知 | Layer 3c | info 提示（meeting_create 后） |
| B7 | 状态消息长度 | Layer 2 | SessionStart 注入 |
| B8 | 模块测试 | Layer 2 | SessionStart + 模板 |
| B9 | 不做投资建议 | Layer 1 | CLAUDE.md 声明 |

### 3.3 安全规则

| 规则 | 触发工具 | 执行层 | 执行方式 |
|------|---------|--------|---------|
| S1: 危险递归删除 (rm -rf /) | Bash | Layer 3a | **hard_block (deny)** |
| S1: 数据库破坏操作 | Bash | Layer 3a | **hard_block (deny)** |
| S1: force push | Bash | Layer 3a | **hard_block (deny)** |
| S2: 硬编码密钥写入 | Write/Edit | Layer 3b | soft_warn + PostToolUse 审计 |
| S2: .env 文件写入 | Write/Edit | Layer 3b | soft_warn |
| S2: chmod 777 | Bash | Layer 3b | soft_warn |
| S3: git add 敏感文件 | Bash | Layer 3a | **hard_block (deny)** |

---

## 4. 安装体验设计

### 4.1 CLAUDE.md 策略

**原则**：OS 不碰用户的全局 CLAUDE.md (~/.claude/CLAUDE.md)，只管理项目级 CLAUDE.md

**安装时行为**：
1. 检查项目 CLAUDE.md 是否存在
2. 如已存在：检查是否有 `<!-- AI-TEAM-OS-START -->` marker
   - 有 marker：更新 marker 内的内容（保留用户其他内容不变）
   - 无 marker：在文件末尾追加 OS section（用 marker 包裹）
3. 如不存在：创建新文件，写入 OS section

**升级时行为**：
- 只更新 marker 内的内容，用户 marker 外的内容完全不动
- OS section 内容极简，升级几乎不会引起冲突

### 4.2 install.py 增强方案

```python
def install():
    """AI Team OS 安装流程"""
    # 1. 合并 .claude/settings.json — 添加 hooks 配置
    merge_settings_json()  # 保留用户已有 hooks，追加 OS hooks

    # 2. 写入/更新项目 CLAUDE.md（marker 包裹）
    update_claude_md()     # 极简 OS section

    # 3. 复制 hook 脚本到 plugin/hooks/（绝对路径）
    install_hooks()        # session_bootstrap, workflow_reminder, send_event 等

    # 4. 复制 Agent 模板到 ~/.claude/agents/
    install_agent_templates()  # 标准化模板含 OS 集成规范

    # 5. 初始化 MCP server 配置
    setup_mcp_config()     # .mcp.json 指向 OS MCP server

    # 6. 健康检查
    health_check()         # 验证 API 可达、hooks 已注册、模板已安装
```

### 4.3 settings.json 合并策略

```python
def merge_settings_json():
    """合并 hooks 到 .claude/settings.json，保留用户已有配置"""
    existing = load_existing_settings()  # 用户已有的 hooks
    os_hooks = {
        "SessionStart": [...],      # session_bootstrap.py
        "PreToolUse": [...],        # workflow_reminder.py + send_event.py
        "PostToolUse": [...],       # send_event.py
        "SubagentStart": [...],     # subagent_context.py (新)
        "SubagentStop": [...],      # send_event.py
        "SessionEnd": [...],        # send_event.py
        "Stop": [...],              # send_event.py
        "UserPromptSubmit": [...],  # context_monitor.py
        "PreCompact": [...],        # pre_compact_save.py
    }
    # 合并：同一事件的 hooks 数组 append，不覆盖
    merged = deep_merge(existing, os_hooks)
    write_settings(merged)
```

---

## 5. 子 Agent 规则继承方案

### 5.1 核心原则：模板 = 角色 DNA，SubagentStart = 入职培训，MCP = 制度兜底

```
子 Agent 启动
    │
    ├─ Agent 模板 (~/.claude/agents/*.md)
    │   └─ 定义「是谁」：角色身份、专业能力、汇报格式、OS 集成简版提醒
    │
    ├─ SubagentStart Hook 注入
    │   └─ 定义「在哪个 OS 里工作」：项目上下文、注册指引、协调规则、安全规则、团队状态
    │
    └─ MCP Tool 校验
        └─ 定义「什么不能做」：流程规则的最终兜底
```

**为什么要冗余？** SubagentStart 注入可能被上下文压缩丢失，模板的 system prompt 保留更久。两者重复提供容错。如果两者都被忽略，MCP tool 拒绝执行不合规操作。

### 5.2 Agent 模板标准结构

```markdown
# {角色名称}

## 身份与记忆
{角色描述、核心能力、工作方式}

## 核心使命
{角色特定的职责列表}

## 不可违反的规则
{角色特定的硬约束}

## OS 集成规范
- 接到任务后第一步：通过 task_memo_read 获取历史上下文
- 执行过程中：关键进展用 task_memo_add 记录
- 完成时：task_memo_add(type=summary) 写入最终总结

## 汇报格式
完成报告：
- **完成内容**：{具体描述}
- **修改文件**：{列表}
- **测试结果**：{通过/失败及详情}
- **建议任务状态**：completed / blocked(原因)
- **建议 memo**：{一句话总结供后续参考}

## 协作规范
- 需要其他角色协助时通过 Leader 协调
- 遵循团队 Loop 节奏，不跳过质量门控
- 不使用 TeamCreate/TeamDelete/task_create（Leader 专属）
- 有问题通过 SendMessage 向 Leader 汇报

## 沟通风格
{角色特定的沟通示例}
```

### 5.3 SubagentStart Hook 注入方案

**技术改造**：将 `inject-context.ps1` 替换为 `subagent_context.py`（Python 脚本）

**注入内容分级**：

#### 通用注入（所有子 agent）
```
=== AI Team OS 项目环境 ===
1. 项目 CLAUDE.md 核心约束（动态读取）
2. OS 注册指引：os_health_check -> agent_register(team_id=当前活跃团队)
3. 文件协调：修改前检查 coordination.md，避免与其他 Agent 冲突
4. 安全规则：不硬编码密钥、不提交 .env、不 force push
5. 汇报规范：完成后使用标准格式通过 SendMessage 汇报 Leader

=== 当前团队状态 ===（动态从 API 获取）
- 团队名称 / 活跃成员 / 进行中任务
```

#### 实施类增强（agent_name 含 dev/engineer/impl）
```
6. 测试要求：每个功能变更需有对应测试
7. 团队成员工作范围（避免文件冲突）
```

#### QA 类增强（agent_name 含 qa/test/observer）
```
6. 验收原则：有罪推定，主动寻找问题
7. 测试覆盖要求与已知盲区
```

#### 研究类增强（agent_name 含 research/analyst）
```
6. 研究输出格式要求
7. memo 记录频率要求
```

### 5.4 Agent 类型检测逻辑

```python
def detect_agent_type(payload: dict) -> str:
    """从 SubagentStart payload 推断 agent 类型"""
    name = (payload.get("agent_name", "") or "").lower()
    prompt = (payload.get("prompt", "") or "").lower()
    combined = f"{name} {prompt}"

    if any(kw in combined for kw in ["qa", "test", "observer", "verify"]):
        return "qa"
    elif any(kw in combined for kw in ["dev", "engineer", "impl", "build", "fix"]):
        return "implementation"
    elif any(kw in combined for kw in ["research", "analyst", "study", "investigate"]):
        return "research"
    else:
        return "general"
```

---

## 6. 脱管场景防范清单

### 6.1 场景分析

| 脱管场景 | 风险等级 | 防范机制 | 剩余风险 |
|----------|---------|---------|---------|
| CC 不读 CLAUDE.md | 低 | SessionStart hook 注入规则（Layer 2 补位） | 无 |
| CC 忘记 SessionStart 注入的规则（被 compact） | 中 | PreToolUse hook 持续提醒（Layer 3 补位） | 低 |
| CC 直接用 Bash/Edit/Write 不用 MCP 工具 | 中 | PreToolUse hook 拦截所有原生工具调用 | 低：Write/Edit deny 有漏洞 |
| CC 大量代码操作但不用任何 OS 工具 | 中 | 行为审计：连续 N 次原生工具调用无 OS 工具时注入提醒 | 低：CC 仍看到提醒 |
| 子 agent 不注册到 OS | 中 | SubagentStart hook 注入注册指引 + 模板中强调 | 中：子 agent 可忽略 |
| 子 agent 完全忽略所有规则 | 中 | MCP 工具拒绝不合规操作（Layer 4 兜底） | 低：子 agent 绕过 MCP 就无法管理任务 |
| 用户绕过 OS 直接使用 CC | 不可防 | SessionStart hook 仍会注入（只要 hooks 存在） | 用户有权绕过 |

### 6.2 行为审计机制（新增）

在 `workflow_reminder.py` 中增加行为审计逻辑：

```python
def _check_os_engagement(state: dict) -> str | None:
    """检测 CC 是否长期不使用 OS 工具（脱管检测）"""
    native_calls = state.get("consecutive_native_calls", 0)

    # 每次 OS MCP 工具调用（task_*, meeting_*, agent_* 等）重置计数
    # 每次原生工具调用（Bash/Edit/Write/Read）增加计数

    if native_calls > 30:
        return (
            "[AI Team OS] 已连续 {native_calls} 次工具调用未使用 OS 管理工具。"
            "当前工作是否已在任务墙上？是否需要记录进度？"
            "-> taskwall_view 查看任务 | task_memo_add 记录进度"
        )
    elif native_calls > 15:
        return (
            "[AI Team OS] 提醒：距上次使用 OS 工具已较久，"
            "建议 taskwall_view 同步任务状态"
        )
    return None
```

### 6.3 终极兜底认知

**CC 不用工具就做不了实质工作**（不能编辑文件、不能运行命令）。因此 PreToolUse hook 覆盖 `Bash|Edit|Write|Read|Agent` 就是事实上的全覆盖。唯一漏洞是 Write/Edit 的 deny 可能不生效，但通过 soft_warn + PostToolUse 审计可以有效补偿。

---

## 7. 实施优先级

### P0 — 立即实施（高收益、低成本）

| 任务 | 文件 | 改动量 | 预期效果 |
|------|------|--------|---------|
| workflow_reminder.py 启用 deny | `plugin/hooks/workflow_reminder.py` | ~30 行 | 安全类规则从"建议"升级为"阻断" |
| SubagentStart hook 改为 Python | 新建 `plugin/hooks/subagent_context.py` + 更新 `.claude/settings.json` | ~100 行 | 子 agent 从"几乎不知道 OS"到"了解核心规则" |
| Hook 配置统一到 settings.json | `.claude/settings.json` | 配置调整 | 消除 hooks.json vs settings.json 双轨问题 |

### P1 — 短期实施（中等收益、中等成本）

| 任务 | 文件 | 改动量 | 预期效果 |
|------|------|--------|---------|
| install.py 增强（settings.json 合并 + CLAUDE.md marker） | `plugin/install.py` | ~150 行 | 新用户安装体验标准化 |
| 行为审计逻辑（脱管检测） | `plugin/hooks/workflow_reminder.py` | ~40 行 | 检测 CC 长期不用 OS 工具 |
| Agent 模板标准化 | `~/.claude/agents/*.md` | 每个模板 +10 行 | 所有模板包含 OS 集成规范 |

### P2 — 中期实施（中等收益、较大成本）

| 任务 | 文件 | 改动量 | 预期效果 |
|------|------|--------|---------|
| MCP 工具内置前置校验 | `src/aiteam/api/routes/*.py` | 每个 handler +10-20 行 | 流程规则 100% 强制 |
| PostToolUse 审计（Write/Edit 安全补偿） | `plugin/hooks/workflow_reminder.py` + API | ~80 行 | 补偿 Write/Edit deny 漏洞 |
| 规则 A/B 分类重构（统一到 rules engine） | 新建 `src/aiteam/rules/` | ~200 行 | 规则管理标准化 |

---

## 8. 架构决策记录（ADR）

### ADR-001: deny/exit(2) 硬阻断的边界

**状态**: Accepted

**上下文**: AI Team OS 需要确保 CC 遵守安全规则和架构完整性规则。CC hooks 的 `permissionDecision: "deny"` 可以阻断工具调用，但经调研发现对 Write/Edit 工具可能存在漏洞。

**决策驱动因素**:
- exit(2)/deny 对 Bash 工具可靠阻断
- exit(2)/deny 对 Write/Edit 工具存在漏洞（可能不完全阻断）
- Agent 工具的 deny 行为需要验证但预期可靠
- 过度使用 deny 会卡住正常工作流

**备选方案**:

方案 A: 所有规则都用 deny
- 优势：统一机制，实现简单
- 劣势：Write/Edit deny 不可靠；工作流规则 deny 会卡住 CC
- 成本：低

方案 B: 按工具类型分级（选定方案）
- 优势：在可靠的地方用 deny，不可靠的地方用替代方案
- 劣势：实现稍复杂，需维护分级逻辑
- 成本：中

方案 C: 完全不用 deny，全部靠 MCP 验证
- 优势：最简单，MCP 验证 100% 可靠
- 劣势：无法约束 CC 原生工具（Bash/Edit/Write）的危险操作
- 成本：低

**决策**: 选择方案 B — 按工具类型分级

**理由**: Bash 类操作（rm -rf、DROP TABLE、force push）和 Agent 操作（缺 team_name）是最需要硬阻断的场景，而 deny 在这些工具上可靠。Write/Edit 的安全问题通过 soft_warn + PostToolUse 审计补偿。工作流规则（B0.9 等）只用 warn 不 block。

**后果**:
- 正面：安全类规则得到真正的硬阻断；不会卡住正常工作流
- 负面：Write/Edit 的安全校验仍是建议性的
- 风险：Agent 工具的 deny 行为需实际验证；如不可靠则退化为 warn

---

### ADR-002: CLAUDE.md 内容策略

**状态**: Accepted

**上下文**: AI Team OS 安装后需要让 CC 知道项目受 OS 管理，但 CLAUDE.md 中写多少 OS 内容存在争议。

**决策驱动因素**:
- CC 对 CLAUDE.md 不是 100% 遵守
- SessionStart hook 可以注入完整规则
- 用户可能已有 CLAUDE.md 内容
- 规则在两处维护会不同步
- 用户打开项目看到大段 OS 规则体验差

**备选方案**:

方案 A: CLAUDE.md 写完整规则
- 优势：不依赖 SessionStart hook
- 劣势：内容冗长；升级易冲突；与 SessionStart 重复维护
- 成本：高维护成本

方案 B: CLAUDE.md 写极简指针（选定方案）
- 优势：不打扰用户；维护成本低；升级无冲突
- 劣势：依赖 SessionStart 注入完整规则
- 成本：低

方案 C: 不写 CLAUDE.md，完全依赖 SessionStart
- 优势：零侵入
- 劣势：SessionStart 之前 CC 不知道 OS 存在
- 成本：最低

**决策**: 选择方案 B — 极简指针 + HTML marker 包裹

**理由**: CLAUDE.md 的价值是"第一印象"（让 CC 知道 OS 存在），不是"规则手册"。5-8 行足以建立认知。完整规则通过 SessionStart 注入更可靠且不会与 CLAUDE.md 不同步。HTML marker 保证升级时只更新 OS section。

**后果**:
- 正面：用户 CLAUDE.md 不被大段 OS 规则污染；维护简单
- 负面：如果 SessionStart hook 失效，CC 只有极简的规则认知
- 风险：SessionStart hook 是单点依赖，需确保其可靠性

---

### ADR-003: 子 Agent 规则注入策略

**状态**: Accepted

**上下文**: CC 子 agent 不继承父 agent 的 hooks 和 MCP 工具。需要设计可靠的方式将 OS 规则传递给子 agent。

**决策驱动因素**:
- 子 agent 不继承 hooks（平台限制）
- 子 agent 不继承 MCP 工具（平台限制）
- SubagentStart hook 可注入 additionalContext
- Agent 模板 (~/.claude/agents/*.md) 定义角色
- SubagentStart 注入可能被上下文压缩丢失

**备选方案**:

方案 A: 只靠 Agent 模板
- 优势：模板是 system prompt，保留时间长
- 劣势：模板是静态的，无法注入动态团队状态
- 成本：低

方案 B: 只靠 SubagentStart 注入
- 优势：可动态获取 API 数据
- 劣势：注入内容可能被压缩丢失
- 成本：低

方案 C: 模板 + SubagentStart 双重保障（选定方案）
- 优势：冗余容错；静态角色 + 动态环境完美互补
- 劣势：部分内容有意重复
- 成本：中

**决策**: 选择方案 C — 双重保障 + 按角色分级

**理由**: 模板定义"是谁"（角色身份、专业能力、汇报格式），SubagentStart 注入"在哪个 OS 里工作"（项目上下文、注册指引、协调规则、安全规则、动态团队状态）。OS 集成规范在两处都出现（有意冗余），防止任一来源被压缩丢失。SubagentStart 按 agent 名称关键词分级注入不同角色的增强规则。

**后果**:
- 正面：子 agent 规则覆盖从"4 行提醒"提升到"完整 OS 认知"
- 负面：有意的内容重复可能让 agent 上下文稍微冗长
- 风险：agent 类型检测基于名称关键词，命名不规范时可能误判（退化为通用注入，可接受）

---

## 附录：相关文件清单

| 文件 | 用途 | 改造需求 |
|------|------|---------|
| `plugin/hooks/workflow_reminder.py` | PreToolUse/PostToolUse 执法 | P0: 启用 deny |
| `plugin/hooks/session_bootstrap.py` | SessionStart 规则注入 | 当前已完善 |
| `.claude/hooks/inject-context.ps1` | SubagentStart 注入 | P0: 替换为 Python |
| `.claude/settings.json` | CC hooks 配置 | P0: 统一所有 hooks |
| `plugin/hooks/hooks.json` | Plugin hooks 配置（旧） | 废弃，迁移到 settings.json |
| `plugin/hooks/sync_rules.py` | CLAUDE.md 规则同步（已废弃） | 确认废弃，可删除 |
| `src/aiteam/api/routes/system.py` | 规则查询 API | 当前已完善 |
| `plugin/hooks/context_monitor.py` | 上下文使用率监控 | P1: 增加行为审计 |
| `~/.claude/agents/*.md` | Agent 模板 | P1: 标准化 OS 集成规范 |
