# 交互与动效

## fragment（reveal 自带，点击渐进——演讲控场）
```html
<p class="fragment">第一点</p>
<p class="fragment">第二点</p>
```
演讲时按方向键逐步显示。variant：`fade-out` / `shrink` / `grow` / `highlight` / `fade-up`（`class="fragment fade-up"`）。

## <details> 可展开细节（不占正文，可选深挖）
```html
<details>
  <summary>展开看详情</summary>
  <p>详细内容...</p>
</details>
```

## iframe 嵌入（在线 demo / 交互图表 / 网页）
```html
<iframe src="https://example.com" width="100%" height="500" frameborder="0"></iframe>
```

## medium-zoom（按需引，图片点击放大）
```html
<script src="https://cdn.jsdelivr.net/npm/medium-zoom@1/dist/medium-zoom.min.js"></script>
<script>mediumZoom('img.zoomable');</script>
```
img 加 `class="zoomable"` 即可点击放大。

## anime.js（按需引，动画，CSS 不够时用）
```html
<script src="https://cdn.jsdelivr.net/npm/animejs@3/lib/anime.min.js"></script>
<script>
  anime({ targets: '.stat-number', translateY: [20,0], opacity: [0,1], duration: 800 });
</script>
```
CSS 动画够用就用 CSS（见 advanced-features.md），复杂动画才用 anime.js。

## countUp.js（按需引，数字滚动，配 stat-card）
```html
<script src="https://cdn.jsdelivr.net/npm/countup.js@2"></script>
<script>
  document.querySelectorAll('[data-countup]').forEach(el => {
    new countUp.CountUp(el, parseFloat(el.dataset.countup), {
      decimalPlaces: +el.dataset.decimals || 0
    }).start();
  });
</script>
```
stat-card 的 `.stat-number` 加 `data-countup="98.5" data-decimals="1"`（见 components.md）。
