# Visual Design（视觉规划/路由层）

`writing-paper` 的**视觉规划/路由层**。分两个时刻：

- **write-section ⑥（意图登记）**：文字定稿后，决定这节要不要图表、几张、每张回答什么问题——只登记**意图**，不做详细设计。
- **make-visual / ingest-results（详细设计 + 产出）**：对着真材料（定稿文字 / 真实数据）做详细设计并产出。审批物是**预览图**（用户看图拍板），不是文字 spec。

两大类图表共用入口；**怎么产**在两条工艺：示意图 `schematic-figure.md`（HTML 绘制），数据可视化 `numerical-display.md`（matplotlib/seaborn）。

## 图表分类（判断轴：内容来源）

- **示意图（schematic）**：内容从**设计意图**画出来的——概念、流程、模型架构、原理阐述、机制对比。不依赖实验数据，方法文字定了就能产。**agent HTML 产草稿，用户 PPT 产终稿**。
- **数据可视化（dataviz）**：内容从**数据**里长出来的——图或表。依赖真实数据（CPE 批次 / 已有数据），数据到了才设计结构、才填真。**绝不用生成式 AI**（造假红线）。

判据只看内容来源，不看长什么样：同样是「对比」，方法机制对比是示意图（画的是意图），baseline 数字对比是数据可视化（画的是数据）。

## 要不要画/表（write-section ⑥ 先决定）

不是每个 claim / 每个点都要图。先判断**文字够不够**：

- **不画**（行内文字 / 数字足够）：单一数字、几个 headline 数、简单到文字一句能说清的 claim、不服务任何 claim 的。
- **画**（文字讲不清 / 讲很费劲）：结构或空间关系、跨多数据点的趋势、密集对比（多 baseline × 多 metric）、内在可视的机制、一眼抓住的痛点直觉（teaser）。

丢弃的记一句理由（进 spec 文档，防以后反复纠结）。

## 意图登记（write-section ⑥，只定这些）

每张图表登记**意图字段**（进 `_draft/visuals/<id>.md` + manifest，status=intent）：

- `id` · `class`（schematic|dataviz）· `subtype` · `section`+`placement`（哪节、节内位置）· `claim_ref`
- **回答什么问题**：`key_takeaway`（几条要点、每条一句——设计锚 + caption 核心）· **为什么要这图**（没有它读者缺什么；一张图要有存在理由）· **正文引用句**（*As shown in Fig X, ...*——不引用的视觉丢掉）
- `caption` 初稿（三段式：What is shown. How to read it. Main takeaway.——不依赖数据，可先写）
- `priority`（must/should/appendix/drop）

**这里不锁的**：示意图的布局细节（zones/connections/图标）、数据图表的具体结构（图类型元素/表行列分组）——详细设计在产出时刻对着真材料做（见下）。

## 详细设计（make-visual / ingest-results，对着真材料）

### 示例锚定（每张图表设计时必做）

设计不凭空想——先找 1~2 个**真实参照**：

1. **先问用户**：有没有风格/布局参考图（尊重用户偏好——有就用用户的）。
2. 没有 → paper-search 找同 venue 同内容类型的论文，优先用 `tex_open` 固定版本，再以 `tex_read` 或 `tex_get_object` 取原图路径或表格源码，源码不可用时降级 pdf-mcp 渲染出那张图/表来看。
3. spec 里记**参照来源 + 借鉴点**（借布局/分组/视觉编码/风格语言，**不抄内容**）。

全文示意图共用一套风格语言——首张定的风格后续复用，不每张各找各的（否则风格打架看着业余）。

### 示意图：subtype → 布局原型

| subtype | 内容 | 布局原型（archetype） |
| --- | --- | --- |
| flow（流程/pipeline） | 数据流/控制流的先后与分支 | linear pipeline（宽幅） |
| architecture（模型架构） | 模块组成与连接关系 | linear / central-hub |
| comparison（机制对比） | 本方法 vs 已有方法的结构差异 | parallel dual-stream，差异点高亮 |
| concept（概念） | 抽象概念的关系示意 | 自由布局，视觉隐喻 |
| principle（原理阐述） | 机制为什么 work 的直觉图 | 自由布局 |

生产路线统一 **HTML+CSS+SVG 手绘**（工艺见 `schematic-figure.md`：图标三级来源 / 真实样本资产 / headless Chrome 渲染 / 预览迭代）。agent 产草稿，**终稿用户 PPT 重绘导出 PDF**（finalize 替换）。

### 数据可视化：抉择程序（对着真数据做）

1. **图还是表**（看数据密度/数量 + 读者任务）：
   - **表**：精确查值是主要任务；类别 >7；多 baseline × 多 metric 密集对比（画成图 series 会糊成一团）；要报精确数字（±std、CI）。
   - **图**：趋势/分布/跨 setting 对比是主要任务；读者要的是形状不是查值；定性样例。
