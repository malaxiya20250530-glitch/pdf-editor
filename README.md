# 📖 PDF 纯净阅读器

**Zero-UI 沉浸式阅读 · 原生 PdfRenderer · 轻量编辑器**

一款没有广告、没有臃肿功能的纯净 PDF 阅读编辑工具。

## 特性

### 📖 纯净阅读
- **Zero-UI 全屏** — 打开 PDF 即沉浸，100% 屏幕给内容
- **毛玻璃 HUD** — 轻触唤出半透明菜单，4秒自动隐退
- **极简滑块** — 拖动时中央弹出大字页码（如 "7/294"）
- **双指缩放** — 原生 Pinch to Zoom，无 +/− 按钮干扰
- **触摸翻页** — 左右/上下滑动翻页

### 🎨 扫描件优化
- **智能反色** — 白底黑字 → 黑底灰字，夜间不刺眼
- **智能切边** — 切除扫描件四周白边，字号自然放大
- **瀑布流模式** — 流畅垂直连续翻页

### ⚙️ 原生引擎
- **Android PdfRenderer** — 系统内置，零额外大小
- 流畅打开 100MB+ 大型技术文档
- 硬件加速渲染

### ✏️ 编辑器
- 合并 / 排序 / 旋转 / 删除页面
- 文字批注 / 手写签名
- 提取页面 / 保存

## 下载

### 方式一：GitHub Release
[Releases](https://github.com/malaxiya20250530-glitch/pdf-editor/releases) 页面下载最新 APK。

### 方式二：自行构建
```bash
git clone git@github.com:malaxiya20250530-glitch/pdf-editor.git
cd pdf-editor
export ANDROID_HOME=/path/to/android-sdk
./gradlew assembleDebug
# APK 在 app/build/outputs/apk/debug/app-debug.apk
```

### 方式三：Web 版
浏览器直接打开 `index.html` 即可使用（无需安装）。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 渲染 | Android `PdfRenderer` (API 26+) | 原生 PDF 渲染，零额外大小 |
| 阅读 UI | HTML + CSS + JS | Zero-UI 设计，pdf.js 兜底 |
| 编辑 | `pdf-lib` | 纯 JS PDF 操作库 |
| 壳 | Android WebView | Java 桥接原生与 Web |

## 对比

| 特性 | 本应用 | WPS | Adobe Acrobat |
|------|-------|-----|---------------|
| 体积 | 1.3MB | 200MB+ | 150MB+ |
| 广告 | ❌ 无 | ✅ 有 | ❌ 无 |
| 离线 | ✅ | ⚠️ 部分需登录 | ✅ |
| 阅读 | Zero-UI | 标准 | 标准 |
| 编辑 | 基础合并/批注 | 完整办公套件 | 专业级 |

## 截图

```
┌──────────────────────┐
│                      │
│    📖 纯净阅读        │
│                      │
│    第 7 / 294 页      │
│                      │
│  ═══●══════════════  │  ← 底部极简进度条
│                      │
│ 轻触屏幕唤出菜单      │
└──────────────────────┘
```

## 许可

MIT
