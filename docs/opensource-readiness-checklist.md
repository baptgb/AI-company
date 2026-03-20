# AI Team OS — 开源发布准备清单

> 审计日期: 2026-03-20
> 审计范围: ai-team-os 仓库全部已跟踪文件（282个）

---

## 1. 敏感信息审计结果

### 1.1 硬编码密钥/Token — 未发现真实密钥

| 状态 | 说明 |
|------|------|
| PASS | 源代码中无硬编码 API Key、密码或 Token |
| PASS | `.env.example` 仅包含占位符（`sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx`），安全 |
| PASS | 无 `.pem`/`.key`/`.p12`/`credentials` 等凭据文件 |
| PASS | CI workflow 无密钥硬编码 |

### 1.2 个人路径硬编码 — 需要修复

以下文件包含开发者本机绝对路径 `C:/Users/TUF/Desktop/AI团队框架/ai-team-os`：

| 文件 | 问题 |
|------|------|
| `.mcp.json:6` | `"cwd": "C:/Users/TUF/Desktop/AI团队框架/ai-team-os"` |
| `.claude/hooks/inject-context.ps1:5` | `$projectRoot = "C:\Users\TUF\Desktop\AI团队框架\ai-team-os"` |
| `plugin/commands/os-up.md:21,38` | `cd C:/Users/TUF/Desktop/AI团队框架/ai-team-os` |
| `plugin/skills/os-register/SKILL.md:38` | `cd C:/Users/TUF/Desktop/AI团队框架/ai-team-os` |
| `docs/system-integration-audit.md:56` | `C:/Users/TUF/.claude/agents/` 引用 |

**建议处理方式**：
- `.mcp.json` — 改为相对路径 `"cwd": "."` 或加入 `.gitignore`（因该文件通常由安装脚本生成）
- `.claude/hooks/inject-context.ps1` — 改用 `$PSScriptRoot` 自动推导项目根目录
- `plugin/commands/os-up.md` / `plugin/skills/os-register/SKILL.md` — 改用占位符如 `<PROJECT_ROOT>` 或说明用户需自行替换
- `docs/system-integration-audit.md` — 文档内的路径改为通用描述

### 1.3 `~/.claude/` 路径引用 — 可接受

多个文档和代码中引用了 `~/.claude/agents/`、`~/.claude/data/` 等路径。这些是 Claude Code 的标准目录结构，属于产品设计的一部分，**无需修改**。

---

## 2. 需要补充的文件

### 2.1 必需文件

- [ ] **README.md** — 项目根目录当前无 README（仅有 `CLAUDE.md`），开源项目必须有
  - 项目简介、功能亮点、架构图
  - 快速开始（安装步骤、依赖要求）
  - 使用示例
  - 贡献指南链接
- [ ] **LICENSE** — 当前无许可证文件，必须选择并添加（建议 MIT 或 Apache 2.0）

### 2.2 推荐文件

- [ ] **CONTRIBUTING.md** — 贡献指南（代码规范、PR流程、开发环境搭建）
- [ ] **CODE_OF_CONDUCT.md** — 社区行为准则
- [ ] **CHANGELOG.md** — 变更日志（至少记录首个公开版本）
- [ ] **SECURITY.md** — 安全漏洞报告流程

### 2.3 可选文件

