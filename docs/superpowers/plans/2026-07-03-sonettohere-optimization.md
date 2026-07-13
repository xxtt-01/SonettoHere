# SonettoHere 全面优化计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 基于深度检查发现的问题，对 SonettoHere 项目进行全面优化，涵盖关键修复、性能优化、前端优化、数据库优化和代码质量改进。

**Architecture:** 优化涉及多个独立子系统（安全沙箱、提示词缓存、前端构建、数据库、代码风格），各任务无交叉文件依赖，可并行执行。

**Tech Stack:** Python 3.11+, FastAPI, Vue 3 + Vite, SQLite, LangChain

---

### Task 1: 修复安全沙箱 `_whitelisted_open` encoding 默认值

**Files:**
- Modify: `tools/base.py:435-473`

**问题:** `_whitelisted_open()` 函数签名 `encoding: str | None = None`，在中文 Windows 上导致 LLM 生成的 Python 代码用 GBK 编码读写 UTF-8 文件时触发 UnicodeDecodeError。

**修复:** 当 `encoding` 未指定且 mode 为文本模式（不含 `b`）时，默认使用 `"utf-8"`。

```python
def _whitelisted_open(
    file,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = None,  # 保持 None 向后兼容
    ...
):
    ...
    # 仅在文本模式下注入 UTF-8 默认编码
    if encoding is None and 'b' not in mode:
        encoding = "utf-8"
    return _real_builtins.open(...)
```

**验证:** `pytest tests/ -x -q` 确保无回归。

---

### Task 2: 提示词文件读取加 lru_cache

**Files:**
- Modify: `agent/prompts.py:1-96`

**问题:** `_read_persona()`, `_scan_anthropic_skills()`, `_scan_macros()` 每次调用都重新读取磁盘文件。这些内容在进程生命周期内基本不变。

**修复:** 
- 对 `_read_persona()` 加 `@functools.lru_cache` — AGENTS.md 和 SOUL.md 静态
- 对 `_scan_anthropic_skills()` 加 `@functools.lru_cache` — skills 目录静态
- 对 `_scan_macros()` 加 `@functools.lru_cache` — macros 目录静态
- `_read_if_exists()` 不缓存 — USER.md 可通过 API 修改
- 顶部加 `import functools`

**验证:** `pytest tests/ -x -q` && python 交互验证缓存命中。

---

### Task 3: 前端 manualChunks 代码分割

**Files:**
- Modify: `web/vite.config.ts`

**问题:** Vite 构建主 chunk 647KB，应将 vue/vue-router 等 vendor 代码拆分。

**修复:** 在 `defineConfig` 中添加 `build.rollupOptions.output.manualChunks`。

```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-vue': ['vue', 'vue-router'],
      },
    },
  },
},
```

**验证:** `npx vite build` 确认 chunk 体积变化。

---

### Task 4: 添加数据库缺失索引

**Files:**
- Create: `api/database/migrations/003_add_sessions_indexes.py`

**问题:** `sessions` 表的 `cleanup_expired` 查询 `DELETE FROM sessions WHERE last_active < ? AND is_const = 0` 触发全表扫描，缺少 `(last_active, is_const)` 复合索引。

**修复:** 创建 migration 003：

```sql
CREATE INDEX IF NOT EXISTS idx_sessions_cleanup
    ON sessions(last_active, is_const);
```

**验证:** 运行迁移并 EXPLAIN QUERY PLAN 确认索引被使用。

---

### Task 5: 修复 TypeScript 类型错误

**Files:**
- Modify: `web/src/components/tools/FilesBubble.vue:239`
- Modify: `web/src/components/tools/WeatherBubble.vue:125-126`

**问题:** computed 属性返回类型与声明类型不匹配。

**修复:**
- FilesBubble.vue:239 — 移除显式类型标注，让 TS 推断 `computed(() => ...)` 返回类型
- WeatherBubble.vue:125 — 在 `return {}` 时使用 `as WeatherData` 或 `as unknown as WeatherData`

```typescript
// FilesBubble.vue:239 — 移除显式类型
const items = computed(() => {
  const raw = td.value.items as Array<Record<string, unknown>> | undefined
  return Array.isArray(raw) ? raw : []
})

// WeatherBubble.vue:125 — 空对象返回正确类型
const td = computed<WeatherData>(() => {
  if (props.toolCall.toolData) return props.toolCall.toolData as WeatherData
  // ...
  return {} as WeatherData
})
```

**验证:** `npx vue-tsc --noEmit` 确认 0 错误。

---

### Task 6: 消除 StarletteDeprecationWarning

**Files:**
- Modify: `tests/conftest.py:1-6`

**问题:** `from starlette.testclient import TestClient` 触发 deprecation warning，建议改用 httpx2。

**修复:** 移除未使用的 `TestClient` 导入（它仅在 `test_auth_middleware.py` 中被导入，conftest.py 自身不使用它）。保留已有的 `ASGITransport, AsyncClient` 导入。

**验证:** `pytest tests/ -x -q` 确认 warning 消除。

---

### Task 7: tools/base.py os.path → pathlib 迁移

**Files:**
- Modify: `tools/base.py`

**问题:** ruff PTH 警告约 20 处，使用 `os.path` 而非 `pathlib.Path`。

**修复:** 将 `tools/base.py` 中的 `os.path` 调用替换为 `pathlib.Path` 等效方法。注意保持 `check_sonetto_blocker()` 和 `check_path_whitelisted()` 的函数签名完全不变。

关键替换对照：
- `os.path.abspath(p)` → `Path(p).resolve()`
- `os.path.normpath(p)` → `Path(p).resolve()`
- `os.path.exists(p)` → `Path(p).exists()`
- `os.path.isdir(p)` → `Path(p).is_dir()`
- `os.path.isfile(p)` → `Path(p).is_file()`
- `os.path.join(a, b)` → `Path(a) / b`
- `os.path.dirname(p)` → `Path(p).parent`
- `os.path.basename(p)` → `Path(p).name`
- `os.path.splitext(p)` → `Path(p).suffix`
- `os.path.getsize(p)` → `Path(p).stat().st_size`
- `os.makedirs(p, exist_ok=True)` → `Path(p).mkdir(parents=True, exist_ok=True)`
- `os.listdir(d)` → `list(Path(d).iterdir())`
- `os.remove(p)` → `Path(p).unlink()`
- `os.rename(src, dst)` → `Path(src).rename(dst)`
- `glob.glob(p)` → `list(Path().glob(p))`

**验证:** `pytest tests/ -x -q` 确认无回归，`ruff check tools/base.py` 确认 PTH 减少。
