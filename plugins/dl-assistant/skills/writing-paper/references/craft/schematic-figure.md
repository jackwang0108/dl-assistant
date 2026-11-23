# Schematic Figure（示意图工艺：HTML+JS 绘制）

`writing-paper` 的**示意图工艺**——make-visual 产出示意图（teaser / pipeline / 架构 / 机制对比 / 概念 / 原理阐述）时读这个。

> **定位红线**：
> - **agent 产草稿，用户产终稿**：agent 用 HTML 画的永远是**草稿**——但它要做得足够好（内容对、布局清、标签精确、风格统一），因为在终稿替换之前它真实进正文编译（读者/协作者看到的就是它）。**终稿永远用户在 PPT 里照草稿重绘、导出 PDF**（finalize 时替换 `figures/<id>.pdf`）。
> - **生产路线只有一条：HTML + CSS + SVG 手绘**。不用 TikZ（没必要）、不用 mermaid（代码文档够用，论文要的精美度它给不了）、不用外部生图模型（已删除——文字必糊、修改靠抽卡，且 PPT 终稿原则抽掉了它的审美价值）。
> - 数据可视化不在这里——matplotlib/seaborn 脚本产，见 `numerical-display.md`。

## 技术形态

- **源**：`_draft/visuals/<id>.html`——自包含单文件（本地工作区，不推 Overleaf）。**产物**：`figures/<id>.pdf`（矢量，headless Chrome `--print-to-pdf` 产出，进正文）。
- **技术栈**：HTML + CSS + inline SVG 手绘为主（方框/箭头/标签/图标，手写 SVG 坐标布局）；布局真复杂才按需加 JS 库。资源引用自由（CDN 可用——环境联网，不强制内联）。
- **画布**：按布局原型定宽高（linear/teaser → 宽幅 16:9 或更宽；cyclic/central-hub → 方幅 1:1），HTML 里写死画布尺寸，渲染窗口对齐。
- **字号**：绝对 px，按最终嵌入栏宽换算（双栏 ~3.3in / 单栏 ~5.5in，见 `venue-specs.md` 图尺寸），**嵌入后 ≥8pt**。
- **风格基调**：flat 2D、clean outlines（~2px）、sans-serif、白底——顶会示意图的主流审美；具体风格由示例锚定（见下）校准。

## 图标三级来源

1. **Font Awesome**（免费集，直接拿 SVG）→ 2. **iconfont.cn**（搜索下载 SVG）→ 3. 都没有再**现场手绘 SVG**（简单几何图标）。

纪律：一张图内（最好全文）图标**同族同线宽**；用 CSS `fill` 统一换成 paper palette 色，不各带各的色。

## 真实样本资产（用户供图）

示意图里常要放**真实样本**（分割/检测任务的输入图、GT、模型预测 mask 等 png/jpg）：

- 用户手动供图，放 `_draft/visuals/assets/<id>/`，HTML 里 `<img>` 引用，渲染时一并进 PDF。
- **数据保真红线**：样本必须**真实**（真实数据 / 真实模型输出）——agent 不伪造、不生成、不美化样本内容本身；只做了了排版层处理（裁切 / 加边框 / 加标注箭头）。
- 样本选择有讲究时（挑哪张图展示效果好），候选摆给用户挑，不擅自定。

## 生产流程（make-visual 的示意图子步）

1. **示例锚定**：**先问用户**有没有风格/布局参考图（尊重用户偏好——有就用用户的）；没有 → paper-search 找 1~2 篇同 venue 同类型论文，优先用 `tex_open` 固定版本，再用 `tex_read` 或 `tex_get_object` 取原图路径，源码不可用时降级 pdf-mcp 渲染那张图来看。spec 里记参照来源 + 借鉴点（借布局/风格语言，**不抄内容**）。全文示意图共用一套风格语言，首张定的风格后续复用，不每张各找各的。
2. **写 HTML 草稿**：按布局原型（下节）排 zones + 连接 + 图标 + palette tint 填充；标签用论文实际术语（与 blueprint / notation.md 一致）。
3. **渲染预览**（两条路都给）：
   - agent：headless Chrome 渲 PNG → ReadMediaFile **自检**（结构对 / 箭头方向对 / 标签对 / 与正文引用句对齐）——先自己质检，别让用户做第一轮。
   - 用户：可直接浏览器 open `_draft/visuals/<id>.html`（能缩放，看得更真）。
