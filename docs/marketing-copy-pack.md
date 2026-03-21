# AI Team OS — Marketing Copy Pack

> 编写日期：2026-03-21
> 用途：多平台宣传文案集合，配合开源发布使用
> GitHub：https://github.com/CronusL-1141/AI-company

---

## 1. Hacker News — Show HN 帖子

**平台**：Hacker News
**字数限制**：标题 < 80字符，正文 200-300 词
**注意事项**：HN 社区厌恶营销话术，尊重技术深度，作者需在线回复评论至少4小时

### 标题

```
Show HN: AI Team OS – Turn Claude Code into a self-managing AI team with 40+ MCP tools
```

### 正文

```
Hi HN, I'm a solo developer who's been using Claude Code daily for the past few months. I kept running into the same wall: CC is great for single-agent tasks, but when a project needs multiple roles working together — architect, frontend dev, QA, tech writer — you end up manually context-switching and losing state between sessions.

So I built AI Team OS, an operating system layer that sits on top of Claude Code via MCP Protocol + Hook System. It lets you spin up multi-agent teams where each agent has a defined role, persistent memory, and structured collaboration patterns.

What it actually does:

- 22 agent templates (backend architect, QA engineer, security reviewer, etc.) — each with tuned system prompts and behavioral rules
- A meeting system with 7 structured templates (brainstorming, tech review, retrospective, etc.) based on frameworks like Six Thinking Hats and DACI
- "Failure Alchemy" — every failed task automatically triggers root cause analysis, stores the pattern as an "antibody" in team memory, and warns future agents before they hit the same issue
- Event-driven task wall with loop engine for automatic task lifecycle management
- Decision timeline — every agent decision is logged with intent, so you can trace why something happened
- React 19 dashboard for visual oversight of the whole team

Tech stack: Python 3.12 + FastAPI backend, MCP server with 40+ tools, React 19 + shadcn/ui dashboard, SQLite (dev) / PostgreSQL (prod).

It's MIT licensed, early stage, and I'd genuinely love feedback on the architecture decisions. The failure learning loop and meeting system are the parts I'm most interested in getting reviewed.

GitHub: https://github.com/CronusL-1141/AI-company
```

---

## 2. Reddit 帖子（3个 Subreddit 版本）

### 2.1 r/ClaudeAI

**平台**：Reddit r/ClaudeAI
**字数限制**：标题 < 300字符，正文建议 300-500 词
**注意事项**：这里的用户是 CC 深度使用者，关注实际使用体验和工作流改善。避免与 CC 官方功能混淆。

**标题**：
```
I built an OS layer for Claude Code that adds multi-agent teams, persistent memory, and structured meetings — open source
```

**正文**：
```
I've been using Claude Code as my primary development tool for a while now. It's incredibly capable for single-agent work, but I kept hitting limitations when projects needed multiple specialized roles working in parallel.

The core frustration: every time I needed CC to switch between "architect mode" and "QA mode" and "frontend dev mode," I was manually managing context, losing state, and repeating instructions. Failures were forgotten between sessions — the same mistakes kept coming back.

So I built AI Team OS — an enhancement layer that runs on top of Claude Code through MCP Protocol and the Hook system. Here's what it adds:

**Multi-agent teams with real structure:**
- 22 ready-to-use agent templates across Engineering (12), Testing (4), Research (3), and Management (3)
- Each agent has a tuned system prompt, behavioral rules, and capability profile
- Intelligent task matching — the system recommends which agent should handle each task based on its characteristics

**Persistent team memory:**
- Agent work products accumulate into searchable team knowledge
- Failures get analyzed and stored as "antibodies" — future agents get early warnings when approaching similar problems
- The AWARE loop: Perceive → Record → Distill → Apply

**Structured collaboration:**
- 7 meeting templates (Brainstorming, Decision Making, Tech Review, Retrospective, Status Sync, Expert Consultation, Conflict Resolution)
- Based on proven methodologies: Six Thinking Hats, DACI, Design Sprint
- Rule: every meeting must produce actionable conclusions

**Transparency:**
- Decision timeline logs every agent decision with intent
- React 19 dashboard shows live team status
- Event stream for real-time monitoring

**How it integrates with CC:**
The Hook system injects context at key points — SessionStart loads the leader briefing and team state, SubagentStart gives each agent its role context, PreToolUse adds safety guardrails. The 40+ MCP tools handle everything from team creation to failure analysis.

Installation is `git clone` + `python install.py` + restart CC. Three steps, no Docker required for basic usage.

It's MIT licensed and very much early stage. I built this to solve my own workflow pain, and I'm sharing it because I think other CC power users might find it useful too. Would love to hear how others are handling multi-role projects in CC.

GitHub: https://github.com/CronusL-1141/AI-company
```

