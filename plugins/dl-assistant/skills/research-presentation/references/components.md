# 组件库

预置 CSS 类（base-styles.css），颜色走 token，换主题（generate-theme.js）自动联动。**重复 3+ 次的视觉模式用组件类，单页独特布局用 inline grid**（见 layout-patterns.md）。

所有文字必须在 `<p>/<li>/<h>` 里，`<div>` 只做布局容器。

## callout 提示框
```html
<div class="callout">
  <div class="callout-title">提示</div>
  <p>内容文字</p>
</div>
```
variant：`tip` / `warning` / `success` / `danger`（加 class，如 `class="callout warning"`）

## stat-card 数字卡（配 countUp.js 数字滚动）
```html
<div class="stat-card">
  <div class="stat-number" data-countup="98.5" data-decimals="1">0</div>
  <div class="stat-label">准确率 %</div>
</div>
```
countUp.js 按需引（见 interactions.md），数字从 0 滚到目标。

## feature-card 特性卡
```html
<div class="feature-card">
  <div class="feature-icon"><i class="fa-solid fa-lightbulb"></i></div>
  <h3>标题</h3>
  <p>描述文字</p>
</div>
```

## timeline 时间线
```html
<div class="timeline">
  <div class="timeline-item"><p><strong>2023</strong> 事件一</p></div>
  <div class="timeline-item"><p><strong>2024</strong> 事件二</p></div>
</div>
```

## badge / tag
```html
<span class="badge">新</span>
```

## compare VS 对比
```html
<div class="compare">
  <div><p>方案 A...</p></div>
  <div class="vs">VS</div>
  <div><p>方案 B...</p></div>
</div>
```

## pull-quote 大字引言
```html
<div class="pull-quote">"引言内容"</div>
```

## blockquote（原 skill 保留）
```html
<blockquote>引言内容<cite>来源</cite></blockquote>
```