4. **迭代循环（确认点：用户看预览图后确认）**：用户指哪不满意 → agent 改 HTML → 重渲染 → 直到满意。确定性修改，指哪改哪，没有抽卡。
5. **落地**：`--print-to-pdf` 产矢量 PDF → `figures/<id>.pdf` → 替换正文方框占位 → 本地验证 → manifest status=draft。
6. **终稿交接**（finalize）：用户照 HTML 草稿在 PPT 重绘 → 导出 PDF 替换 `figures/<id>.pdf` → manifest status=final。草稿里写清交接备注（哪些元素是占位表达、哪些细节终稿要补），落 `<id>.md`。

**渲染命令**（Chrome 路径用 `PUPPETEER_EXECUTABLE_PATH`，与 mmdc 同一个）：

```bash
# 预览 PNG
"$PUPPETEER_EXECUTABLE_PATH" --headless=new --screenshot=_draft/visuals/<id>.png \
  --window-size=<W>,<H> --hide-scrollbars "file://$PWD/_draft/visuals/<id>.html"
# 矢量 PDF（进 figures/）
"$PUPPETEER_EXECUTABLE_PATH" --headless=new --print-to-pdf=figures/<id>.pdf \
  --no-pdf-header-footer "file://$PWD/_draft/visuals/<id>.html"
```

## 布局原型（archetype）

按内容结构选：

- **linear pipeline**（左→右，数据处理 / encode-decode）→ 宽幅
- **cyclic / iterative**（RL / 优化 / 反馈环）→ 方幅
- **parallel dual-stream**（多模态融合 / 对比学习）→ 宽幅
- **central hub**（agent-环境 / 知识图谱）→ 方幅
- **teaser**（论文主图，5 秒 get 贡献：problem → method → finding 三段）→ 宽幅

## 文字纪律

- 图内标签 = **论文实际术语**（方法名 / module 名，与 blueprint、notation.md 一致），一个字母都不许错——文字即代码，100% 精确，这是 HTML 路线相对生图的核心优势。
- 标签精简：只放读者理解结构必需的文字，句子级解释归 caption，不堆进图里。

## 配色（paper palette + 语义色小套）

- **主体用 paper palette**：分区/系列填充用 palette 色相的**浅色 tint**（不另搞 pastel——palette 已锁定，另搞 pastel 跟它冲突），强调处用主色。HEX 写 CSS 变量，全文一致。
- **语义色小套**（palette 锁定时一并定，上色卡一起确认）：3~4 个固定语义色（如 success / warning / neutral-gray），**只用于语义角色**（正/负、升/降、对照或基线灰）——不许拿语义色当普通填充色用。
- **红绿双编码**：红绿配对在灰度打印下分不出——用红/绿表达正负时，必须同时用形状/符号/文字表达（不只靠颜色）。

## 自查 checklist

```markdown
## 示意图自查（落地前）

- [ ] 示例锚定做过了（用户给的参考 或 搜的同 venue 论文图，spec 记了借鉴点）
- [ ] 布局按 archetype；画布尺寸与渲染窗口对齐；嵌入后字号 ≥8pt
- [ ] 图内标签 = 论文术语，逐字母核过；无句子级文字堆图里
- [ ] 图标同族同线宽，fill 换 palette 色
- [ ] 真实样本是用户给的真图，未伪造未美化内容
- [ ] palette tint 填充 + 语义色只用于语义角色；红绿有双编码
- [ ] agent 渲 PNG 自检过了（结构/箭头/标签/引用句）才给用户审
- [ ] 用户看预览图后确认才落地；终稿交接备注写进 <id>.md
```

> 红线提醒：示意图里**绝不画/编实验数据**（数据图表走 `numerical-display.md`，绝不用生成式 AI）。
