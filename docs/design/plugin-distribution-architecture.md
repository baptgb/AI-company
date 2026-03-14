# AI Team OS — 零配置安装与分发架构设计

> Plugin分发架构师 深度研究报告
> 日期: 2026-03-14

---

## 一、Executive Summary

本文档设计AI Team OS作为Claude Code Plugin的完整打包和分发方案。核心目标是将当前需要6步手动配置的安装流程，简化为：

```
/plugin marketplace add ai-team-os/ai-team-os
/plugin install ai-team-os@ai-team-os
→ 完成。开始工作。
```

经过对CC Plugin系统的深度研究，我提出**"MCP Server嵌入API + SQLite零配置 + Plugin自动注册"**的架构方案，实现真正的零配置启动。

---

## 二、CC Plugin系统深度分析

### 2.1 Plugin目录结构规范

根据CC官方文档，Plugin的标准目录结构为：

```
ai-team-os-plugin/
├── .claude-plugin/           # 元数据目录
│   └── plugin.json           # 插件清单（唯一必要文件）
├── commands/                 # Slash命令（Markdown文件）
├── agents/                   # 自定义Agent定义
├── skills/                   # Agent Skills（SKILL.md）
├── hooks/                    # 事件处理器
│   └── hooks.json            # Hook配置
├── .mcp.json                 # MCP Server配置
├── .lsp.json                 # LSP Server配置（可选）
├── settings.json             # 默认设置
├── scripts/                  # Hook/工具脚本
└── servers/                  # MCP Server可执行文件
```

**关键规则**：
- `.claude-plugin/` 只放 `plugin.json`，其他组件放plugin根目录
- 所有路径使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量引用
- Plugin安装时会被**复制**到 `~/.claude/plugins/cache`，不能引用外部文件
- Plugin的Skills用 `/plugin-name:skill-name` 命名空间格式

### 2.2 plugin.json 完整规范

```json
{
  "name": "ai-team-os",
  "version": "1.0.0",
  "description": "AI Agent Team Operating System — 团队协作、会议、任务、记忆管理",
  "author": {
    "name": "AI Team OS",
    "email": "contact@aiteamos.dev"
  },
  "homepage": "https://github.com/ai-team-os/ai-team-os",
  "repository": "https://github.com/ai-team-os/ai-team-os",
  "license": "MIT",
  "keywords": ["ai-team", "agent-orchestration", "mcp", "collaboration"]
}
```

字段说明：
- `name`（必须）: kebab-case，用作命名空间前缀
- `version`: 语义版本号，控制缓存和更新检测
- 组件路径字段（`commands`, `agents`, `skills`, `hooks`, `mcpServers`）：可在plugin.json声明，也可用默认目录自动发现

### 2.3 MCP Server打包方式

Plugin可通过两种方式声明MCP Server：

**方式A: 独立 `.mcp.json` 文件**（推荐，关注点分离）
```json
{
  "ai-team-os": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/start-server",
    "args": ["--db", "${CLAUDE_PLUGIN_ROOT}/data/aiteam.db"],
    "env": {
      "AITEAM_DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data/aiteam.db"
    }
  }
}
```

**方式B: 内联到 plugin.json**
```json
{
  "name": "ai-team-os",
  "mcpServers": {
    "ai-team-os": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/start-server",
      "args": ["--embedded"]
    }
  }
}
```

**关键行为**：
- Plugin启用时MCP Server**自动启动**
- Plugin禁用时MCP Server**自动停止**
- 支持 stdio / SSE / HTTP 三种transport
- 使用 `${CLAUDE_PLUGIN_ROOT}` 确保路径正确

### 2.4 Hooks自动注册机制

**核心发现：Plugin的Hooks是自动注册的！**

当Plugin启用时：
1. CC自动发现 `hooks/hooks.json`
2. 所有Hook自动加载并与用户/项目Hook合并
3. 在 `/hooks` 菜单中标记 `[Plugin]` 来源
4. Plugin禁用时自动卸载

