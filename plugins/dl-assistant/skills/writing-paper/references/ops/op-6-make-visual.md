# 目标 6：make-visual（单个图表：详细设计 + 产出）

## 何时用

把 manifest 里 status=intent 的某个条目产出来。工作单元是**单个图表资产**，不是批量阶段——哪张的输入齐了就做哪张（示意图：方法文字定了就能做；数据可视化：对应数据批到了、或数据本就在手就能做）。

**与 write-section ⑥ 的分工**：⑥ 只登记意图（要不要、几张、回答什么问题）；本操作做**详细设计 + 产出**——对着真材料（定稿文字 / 真实数据）一次设计准。审批物是**预览图**（用户看图拍板），不是文字 spec。

## 读哪些

- `_draft/visuals/manifest.json` + 目标 `<id>.md`（意图字段）。
- `references/craft/visual-design.md`（分类路由 + 示例锚定 + palette + 抉择程序）。
- 示意图：`references/craft/schematic-figure.md`（HTML 工艺：图标三级来源 / 真实样本资产 / 渲染 / 迭代）。
- 数据可视化：`references/craft/numerical-display.md`。

## 示意图子步（HTML 路线）

1. **示例锚定**：**先问用户**有没有风格/布局参考图（有就用用户的，尊重偏好）；没有 → paper-search 找 1~2 篇同 venue 同类型论文，优先用 `tex_open` 固定版本，再用 `tex_read` 或 `tex_get_object` 取原图路径，源码不可用时降级 pdf-mcp 渲染那张图来看。参照来源 + 借鉴点记进 `<id>.md`。全文首张定的风格语言后续复用。
2. **详细设计**：对着定稿的方法文字定布局（archetype / zones / 连接 / 图标 / 真实样本资产需求），补进 `<id>.md`。需要用户供真实样本（png/jpg）的，告诉用户放 `_draft/visuals/assets/<id>/`。
3. **写 HTML 草稿**：`_draft/visuals/<id>.html`（工艺见 `schematic-figure.md`——palette tint、标签=论文术语、图标同族、字号嵌入后 ≥8pt）。
4. **渲染自检**：headless Chrome 渲 PNG → ReadMediaFile 自检（结构/箭头/标签/与正文引用句对齐）。先自己质检，别让用户做第一轮。
5. **确认点：用户看图拍板**：用户看 PNG 或直接浏览器 open HTML → 指哪不满意改哪（改 HTML 重渲，确定性修改）→ 直到满意。满意即 manifest status=designed。
6. **落地**：`--print-to-pdf` 产矢量 PDF → `figures/<id>.pdf` → 替换正文方框占位 → 本地验证 → manifest status=draft + 写终稿交接备注（哪些元素是占位表达、终稿要补什么，finalize 用户 PPT 重绘用）。

## 数据可视化子步

1. **示例锚定**：同示意图（问用户 → 搜同 venue 论文的同类图/表）。
2. **详细设计（对着真数据）**：走抉择程序定图/表；图 → 类型 + 元素；表 → 结构（几行几列/表头含义/每行含义/best-second 标记）。补进 `<id>.md`。
3. **快稿预览（确认点：用户看图拍板）**：当场写 `_draft/scripts/plot_<名>.py`（seaborn 默认 / matplotlib 兜底，加载 paper palette）出**快稿**→ 渲 PNG 给用户看 → 不满意改脚本重渲 → 满意即 manifest status=designed。**数据图绝不用生成式 AI**（造假红线）。
4. **落地**：正式产图（svg+pdf 落 `figures/`）/ 表落 `tables/<id>.tex`（正文 `\input`）→ `numerical-display.md` 自查（数据保真 / 编码类型 / mark 规范 / 可读）+ 引用句对齐 → 占位替换 → 本地验证 → manifest status=draft。

## palette 锁定（本操作首次需要真色时）

palette 未锁时先锁：按 `visual-design.md` 选定（agent 从配色网站挑候选或用户给定）+ **语义色小套**（3~4 个固定语义色）→ **渲染色卡图**（色块 + 角色 + hex + **灰度版**，落 `_draft/visuals/palette.png`）给用户看图确认（好不好看 + 区分度够不够，灰度兜底）→ 确认才锁。hex 不直观，色卡是给用户看的，不许只报一串 hex 让用户脑补。

## 产出

示意图：`_draft/visuals/<id>.html` + `figures/<id>.pdf`（草稿）+ 终稿交接备注。数据可视化：`_draft/scripts/plot_<名>.py` + `figures/`（svg+pdf）或 `tables/<id>.tex`。两者：`<id>.md` 详细设计字段 + manifest status 更新。

## 状态更新

manifest 条目 status（intent→designed→draft）；state 的 palette.locked；backlog 关单。

## 确认点

每张：示例锚定（用户给参考 或 认可搜来的参照）/ 看图拍板（示意图 HTML 渲染图；数据图快稿）。palette：色卡确认（含语义色）。

## 易错点

- **详细设计对着真材料**——示意图对定稿文字，数据图表对真实数据；不对着想象中的内容锁结构。
- **审批物是预览图，不是文字 spec**——用户看图拍板才算数；文字 spec（`<id>.md`）是设计记录。
- **agent 先自检再交用户**——渲 PNG 自查结构/标签/引用句，别让用户做第一轮质检。
- **示意图 agent 只产草稿**——终稿永远用户 PPT 重绘导出 PDF（finalize 替换）；草稿也要做好（它先进正文）。
- **真实样本必须用户供真图**——不伪造、不生成、不美化样本内容（数据保真红线）。
- **数据图绝不用生成式 AI**——只确定性代码。
- **示例锚定先问用户**——用户有参考图就用用户的，别直接去搜。
