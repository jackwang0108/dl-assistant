# Reveal.js 高级功能

以下功能仅在用户明确提出时使用。

## 片段（逐步显示）

逐步显示内容。

```html
<p class="fragment">Appears on click</p>
<p class="fragment fade-up">Slides up</p>
<p class="fragment highlight-red">Turns red</p>
```

可选的片段动画如下。
- `fade-in` （默认）
- `fade-out`
- `fade-up`, `fade-down`, `fade-left`, `fade-right`
- `highlight-red`, `highlight-green`, `highlight-blue`
- `strike` （删除线）

## 讲者备注

添加仅在讲者视图中可见的备注，按 `S` 打开该视图。

```html
<section>
  <h2>Slide Title</h2>
  <p>Visible content</p>
  <aside class="notes">
    Private notes for the presenter.
    - Remember to mention X
    - Transition to next topic
  </aside>
</section>
```

## 背景

### 纯色
```html
<section data-background-color="#283b95">
```

### 图片
```html
<section data-background-image="image.jpg">
<section data-background-image="image.jpg" data-background-opacity="0.5">
<section data-background-image="image.jpg" data-background-size="contain">
```

### 渐变
```html
<section data-background-gradient="linear-gradient(to bottom, #283b95, #17b2c3)">
<section data-background-gradient="radial-gradient(#283b95, #17b2c3)">
```

## Auto-Animate

自动为相邻页面之间的元素添加动画。具有相同 `data-id` 的元素会平滑过渡。

```html
<section data-auto-animate>
  <h1>Title</h1>
</section>
<section data-auto-animate>
  <h1>Title</h1>
  <h2>Subtitle appears with animation</h2>
</section>
```

以下示例演示多个对应元素的过渡。

```html
<section data-auto-animate>
  <div data-id="box" style="width: 100px; height: 100px; background: blue;"></div>
</section>
<section data-auto-animate>
  <div data-id="box" style="width: 300px; height: 150px; background: red;"></div>
</section>
```

## 转场

为单页设置转场。

```html
<section data-transition="fade">
<section data-transition="slide">
<section data-transition="convex">
<section data-transition="concave">
<section data-transition="zoom">
<section data-transition="none">
```

进入和退出可分别设置不同的转场。
```html
<section data-transition="slide-in fade-out">
```

## 幻灯片可见性

从正常播放流程隐藏幻灯片，仅通过 URL 访问。
```html
<section data-visibility="hidden">
```

导航时跳过幻灯片，同时保留其可见性。
```html
<section data-visibility="uncounted">
```

## 代码高亮

基本的语法高亮。
```html
<pre><code class="language-python">
def hello():
    print("Hello")
</code></pre>
```

支持的语言包括 `javascript`, `python`, `html`, `css`, `java`, `ruby`, `go`, `rust`, `sql`, `bash`, `json`, `yaml`等。

**按操作逐步高亮指定行**
```html
<pre><code data-line-numbers="1-2|3|4">
let a = 1;
let b = 2;
let c = x => 1 + 2 + x;
c(3);
</code></pre>
```

先高亮第 1–2 行，再依次高亮第 3 行和第 4 行。

**静态行高亮（一次显示）**
```html
<pre><code data-line-numbers="3,5-7">
...
</code></pre>
```

## 内置辅助类

reveal.js 自带的布局辅助类（直接用，无需自定义 CSS）：

- `r-fit-text` — 自动缩放文字填满幻灯片（大标题用）
- `r-stretch` — 元素拉伸填满剩余垂直空间（图片用）
- `r-stack` — 元素堆叠（层叠动画用）

```html
<h1 class="r-fit-text">BIG TITLE</h1>
<img class="r-stretch" src="diagram.png">
<div class="r-stack">
  <img class="fragment" src="v1.png">
  <img class="fragment" src="v2.png">
</div>
```

## CSS 动画（轻量自制，不引 GSAP）

用 `@keyframes` 自制入场/强调动画，配合 fragment 触发。在 styles.css 加：

```css
@keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
.animate-fade-up { animation: fadeUp 0.6s ease-out; }

@keyframes pulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.05); } }
.animate-pulse { animation: pulse 2s ease-in-out infinite; }
```

用：
```html
<div class="animate-fade-up"><p>入场动画</p></div>
```

CSS 动画够用就用 CSS；复杂时间线/物理动画才用 anime.js（见 interactions.md）。
