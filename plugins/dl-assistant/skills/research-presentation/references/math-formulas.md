# 数学公式 (KaTeX)

初始 HTML 已加载 KaTeX，并注册了自动渲染。写 LaTeX 即可，`$...$` 行内、`$$...$$` 行间。触发 `slidechanged` 事件时自动渲染当前页。

## 行内
```html
<p>能量 $E = mc^2$ 关系</p>
```

## 行间
```html
<p>$$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$</p>
```

## 常用语法
- 分数：`\frac{a}{b}`
- 求和：`\sum_{i=1}^{n}`
- 积分：`\int_a^b`
- 矩阵：`\begin{bmatrix}a&b\\c&d\end{bmatrix}`
- 上下标：`x^2`、`x_i`
- 希腊字母：`\alpha \beta \gamma \theta \omega`

## 推导 fragment（逐步显示推导步骤）
配合 reveal fragment，每步一个 fragment，演讲时按方向键逐步显示：
```html
<div class="content">
  <p>$$a^2 + b^2$$</p>
  <p class="fragment">$$= c^2$$</p>
  <p class="fragment">$$\Rightarrow c = \sqrt{a^2 + b^2}$$</p>
</div>
```

## decktape 截图
`?export` 模式公式已渲染（无动画），截图无问题。
