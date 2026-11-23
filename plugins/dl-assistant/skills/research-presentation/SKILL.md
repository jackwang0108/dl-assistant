---
name: research-presentation
description: 使用 reveal.js 制作可在浏览器播放的幻灯片。适用于用户需要演示文稿或幻灯片的场景。生成无需构建的 HTML 和 CSS，支持动态主题、可复用组件、多栏布局、动画、讲者备注，以及 highlight.js、KaTeX、Mermaid、D3、Chart.js 和 Plotly。
---

# 使用 reveal.js 制作幻灯片

使用 reveal.js 制作 HTML 幻灯片。直接在浏览器打开 HTML 即可播放，无需构建。

## 交付文件

一份 reveal.js 演示文稿包含以下文件。

1. **HTML 文件**包含各页幻灯片，并从 CDN 加载 reveal.js。
2. **CSS 文件**定义布局、色彩、字体和组件样式。

## 设计要求

**制作前先分析内容，再选择设计元素。**

1. **分析主题**。明确汇报内容、所属领域和适合的语气。
2. **参考品牌规范**。用户提到公司或组织时，考虑其品牌色和视觉规范。
3. **根据内容选择配色**。所选颜色应适合汇报主题。
4. **说明设计理由**。写代码前，先说明采用这些设计的原因。

具体要求如下。
- 写代码前，先说明设计如何配合内容。
- 使用 Arial、Helvetica、Georgia、Verdana 等常见字体，或在 CSS 中通过 `@import` 加载 Google Fonts。
- 用字号、字重和颜色区分内容层级。
- 保持文字与背景的对比度，采用合适的字号和整齐的对齐方式。
- 在各页统一重复元素的样式和间距。
- **字号统一用 `pt`**。幻灯片尺寸固定，`pt` 的显示效果容易预估，与 PowerPoint 和 Keynote 常见的字号单位一致。字号不要用 `em`、`rem` 或 `px`。

### 选择配色

根据具体汇报确定配色。
- 选择适合当前主题的颜色，避免直接套用默认配色。
- 兼顾主题、领域、语气、节奏、目标听众和用户提到的品牌规范。
- 可以尝试不同搭配。医疗主题也可以用绿色以外的颜色，金融主题也可以用深蓝以外的颜色。
- 选取 3–5 种能协调使用的颜色，分配为主色、辅助色和强调色。
- 确保文字在所用背景上清晰可读。

以下配色可直接使用、调整，也可以自行搭配。

1. **经典蓝色**。深海军蓝（#1C2833）、石板灰（#2E4053）、银灰（#AAB7B8）、米白（#F4F6F6）。
2. **青绿与珊瑚红**。青绿（#5EA8A7）、深青绿（#277884）、珊瑚红（#FE4447）、白色（#FFFFFF）。
3. **红色为主**。红色（#C0392B）、亮红（#E74C3C）、橙色（#F39C12）、黄色（#F1C40F）、绿色（#2ECC71）。
4. **暖粉色**。灰紫（#A49393）、浅粉（#EED6D3）、玫瑰粉（#E8B4B8）、奶油白（#FAF7F2）。
5. **酒红与金色**。酒红（#5D1D2E）、深红（#951233）、铁锈红（#C15937）、金色（#997929）。
6. **紫色与翠绿**。紫色（#B165FB）、深蓝（#181B24）、翠绿（#40695B）、白色（#FFFFFF）。
7. **奶油色与森林绿**。奶油色（#FFE1C7）、森林绿（#40695B）、白色（#FCFCFC）。
8. **粉色与紫色**。亮粉（#F8275B）、珊瑚红（#FF574A）、玫瑰粉（#FF737D）、紫色（#3D2F68）。
9. **青柠绿与梅紫**。青柠绿（#C5DE82）、梅紫（#7C3A5F）、珊瑚红（#FD8C6E）、蓝灰（#98ACB5）。
10. **黑色与金色**。金色（#BF9A4A）、黑色（#000000）、奶油白（#F4F6F6）。
11. **鼠尾草绿与陶土红**。鼠尾草绿（#87A96B）、陶土红（#E07A5F）、奶油白（#F4F1DE）、炭灰（#2C2C2C）。
12. **炭灰与红色**。炭灰（#292929）、红色（#E33737）、浅灰（#CCCBCB）。
13. **亮橙色**。橙色（#F96D00）、浅灰（#F2F2F2）、炭灰（#222831）。
14. **森林绿**。黑色（#191A19）、绿色（#4E9F3D）、深绿（#1E5128）、白色（#FFFFFF）。
15. **复古多色**。紫色（#722880）、粉色（#D72D51）、橙色（#EB5C18）、琥珀色（#F08800）、金色（#DEB600）。
16. **复古大地色**。芥末黄（#E3B448）、鼠尾草绿（#CBD18F）、森林绿（#3A6B35）、奶油白（#F4F1DE）。
17. **灰粉与棕灰**。灰玫瑰色（#AD7670）、棕灰（#B49886）、蛋壳白（#F3ECDC）、灰白（#BFD5BE）。
18. **橙色与蓝绿**。浅橙（#FC993E）、灰蓝绿（#667C6F）、白色（#FCFCFC）。