- [ ] `.github/ISSUE_TEMPLATE/` — Issue 模板（bug report、feature request）
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` — PR 模板

---

## 3. .gitignore 审计

### 3.1 当前覆盖情况 — 基本完善

| 类别 | 已覆盖 | 说明 |
|------|--------|------|
| Python 构建产物 | YES | `__pycache__/`, `*.egg-info/`, `dist/`, `build/` |
| 虚拟环境 | YES | `.venv/`, `venv/` |
| IDE 文件 | YES | `.vscode/`, `.idea/` |
| 环境变量 | YES | `.env`, `.env.local` |
| Node modules | YES | `dashboard/node_modules/` |
| 数据库文件 | YES | `*.db`, `*.sqlite3` |
| 测试缓存 | YES | `.pytest_cache/`, `.mypy_cache/`, `.coverage` |
| 临时文件 | YES | `tempnpm-cache/`, `test-screenshots/`, `aiteam.db.migrated` |
| Docker override | YES | `docker-compose.override.yml` |

### 3.2 需要补充的条目

- [ ] `~/.claude/data/` — 运行时数据目录（实际在用户 home 目录，不在仓库内，但建议在文档中说明）
- [ ] `.ruff_cache/` — Ruff linter 缓存（当前存在于磁盘但未在 .gitignore 中，未被 git 跟踪可能是因为没有 `git add`）
- [ ] `tmp_*.json` — 临时 JSON 文件（如 `tmp_tech_strategist_r1.json`），建议加 `tmp_*` 规则
- [ ] `test_api_*.py`（根目录下的临时测试文件）— 或直接从仓库中移除

---

## 4. 已跟踪但需评估的文件

### 4.1 建议从 git 移除

| 文件 | 原因 |
|------|------|
| `test_api_comprehensive.py` | 根目录下的临时测试文件（12.8KB），应迁移到 `tests/` 或删除 |
| `coordination.md` | 内部协调文档，不适合公开 |
| `.claude/settings.local.json` | 内容为空 `{}`，本地设置文件不应跟踪 |

### 4.2 需评估是否保留

| 文件/目录 | 说明 |
|------------|------|
| `.mcp.json` | MCP 服务配置，含个人路径。建议加入 `.gitignore`，提供 `.mcp.json.example` |
| `.claude/settings.json` | 含 SubagentStart hook 配置，引用个人路径。建议模板化 |
| `.claude/hooks/inject-context.ps1` | Windows 专用脚本，含硬编码路径。需参数化 |

### 4.3 Agent 模板（22个）— 保留

`.claude/agents/` 下的 22 个 Agent 模板是项目核心功能，内容无敏感信息，应保留。其中引用的 `禁止 git add .env/credentials/.pem/.key` 是安全规范，安全。

---

## 5. 代码质量检查

| 项目 | 状态 | 说明 |
|------|------|------|
| CI Pipeline | OK | ci.yml + lint.yml 已配置 |
| 单元测试 | OK | `tests/unit/` 存在，CI 中运行 |
| TypeScript 类型检查 | OK | Dashboard 有 `tsc -b --noEmit` 检查 |
| Linter | OK | 有 lint.yml workflow |
| `.env.example` | OK | 模板完整，占位符安全 |

---

## 6. 行动项优先级

### P0 — 发布前必须完成

1. [ ] 添加 **LICENSE** 文件
2. [ ] 编写 **README.md**（英文为主，可附中文说明）
3. [ ] 修复所有硬编码个人路径（`.mcp.json`、`inject-context.ps1`、`os-up.md`、`SKILL.md`）
4. [ ] 将 `.mcp.json` 改为 `.mcp.json.example` + 加入 `.gitignore`
5. [ ] 移除或迁移 `test_api_comprehensive.py`（根目录临时文件）

### P1 — 强烈建议

6. [ ] 添加 **CONTRIBUTING.md**
7. [ ] `.claude/settings.json` 路径参数化，或提供 `.claude/settings.json.example`
8. [ ] `.gitignore` 补充 `.ruff_cache/`、`tmp_*` 规则
9. [ ] 评估 `coordination.md` 是否移除（内部文档）
10. [ ] 添加 **SECURITY.md**

### P2 — 锦上添花

11. [ ] 添加 **CHANGELOG.md**
12. [ ] 添加 **CODE_OF_CONDUCT.md**
13. [ ] GitHub Issue/PR 模板
14. [ ] `docs/system-integration-audit.md` 中个人路径改为通用描述
15. [ ] 考虑添加 `install.py` 自动生成 `.mcp.json` 的功能（消除手动配置）

---

## 7. 安全总结

| 维度 | 评估 | 风险等级 |
|------|------|----------|
| 密钥泄露 | 无真实密钥 | 低 |
| 个人信息 | 用户名 "TUF" 出现在路径中 | 中 — 需修复 |
| 数据库文件 | 未跟踪，.gitignore 已覆盖 | 低 |
| 依赖安全 | 未审计 npm/pip 依赖 | 待评估 |
| CI/CD 安全 | 无密钥硬编码 | 低 |

**整体评估**: 仓库安全状况良好，无高风险泄露。主要工作是个人路径参数化和补充开源社区文件。