---

### 2.2 r/MachineLearning

**平台**：Reddit r/MachineLearning
**字数限制**：标题需含 [P] tag（Project），正文 300-500 词
**注意事项**：这是学术/技术社区，关注架构创新和技术实现细节。避免"产品宣传"语气，聚焦工程设计决策。

**标题**：
```
[P] AI Team OS — Multi-agent orchestration OS with failure learning loops, structured meeting protocols, and decision traceability
```

**正文**：
```
I've been exploring a different approach to multi-agent coordination — instead of building another standalone agent framework, I built an operating system layer that enhances an existing capable agent (Claude Code) with team-level coordination primitives.

**The core hypothesis:** most multi-agent failures come from coordination overhead, not individual agent capability. So rather than improving agents themselves, I focused on the organizational layer — how agents divide work, share knowledge, learn from failures, and make traceable decisions.

**Architecture (5 layers):**

```
Layer 5: Dashboard — React 19 + TypeScript (visualization + intervention)
Layer 4: CLI + REST API — Typer + FastAPI + WebSocket
Layer 3: Orchestrator — LangGraph StateGraph (4 orchestration modes)
Layer 2: Memory — Mem0 / File fallback (4-level isolation)
Layer 1: Storage — SQLite / PostgreSQL
```

**Key design decisions I'd like feedback on:**

1. **Failure Alchemy** — When a task fails, the system automatically extracts the root cause and classifies the learning into three categories:
   - *Antibody*: stored experience to prevent repeat failures
   - *Vaccine*: high-frequency patterns converted to pre-task warnings
   - *Catalyst*: analysis injected into agent system prompts

   This creates a continuous learning loop without fine-tuning or gradient updates — it's purely prompt-level adaptation driven by structured failure analysis.

2. **4-mode orchestration via LangGraph StateGraph:**
   - Coordinate: Leader plans → agents execute sequentially → leader synthesizes
   - Broadcast: Task fanned out → parallel execution → results merged
   - Route: Task classified → routed to specialist agent
   - Meet: Facilitator-driven multi-round discussion with consensus detection

3. **Meeting system with structured protocols:** 7 templates based on established methodologies (Six Thinking Hats, DACI Framework, Design Sprint). Each meeting enforces an output contract — must produce actionable decisions, not just discussion summaries.

4. **4-layer rule enforcement:** Awareness (CLAUDE.md) → Guidance (SessionStart hook) → Enforcement (PreToolUse hook) → Contract (MCP validation). 48+ rules governing agent behavior, safety, and collaboration patterns.

**What this is NOT:** This is not a general-purpose agent framework. It's specifically an enhancement layer for Claude Code, deeply integrated via MCP Protocol and Hook System. The agents don't run their own LLM calls — they are Claude Code sub-agents with injected context and behavioral constraints.

40+ MCP tools, 22 agent templates, MIT licensed.

Repo: https://github.com/CronusL-1141/AI-company

I'm most interested in feedback on the failure learning approach (prompt-level adaptation vs. fine-tuning) and whether the meeting protocols actually improve multi-agent decision quality in practice.
```

---

### 2.3 r/SideProject

**平台**：Reddit r/SideProject
**字数限制**：标题简洁，正文 200-400 词
**注意事项**：这里的氛围是独立开发者互相欣赏和支持，语气轻松真诚，关注"为什么做"和"做了多久"。

**标题**：
```
I turned Claude Code into a team of AI agents that learn from their mistakes — AI Team OS (open source)
```