### 内容与布局

即使相邻页面的内容类型相似，也可以使用不同的布局。

- **交替采用布局**，例如分栏、纵向排列的内容区和卡片。
- 按内容需要选用普通文本、自定义容器或块引用。
- 用 `<strong>` 强调重要术语，用不同颜色区分内容类别。
- 可在列表之间加入引用、内容区或分栏。
- 避免连续多页使用相同布局。

让页面便于快速阅读。
- 用简短要点呈现内容，避免堆放长段落。
- 尽量每页只讲一个主要观点。
- 可使用 Font Awesome 图标帮助区分内容。

**内容较少时可放大文字**，合理利用页面空间。

## 制作流程

### 第 1 步：规划幻灯片结构

根据用户提供的内容，确定以下事项。
- 需要多少页。
- 哪些页用作分节标题，采用居中的大字布局。
- 哪些内容需要用纵向幻灯片组展示补充细节。

### 第 2 步：生成初始 HTML

运行与本文件同目录下的 `scripts/create-presentation.js` 生成初始 HTML。

```bash
node <path-to-skill>/scripts/create-presentation.js --structure 1,1,d,3,1,d,1 --title "My Presentation" --output presentation.html
```

**脚本路径**。以本文件所在目录为起点查找 `scripts/create-presentation.js`，运行前先确认插件的实际安装路径。

可用参数如下。
- `--slides N` 生成 N 页横向幻灯片，适用于简单结构。
- `--structure <list>` 用逗号分隔的值指定混合结构。
  - `1` 表示单页横向幻灯片。
  - `N`（N > 1）表示 N 页纵向排列的幻灯片。
  - `d` 表示分节标题页。文字居中，无内容容器。
- `--output <file>` 指定输出文件名，默认为 presentation.html。
- `--title <text>` 指定演示文稿标题。
- `--styles <file>` 指定 CSS 文件名，默认为 styles.css。

以下是运行示例。
```bash
# 10 horizontal slides
node <path-to-skill>/scripts/create-presentation.js --slides 10 --output presentation.html

# Mixed structure: intro, 2 content slides, divider, 3-slide vertical stack, divider, closing
node <path-to-skill>/scripts/create-presentation.js --structure 1,1,1,d,3,d,1 --title "Q4 Review" --output presentation.html
```

### 第 3 步：生成主题

按内容选定主色后，运行 `generate-theme.js` 生成 `styles.css`，其中包含配色、字体、提示框和代码块样式。主色、明暗模式和字体搭配见[主题生成说明](references/theme-generation.md)。

```bash
node <path-to-skill>/scripts/generate-theme.js --primary "#1C2833" --mode light --font-pairing academic --output styles.css
```

脚本生成三层样式变量（基础值、用途、组件），按 WCAG 检查对比度，并自动将强调色和辅助色的对比度调至至少 4.5:1。按输出修改 HTML 中 `<link id="highlight-theme">` 的 `href`，深色模式用 monokai-sublime，浅色模式用 github。

`base-styles.css` 定义脚本要填充的 CSS 变量。

