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
