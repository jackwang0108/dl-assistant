# 按信息关系选择布局

同一组比较保持位置、颜色和尺度一致；不为了视觉变化改排列。每页一个明确任务，可以包含多个有关系的图/信息块，不是机械限制每页一个对象。

根section带唯一id，标题后用.content承载正文。图片优先figure/figcaption；纯布局用div，文字用语义元素。span和SVG文字可以正常使用，只需明确其字体/颜色继承，不按标签名称判定可读性。

```html
<section id="method-overview">
  <h2>方法如何保留时间信息？</h2>
  <div class="content grid" style="grid-template-columns:minmax(0,1.4fr) minmax(0,1fr)">
    <figure>
      <div class="visual"><img data-asset-id="method" src="assets/method.svg" alt="带时间顺序的处理流程"></div>
      <figcaption>根据当前实现绘制，示意图。</figcaption>
    </figure>
    <div><p>在此解释读图顺序和关键关系。</p></div>
  </div>
  <p class="footnote">实际来源及范围。</p>
  <aside class="notes">先指输入与输出，再讲需要保留的关系。</aside>
</section>
```

- 单一复杂图：让图占主体，少量标注说明读图顺序，不再旁边重复一屏文字。
- 图文并列：根据图的细节给足空间；左右比例由内容决定，不默认对半。
- 方法比较：两侧同样样本/尺度/颜色，差异在同一位置标注；不能将一个方法的有利样本与另一个方法的不利样本拼在一起。
- 结果图：标题说明待答问题/观察，图旁只写有依据的解释与限制；完整条件和来源保持可取得。
- 图表/代码+输出：给容器min-height:0并测试实际尺寸，避免flex/grid子元素把页面撑开。

SVG/图片内部小字不因外层没溢出就变得可读。局部放大可用第二个裁剪图或DOM局部标注，记录裁剪关系，不删掉会改变解释的证据。附录另页不与正文重叠隐藏。
