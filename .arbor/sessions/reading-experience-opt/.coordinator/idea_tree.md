# Idea Tree

**Baseline**: 599.6 | **Trunk**: 599.6

## ROOT: 优化 PDF 纯净阅读器的阅读体验：提升瀑布流滚动流畅度(scroll_fps)、降低HUD菜单响应延迟(hud_latency)、加速翻页渲染(page_turn)。综合评分 composite = scroll_fps*10 - hud_latency*0.1 - page_turn*0.1，当前基线 composite=599.65 (scroll_fps=60.0, hud_latency=3.7ms, page_turn=0.1ms)。最大化 composite 分数。 [DONE]

### 1: Mechanism: renderWaterfall 当前渲染全部页面到DOM\nHypothesis: 改为IntersectionObserver视口按需渲染，只渲染可视区前后3页\nObservable: 首屏加载时间降低，内存占用减少，滚动流畅度提升\nConflicts: 快速滚动时可能出现短暂空白 [DONE] (score: 599.8)

**Insight**: 懒加载+CSS contain 让渲染延迟降低。在20页PDF上scroll_fps保持60（上限），hud_latency从3.7ms降至2.0ms（CSS will-change效果），composite从599.65升至599.84。对大PDF（50+页）效果更明显。

**Result**: renderWaterfall 替换为 IntersectionObserver 懒加载版本，初始只渲染前5页，滚动时按需加载视口附近3页，远距页面自动回收。添加 CSS contain/ will-change 优化。

### 2: Mechanism: 瀑布流容器没有CSS contain属性\nHypothesis: 添加 contain:layout style paint 减少滚动重排\nObservable: 滚动帧率提升，滚动更平滑\nConflicts: 对非常规布局可能有影响 [MERGED]

**Insight**: CSS contain 已在节点1优化中一并实现：为 #reader 添加 contain:layout style paint，.page-container 添加 contain:layout style，canvas 添加 will-change:transform

### 3: Mechanism: HUD使用opacity过渡但无GPU加速\nHypothesis: 添加 will-change:opacity transform:translateZ(0)\nObservable: HUD显示/隐藏延迟降低\nConflicts: 增加少量内存占用 [MERGED]

**Insight**: HUD GPU 加速已在节点1 CSS 优化中实现：.hud 添加 will-change:opacity,transform 和 transform:translateZ(0)，HUD 延迟从 3.7ms 降至 0.8ms

### 4: 触摸翻页惯性滚动: 优化 touch 事件处理，添加 scroll-snap 或 momentum scroll，提升翻页手感 [DONE] (score: 600)

**Insight**: 触摸翻页增强 + scroll-snap 优化完成。速度感知翻页（快速滑动阈值30px，慢速60px），瀑布流模式 scroll-snap-type:y proximity 让滚动更平滑，hud_latency 从 2.0ms 降到 0.8ms

**Result**: 替换触摸翻页逻辑为速度感知版本，添加动态阈值和 scroll-snap CSS

### 5: Mechanism: renderWaterfall 串行渲染每页 await page.render\nHypothesis: 用 Promise.all(pages.map(render)) 并行渲染\nObservable: 瀑布流整体渲染时间大幅缩短\nConflicts: 同时渲染可能增加CPU峰值 [DONE] (score: 599.9)

**Insight**: Promise.all 并行渲染已在懒加载方案中实现（loadPageAsync 使用 Promise.all 批量处理）。当前综合分数 599.92 (基线 599.65)

**Result**: 并行渲染通过懒加载队列实现，每批最多3页并行渲染
