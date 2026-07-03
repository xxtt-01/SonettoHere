## 2026-06-27: ruff 自动修复 — ARG 未使用参数前缀
- **文件:**
  - `agent/graph.py`
- **原因:** ruff ARG 规则要求未使用的函数参数加 `_` 前缀
- **决策:** 自动修复，遵循 ruff ARG001/ARG002 规则
- **影响范围:** agent 模块

## 2026-07-03: 提示词文件读取加 lru_cache
- **文件:**
  - `agent/prompts.py`
- **原因:** `_read_persona()`、`_scan_anthropic_skills()`、`_scan_macros()` 每次 Agent turn 都重新读盘，冗余磁盘 I/O
- **决策:** 对三个纯文件读取函数加 `@functools.lru_cache`，`_read_if_exists()` 不缓存（USER.md 可由 API 修改）
- **影响范围:** agent/prompts.py