Hook配置格式与项目Hook完全一致，但需使用 `${CLAUDE_PLUGIN_ROOT}` 引用脚本：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-bootstrap.sh",
            "timeout": 3000
          }
        ]
      }
    ]
  }
}
```

### 2.5 Marketplace分发规范

**marketplace.json**：
```json
{
  "name": "ai-team-os",
  "owner": {
    "name": "AI Team OS Team",
    "email": "contact@aiteamos.dev"
  },
  "metadata": {
    "description": "AI Agent Team Operating System plugins",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "ai-team-os",
      "source": "./plugin",
      "description": "Complete AI Team OS with MCP server, hooks, and dashboard",
      "version": "1.0.0",
      "category": "ai-team",
      "tags": ["team", "agent", "collaboration", "mcp"]
    }
  ]
}
```

分发来源支持：
- **相对路径**（`./plugin`）— 同仓库内
- **GitHub仓库**（`owner/repo`）— 推荐
- **npm包**（`@scope/package`）— 可选
- **pip包**（`package`）— 可选
- **git-subdir** — monorepo子目录

---

## 三、零配置启动策略设计

### 3.1 核心架构决策：API Server嵌入MCP Server

**现状问题**：当前架构中，MCP Server是FastAPI的HTTP客户端（thin proxy），必须先启动FastAPI才能工作。这导致用户需要手动 `aiteam up`。

**推荐方案：将API逻辑直接嵌入MCP Server进程**

```
┌─────────────────────────────────────────┐
│              MCP Server (stdio)          │
│  ┌───────────────────────────────────┐  │
│  │   FastMCP Tool Handlers           │  │
│  │   (20+ MCP tools)                 │  │
│  └───────────┬───────────────────────┘  │
│              │ 直接调用                   │
│  ┌───────────▼───────────────────────┐  │
│  │   Service Layer                   │  │
│  │   (业务逻辑，原API routes逻辑)      │  │
│  └───────────┬───────────────────────┘  │
│              │                           │
│  ┌───────────▼───────────────────────┐  │
│  │   SQLAlchemy + SQLite             │  │
│  │   (嵌入式数据库，零配置)             │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   Optional: Background HTTP API   │  │
│  │   (仅Dashboard需要时启动)          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**优势**：
1. **零配置**：MCP Server由CC自动管理生命周期，无需手动启动
2. **单进程**：无需管理额外的后台daemon
3. **数据本地化**：SQLite文件在plugin目录内，无外部依赖
4. **可选升级**：用户可选配置PostgreSQL，但默认SQLite即可工作

**实施路径**：
```
Phase 1: 重构Service Layer，使其不依赖FastAPI
         MCP Tool → Service Layer → SQLAlchemy → SQLite

Phase 2: MCP Server直接调用Service Layer
         移除HTTP proxy模式

Phase 3: 可选HTTP API作为后台线程
         仅当Dashboard或外部集成需要时启动
```

### 3.2 SQLite零配置存储

```python
# 数据库路径自动解析
import os

def get_db_path():
    """零配置数据库路径：优先环境变量，否则用plugin根目录"""
    # 优先级1: 用户显式配置
    if db_url := os.environ.get("AITEAM_DATABASE_URL"):
        return db_url

    # 优先级2: Plugin根目录
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        data_dir = os.path.join(plugin_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return f"sqlite+aiosqlite:///{os.path.join(data_dir, 'aiteam.db')}"

    # 优先级3: 用户主目录
    home_dir = os.path.expanduser("~/.aiteam")
    os.makedirs(home_dir, exist_ok=True)
    return f"sqlite+aiosqlite:///{os.path.join(home_dir, 'aiteam.db')}"
```

**数据位置策略**：
- Plugin缓存目录 `~/.claude/plugins/cache/ai-team-os/data/` — 默认
- 用户主目录 `~/.aiteam/` — fallback
- 自定义路径 — 通过 `AITEAM_DATABASE_URL` 环境变量

**注意**：Plugin缓存目录在版本更新时会被替换，所以**数据文件应存储在缓存外部**（如 `~/.aiteam/`），或在启动时自动迁移。

**推荐数据存储位置**：`~/.aiteam/data/aiteam.db`
- 不会被plugin更新覆盖
- 跨版本持久化
- 用户可控

### 3.3 MCP Server启动流程