**正文**：
```
Hey everyone! Sharing a side project I've been working on for a while.

**The problem I was solving:**
I use Claude Code for almost all my development work. It's amazing for single tasks, but when a project gets complex enough to need an architect, a frontend dev, a QA engineer, and a tech writer — I was basically playing traffic cop, manually switching contexts and losing track of what each "role" knew.

The worst part? When something failed, it was just... gone. Next session, same mistake. No learning.

**What I built:**
AI Team OS — an open source operating system layer for Claude Code that adds:

- **Multi-agent teams** with 22 pre-built role templates (backend architect, security reviewer, TDD guide, etc.)
- **Persistent memory** that survives across sessions — the team actually remembers and learns
- **"Failure Alchemy"** — every failure gets automatically analyzed, and the lesson gets stored so future agents get warned before they make the same mistake
- **7 structured meeting templates** for when agents need to collaborate on decisions (brainstorming, tech review, retrospective, etc.)
- **A dashboard** to see what every agent is doing in real time

**Tech stack:** Python + FastAPI backend, React 19 dashboard, 40+ MCP tools, SQLite/PostgreSQL storage.

**The part I'm most proud of:** the failure learning loop. When an agent fails at something, the system extracts the root cause, classifies it, and stores it as an "antibody" in team memory. Next time any agent approaches a similar task, they get an early warning. It's like organizational knowledge accumulation, but for AI teams.

It's MIT licensed, early stage, and definitely rough around the edges. But it's solving a real problem for me, and I figured other developers using Claude Code might find it useful too.

Would love any feedback — especially on the UX and whether the agent template library covers the roles you'd actually need.

GitHub: https://github.com/CronusL-1141/AI-company
```

---

## 3. dev.to / Medium 技术文章

**平台**：dev.to 或 Medium
**字数限制**：2000-3000 词（完整技术文章）
**注意事项**：dev.to 更偏向实战教程，Medium 更偏向思考和叙事。建议先发 dev.to（开发者密度更高）。

### 标题选项（3选1）

1. **"I Built an OS That Makes Claude Code Work Like a Real Engineering Team"**
   — 叙事导向，适合 Medium，引发好奇心

2. **"From Single Agent to AI Team: How I Added Multi-Agent Orchestration to Claude Code with MCP"**
   — 技术教程导向，适合 dev.to，聚焦 how-to

3. **"What If Your AI Could Learn From Its Own Failures? Building a Failure Alchemy System for Multi-Agent Teams"**
   — 概念导向，适合两个平台，聚焦最独特的功能

### 文章大纲

```markdown
# [选定标题]

## 1. The Problem: Why Single-Agent AI Hits a Ceiling
- 描述 Claude Code 单 Agent 模式的天花板
- 真实场景：一个需要 architect + frontend + QA + writer 的项目
- 手动 context-switching 的痛苦和状态丢失
- Hook: "I was spending more time managing the AI than doing actual work."

## 2. The Idea: What If Claude Code Had an Org Chart?
- 从"工具"到"操作系统"的思维转变
- 关键洞察：coordination overhead > individual capability
- 为什么不用 CrewAI/AutoGen/LangGraph（它们是独立框架，不是 CC 增强层）
- 设计目标：可解释、可学习、可适应、可管理

## 3. Architecture: Five Layers of an AI Team OS
- 五层架构图解（Storage → Memory → Orchestrator → API → Dashboard）
- MCP Protocol 作为桥梁：40+ tools 的设计思路
- Hook System：5个注入点如何串联 CC 和 OS
- 代码示例：一个 team_create + agent_register + task_run 的完整流程

## 4. The Feature I'm Most Proud Of: Failure Alchemy
- 问题：AI Agent 没有组织记忆，同样的错误反复发生
- 解决方案：Antibody / Vaccine / Catalyst 三级学习
- 真实案例：一个构建失败如何被捕获、分析、存储，并在后续任务中预防
- 代码示例：failure_analysis MCP tool 的输入输出

## 5. Making AI Teams Actually Collaborate: The Meeting System
- 7 种会议模板及其方法论基础
- 为什么"自由讨论"在 multi-agent 场景中不工作
- 关键设计：每个会议必须输出可执行结论
- 示例：一个 Tech Review 会议的完整流程

## 6. What I Learned Building This
- 经验教训 1：规则系统比提示工程更重要（48+ rules）
- 经验教训 2：透明度是信任的基础（决策时间线）
- 经验教训 3：Agent 模板需要领域知识，不能光靠通用 prompt
- 当前局限性和下一步计划（诚实地说还有什么不行）

## 7. Try It Yourself
- 三步安装指南
- 推荐的第一个场景：创建一个 Web 开发团队
- 如何贡献：Agent 模板、会议模板、Bug fix
- GitHub 链接 + Discord 社区链接
```

### 开头 Hook（第一段）

