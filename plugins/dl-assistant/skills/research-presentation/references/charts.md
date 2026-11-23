# 在 Reveal.js 幻灯片中添加图表

通过 [reveal.js-plugins/chart](https://github.com/rajgoel/reveal.js-plugins) 插件在幻灯片中使用 Chart.js。

## 安装

初始 HTML 默认包含图表插件及以下内容。

```html
<!-- In <head> -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Before Reveal.initialize() -->
<script src="https://cdn.jsdelivr.net/npm/reveal.js-plugins@latest/chart/plugin.js"></script>

<!-- In Reveal.initialize() -->
Reveal.initialize({
  plugins: [ RevealChart ],
  chart: {
    defaults: {
      color: 'lightgray',
      borderColor: 'lightgray'
    }
  }
});
```

## 图表类型

**支持的类型** `line`, `bar`, `pie`, `doughnut`, `radar`, `polarArea`, `bubble`, `scatter`

常用类型如下。
- **bar** - 比较不同类别
- **line** - 展示随时间变化的趋势
- **pie/doughnut** - 展示各部分占比
- **scatter** - 展示变量间的关系

## 图表尺寸要求

图表必须使用以下四种布局之一，以填满分配的空间并避免越界。

1. **整页** - 图表占满标题下方的空间
2. **半页（左右）** - 图表和其他内容分居左右
3. **半页（上下）** - 图表和其他内容分居上下
4. **四分之一页** - 图表占一个区域，其余三个区域放其他内容

### 必需的 CSS 设置

每个图表需要以下设置。
1. **使用 Flexbox 的 section** with `display: flex; flex-direction: column; height: 100%;`
2. **图表容器 div** with `flex: 1; position: relative; min-height: 0;`（网格布局还需设置 `min-width: 0`）
3. **`maintainAspectRatio: false`** 设在图表选项中

### 整页图表布局

```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; position: relative; min-height: 0;">
    <canvas data-chart="bar">
    <!--
    {
      "data": {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [{
          "label": "Revenue",
          "data": [45, 52, 61, 78],
          "backgroundColor": "#2196F3"
        }]
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

### 半页图表布局（左右）

图表在右，其他内容在左。

```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; min-height: 0; min-width: 0;">
    <div style="display: flex; flex-direction: column; justify-content: center; background: #f5f5f5; padding: 20px; border-radius: 8px;">
      <p><strong>Key Points</strong></p>
      <ul>
        <li>First insight</li>
        <li>Second insight</li>
        <li>Third insight</li>
      </ul>
    </div>
    <div style="position: relative; min-height: 0; min-width: 0;">
      <canvas data-chart="pie">
      <!--
      {
        "data": {
          "labels": ["A", "B", "C"],
          "datasets": [{
            "data": [45, 35, 20],
            "backgroundColor": ["#2196F3", "#4caf50", "#ff9800"]
          }]
        },
        "options": {
          "maintainAspectRatio": false
        }
      }
      -->
      </canvas>
    </div>
  </div>
</section>
```

### 半页图表布局（上下）

其他内容在上，图表在下，两部分高度相等。

```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; display: grid; grid-template-rows: 1fr 1fr; gap: 20px; min-height: 0; min-width: 0;">
    <div style="display: flex; align-items: center; justify-content: center; background: #f5f5f5; padding: 20px; border-radius: 8px;">
      <div>
        <p><strong>Analysis Summary</strong></p>
        <p>Description of what the chart shows and key takeaways.</p>
      </div>
    </div>
    <div style="position: relative; min-height: 0; min-width: 0;">
      <canvas data-chart="line">
      <!--
      {
        "data": {
          "labels": ["Jan", "Feb", "Mar", "Apr"],
          "datasets": [{
            "label": "Trend",
            "data": [10, 25, 35, 50],
            "borderColor": "#2196F3",
            "fill": false
          }]
        },
        "options": {
          "maintainAspectRatio": false
        }
      }
      -->
      </canvas>
    </div>
  </div>
</section>
```

### 上方内容与下方图表（不等比例）

上方内容区占 1/4 或 1/3，图表占其余空间。明确指定比例以控制尺寸。

**内容占 1/4，图表占 3/4**
```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; display: grid; grid-template-rows: 1fr 3fr; gap: 20px; min-height: 0; min-width: 0;">
    <div style="display: flex; align-items: center; background: #f5f5f5; padding: 15px 20px; border-radius: 8px;">
      <p><strong>Key insight:</strong> Revenue grew 25% quarter-over-quarter, exceeding targets.</p>
    </div>
    <div style="position: relative; min-height: 0; min-width: 0;">
      <canvas data-chart="bar">
      <!--
      {
        "data": {
          "labels": ["Q1", "Q2", "Q3", "Q4"],
          "datasets": [{
            "label": "Revenue",
            "data": [45, 52, 61, 78],
            "backgroundColor": "#2196F3"
          }]
        },
        "options": {
          "maintainAspectRatio": false
        }
      }
      -->
      </canvas>
    </div>
  </div>
</section>
```

**内容占 1/3，图表占 2/3**
```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Chart Title</h2>
  <div style="flex: 1; display: grid; grid-template-rows: 1fr 2fr; gap: 20px; min-height: 0; min-width: 0;">
    <div style="display: flex; flex-direction: column; justify-content: center; background: #f5f5f5; padding: 15px 20px; border-radius: 8px;">
      <p><strong>Summary</strong></p>
      <ul style="margin: 10px 0 0 0;">
        <li>Strong Q4 performance</li>
        <li>All regions exceeded targets</li>
      </ul>
    </div>
    <div style="position: relative; min-height: 0; min-width: 0;">
      <canvas data-chart="line">
      <!--
      {
        "data": {
          "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
          "datasets": [{
            "label": "Growth",
            "data": [100, 120, 135, 150, 180, 210],
            "borderColor": "#2196F3",
            "fill": false
          }]
        },
        "options": {
          "maintainAspectRatio": false
        }
      }
      -->
      </canvas>
    </div>
  </div>
</section>
```

**常用行高比例**
- `1fr 3fr` - 内容占 25%，图表占 75%，适合少量文字
- `1fr 2fr` - 内容占 33%，图表占 67%，适合短段落或要点列表
- `1fr 1fr` - 各占 50%

### 四分之一页图表布局

图表位于右下角，其余三个区域放其他内容。

```html
<section style="display: flex; flex-direction: column; height: 100%;">
  <h2>Dashboard View</h2>
  <div style="flex: 1; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 15px; min-height: 0; min-width: 0;">
    <div style="display: flex; align-items: center; justify-content: center; background: #e3f2fd; padding: 15px; border-radius: 8px;">
      <div style="text-align: center;">
        <p style="font-size: 2em; margin: 0; color: #1565c0;">$2.4M</p>
        <p style="margin: 0; color: #666;">Total Revenue</p>
      </div>
    </div>
    <div style="display: flex; align-items: center; justify-content: center; background: #e8f5e9; padding: 15px; border-radius: 8px;">
      <div style="text-align: center;">
        <p style="font-size: 2em; margin: 0; color: #2e7d32;">+18%</p>
        <p style="margin: 0; color: #666;">Growth Rate</p>
      </div>
    </div>
    <div style="display: flex; align-items: center; justify-content: center; background: #fff3e0; padding: 15px; border-radius: 8px;">
      <div style="text-align: center;">
        <p style="font-size: 2em; margin: 0; color: #ef6c00;">847</p>
        <p style="margin: 0; color: #666;">New Customers</p>
      </div>
    </div>
    <div style="position: relative; min-height: 0; min-width: 0;">
      <canvas data-chart="doughnut">
      <!--
      {
        "data": {
          "labels": ["Product A", "Product B", "Product C"],
          "datasets": [{
            "data": [40, 35, 25],
            "backgroundColor": ["#2196F3", "#4caf50", "#ff9800"]
          }]
        },
        "options": {
          "maintainAspectRatio": false,
          "plugins": {
            "legend": { "position": "bottom" }
          }
        }
      }
      -->
      </canvas>
    </div>
  </div>
</section>
```

## plotly（按需引，交互式科学图）

Chart.js 画不了的科学图（3D 散点/等高线/热图/box/violin）用 plotly。用 plotly 的 slide 按需引 CDN：

```html
<script src="https://cdn.jsdelivr.net/npm/plotly.js@2/dist/plotly.min.js"></script>
<div id="plot" style="width:100%;height:500px"></div>
<script>
  Plotly.newPlot('plot', [{
    x: [1,2,3], y: [2,5,4], z: [3,6,2],
    mode: 'markers', type: 'scatter3d', marker: {size:8, color: '#2196F3'}
  }], {margin:{l:0,r:0,b:0,t:30}});
</script>
```

### Chart.js vs plotly 选型
- **Chart.js**：基础图（line/bar/pie/doughnut/radar），轻、全局已引。优先用。
- **plotly**：科学图（3D/等高线/热图/box/violin/统计），按需引。Chart.js 画不了时才用。

### decktape 截图注意
plotly 交互模式在 headless 截图可能渲染不全。截图前确保渲染完（`Plotly.newPlot` 返回的 Promise resolve），或用 `Plotly.to图片` 导出静态图嵌入。

## 布局原理

Chart.js 默认保持 2:1 的宽高比，在空间有限的幻灯片中可能造成溢出。Flexbox 和网格布局通过以下设置控制尺寸。

1. **`height: 100%` 用于 section** - 让页面占满可用空间
2. **`flex: 1` 用于容器** - 填满标题下方的剩余空间
3. **`min-height: 0; min-width: 0`** - 允许弹性或网格布局中的子元素缩到小于内容本身尺寸，避免溢出
4. **`position: relative`** - Chart.js 根据容器调整尺寸所需的设置
5. **`maintainAspectRatio: false`** - 让 Chart.js 填满容器，不再强制保持宽高比

## 图表样式

### 配色

在 JSON 配置中设置颜色。

```json
"datasets": [{
  "data": [12, 19, 8, 15],
  "backgroundColor": ["#2196F3", "#ff9800", "#4caf50", "#e91e63"]
}]
```

### 常用图表色组

```javascript
// Blues
["#1565c0", "#1976d2", "#1e88e5", "#2196f3", "#42a5f5"]

// Warm palette
["#c62828", "#ef6c00", "#f9a825", "#2e7d32", "#1565c0"]

// Grayscale
["#212121", "#424242", "#616161", "#757575", "#9e9e9e"]

// Categorical (distinct)
["#2196F3", "#ff9800", "#4caf50", "#e91e63", "#9c27b0"]
```

## 常用选项

### 隐藏图例

```json
"options": {
  "maintainAspectRatio": false,
  "plugins": {
    "legend": { "display": false }
  }
}
```

### 自定义坐标轴标签

```json
"options": {
  "maintainAspectRatio": false,
  "scales": {
    "y": {
      "title": { "display": true, "text": "Revenue ($)" }
    },
    "x": {
      "title": { "display": true, "text": "Quarter" }
    }
  }
}
```

### Y 轴从零开始

```json
"options": {
  "maintainAspectRatio": false,
  "scales": {
    "y": { "beginAtZero": true }
  }
}
```

### 图例位置

```json
"options": {
  "maintainAspectRatio": false,
  "plugins": {
    "legend": { "position": "bottom" }
  }
}
```

## CSV 数据格式

可用 CSV 提供图表数据。

```html
<canvas data-chart="line">
<!--
Month, Sales, Expenses
Jan, 40, 30
Feb, 50, 35
Mar, 60, 40
Apr, 55, 38
May, 70, 45
-->
</canvas>
```

首行为标签，后续各列为数据集。

## 外部 CSV 文件

数据较多时，使用外部 CSV 文件。

```html
<canvas data-chart="line" data-chart-src="data/sales.csv">
<!--
{
  "options": {
    "maintainAspectRatio": false,
    "plugins": { "legend": { "position": "bottom" } }
  }
}
-->
</canvas>
```

## 验证

运行脚本检查图表是否超出页面。

```bash
node scripts/check-overflow.js presentation.html
```

## 使用建议

1. **使用规定的 Flexbox 布局** - 避免直接为 canvas 设置固定高度
2. **必须设置 `maintainAspectRatio: false`** 设在图表选项中
3. **保持图表简洁** - 每页只放汇报需要的信息
4. **统一配色** - 与幻灯片的整体配色一致
5. **控制数据点数量** - 4–8 个数据点较易阅读
6. **检查溢出** - 添加图表后运行 `check-overflow.js`
