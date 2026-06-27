# Project Context: SonettoHere

SonettoHere — 基于 LangChain + LangGraph 的 ReAct AI Agent，提供完整的 Web 聊天界面。

## Glossary

| 术语 | 定义 |
|------|------|
| **SonettoHere** | 项目名称，v2.6.0，一个本地的 AI Agent Web 应用 |
| **ReAct Agent** | 基于 LangGraph 的思考-行动-观察循环的 AI Agent |
| **Provider** | LLM 提供商适配器，支持 DeepSeek/Qwen/OpenAI 等 OpenAI 兼容 API |
| **Tool** | AI Agent 可调用的内置工具，30+ 个，涵盖文件/网络/地图/Todo 等 |
| **MCP** | Model Context Protocol，通过 YAML 配置接入外部工具服务的协议 |
| **Skill** | anthropic_skills/ 下的独立技能包，AI 自主识别并调用 |
| **Macro** | macros/ 下的轻量流程指引，以 `!` 触发 |
| **SubAgent** | 主 Agent 创建的子会话 Agent，用于执行独立子任务 |
| **Const Session** | 固定会话，持久化保存到 YAML，重启后恢复 |
| **SonettoBlocker** | 拒止锚安全机制，通过目录标记文件阻断 AI 文件访问 |
| **Path Whitelist** | 路径白名单，限制 AI 可读写的文件目录范围 |
| **LTMI** | LongTermMemoryInterface，长期记忆接口 |
| **Vignette** | 记忆分区视图，按主题分区的记忆卡片展示 |

## Project Structure

```
SonettoHere/
├── agent/          # Agent 图构建 + 提示词
├── api/            # FastAPI 后端（路由/提供商/中间件/回调）
├── web/            # Vue 3 + TypeScript 前端
├── tools/          # 30+ 内置工具（文件/网络/地图/Todo/记忆等）
├── config/         # 全局配置 + 人设文件（SOUL.md/USER.md/AGENTS.md）
├── macros/         # 宏系统目录
├── anthropic_skills/  # Skill 技能包
├── tests/          # 测试目录（当前覆盖率不足）
├── dev_docs/       # 设计文档/项目计划/安全文档
└── memory/         # 长期记忆实现
```

## Design Decisions

### 数据持久化
- 当前全部使用 YAML 文件持久化（`api/data/`）
- 计划分步迁移到 SQLite：
  1. 会话管理（SessionManager）
  2. 长期记忆（Memory）
  3. 提供商配置（ProviderConfig）

### LLM 提供商管理
- Provider Adapter 模式，统一接口适配不同 API
- 配置存储在 `providers.yaml`，通过 Web UI 管理
- 不依赖 .env 管理模型配置

### 安全体系
- 三层防护：API Token 认证 → 路径白名单 → SonettoBlocker 拒止锚
- 代码执行审批制（审核/自动双模式）
- 所有文件操作经过白名单+拒止锚双重检查