```
CC启用Plugin
  → 读取 .mcp.json
  → 启动 MCP Server (stdio)
    → 初始化 SQLite（自动建表/迁移）
    → 注册 20+ MCP Tools
    → 等待CC发送tool调用
  → 同时注册 Hooks
  → 同时加载 Skills/Commands/Agents
```

启动脚本 `servers/start-server`（跨平台）：

```bash
#!/usr/bin/env bash
# ai-team-os MCP Server启动器
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}"

# 确保Python依赖已安装
if ! python -c "import fastmcp" 2>/dev/null; then
    pip install -q "aiteam[mcp]" 2>/dev/null
fi

# 启动MCP Server
exec python -m aiteam.mcp.embedded_server \
    --db-path "${AITEAM_DB_PATH:-$HOME/.aiteam/data/aiteam.db}"
```

---

## 四、Hooks自动注册设计

### 4.1 Plugin Hooks配置

基于研究结果，Plugin的hooks是**完全自动注册**的，无需用户手动配置。

当前hooks需要适配为Plugin格式：

**当前（项目级hook，硬编码路径）**：
```json
{
  "type": "command",
  "command": "python plugin/hooks/send_event.py SubagentStart"
}
```

**目标（Plugin hook，使用CLAUDE_PLUGIN_ROOT）**：
```json
{
  "type": "command",
  "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py SubagentStart"
}
```

### 4.2 完整Hooks配置

```json
{
  "description": "AI Team OS — 实时团队协作事件监听",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/session_bootstrap.py",
            "timeout": 5000,
            "statusMessage": "AI Team OS initializing..."
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py SessionEnd",
            "timeout": 2000
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py SubagentStart",
            "timeout": 2000
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py SubagentStop",
            "timeout": 2000
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Agent|Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py PreToolUse",
            "timeout": 2000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Agent|Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py PostToolUse",
            "timeout": 2000
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py Stop",
            "timeout": 2000
          }
        ]
      }
    ],
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py TeammateIdle",
            "timeout": 2000
          }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/send_event.py TaskCompleted",
            "timeout": 2000
          }
        ]
      }
    ]
  }
}
```

### 4.3 Hook脚本的通信模式变化

**当前模式**（Hook → HTTP API → 数据库）：
```
CC Hook事件 → send_event.py → POST http://localhost:8000/api/hooks/event → FastAPI → DB
```

**嵌入式模式**（Hook → 本地文件/IPC → MCP Server读取）：

由于MCP Server已经嵌入了数据库访问，Hook脚本需要一种方式将事件发送给MCP Server进程。方案选择：

**方案A: SQLite直写（推荐）**
```
CC Hook事件 → send_event.py → 直接写入SQLite → MCP Server下次查询时读取
```
- 优势：无需网络通信，极简
- 实现：hook脚本直接用sqlite3模块写事件表
- 无需API Server运行

**方案B: Unix Socket / Named Pipe**
```
CC Hook事件 → send_event.py → Unix Socket → MCP Server进程接收
```
- 优势：实时性更好
- 劣势：跨平台兼容需要处理（Windows用Named Pipe）

**方案C: 保留HTTP（兼容模式）**
```
CC Hook事件 → send_event.py → POST localhost:PORT → MCP Server内嵌HTTP → DB
```
- 优势：与当前架构最兼容
- 劣势：需要MCP Server额外监听HTTP端口

**推荐: 方案A（SQLite直写）作为默认，方案C作为可选**

---

## 五、Dashboard分发策略

### 5.1 方案评估

| 方案 | 描述 | 优势 | 劣势 |
|------|------|------|------|
| A: 内嵌Web UI | MCP Server内建简易HTTP serve | 零额外依赖 | 功能受限 |
| B: 独立npm包 | `npm install -g aiteam-dashboard` | 完整功能 | 额外安装步骤 |
| C: 静态文件预构建 | Vite build → MCP Server serve | 零配置，完整UI | Plugin包体积增大 |
| D: 远程托管 | Dashboard托管在云端，数据通过API | 零安装 | 需要网络，数据安全 |

### 5.2 推荐：方案C + 方案B的混合

**默认体验（方案C）**：
- 在Plugin构建时预编译React Dashboard为静态文件
- MCP Server内嵌一个轻量HTTP服务器（如aiohttp或内建http.server）
- 用户通过 `/ai-team-os:dashboard` 命令打开本地Web UI
- 端口自动分配，避免冲突