使用 Google Fonts 时，在 CSS 文件顶部加入 `@import`。
```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;600&display=swap');

:root {
  --heading-font: "Playfair Display", Georgia, serif;
  --body-font: "Lato", Helvetica, sans-serif;
  /* ... */
}
```

基础样式包含以下内容。

1. **CSS 变量**便于统一调整。
```css
:root {
  /* ===========================================
     BACKGROUND COLOR - Set this first!
     =========================================== */
  --background-color: #ffffff;  /* Change for dark themes (e.g., #1a1a2e) */

  /* Typography - ALWAYS use pt for font sizes */
  --heading-font: "Source Sans Pro", Helvetica, sans-serif;
  --body-font: "Source Sans Pro", Helvetica, sans-serif;
  --base-font-size: 32px;  /* Only px value - sets reveal.js base */
  --text-size: 16pt;       /* Base body text - intentionally small */
  --h1-size: 48pt;
  --h2-size: 36pt;
  --h3-size: 24pt;

  /* Colors - customize these for each presentation */
  --primary-color: #2196F3;
  --secondary-color: #ff9800;
  --text-color: #222;       /* Use light color (e.g., #FAF7F2) for dark backgrounds */
  --muted-color: #666;      /* Adjust for dark backgrounds too */
}
```

2. **reveal.js 样式覆盖**使用 `.reveal` 前缀。
```css
.reveal {
  font-family: var(--body-font);
}

.reveal h1, .reveal h2, .reveal h3 {
  font-family: var(--heading-font);
  text-transform: none;
  color: var(--text-color);
}

.reveal p, .reveal li {
  font-size: var(--text-size);
  color: var(--text-color);
}
```

3. **页面布局样式**控制内边距和位置。
```css
.reveal .slides section {
  padding: 40px 60px;
  text-align: left;
}
```

4. **字号辅助类**用于放大内容较少的页面中的文字。
```css
/* Base text is 16pt - use these classes to increase size when needed */
.text-lg { font-size: 18pt; }    /* Slightly larger */
.text-xl { font-size: 20pt; }    /* Medium emphasis */
.text-2xl { font-size: 24pt; }   /* Strong emphasis */
.text-3xl { font-size: 28pt; }   /* Very large */
.text-4xl { font-size: 32pt; }   /* Maximum body text */
.text-muted { color: var(--muted-color); }
.text-center { text-align: center; }
```

字号设置说明如下。
- 默认正文字号（`--text-size: 16pt`）较小，便于容纳较多内容。
- 内容较少的页面可用 `.text-lg`、`.text-xl` 等类放大正文。
- 分页调整字号，既可减少内容较多的页面溢出，也能合理利用内容较少的页面空间。

**重复样式使用独立 CSS 类**

每页的网格和弹性布局可用内联样式。相同样式出现至少 3 次时，在 `styles.css` 中定义独立类以保持一致，避免重复内联样式。常见例子包括数字卡片、功能卡片、时间线和人物简介卡片。

### 第 4 步：填写 HTML 内容

**使用 Edit 工具分次填写，每次处理一页或几页。** 初始 HTML 为每页生成了独立的占位文字（例如 `Slide 2 Title Here`），可以据此定位。用局部编辑降低出错概率，避免用 Write 工具重写整个 HTML 文件。

按下列结构填写。

**标准幻灯片结构**
```html
<section id="unique-slide-id">
  <h2>Slide Title</h2>
  <div class="content">
    <!-- Content here -->
  </div>
</section>
```

**多栏布局统一使用内联 CSS Grid**。避免新建 `.grid-2` 之类的通用类。
```html
<!-- Equal columns -->
<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px;">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

<!-- Three columns -->
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px;">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>

<!-- Unequal columns -->
<div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
  <div>Narrow sidebar</div>
  <div>Wide main content</div>
</div>
```

每页可以用内联样式单独设置列宽比例和间距，无需为各种布局新增通用类。

