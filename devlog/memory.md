## 2026-06-27: ruff 自动修复 — N802/PTH/ARG
- **文件:**
  - `memory/memory_manager.py`
  - `memory/narrative.py`
- **原因:** ruff lint 修复，Task 1.2.1
- **决策:**
  - N802: `NOW()` → `_now()`
  - PTH: `os.path` / `os.makedirs` / `os.path.exists` → pathlib 等效方法
  - ARG001: 未使用参数加 `_` 前缀
- **影响范围:** memory 模块