**高级用户（方案B）**：
- 完整的 `aiteam-dashboard` npm包
- 支持开发模式、热重载
- 通过 `npx aiteam-dashboard` 启动

**实现细节**：
```
plugin/
├── dashboard/                # 预构建的静态文件
│   ├── index.html
│   ├── assets/
│   └── ...
├── scripts/
│   └── serve_dashboard.py    # 内嵌HTTP服务器
└── skills/
    └── dashboard/
        └── SKILL.md          # /ai-team-os:dashboard 命令
```

Dashboard SKILL.md:
```markdown
---
description: Open AI Team OS Dashboard in browser
---
Start the AI Team OS Dashboard by running the embedded web server
and opening the browser. The dashboard shows real-time team status,
meetings, tasks, and agent activities.

Run: python ${CLAUDE_PLUGIN_ROOT}/scripts/serve_dashboard.py
Then open the URL shown in the output.
```

---

## 六、跨平台兼容性

### 6.1 平台差异处理

| 问题 | Windows | macOS | Linux |
|------|---------|-------|-------|
| 路径分隔符 | `\` → 需要处理 | `/` | `/` |
| Python命令 | `python` or `py` | `python3` | `python3` |
| SQLite路径 | `%APPDATA%/.aiteam/` | `~/.aiteam/` | `~/.aiteam/` |
| Shell脚本 | 需要 `cmd /c` 包装 | bash | bash |
| 权限 | 无chmod需求 | 需要chmod +x | 需要chmod +x |

### 6.2 跨平台启动器

由于CC在Windows上运行 `npx` 需要 `cmd /c` 包装，Python脚本是更好的跨平台选择：

**MCP Server .mcp.json（跨平台）**：
```json
{
  "ai-team-os": {
    "command": "python",
    "args": [
      "${CLAUDE_PLUGIN_ROOT}/servers/mcp_launcher.py"
    ],
    "env": {
      "AITEAM_DATA_DIR": "${HOME}/.aiteam/data",
      "PYTHONPATH": "${CLAUDE_PLUGIN_ROOT}/lib"
    }
  }
}
```

**mcp_launcher.py**：
```python
"""跨平台MCP Server启动器"""
import os
import sys
import subprocess

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(__file__))
sys.path.insert(0, os.path.join(plugin_root, "lib"))

# 确保依赖已安装
try:
    import fastmcp
    import sqlalchemy
except ImportError:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q",
        "fastmcp", "sqlalchemy", "aiosqlite"
    ])

# 启动embedded server
from aiteam.mcp.embedded_server import main
main()
```

### 6.3 Python版本要求

- **最低要求**: Python 3.11（match语句、asyncio改进）
- **推荐**: Python 3.12+
- **检测方式**: 启动脚本检查版本并给出清晰错误信息

### 6.4 依赖管理

Plugin内嵌的Python依赖有两种策略：

**策略A: pip install 自动安装（推荐初期）**
```python
# 首次启动时自动安装
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "fastmcp>=2.0", "sqlalchemy>=2.0", "aiosqlite>=0.20"
])
```

**策略B: vendored依赖（长期目标）**
- 将所有Python依赖预打包到 `lib/` 目录
- 使用 `pip install --target` 预构建
- 零网络依赖，但增大包体积

**策略C: pip source distribution**
- Plugin source声明为 `pip` 类型
- CC通过 `pip install` 安装整个包
- 利用pip的依赖解析

marketplace.json中使用pip source：
```json
{
  "name": "ai-team-os",
  "source": {
    "source": "pip",
    "package": "aiteam",
    "version": ">=1.0.0"
  }
}
```

---

## 七、升级和数据迁移

### 7.1 版本升级流程

```
用户执行 /plugin marketplace update
  → CC下载新版本Plugin
  → 替换 ~/.claude/plugins/cache/ai-team-os/
  → 下次启动CC或执行 /reload-plugins
  → MCP Server重启
  → 检测数据库schema版本
  → 自动执行迁移
  → 正常运行
```

### 7.2 数据库Schema迁移

**方案: 内嵌Alembic迁移**

```python
# embedded_server.py 启动时
from alembic.config import Config
from alembic import command

