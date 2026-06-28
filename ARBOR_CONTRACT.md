# Arbor Research Contract — PDF 纯净阅读器

## 目标项目
- **项目目录**: `~/workspace/pdf-editor`
- **分支**: `main`
- **运行会话**: `reading-experience-opt`

## 优化目标
优化 PDF 纯净阅读器的**阅读体验**，包括：
1. **瀑布流滚动流畅度** — 保持/提升 scroll_fps
2. **HUD 菜单响应延迟** — 降低 hud_latency
3. **翻页渲染速度** — 降低 page_turn

## 指标
- **综合分数**: `composite = scroll_fps * 10 - hud_latency * 0.1 - page_turn * 0.1`
- **方向**: 最大化
- **基线**: `599.65` (scroll_fps=60.0, hud_latency=3.7ms, page_turn=0.1ms)
- **评估命令**: `cd {cwd} && node eval.js --split dev`
- **B_dev**: dev 切分 (默认)
- **B_test**: 无独立测试集

## 优化范围
- ✅ 编辑 `index.html` (核心源代码)
- ✅ 编辑 `eval.js` (评估脚手架)
- ❌ 不修改 `node_modules/`
- ❌ 不修改已有 APK 文件

## 运行配置
- **模式**: 完整优化 (real)
- **预算**: 最多 10 个优化循环
- **交互模式**: auto
- **Scope**: effect-leaning (效果优先)

## 约束
- 不破坏现有功能（文件打开、编辑、PDF操作等）
- 不引入外部依赖
- 保持单个 HTML 文件架构
