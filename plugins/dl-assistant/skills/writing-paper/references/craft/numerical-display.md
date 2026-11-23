# Numerical Display（数据类工艺：数据图 + 表 + 定性图）

`writing-paper` 的**数据类视觉工艺**——make-visual / ingest-results 在**产出时刻**产数据图、填表、做定性图时读这个。

> **角色（新设计）**：form（图还是表）/ encoding / 表结构**不是 write-section 的 spec 给的**——write-section ⑥ 只登记了意图；它们在这里、对着**真实数据**决定（Step 0）。本文件管「根据实际实验数据怎么定 + 怎么产好」。
>
> **红线**：
> - **绝不用生成式 AI 画/改数据**（造假）——数据图/表只用确定性代码（seaborn / matplotlib）+ booktabs；全文任何图都不用生成式 AI（示意图走 HTML，见 `schematic-figure.md`）。
> - **数字由脚本从数据生成，不手敲**——图的数字、`tables/<id>.tex` 的数字都从 CPE 数据目录/数据文件读数生成（产物即真相：可重跑再生）；手敲转录是真实事故源。
> - 定性图的样本必须**真实**（真实数据/真实模型输出），不伪造、不生成、不美化内容本身。

## Step 0：定 form（根据实际实验数据执行抉择程序）

读 `visual-design.md`「数据可视化抉择程序」（程序本体在那，单一真相源），对着真实数据执行：

1. **图还是表**（看数据密度/数量 + 读者任务）：精确查值为主 / 类别 >7 / 多 baseline × 多 metric 密集对比 / 要报 ±std、CI → **表**；趋势/分布/跨 setting 对比为主、读者要形状不要查值 / 定性样例 → **图**。
2. **图 → 类型 + 元素**：epoch/步数趋势 → line；类别对比 → bar；两变量关系 → scatter；矩阵/相关性 → heatmap；分布 → violin/box。元素逐个定（轴/图例/误差棒/标注，规格见原则 3、6）。
3. **表 → 结构**：几行几列、表头每列含义、每行是什么、best/2nd 标记（规格见原则 5）。
4. **快稿预览（确认点：用户看预览图后确认）**：先出快稿（真数据、快速出图，不精雕细琢）→ 渲 PNG 给用户看 → 不满意改 → 确认后才按下面原则精修出正式版。**审批物是预览图，不是文字描述**。

## 原则

### 1. 数据保真（最高优先）

- 一个 claim 一个 **canonical 值**（全文/表/图/abstract 一致，不自相矛盾；登记进 state 节 digest 的 key_numbers）。
- 排除的 run **不进汇总**（要标就 open/hatched marker 点名，绝不混进 mean/std）。
- 不可比条件（不同 N/epoch/初始化）**视觉区分**（facet break / label marker），不画成对等。
- **多 seed 必报散布**：mean ± std 标清 seed 数；显著性用 CI 或文字说明，**不堆星号**。

### 2. 用色：paper palette + 语义色小套

**paper palette + 语义色在 `visual-design.md`「paper palette」段一次锁定**；本节管数据图怎么用：

- **按颜色编码的数据类型选**：分类数据（标识哪条 series 是谁）→ 几个不同色相；有序数值（表示大小）→ 同一色相的深浅渐变；有中点的极性（正/负）→ 两色 + 灰中点；突出一条主线 → 一条亮色 + 其余全部灰色。
- **语义角色用语义色**：正/负、升/降、对照或基线灰——只用锁定时定的那套语义色，不临时挑。**红绿双编码**：红/绿表正负时必须同时用形状/线型/文字表达（灰度打印下单靠红绿分不出）。
- **禁**：rainbow（多色渐变表大小）/ dual-axis（两 y 轴造假相关）/ nominal 上 value-ramp（给无序类别上深浅=双重编码）/ 生成第 9 色（类别 >8 个就改分面或合并进 Other，别硬加色）。
- 散点/小多重图渲染灰度版自查——series 灰度下分得开才算过（区分度兜底；分不开就线型/marker 双编码）。

### 3. mark 规格 + 反模式（图）

去掉一切不编码数据的装饰（3D / 阴影 / 渐变 / 粗边框 / 虚线网格 / 逐点标值）；视觉重量只留给数据本身：

- bar/column：≤ 槽宽、留间隙、单 baseline 起。
- line：2px、round join；marker ≥8px（r≥4）、filled。
- area fill：~10% 半透明（不是饱和实心块）。
- gridline/axis：hairline（1px）、recessive、**solid 不虚线**、开口 L 形（去 top/right spine）。
- 数据占轴 ≥75%；y 范围贴近数据（都在 80-95 别用 0-100）。**log 轴绝不画实心柱**（柱长编码失真）。
- **反模式补充**：截断轴必须标注（broken axis 记号，不标=造假嫌疑）；饼图类别 >5 换 bar；stacked bar 读不出分组对比就换 grouped；heatmap 必须给 colorbar 且量程说明。

### 4. 图类型要点

- **line**：series ≤6（再多分面）；趋势图 x 轴必须是自变量（epoch/步数/规模），别用 run 编号。
- **bar**：组内顺序全文一致（baseline 顺序各图统一）；组间对比用 grouped，构成对比才 stacked。
- **scatter**：点重叠严重时 alpha/降采样/rug；两变量关系必须标轴单位。
- **heatmap**：行列顺序有意义（聚类或固有序），色阶量程贴数据。
- **violin/box**：分布图必须标样本量；seed 数少（<5）用散点条（strip）代替，别装分布。

### 5. 表结构与排版