def auto_migrate(db_path: str):
    """启动时自动执行数据库迁移"""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location",
        os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url",
        f"sqlite:///{db_path}")

    command.upgrade(alembic_cfg, "head")
```

### 7.3 数据备份策略

```python
def backup_before_migrate(db_path: str):
    """迁移前自动备份"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        # 保留最近5个备份
        cleanup_old_backups(db_path, keep=5)
```

### 7.4 配置向后兼容

```python
# 配置版本检测
CONFIG_VERSION = "1.0"

def load_config():
    config_path = os.path.expanduser("~/.aiteam/config.json")
    if os.path.exists(config_path):
        config = json.load(open(config_path))
        if config.get("version") != CONFIG_VERSION:
            config = migrate_config(config)
    else:
        config = default_config()
    return config
```

---

## 八、完整Plugin目录结构设计

```
ai-team-os-plugin/
├── .claude-plugin/
│   └── plugin.json                   # 插件清单
│
├── .mcp.json                         # MCP Server配置
│
├── skills/                           # Agent Skills
│   ├── team-setup/
│   │   └── SKILL.md                  # /ai-team-os:team-setup
│   ├── dashboard/
│   │   └── SKILL.md                  # /ai-team-os:dashboard
│   ├── status/
│   │   └── SKILL.md                  # /ai-team-os:status
│   └── meeting/
│       └── SKILL.md                  # /ai-team-os:meeting
│
├── agents/                           # 自定义Agent
│   ├── team-coordinator.md           # 团队协调Agent
│   └── project-manager.md            # 项目管理Agent
│
├── commands/                         # Slash命令
│   ├── quick-start.md                # /ai-team-os:quick-start
│   └── health-check.md              # /ai-team-os:health-check
│
├── hooks/                            # Event Hooks
│   └── hooks.json                    # 自动注册的Hook配置
│
├── scripts/                          # Hook处理脚本
│   ├── send_event.py                 # 事件发送（SQLite直写）
│   ├── session_bootstrap.py          # Session初始化
│   └── serve_dashboard.py           # Dashboard服务器
│
├── servers/                          # MCP Server
│   └── mcp_launcher.py              # 跨平台启动器
│
├── lib/                              # Python库（嵌入式）
│   └── aiteam/                       # 核心业务逻辑
│       ├── mcp/
│       │   └── embedded_server.py    # 嵌入式MCP Server
│       ├── storage/
│       │   ├── models.py             # SQLAlchemy模型
│       │   └── repository.py         # 数据访问层
│       ├── services/                  # 业务逻辑层（从API routes抽取）
│       │   ├── team_service.py
│       │   ├── agent_service.py
│       │   ├── meeting_service.py
│       │   ├── task_service.py
│       │   └── event_service.py
│       └── migrations/               # Alembic迁移
│           ├── env.py
│           └── versions/
│
├── dashboard/                        # 预构建的Dashboard静态文件
│   ├── index.html
│   └── assets/
│
├── settings.json                     # 默认设置
├── LICENSE
├── README.md
└── CHANGELOG.md
```

---

## 九、Marketplace发布流程

### 9.1 自建Marketplace（推荐初期）

```
ai-team-os/                          # GitHub仓库
├── .claude-plugin/
│   └── marketplace.json              # Marketplace清单
├── plugin/                           # Plugin目录
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── .mcp.json
│   ├── skills/
│   ├── hooks/
│   └── ...
└── README.md
```

marketplace.json:
```json
{
  "name": "ai-team-os",
  "owner": {
    "name": "AI Team OS",
    "email": "contact@aiteamos.dev"
  },
  "metadata": {
    "description": "AI Agent Team Operating System for Claude Code",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "ai-team-os",
      "source": "./plugin",
      "description": "Complete AI Team OS — team coordination, meetings, tasks, and monitoring",
      "version": "1.0.0",
      "category": "ai-team",
      "tags": ["team", "agent", "orchestration", "collaboration", "mcp"]
    }
  ]
}
```

用户安装流程：
```bash
# 添加marketplace
/plugin marketplace add ai-team-os/ai-team-os

# 安装plugin
/plugin install ai-team-os@ai-team-os

# 完成！所有组件自动启动
```

### 9.2 提交到官方Marketplace（长期目标）

官方提交入口：
- Claude.ai: `claude.ai/settings/plugins/submit`
- Console: `platform.claude.com/plugins/submit`

需要满足的质量标准（推测）：
1. 完善的 `plugin.json` 元数据
2. 安全审计通过（无恶意代码）
3. 清晰的文档和README
4. 稳定的版本管理
5. 跨平台兼容性

官方Marketplace安装：
```bash
/plugin install ai-team-os@claude-plugins-official
```

### 9.3 团队自动分发

通过项目的 `.claude/settings.json` 配置自动发现：
```json
{
  "extraKnownMarketplaces": {
    "ai-team-os": {
      "source": {
        "source": "github",
        "repo": "ai-team-os/ai-team-os"
      }
    }
  },
  "enabledPlugins": {
    "ai-team-os@ai-team-os": true
  }
}
```

团队成员克隆仓库后，CC自动提示安装Plugin。

---

## 十、实施路线图

### Phase 1: Service Layer重构（1-2周）
1. 从FastAPI routes中抽取纯业务逻辑到 `services/` 层
2. Service Layer只依赖SQLAlchemy，不依赖FastAPI
3. 编写 `embedded_server.py`，MCP Tool直接调用Service Layer
4. SQLite零配置初始化和自动迁移

### Phase 2: Plugin打包（3-5天）
1. 创建标准Plugin目录结构
2. 适配hooks使用 `${CLAUDE_PLUGIN_ROOT}`
3. 编写 `plugin.json` 和 `.mcp.json`
4. Hook脚本改为SQLite直写模式
5. 预构建Dashboard静态文件

### Phase 3: 分发和测试（3-5天）
1. 创建marketplace.json
2. 本地测试：`claude --plugin-dir ./plugin`
3. 跨平台测试（Windows/macOS/Linux）
4. 创建GitHub仓库，推送marketplace
5. 端到端安装测试

### Phase 4: 优化和官方提交（持续）
1. 依赖vendoring（减少网络依赖）
2. Dashboard预构建流水线
3. 提交到Anthropic官方Marketplace
4. 版本自动更新机制

---

## 十一、风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Python依赖安装失败 | 首次启动卡住 | 提供清晰错误信息，fallback到最小功能集 |
| SQLite并发写入冲突 | Hook写入与MCP读取冲突 | 使用WAL模式，SQLite支持并发读+单写 |
| Plugin缓存覆盖数据 | 用户数据丢失 | 数据存储在 `~/.aiteam/` 而非缓存目录 |
| Windows路径问题 | MCP Server启动失败 | 使用Python pathlib，避免shell脚本 |
| 大体积Plugin | 下载/安装慢 | Dashboard静态文件可选，核心功能精简 |
| CC Plugin API变更 | Plugin不兼容 | 关注CC版本更新，维护兼容性矩阵 |

---

## 十二、与当前架构的对比

| 维度 | 当前架构 | 目标架构 |
|------|----------|----------|
| 安装步骤 | 6步手动 | 2步命令 |
| API Server | 独立FastAPI进程 | 嵌入MCP Server |
| 数据库 | SQLite/PostgreSQL手动配置 | SQLite自动初始化 |
| Hooks | 手动配置settings.json | Plugin自动注册 |
| MCP Server | 手动配置.mcp.json | Plugin自动启动 |
| Dashboard | npm run dev手动启动 | 预构建静态文件+命令启动 |
| 升级 | git pull + pip install | /plugin marketplace update |
| 跨项目复用 | 每个项目重新配置 | 一次安装，所有项目可用 |

---

## 参考来源

- [CC Plugin Marketplace文档](https://code.claude.com/docs/en/plugin-marketplaces)
- [CC Plugin创建文档](https://code.claude.com/docs/en/plugins)
- [CC Plugin技术参考](https://code.claude.com/docs/en/plugins-reference)
- [CC Hooks规范](https://code.claude.com/docs/en/hooks)
- [CC MCP集成文档](https://code.claude.com/docs/en/mcp)
- [CC Plugin发现和安装](https://code.claude.com/docs/en/discover-plugins)
- [Anthropic官方Plugin仓库](https://github.com/anthropics/claude-plugins-official)