```
Six months ago, I asked Claude Code to build a feature that needed an architect to
design the API, a frontend developer to implement the UI, a QA engineer to write tests,
and a tech writer to document it. What I got instead was one agent trying to do all four
jobs, forgetting what it decided as architect by the time it started writing tests, and
repeating the same build failure three times because it had no memory of the first two
attempts. That's when I decided to stop treating Claude Code as a tool and start treating
it as an operating system — one that needed an org chart, a meeting room, and a way to
learn from its own mistakes.
```

---

## 4. GitHub Discussion / Issue 回复模板

**平台**：CrewAI / AutoGen / LangGraph 等项目的 Discussion 或 Issue
**字数限制**：100-200 词
**注意事项**：
- 绝对不能硬广，必须先提供价值（回答问题或贡献观点）
- 只在对方讨论 "team collaboration" / "multi-agent coordination" / "agent memory" 等相关话题时回复
- 自然地提及自己的项目，作为"另一种思路"
- 保持尊重，承认对方项目的优势

### 模板 A：讨论 multi-agent coordination 时

```
I've been exploring a similar problem from a different angle. Instead of building
a standalone multi-agent framework, I tried adding a coordination layer on top of
an existing capable agent (Claude Code) via MCP Protocol.

The main insight that drove my approach: most multi-agent failures I observed came
from coordination overhead rather than individual agent capability. So I focused on
organizational primitives — structured meeting protocols, persistent team memory,
and a failure learning loop that stores root cause analyses as "antibodies" for
future tasks.

It's a very different tradeoff from [CrewAI/AutoGen/LangGraph] — I'm trading
generality for deep integration with one specific platform. Still early and
definitely has limitations, but the failure learning system has been surprisingly
effective at preventing repeat mistakes.

If anyone's interested in comparing approaches: https://github.com/CronusL-1141/AI-company
(MIT licensed). Happy to discuss the design decisions.
```

### 模板 B：讨论 agent memory / learning 时

```
This is a great discussion. We ran into the same challenge — agents repeating the
same failures because there's no organizational memory between sessions.

The approach I ended up taking was what I call "Failure Alchemy" — when any agent
task fails, the system automatically:
1. Extracts the root cause
2. Classifies the failure pattern
3. Stores it as an "antibody" in team memory
4. Injects warnings into future agent prompts when similar tasks come up

It's not as sophisticated as fine-tuning or RLHF — it's purely prompt-level
adaptation. But in practice, it's caught a surprising number of repeat failures,
especially for environment-specific issues (wrong paths, missing dependencies,
API quirks).

I built this as part of an open source project that adds team coordination to
Claude Code: https://github.com/CronusL-1141/AI-company. The failure learning
module is the part I'd most appreciate feedback on.
```

### 模板 C：讨论 agent roles / templates 时

```
Interesting thread. I spent a lot of time on agent role design and found that
generic "you are a backend developer" prompts are way less effective than
role templates with specific behavioral rules, tool preferences, and
collaboration patterns baked in.

For example, my QA engineer template doesn't just say "test things" — it
specifies test strategy selection criteria, coverage requirements, how to
communicate with the developer who wrote the code, and what to do when a
test failure is ambiguous (escalate to tech review meeting vs. investigate
further).

I ended up with 22 templates covering Engineering (12), Testing (4),
Research (3), and Management (3). They're part of an open source project:
https://github.com/CronusL-1141/AI-company

Would be curious to hear how others are structuring their agent roles —
especially the balance between specificity and flexibility.
```

---

## 5. Twitter/X 发布线程

**平台**：Twitter/X
**字数限制**：每条 tweet < 280 字符（含链接）
**注意事项**：
- 第1条必须抓眼球且独立可读
- 每条都应有独立价值（有人只看一条就划走）
- 最后一条 CTA 不要太硬
- 附图：第1条附 dashboard 截图，第4条附架构图

### Thread（7条）

**1/7 — Hook + 核心概念**
```
I built an open source OS that turns Claude Code into a self-managing AI team.

22 agent roles. Structured meetings. A memory system that learns from failures.

Not another agent framework — an operating system layer for the agent you already use.

https://github.com/CronusL-1141/AI-company

🧵 Here's what it does and why I built it ↓

[附图：Dashboard Command Center 截图]
```

