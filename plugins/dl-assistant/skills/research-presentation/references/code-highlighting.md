# 代码高亮 (highlight.js + diff2html + 复制按钮)

## highlight.js（全局已引，RevealHighlight plugin 已注册）
代码块自动高亮，标语言即可：
```html
<pre><code class="language-python">def hello():
    print("hi")
</code></pre>
```
支持语言见 highlight.js common 包。

## 代码块组件（带语言标签 + 复制按钮位）
```html
<div class="code-block">
  <span class="code-lang">python</span>
  <button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentElement.querySelector('code').textContent)">复制</button>
  <pre><code class="language-python">def hello():
    print("hi")
</code></pre>
</div>
```
`.code-block` 走 `--code-bg` token，换主题自动联动。复制按钮用 `navigator.clipboard`，无需额外库。

## diff2html（按需引，展示代码 diff）
仅在展示代码差异的页面通过 CDN 加载 diff2html。
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/diff2html/bundles/css/diff2html.min.css">
<script src="https://cdn.jsdelivr.net/npm/diff2html/bundles/js/diff2html.ui.min.js"></script>
```
用法：
```html
<div id="diff"></div>
<script>
  const diffString = `--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@\n-old\n+new\n`;
  document.getElementById('diff').innerHTML = Diff2Html.html(diffString, {inputFormat:'diff', outputFormat:'side-by-side'});
</script>
```

## highlight 主题
HTML 的 `<link id="highlight-theme">` 按 mode 切（generate-theme.js 推荐：dark→`monokai-sublime`，light→`github`）。改 href：
```
https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/<主题>.min.css
```