HTML 结构要求如下。
- 为每个 `<section>` 设置唯一的 `id`，以便稳定定位。
- 居中的分节标题页使用 `class="section-divider"`。
- 主体内容放在 `<div class="content">` 中，以保持间距一致。该容器使用 Flexbox，占据标题下方的剩余高度。
- 用 `<div class="footnote">` 放置页底的署名或来源。
- **所有可见文字放在 `<p>`、`<li>` 或 `<h1>`–`<h6>` 内**，以继承 CSS 定义的基础字号、颜色和行高。`<div>` 只作网格或弹性布局容器，容器里的正文用 `<p>`；也不要将正文直接放进 `<span>`。

### 第 5 步：检查内容是否越界

运行检查脚本，确认各页内容都在幻灯片边界内。

```bash
node scripts/check-overflow.js presentation.html
```

脚本检查每页的两个方向。
- **纵向溢出**指内容高度超过页面高度。
- **横向溢出**指内容宽度超过页面宽度。

发现溢出时，删减受影响页面的内容或调整字号。

<a id="step-6-visual-review-with-screenshots"></a>

### 第 6 步：逐页检查截图
**必须检查每一页的截图。** 有些视觉问题只有逐页核对才能发现。

对所有页面截图。

```bash
cd <presentation-directory>
npx decktape reveal "presentation.html?export" output.pdf \
  --screenshots \
  --screenshots-directory "screenshots/$(date +%Y%m%d_%H%M%S)"
```

`?export` 参数会关闭图表动画，便于导出 PDF。直接在浏览器打开 HTML 时，图表仍会播放动画。

命令会生成带时间戳的目录（例如 `screenshots/20241210_143052/`），便于区分版本并比较修正前后的截图。

使用 Read 工具查看每一张截图。

#### 截图检查项目

溢出脚本可检查大部分布局问题，下列情况需要结合截图核对。

1. **容器继承的文字颜色**。深色页面若使用浅色文字，浅底容器可能也继承浅色文字。必要时为该容器显式设置深色文字。

2. **自定义列表样式**。覆盖默认样式后，检查列表符号与各容器背景是否有足够对比度。

3. **图标加载**。Font Awesome 加载失败时，图标可能显示成空方框或完全消失。

4. **嵌套布局是否越界**。复杂嵌套布局可能有脚本未检出的溢出。

5. **意外换行**。检查预期单行显示的文字是否折成两行，特别是各列标题的换行是否造成对齐不一致。

修正后，重新截取受影响的页面。
```bash
npx decktape reveal "presentation.html?export" output.pdf \
  --screenshots \
  --screenshots-directory "screenshots/$(date +%Y%m%d_%H%M%S)" \
  --slides 2,5,7-9
```

复查更新后的截图。用带时间戳的新目录与上一个版本比较。

### 第 7 步：告知用户如何在浏览器编辑

完成演示文稿后，告知用户可以用随附的编辑脚本在浏览器直接修改文字。

```bash
node <path-to-skill>/scripts/edit-html.js <presentation-directory>/presentation.html
```

脚本会通过本地服务器打开演示文稿。用户可以点击文字编辑并保存回文件，适合调整措辞和修正错字。

**每次交付演示文稿时都附上这条使用说明。** 例如：

> 可以在浏览器中直接调整措辞。
> ```
> node <resolved-path>/scripts/edit-html.js <presentation-directory>/presentation.html
> ```
> 点击文字开始编辑，按 Escape 取消选中，再点击 Save 保存。完成后按 Ctrl+C 停止服务器。

## CSS 组件参考

### 块引用
```css
.reveal blockquote {
  border-left: 4px solid var(--primary-color);
  padding-left: 20px;
  margin: 20px 0;
  font-style: italic;
  background: none;
  box-shadow: none;
  width: 100%;
}

.reveal blockquote cite {
  display: block;
  margin-top: 10px;
  font-style: normal;
  color: var(--muted-color);
}
```

### 图标（Font Awesome）

生成的初始 HTML 已包含 Font Awesome。用法如下。
```html
<i class="fa-solid fa-lightbulb"></i>
<i class="fa-solid fa-check"></i>
<i class="fa-solid fa-gears"></i>
```

## 高级功能

逐步显示、讲者备注、自定义背景、自动动画和转场的用法见[高级功能](references/advanced-features.md)。

## Reveal.js 配置

