# 图 (mermaid + d3 + rough.js + leaflet)

## mermaid（全局已引，流程/架构/时序/类图）
在 slide 里放 `<div class="mermaid">`，写 mermaid 语法，slidechanged 时自动渲染当前页。
```html
<div class="mermaid">
graph LR
  A[输入] --> B[处理]
  B --> C{判断}
  C -->|是| D[输出]
  C -->|否| E[重试]
</div>
```
支持：graph/flowchart（流程）、sequenceDiagram（时序）、classDiagram（类图）、stateDiagram（状态）、gitGraph 等。语法见 mermaid 文档。

## d3（按需引，复杂网络/力导向图）
仅在需要 D3 的页面加载。
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
```
d3 灵活但代码多、LLM 生成易错。**mermaid 画不了的网络/力导向图才用 d3**。decktape 截图前确保渲染完（等 simulation.tick 结束）。

## rough.js（按需引，手绘风图）
可用手绘风格的矩形、圆和线绘制概念图或草图。
```html
<script src="https://cdn.jsdelivr.net/npm/roughjs@4/bundled/rough.js"></script>
<canvas id="rough" width="400" height="200"></canvas>
<script>
  const rc = rough.canvas(document.getElementById('rough'));
  rc.rectangle(20, 20, 160, 100, { roughness: 2, fill: 'var(--color-primary)' });
  rc.circle(280, 70, 80, { roughness: 1.5 });
</script>
```

## leaflet（按需引，地图）
仅在包含地图的页面加载 CSS 和 JavaScript。
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9/dist/leaflet.js"></script>
<div id="map" style="height:400px"></div>
<script>
  const map = L.map('map').setView([39.9, 116.4], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
  L.marker([39.9, 116.4]).addTo(map).bindPopup('北京');
</script>
```
decktape 截图前等 tile 加载完（networkidle0 通常够，必要时加 setTimeout）。
