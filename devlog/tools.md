
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

## 2026-07-09: tools/files/*.py + path_whitelist 全面 PTH 迁移
- **文件:**
  - `tools/files/tool_file_read.py`
  - `tools/files/tool_file_write.py`
  - `tools/files/tool_file_edit.py`
  - `tools/files/tool_file_manage.py`
  - `tools/files/tool_file_search.py`
  - `api/routes/path_whitelist.py`
- **原因:** 消除 ruff PTH 警告，统一使用 pathlib 进行路径操作
- **决策:**
  - 各文件内 `os.path.*` 调替换为 `Path.*` 等效操作
  - `open()` → `Path.open()`（配合 Path 对象使用）
  - `os.path.abspath()` → `Path.resolve()`（仅用于返回数据，不影响安全校验逻辑）
  - `os.path.normpath(data["path"])` → `str(Path(data["path"]).resolve())`（在存储时解析为绝对路径，与 _load_path_whitelist 运行时 resolve 一致）
  - `os.listdir()` → `Path.iterdir()`（返回 Path 对象，需 .name 属性取文件名）
  - `glob.glob()` → `Path().glob()`（返回 Path 对象）
  - 安全校验函数 `check_path_whitelisted()` / `check_path_access()` 调用保留 str 传参
  - tool_file_search.py: Path.parent 代替 os.path.dirname，Path('.').exists() 恒 True 无需额外 if 检查
- **影响范围:** 6 个文件，ruff PTH 全项目减少 65 个
- **测试:** 214 测试全部通过

## 2026-07-10: 交互工具 ask_user 事件增加 tool_call_id
- **文件:**
  - `tools/interaction/tool_ask_qa.py`
  - `tools/interaction/tool_single_choice.py`
  - `tools/interaction/tool_multi_choice.py`
- **原因:** Issue #228 — 多同名交互工具并发时前端无法区分，需要唯一工具调用标识
- **决策:** 每个交互工具的 `_arun` 通过 `interaction.current_tool_call_id.get()` 读取当前工具 `run_id`，在 `ask_user` 事件 payload 中加入 `tool_call_id`
- **影响范围:** tools/interaction/ 下 3 个文件
