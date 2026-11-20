# 用真实数据制作和解释图表

先明确图要回答什么，再选编码。趋势用线，离散比较用点/条，分布用适当分布图，逐样本关系用散点；表格适合精确少量读数。未指定图形不默认饼图、3D或仪表盘。

图的来源、条件/划分、样本/重复、单位、统计量、不确定性、缺失/排除和选择规则要可查。不同训练预算或数据划分不能只放在同一坐标上宣称公平比较。变换坐标/截断轴/平滑要说明；颜色/尺度跨方法保持一致。

## 本地Chart.js

生成时启用--features charts。默认支持内嵌JSON和有表头的CSV，外部数据文件需本地HTTP预览。使用chart-container给画布真实高度。

```html
<div class="chart-container" data-asset-id="paired-errors">
  <canvas data-chart="bar" aria-label="同条件下各分组的错误率比较" role="img"><!--
  {"data":{"labels":["分组A","分组B"],"datasets":[{"label":"实际实验读数","data":[1,2]}]},"options":{"maintainAspectRatio":false}}
  --></canvas>
</div>
```

上例数字仅说明语法，使用时替换为实际数据，不作为研究证据。可用类型：line/bar/pie/doughnut/radar/polarArea/bubble/scatter。scatter/bubble使用x/y与可选r，空读数可null，不能用NaN/Infinity或无说明的0填缺失。

`data-chart-src="assets/results.json"` 可读本地配置；CSV第一列为类别，其余为数值列，支持引号字段。正式复杂统计、科研图、误差带/小提琴图等优先由标准绘图工具生成SVG/PDF/PNG，保留数据和绘图脚本；不要为了使用JS重新实现不可靠统计。

动态选择分组、查看单点、切换尺度等可以增强解释，但初始视图应能回答主要问题；PDF保留必要分组/尺度和静态注释。教学习例和真实结果分别标注，交互产生的视觉变化不等于新增实验证据。

check-charts核格式、类型、数值和部分结构，不证明图形适配、来源真实或统计正确。仍需实际查看坐标/图例、中文、误差/对数轴和关键读数，检查Canvas在导出时是否已完成绘制。
