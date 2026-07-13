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

## 2026-07-03: 前端 manualChunks 分包 — vue/vue-router 拆分
- **文件:**
  - `web/vite.config.ts`
- **原因:** Task 3 优化 — Vite 构建产物主 chunk 过大（647KB），将 vue + vue-router 分离为独立 vendor chunk
- **决策:** 在 `build.rollupOptions.output.manualChunks` 中添加 `vendor-vue` 条目，将 `vue` 和 `vue-router` 打包到 `vendor-vue-*.js`
- **影响范围:** web/vite.config.ts（仅新增 `build` 配置节），构建产物：vendor-vue chunk ~105kB，主 index chunk 降至 ~541kB

## 2026-07-03: Vue vendor chunk 代码分割 + TypeScript 类型修复
- **文件:**
  - `web/vite.config.ts`
  - `web/src/components/tools/FilesBubble.vue`
  - `web/src/components/tools/WeatherBubble.vue`
- **原因:** 主 chunk 647KB 过大；vue-tsc 3 个 TS 类型错误
- **决策:** vite.config.ts 添加 manualChunks 拆出 vendor-vue (105KB)；修复 computed 类型断言
- **影响范围:** web/

## 2026-07-10: 修复多同名工具前端事件匹配 — 改用 tool_call_id 精确匹配
- **文件:**
  - `web/src/types/index.ts`
  - `web/src/composables/useChat.ts`
  - `web/src/views/PlaygroundView.vue`
- **原因:** Issue #228 — `findRunningTool` 按 `tool_name` 匹配同名多实例时总是返回最后一个，导致交互数据挂错到错误的气泡
- **决策:**
  - `types/index.ts`: `ToolStartEvent`/`ToolEndEvent`/`ToolErrorEvent`/`AskUserEvent` Payload 增加 `tool_call_id`，`ToolCall` 接口增加 `toolCallId`
  - `useChat.ts`: `tool_start` 时存储 `toolCallId`；`tool_end`/`tool_error` 改用 `findToolByCallId` 精确匹配；`ask_user` 优先按 `tool_call_id` 匹配，退避到"首个未配对"按名匹配
  - `PlaygroundView.vue`: mock ToolCall 增加 `toolCallId` 字段
- **影响范围:** web/src/ 下 3 个文件