```javascript
Reveal.initialize({
  controls: true,          // Show navigation arrows
  progress: true,          // Show progress bar
  slideNumber: true,       // Show slide numbers
  hash: true,              // Update URL hash for each slide
  transition: 'slide',     // none/fade/slide/convex/concave/zoom
  center: false,           // Vertical centering of slide content
  autoSlide: 0,            // Auto-advance (ms), 0 to disable
  loop: false,             // Loop presentation
});
```

`center` 默认为 `false`，内容从顶部对齐，适合信息较多的页面。需要内容垂直居中时，可设为 `true`。

## Reveal.js 内置 CSS 类

以下类可直接使用，无需定义额外样式。

- `r-fit-text` 自动调整字号，使文字填满幻灯片。
- `r-stretch` 拉伸元素，使其填满剩余纵向空间。
- `r-stack` 将多个元素叠放在一起。

```html
<h1 class="r-fit-text">BIG TEXT</h1>
<img class="r-stretch" src="image.jpg">
```

## 添加图表

**添加任何图表前，必须先完整阅读[图表说明](references/charts.md)。** 图表需要按指定的 Flexbox 或网格结构布局，以免超出页面边界。

初始 HTML 已包含 Chart.js 插件，可以添加柱状图、折线图、饼图、环形图和散点图。

**图表需放在 Flexbox 容器内，并设置 `maintainAspectRatio: false`。**

```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; position: relative; min-height: 0;">
    <canvas data-chart="bar">
    <!--
    {
      "data": {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [{ "label": "Revenue", "data": [12, 19, 8, 15] }]
      },
      "options": {
        "maintainAspectRatio": false
      }
    }
    -->
    </canvas>
  </div>
</section>
```

[图表说明](references/charts.md)包含以下内容。
- 整页、左右半页、上下半页、四分之一页和不等比例（1fr 2fr、1fr 3fr）布局。
- 为什么需要 Flexbox 布局，以及 Chart.js 如何处理宽高比。
- 柱状图、折线图、饼图、环形图、散点图等类型。
- 图表样式与配色选项。
- CSV 数据格式，也可用来替代 JSON。

## 依赖

脚本所需依赖安装在插件根目录的 `node_modules` 中。
- **Node.js** 用于运行脚本。
- **Puppeteer** 供 `check-overflow.js` 和 Decktape 使用。
- **Decktape** 用于截图和导出 PDF，通过 `npx decktape` 运行。参见[安装说明](references/engineering.md)。

**浏览器启动失败时的处理**。`check-overflow.js` 先尝试启动完整 Chrome，失败后自动改用 `chrome-headless-shell`。Puppeteer 下载的 Chrome 可能不完整，重复运行 `puppeteer browsers install` 不会校验已有下载。备用浏览器也无法启动时，按提示运行 `npx puppeteer browsers install chrome-headless-shell`，或设置 `PUPPETEER_EXECUTABLE_PATH` 指向可用的 Chrome。使用 Decktape 时也可按同样方式处理。

**初始 HTML 自动加载的库**包括 reveal.js、Chart.js、Font Awesome、highlight.js、KaTeX、Mermaid 和 qrcode.js。
**仅在使用这些库的页面加载** D3、Iconify、Plotly、diff2html、rough.js、Leaflet、anime.js、countUp.js 和 medium-zoom。具体用法见下表。

## 参考文档

| 想做什么 | 查这个 |
|---|---|
| 生成主题（配色/字体派生）| references/theme-generation.md |
| 用组件（callout/stat/card/timeline/badge/compare/quote）| references/components.md |
| 布局（多列/图文/代码+输出）| references/layout-patterns.md |
| 代码高亮/diff/复制按钮| references/code-highlighting.md |
| 数学公式/推导 fragment| references/math-formulas.md |
| 图（mermaid/d3/rough.js/leaflet）| references/diagrams.md |
| 图表（Chart.js/plotly）| references/charts.md |
| 交互动效（fragment/details/zoom/anime/countUp）| references/interactions.md |
| 二维码/图标| references/utilities.md |
| reveal 高级（fragment/auto-animate/r-fit-text/CSS 动画）| references/advanced-features.md |
