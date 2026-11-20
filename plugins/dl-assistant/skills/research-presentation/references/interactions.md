# 交互、样本比较与媒体

JavaScript可以支持讲述过程，关键是让听众看到输入改变后哪些量改变。每个交互明确输入、输出、范围、初始/重置状态、预期讲解和局限；主报告不依赖现场联网或临时训练。

## 可选形式

- 同一样本对照：并列显示、切换、局部放大、图像叠加或拖动比较。标注同一输入和处理条件，防止不同裁剪/尺度制造改善。
- 参数演示：滑块改变阈值、窗口、采样或简单模型参数；显示数值与结果，明确是可检查的教学例子还是已有实测点的选择，不插值后冒称真实性能。
- 信息流/算法步骤：按钮或方向键逐步高亮当前对象、消息/数据流，保留前后关系。
- 代码与结果：代码行高亮联动实际输出或已知小例子，说明运行来源；不能模拟输出冒充已经执行项目。
- 图像细节：点击局部放大、标注关键区域、显示原图与裁剪关系。
- 音频：本地播放器与波形/频谱/时间标记对应；A/B要是相同样本、同一条件的可比较版本。播放差异有响度/设备等条件，不把随意试听当正式评测。
- 视频/项目演示：本地视频、界面录像或可离线运行的小型demo；标版本、场景与已验证范围，预备关键帧/截图。

## 实现与静态替代

运行依赖本地HTML/CSS/JS和素材；图形复杂度以帮助解释为准。按钮和input应有label/键盘操作，避免阻断Reveal翻页；离开页面停止媒体/动画，返回可恢复到说明过的状态。没有必要展示的循环动画不要自动播放。

```html
<div class="live-only" data-interactive data-static-fallback="threshold-summary">
  <label for="threshold">示例阈值</label><input id="threshold" type="range" min="0" max="1" step="0.1" value="0.5">
  <output id="threshold-output" for="threshold">0.5</output>
</div>
<div id="threshold-summary" class="export-only">
  <p>在此提供几个有意义的关键状态及解释，不能只写“请看HTML”。</p>
</div>
```

视频/audio/iframe同样用data-static-fallback引用本页的实际替代内容。PDF中live-only隐藏、export-only显示；默认fragments合并，互斥/替换动画用显式静态图，防止叠在一起。静态替代需保留输入、输出、条件和结论范围，不只是装饰性poster。

自定义异步图/字体/数据准备通过 `Presentation.register(() => actualPromise)` 在 `Presentation.start()` 前登记。ready后仍有用户触发的异步操作，逐个实际验证；自动截图不会替你操作每个滑块/按钮。

检查：操作能否改变预期对象，回退/重置是否正常，讲述能否控制节奏，关键状态是否可读，断网时素材可取，PDF是否保留必要内容。更多界面不等于更多信息。

静态替代为整张figure时，可给容器class="export-only static-figure"，让图按剩余空间缩放；仍需检查图中文字，不把缩放当可读性认证。