**2/7 — 问题描述**
```
The problem:

Claude Code is built for one agent doing one job.

But real projects need an architect, a frontend dev, a QA engineer, and a tech writer — all keeping track of shared context.

I was spending more time managing the AI than doing actual work.
```

**3/7 — 核心功能：Agent Templates**
```
Solution part 1: Agent Templates

22 pre-built roles across Engineering, Testing, Research, and Management.

Each template isn't just a system prompt — it includes behavioral rules, tool preferences, and collaboration patterns.

The system even recommends which agent should handle each task.
```

**4/7 — 核心功能：Failure Alchemy**
```
The feature I'm most proud of: Failure Alchemy

When an agent fails, the system automatically:
→ Extracts the root cause
→ Classifies the pattern
→ Stores it as an "antibody" in team memory
→ Warns future agents before they hit the same issue

Your AI team actually learns from mistakes.

[附图：Failure Alchemy 流程图或架构图]
```

**5/7 — 核心功能：Meeting System**
```
Solution part 3: Structured meetings for AI agents

7 templates: Brainstorming, Decision Making, Tech Review, Retrospective, Status Sync, Expert Consultation, Conflict Resolution.

Based on Six Thinking Hats, DACI, and Design Sprint.

Rule: every meeting must produce actionable conclusions.
```

**6/7 — 技术栈 + 透明度**
```
Under the hood:

• Python 3.12 + FastAPI
• 40+ MCP tools (native Claude Code integration)
• LangGraph for orchestration (4 modes)
• React 19 dashboard for visual oversight
• 48+ behavioral and architectural rules
• Decision timeline — trace why any agent made any choice

MIT licensed. No vendor lock-in.
```

**7/7 — CTA**
```
AI Team OS is early stage and very much a work in progress.

If you're a Claude Code user who's felt the single-agent ceiling, I'd love your feedback.

If you have ideas for new agent templates or meeting protocols — PRs are welcome.

GitHub: https://github.com/CronusL-1141/AI-company

What roles would you add to the template library?
```

---

## 附录：常见问答准备（适用于所有平台评论区）

### Q: How is this different from CrewAI/AutoGen?

```
Great question. The key difference is the integration model:

CrewAI and AutoGen are standalone frameworks — they run their own agent loops
independently. AI Team OS is an enhancement layer built specifically for Claude Code,
integrated via MCP Protocol and Hook System.

Think of it this way: CrewAI builds the whole car. AI Team OS adds GPS navigation,
dashcam, and collision avoidance to the car you already drive.

The tradeoff is clear: we're less general (CC-only), but the integration is much
deeper — we can inject context at session start, monitor tool usage in real time,
and enforce safety rules at the hook level. That's not possible with standalone frameworks.
```

### Q: Does this actually work or is it vaporware?

```
Fair question — the repo has working code, not just a README. Here's what's real
and testable today:

- 40+ MCP tools that you can call from Claude Code right now
- 22 agent templates with full system prompts and behavioral rules
- SQLite-backed storage with working CRUD for teams, agents, tasks, events
- React 19 dashboard (screenshot in the README)
- Failure analysis that generates structured root cause reports

What's still rough: production hardening, full test coverage, multi-tenant isolation.
It's an early-stage open source project, not a polished product. I'm transparent about
what's done and what's not in the roadmap section.
```

### Q: Why not just use Claude's built-in project/memory features?

```
Claude Code's built-in features (CLAUDE.md, conversation memory) are great for
single-agent context. But they don't solve multi-agent coordination:

- How do you give 5 agents different roles and behavioral rules?
- How do you run structured meetings between agents?
- How do you extract lessons from failures and warn future agents?
- How do you trace which agent made which decision and why?

AI Team OS adds the organizational layer that sits above individual agent capabilities.
It uses CLAUDE.md as one of its rule injection points, but adds 3 more enforcement
layers on top.
```

### Q: Can I use this with other LLMs besides Claude?

```
Currently, no — it's deeply integrated with Claude Code via MCP Protocol and the
Hook System. These are CC-specific APIs.

I designed it this way intentionally. Deep integration with one platform > shallow
integration with many. The hook system lets us do things that aren't possible with
generic frameworks (inject context at session start, enforce rules at tool-use time,
monitor context consumption).

If other AI coding tools adopt MCP, the MCP server portion could potentially work
with them. But the hook system is CC-specific.
```

---

*最后更新：2026-03-21*
*用于 AI Team OS 开源发布宣传*