2. **图 → 类型 + 元素**：类型按数据形态选——epoch/步数趋势 → line；类别对比 → bar；两变量关系 → scatter；矩阵/相关性 → heatmap；分布 → violin/box。元素逐个定：轴（量程贴数据，数据占轴 ≥75%）、图例（≥2 series 才要）、误差棒（多 seed 必有，标清 seed 数）、标注（只标 endpoint/extreme/the one，不每点标值）。mark/用色规格见 `numerical-display.md`。
3. **表 → 结构**：几行几列、表头每列含义、每行是什么（一个 baseline？一个 setting？一个 ablation 臂？）、best/second 标记规则（bold/underline）。**表结构对着真实数据定**（数据到达的 ingest-results 时，或数据本就在手时）——不对着想象中的数据锁结构。

## 原则（设计判据）

### 1. 每张图表服务一个 claim
不服务任何 claim（C-ID）的图表 → 移 appendix 或 drop。没有证据的维度不强说。

### 2. 先定 class/subtype/form 再画
form 由**信息目的**定，不是先想「画个图」：概念/机制/结构 → 示意图；精确数字/真实结果 → 数据可视化（再走抉择程序定图/表）。

### 3. caption 三段式（self-contained）
`What is shown. How to read it. Main takeaway.`（不读正文也懂）。

### 4. 数据保真（数据可视化的地基）
一个 claim 一个 canonical 值（全文/图表/abstract 一致）；排除的 run 不进汇总（或 open/hatched marker 点名）；不可比条件视觉区分；**绝不画/编数据**。

## 占位规则（意图登记之后、产出之前）

意图登记后正文落**轻占位**，真图真结构由 make-visual / ingest-results 替换：

- **figure 占位**：通用方框 + caption 初稿（三段式）+ `\label{fig:<id>}`。
- **table 占位**：只落注释占位（`% TODO: tab-<id> 结构待数据到达后定`）+ caption 初稿 + `\label{tab:<id>}`——**不锁 booktabs 结构**（结构对着真数据定）。例外：数据本就在手（改稿/数据先行），可直接定结构落骨架。
- 占位不阻塞编译，汇报里标出；转译、编译纪律详见 `latex-landing.md`。

## 图表资产台账 manifest（`_draft/visuals/manifest.json`）

每个图表资产一条，schema 见 `references/templates/visuals-manifest-template.json`。关键字段语义：

- `id` / `label`：id 是资产名（fig-1 / tab-1），label 是 LaTeX label（`fig:<id>` / `tab:<id>`）——占位和 `\ref` 都用它。
- `class` / `subtype` / `production`：分类路由结论；`production`：schematic=`html`，dataviz=`matplotlib`。
- `status`：**intent**（意图登记+占位，write-section）→ **designed**（详细设计+预览图，用户看图拍板）→ **draft**（落地正文：占位替换/填真完成）→ **final**（终稿替换，finalize——示意图用户 PPT 终稿）。
- `spec` / `section` / `data_ref` / `version`：spec 路径、归属节、数据来源（dataviz 用）、改动版本号。

维护分工：write-section 注册条目（intent+占位）；make-visual / ingest-results 详细设计（designed）+ 落地（draft）；finalize 置 final。`paper-state.json` 只管节状态与 palette 锁，图表粒度状态全在 manifest。

## paper palette + 语义色（产出任何图之前先锁定一次）

配色是**项目级、一次性**决定——任何图（示意图 + 数据可视化）产出前先锁定，全文复用。不能每张图临时选（不统一）。

- **流程**：agent 从配色网站（[colorhunt.co](https://colorhunt.co) / [coolors.co/palettes/trending](https://coolors.co/palettes/trending)）挑 2~3 个候选，或用户直接给定 → **渲染色卡图**（每色一个色块 + 角色 + hex，落 `_draft/visuals/palette.png`；**附灰度版一行**）给用户**看图**确认——hex 不直观，只报一串 hex 让用户脑补等于没确认。用户按两件事拍板：**好不好看**（审美，主观，用户说了算）+ **区分度够不够**（相邻色/series 之间分得开吗——灰度版是客观兜底：灰度下糊成一团的，区分度不够，换或加线型/marker 双编码）。确认点：用户看图拍板才锁，state 记 `palette.locked` + swatch 路径。
- **语义色小套**：palette 主色之外，锁定时一并定 **3~4 个固定语义色**（如 success / warning / neutral-gray），也上色卡一起确认。使用纪律：语义色**只用于语义角色**（正/负、升/降、对照或基线灰），不许当普通填充色；系列与分区填充仍用 palette 主色。**红绿双编码**：用红/绿表正负时必须同时用形状/符号/文字表达——灰度打印下单靠红绿分不出（老派 reviewer 真打印）。
- **使用纪律**：锁后全部图用 palette HEX + 语义色套，不许各写各的色。数据可视化按编码类型用（categorical/sequential/diverging/emphasis + 禁项，见 `numerical-display.md` 原则 2）；示意图填充用 palette 色相的浅色 tint（见 `schematic-figure.md`）。
- palette 锁定后改动 = 全文图返工——锁之前把确认做扎实。

## 输出

```markdown
# 视觉意图清单（某节，write-section ⑥ 产）
## 每张图表 | id | class | subtype | 放哪 | 回答什么问题（key takeaway 几条）| claim_ref | priority
## 每张的 spec 文档（意图字段）+ manifest 条目（status=intent）
## 删除/合并建议（不服务 claim 的 → appendix/drop，记理由）
# 详细设计字段（zones/encoding/structure/exemplar 参照）→ 产出时刻补进同一 spec 文档
```
