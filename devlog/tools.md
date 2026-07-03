
## 2026-07-03: 迁移 os.path 到 pathlib.Path（Task 7）
- **文件:**
  - `tools/base.py`
- **原因:** 消除 ruff PTH 警告，统一使用 pathlib 进行路径操作
- **决策:**
  - `os.path.abspath()` → `str(Path(p).resolve())`
  - `os.path.normpath()` → `str(Path(p).resolve())`
  - `os.path.isdir()` → `Path(p).is_dir()`
  - `os.path.join()` → Path `/` 运算符
  - `os.path.splitext()` → `Path.stem` / `Path.suffix`
  - `os.listdir()` → `Path.iterdir()`
  - `_PROJECT_ROOT` 等全局变量从 str 改为 Path，必要时用 `str()` 转换（如 YAML 序列化）
- **影响范围:** `tools/base.py`，仅影响内部路径操作实现，不改变函数签名或外部行为
- **测试:** 全部 214 个测试通过