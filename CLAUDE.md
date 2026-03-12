# AI Team OS — 项目指令

## 项目概览
通用可复用的AI Agent团队操作系统框架，包含CLI工具、REST API、Web Dashboard。
- **包名**: `aiteam`
- **CLI入口**: `aiteam`
- **技术栈**: Python 3.11+ / LangGraph / Mem0 / FastAPI / React + TypeScript

## 架构
五层架构（Layer 1-5）：Storage → Memory → Orchestrator → CLI+API → Dashboard
详见 `docs/architecture.md`

## 开发规则
1. **所有输出使用中文**
2. **文件驱动协调**: 每个工程师只写自己负责的目录，更新 `coordination.md` 状态
3. **共享类型**: 所有模块引用 `src/aiteam/types.py` 中的类型定义，不自行定义
4. **接口契约**: 遵循 `docs/api-contracts.md` 中定义的接口签名
5. **代码风格**: PEP 8，类型注解，async优先
6. **测试**: 每个模块需有对应单元测试
7. **状态消息**: ≤200字，写入coordination.md

## 目录职责分配
| 目录 | 负责人 | 说明 |
|------|--------|------|
| `src/aiteam/storage/` | storage-engineer | 数据模型、持久化 |
| `src/aiteam/memory/` | memory-engineer | 记忆管理、上下文恢复 |
| `src/aiteam/orchestrator/` | graph-engineer | LangGraph编排模式 |
| `src/aiteam/cli/` | cli-engineer | CLI命令 |
| `src/aiteam/api/` | integration-engineer | REST API + WebSocket |
| `src/aiteam/types.py` | tech-lead | 全局共享类型（只读引用） |
| `src/aiteam/config/` | tech-lead | 配置管理 |
| `dashboard/` | frontend-engineer(s) | React Dashboard |
| `tests/` | qa-engineer | 测试 |
| `docs/` | tech-lead | 文档 |

## 当前阶段
Milestone 1 — 核心可用（CLI + SQLite + Coordinate编排）

## 约束
- M1阶段不引入Docker/PostgreSQL/Redis依赖
- M1使用SQLite + 文件系统作为存储和记忆后端
- 不自建LLM Provider抽象层，直接使用LangChain ChatModel
- 不做具体投资建议或交易信号（继承自研究项目约束）
