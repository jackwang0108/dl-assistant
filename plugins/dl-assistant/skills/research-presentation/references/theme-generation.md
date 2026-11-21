# 主题生成 (generate-theme.js)

agent 每次基于 slide 内容**动态生成一整套主题**（配色+字体+callout+代码块配色），不预设固定主题。实现层与内容层无关——规则通用，不绑场景。

## 工作流
1. 分析 slide 内容 → 定主色 hex + mode + 字体配对
2. 调 `generate-theme.js` 生成 styles.css（三层 token + 组件 token + 对比度校验）
3. 改 HTML 的 `<link id="highlight-theme">` href 匹配 mode

## 从内容定主色（通用规则）
- 从主题/情绪/品牌色提取主色（如环保→绿、科技→蓝、暖→橙；用户提品牌就用品牌色）
- 避免 autopilot 默认蓝；主色为锚，派生辅色/强调色
- 给主色 hex（如 `#1C2833`）

## 定 mode
- `light`：白底，内容多/正式
- `dark`：深底，code 多/炫/护眼

## 字体配对（3 套，`--font-pairing` 参数）
- `academic`：衬线标题(Source Serif Pro) + 无衬线正文，正式
- `modern`：无衬线(Source Sans Pro)，通用
- `mono-heavy`：等宽标题(JetBrains Mono) + 无衬线正文，代码多
- Google Fonts `@import` 加在 styles.css 顶部

## 调脚本
```bash
node scripts/generate-theme.js --primary "#1C2833" --mode light --font-pairing academic --output styles.css
```

## 校验报告
脚本输出 WCAG 对比度，text vs background 应 ≥ 4.5:1。不过的调主色或换 mode。accent/辅色已自动调到过 4.5（保留色相）。

## highlight 主题联动
脚本按 mode 推荐 highlight.js 主题（dark→monokai-sublime，light→github）。改 HTML `<link id="highlight-theme">` 的 href 到推荐主题。

## 三层 token（generate-theme.js 产出）
- primitive：raw hex（--color-primary/secondary/accent）
- semantic：用途别名（--text-color/--background-color/--box-bg）
- component：组件级（--callout-bg/--stat-card-bg/--code-bg）
组件类只引用 semantic/component token，换主题只改 :root，组件自动联动。
