# 布局速查 (inline grid)

保持原 skill inline 哲学：**不造 preset layout 类**，每页用 inline `style="display:grid"` 自由搭。每个 `<section>` 要有唯一 `id`，主内容包在 `<div class="content">` 里。

所有可见文字必须在 `<p>/<li>/<h1>-<h6>` 里（继承基础样式），`<div>` 只做布局容器。

## 单栏
```html
<div class="content">
  <p>内容</p>
</div>
```

## 双栏
```html
<div style="display:grid; grid-template-columns:repeat(2,1fr); gap:30px;">
  <div><p>左</p></div>
  <div><p>右</p></div>
</div>
```

## 三栏
```html
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:25px;">
  <div><p>1</p></div><div><p>2</p></div><div><p>3</p></div>
</div>
```

## 不等列（1fr 2fr）
```html
<div style="display:grid; grid-template-columns:1fr 2fr; gap:30px;">
  <div><p>窄</p></div>
  <div><p>宽</p></div>
</div>
```

## 图文左右
```html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:30px; align-items:center;">
  <div><img src="..." style="width:100%"></div>
  <div><p>说明文字</p></div>
</div>
```

## 代码 + 输出
```html
<div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
  <div class="code-block"><pre><code class="language-python">...</code></pre></div>
  <div><p>输出说明</p></div>
</div>
```

## 数据卡行（stat-card grid）
```html
<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:20px;">
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
</div>
```

## 时间线
用 `.timeline` 组件（见 components.md），不用 inline grid。