**结构（设计决定，根据实际实验数据定）**：

- **行是什么**：一个 baseline？一个 setting？一个消融臂？——一张表行语义唯一。
- **列是什么**：metric 分组（多 metric 用 `\multicolumn` 分组表头）；设置列（数据集/规模）在左，结果列在右。
- **行排序**：baseline 按年代或性能排（全文统一一种）；**ours 固定位置**（通常末行加粗或与 baseline 区间 `\midrule` 隔开）。
- **分组**：消融表按消融臂分组（`\midrule` 分隔：完整模型 / -A / -B / …），读懂「每个组件贡献」。
- **宽表**：行远多于列（或反之）考虑 transpose——谁做行取决于读者要逐行读什么。
- **一表一核心对比**；塞太多列读不动 → 拆表或移附录。

**排版**：

- booktabs（`\toprule/\midrule/\bottomrule`，**无竖线**）。
- 列对齐（数字右/居中，文字左）；**精度一致**（同列小数位相同）、单位/百分比标清。
- **best / 2nd-best**：`**bold**` / `_underline_`。
- **±std 排法**：主数字正常字号，std 小号上标或括号小字（`{​\scriptsize ±0.2}`），不挤主数字。

### 6. 定性图（样本网格）

- **布局**：网格——行 = 样本，列 = 输入 / GT / ours / baselines（列含义在 caption 说清）。
- **裁切一致**：所有列同区域 crop、同分辨率；不单独美化某一列。
- **高亮标注**：差异区域用箭头/框，颜色用 palette 强调色；标注样式全文统一。
- **样本选择**：有讲究时（挑哪张展示效果好）候选摆给用户挑，不擅自定；**失败案例**（如有）同样真实呈现。

### 7. 标签经济

- **不每点标值**（标了也没人读）；只标 endpoint / extreme / the one（故事 series）。
- ≥2 series 才 legend；单 series 无 legend（title 即说明）。
- **文字用中性色，不用 series 色**：label / legend / 轴字一律中性色，只有数据 mark（点/线/柱）用 series 色（浅色 series 当文字会读不清）。label 塞不进 bar 内就移外面，别裁。
- 轴 tick 取整（0 / 1,000 / 2,000）、千分位。

### 8. paper 适配

- **venue 尺寸**：按 `venue-specs.md` 图尺寸节——双栏单栏图宽 ~3.3in / 跨栏 ~7.0in，单栏 ~5.0-5.5in；对应 spec 的 `size`。
- **字号按图的最终物理尺寸定**：按 venue 定图在论文里的**最终显示宽度**，字号设成在**那个物理尺寸下嵌入后 ≥8pt（双栏）/ ≥9pt（单栏）**——不是 authoring canvas 上看到的 pt 数。authoring 比最终大就等比换算（`final_pt = author_pt × 最终宽 / author 宽`）。层级靠相对大小保三档（标题/轴标题 > 图例/标注 > 刻度）。
- **灰度打印检查**：渲染成灰度看一遍——series 还分得开吗？分不开就线型/marker 双编码（区分度兜底；老派 reviewer 真打印）。
- **绘图库**：**seaborn 默认**（统计图全覆盖：bar/line/violin/box/heatmap/scatter/facet，底层 matplotlib、矢量输出同路径）；**matplotlib 兜底**（复杂多面板 / 手动标注 / 非标准图）。
- **绘图脚本当场写、放对位置、用 paper palette**：脚本写到 **`_draft/scripts/plot_<名>.py`**，不散落别处；**加载并使用锁定的 paper palette**，**不自挑色**；套 rcParams（`svg.fonttype=none` / `pdf.fonttype=42`）。**脚本从数据读数**（CPE 数据目录/数据文件路径参数化），数字不手敲；表格 `tables/<id>.tex` 同样脚本生成。
- **矢量输出**：脚本**必须导出 svg + pdf**（svg 可编辑源、pdf 给 `\includegraphics`）；**绝不用 png 截图插论文**（放大糊）。

## 自查 checklist

```markdown
## 数据类自查

- [ ] Step 0 根据实际实验数据定了 form（非 spec 给）；快稿预览用户确认过
- [ ] 数字脚本从数据生成（图 + tables/<id>.tex），无手敲
- [ ] 无造假（纯确定性代码；排除 run 不进汇总；定性样本真实未美化）
- [ ] 一个 claim 一个 canonical 值；不可比条件视觉区分；多 seed 报散布（无星号堆）
- [ ] 用 paper palette + 语义色按角色用；红绿双编码；无 rainbow/dual-axis/nominal value-ramp/>8 色
- [ ] mark 无装饰（无 3D/阴影/渐变/虚线网格；log 轴无实心柱；截断轴有标注）
- [ ] 图类型要点（series ≤6/顺序一致/样本量标注……）
- [ ] 表结构（行语义唯一/列分组/行排序/ours 位置/消融分组/宽表转置判断）+ booktabs 排版（对齐/精度/best-2nd/±std 排法）
- [ ] 定性图（列含义进 caption/裁切一致/高亮用强调色/样本选择给用户挑）
- [ ] 标签经济（不每点标值；文字用中性色）
- [ ] venue 尺寸 + 字号按最终物理尺寸（双栏 ≥8pt / 单栏 ≥9pt）+ 灰度可分 + 脚本放 `_draft/scripts/` + 用 palette + 导出 svg+pdf（无 png）
```

> 不是 railroad——给原则 + 规格，按原则判，只拦"造假 / 失真 / 编码错 / 装饰过载 / 标签泛滥 / 非矢量 / 手敲数字"。
