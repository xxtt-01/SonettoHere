## 2026-06-27 22:07: 前端响应式侧边栏 + 连接加载指示
- **文件:**
  - `web/src/App.vue`
  - `web/src/components/ChatWindow.vue`
  - `web/src/views/ChatView.vue`
- **原因:** Phase 3 Task 2 & 3 — 小屏幕下侧边栏固定定位 + 滑动隐藏，WebSocket 未连接时显示加载状态
- **决策:**
  - 768px 以下侧边栏 fixed 定位，collapsed 时 translateX(-100%) 完全隐藏，main 区域占满宽度
  - ChatWindow 新增可选 connected prop，未连接+无内容时显示旋转加载动画和"正在连接..."文字
- **影响范围:** web/src/App.vue (CSS 媒体查询), web/src/components/ChatWindow.vue (loading 组件), web/src/views/ChatView.vue (传递 connected prop)

## 2026-06-27 22:07: 前端测试基础设施（Vitest + happy-dom）
- **文件:**
  - `web/package.json`
  - `web/package-lock.json`
  - `web/vitest.config.ts`
  - `web/src/__tests__/setup.ts`
  - `web/src/__tests__/smoke.test.ts`
- **原因:** 建立 Vue 3 前端测试基础设施，支持组件和逻辑单元测试
- **决策:** 使用 Vitest（Vite 原生测试框架）+ happy-dom（轻量 DOM 环境），配置 @ 别名别名解析、localStorage/crypto 全局 mock
- **影响范围:** web/ 前端项目，新增 devDependencies 和测试脚本入口

## 2026-06-28: 添加 Icon 组件冒烟测试
- **文件:**
  - `web/src/__tests__/Icon.test.ts` (new)
- **原因:** Risk 4 — 为前端 Icon 组件添加快速冒烟测试，验证渲染和尺寸样式
- **决策:**
  - 测试渲染：mount 后确认组件存在且内部 `<svg>` 元素已渲染
  - 测试尺寸：验证父级 `<span>` 的 style 包含指定像素值（Icon.vue 将 size 应用于 span，svg 通过 100% 撑满）
- **影响范围:** web/src/__tests__/（新增独立组件测试文件）

## 2026-06-27: 清理前端调试 console.log 语句
- **文件:**
  - `web/src/components/ChatInput.vue`
  - `web/src/components/MomentCard.vue`
  - `web/src/components/ToolBubbleRouter.vue`
  - `web/src/components/tools/AskUserBubble.vue`
  - `web/src/components/tools/WeatherBubble.vue`
- **原因:** Task 1.2.4 消除调试残留，减少生产环境控制台输出
- **决策:** 将明确的调试日志注释为 `// TODO: dead?`，保留 console.error/warn 和 [useChat]/[useSession]/[ltm-fe] 前缀日志
- **影响范围:** web/src/components/ 下 5 个 Vue 组件
