## 2026-06-28: 修复 YAML 编码 Bug + _reason 命名 Bug
- **文件:**
  - `memory/memory_manager.py`
  - `memory/narrative.py`
- **原因:**
  - memory_manager.py: 文件读写未指定 `encoding="utf-8"`，在非 UTF-8 系统区域设置下写入 YAML 时出现编码错误
  - narrative.py: `delete_memory` 参数名为 `_reason`（带下划线前缀），工具调用框架按名称传参时无法匹配到正确的形式参数
- **决策:**
  - memory_manager.py: 所有 `open()` / `Path.open()` 调用显式指定 `encoding="utf-8"`
  - narrative.py: `_reason` → `reason`，与 `update_memory` 的参数命名保持一致
- **影响范围:** memory/memory_manager.py（4 处文件读写）, memory/narrative.py（1 处参数重命名）
- **踩坑:** `_reason` 是 ruff ARG001 修复的遗留产物，自动修复时未考虑工具框架的参数名匹配机制

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