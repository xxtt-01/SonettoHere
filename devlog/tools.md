
## 2026-07-03: 修复安全沙箱 `_whitelisted_open` 编码问题
- **文件:**
  - `tools/base.py`
- **原因:** `_whitelisted_open()` 默认 encoding=None，中文 Windows (GBK) 下 LLM 生成代码读写 UTF-8 文件会崩溃
- **决策:** 当 encoding 未指定且 mode 为非二进制时，默认使用 utf-8
- **影响范围:** tools/base.py

## 2026-07-03: 完成 `open()` → `Path.open()` 全面迁移
- **文件:**
  - `tools/base.py`
- **原因:** 消除最后 6 个 PTH123 ruff 警告
- **决策:** 6 处 `open(path, ...)` 改为 `path.open(...)`（path 已是 Path 对象）
- **影响范围:** tools/base.py
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
## 2026-07-09: 补充 get_safe_builtins 安全边界文档
- **文件:** `tools/base.py`
- **原因:** 沙箱仅防护 open()，os.open/subprocess 可绕过，需明确告知开发者
- **决策:** 在 docstring 添加 caution 块，说明 LLM 信任环境的设计约束
- **影响范围:** tools/base.py
