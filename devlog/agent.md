## 2026-06-27: ruff 自动修复 — ARG 未使用参数前缀
- **文件:**
  - `agent/graph.py`
- **原因:** ruff ARG 规则要求未使用的函数参数加 `_` 前缀
- **决策:** 自动修复，遵循 ruff ARG001/ARG002 规则
- **影响范围:** agent 模块

## 2026-07-03: 提示词文件读取加 lru_cache（后修复 _read_persona 取消缓存）
- **文件:**
  - `agent/prompts.py`
- **原因:** `_scan_anthropic_skills()`、`_scan_macros()` 每次 Agent turn 重新扫描目录，冗余磁盘 I/O
- **决策:** `_scan_anthropic_skills()` 和 `_scan_macros()` 加 `@functools.lru_cache`（目录扫描开销大且运行时不变）
- **_read_persona 回退:** 最初三个函数都加了缓存，但 Persona API (PUT /api/persona) 会修改 SOUL.md，缓存导致更新不生效。移除 _read_persona 缓存，每次重新读盘（文件 ~6KB，性能影响可忽略）
- **影响范围:** agent/prompts.py
## 2026-07-09: UP033 ruff 合规 — @lru_cache(maxsize=None) → @cache
- **文件:** `agent/prompts.py`
- **原因:** ruff UP033 规则提示 `@cache` 是 `@lru_cache(maxsize=None)` 的简化写法
- **决策:** 两个扫描函数改为 `@functools.cache`，语义等价更简洁
- **影响范围:** agent/prompts.py
