---
name: writing-paper
description: "按用户当前需要撰写或修改论文，规划补充实验，将实测结果写入正文和图表，并检查、定稿与交接。通过论文进度记录、论文提纲和目标会议要求衔接八项操作。每项操作完成后，根据实际进度给出下一步建议，等用户确认。"
---

# Writing Paper

## 解决什么问题

研究方法和已有实验结果经 `code-idea-execution` 验证、用户与 `code-idea-iterate` 确认开始写作后，按目标会议要求把这些材料写成可投稿的论文。

根据当前需要选择操作，例如调整论文论证、重写一节、处理刚收到的实验数据或制作一张图。每完成一项，读取论文进度记录，向用户说明建议的下一步及理由，由用户确认后继续。

跑在**本地**，数据/代码在 GPU 服务器——需要时找用户弄到本地（不绑 ssh/scp，不管怎么传）。

**论文根 = `<方向根>/papers/<slug>/`（一个 Overleaf git clone）**：agent 通常在**方向工作目录根**运行；用户先在 Overleaf 从会议 author kit 建项目，把**项目官方 git 链接**（Overleaf 项目菜单提供）给 agent → agent clone 到方向根的 `papers/` 下（slug 默认 = Overleaf 项目名）。论文根按四级发现：① 用户显式指定 → ② CWD 本身是论文根（含主 tex + `_draft/`）→ ③ CWD `papers/` 下唯一候选 → ④ 多个或没有 → 问用户。**多篇论文并行 = `papers/` 下多个独立 clone**，工作区物理隔离。论文根是 git 仓库，agent 在里面 fetch/commit/push。写作循环**本地编译**（`latexmk`，本地验证高频走本地）；`overleaf-mcp` 只在**关键节点同步**时用（里程碑/用户要求/协作需要：push + 远端编译确认 + 渲染回归）。

## 边界

**做**：起手（目标会议要求 + 环境）→ 蓝图（随工作进展更新的文档）→ 实验规划（版本化批次）→ 逐节写/改（WYSIWYG）→ 图表产出（示意图/数据可视化）→ 将实验结果写入论文 → 写作质量检查 → 定稿交接。

**不做**（交给相邻 skill）：

| 场景                            | 用                                                                                                 |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| 跑论文级实验（产最终说明+报告） | `code-paper-experiment`（CPE 侧产最终说明+报告+增量写结果，是 CPE 的单独 effort，本 skill 只消费） |
| LaTeX 编译/渲染/产物            | 本地 `latexmk`/`pdftoppm`（写作循环默认）；`overleaf-mcp` 只在关键节点同步用（远端编译确认，by-name 引用）                    |
| 文献检索（当场取 bib 元数据）   | `paper-search` MCP（by-name 引用）                                                                 |
| 示意图终稿（PPT 重绘导出 PDF） | 用户（agent 用 HTML 产草稿并迭代到用户满意；终稿永远用户 PPT 画）                                  |
| 黑盒盲审                        | `writing-paper-review`                                                                             |
| rebuttal（产修改需求清单）      | `writing-paper-response`                                                                           |
| 投稿前终审 + authorkit 材料填写 | `writing-paper-submission`                                                                         |

## 在系统里的位置

```mermaid
flowchart LR
    IT["code-idea-iterate"] --> PKG[/论文准备材料 + claims.json/]
    PKG --> WP["writing-paper<br/>（本地·写作线）"]
    WP --> EPLAN[("实验计划包 plan vN<br/>_draft/experiments/")]
    EPLAN --> CPE["code-paper-experiment<br/>（GPU·实验线）"]
    CPE --> EDATA[("实验数据包 paper-data-pkg-vN<br/>（分批回）")]
    EDATA --> WP
    WP --> DRAFT[("论文草稿<br/>papers/ 下 Overleaf clone")]
    DRAFT --> OVL["本地编译 latexmk<br/>关键节点 overleaf-mcp 远端确认"]
    OVL --> PDF[/论文 PDF/]
    PDF --> WREV["writing-paper-review"]
    DRAFT --> WRESP["writing-paper-response"]
    WRESP --> REVLIST[("修改需求清单<br/>→ 待办项队列")]
    REVLIST --> WP
    WP --> VC[("目标会议要求<br/>_draft/venue-contract.md")]
    VC --> WPSUB["writing-paper-submission"]
    DRAFT --> WPSUB
```

### 机器角色（单 GPU 解耦）

| 机器                                 | 上面有啥                                    | writing-paper 怎么拿       |
| ------------------------------------ | ------------------------------------------- | -------------------------- |
| **本地**（论文根 = `papers/` 下的 Overleaf clone） | writing-paper 自己跑；产草稿 + PDF          | 直接                       |
| **GPU 服务器**                       | 论文准备材料 + claims.json + 中期 repo + 实验数据 | 找用户弄到本地（不绑传输） |

## 产出与保存

```
<方向根>/papers/<slug>/（论文根 = Overleaf git clone；根目录只有 LaTeX 该有的，干净）
├── <主 tex>.tex                # authorkit 主文件——名字随 kit（main.tex / egpaper_final.tex / <conf><year>.tex…），op-1 探明后记进 config.json；只做 \input，不堆正文
├── *.sty / *.cls / *.bst 等     # authorkit 自带（pre-existing，不动）
├── sections/*.tex              # 每节一个文件（死纪律：主 tex 不堆正文）
├── tables/<id>.tex             # 数据表单独成文件，正文 \input（脚本重生成只碰小文件）
├── figures/                    # 图输出（svg/pdf）——编译用；示意图终稿用户放这
├── refs.bib                    # bib（当场构造非正式条目；正式格式收尾用户修）
└── _draft/                     # 写作工作区（.gitignore，不推 Overleaf、不编译）
    ├── config.json             # 起手 config（材料/项目/会议/服务器路径）
    ├── paper-state.json        # 论文进度记录，结构见 templates/paper-state-template.json
    ├── venue-contract.md       # 目标会议的页限、匿名、强制章节及图表要求
    ├── venue-contract.json     # 契约的硬合规项机读子集（页限/匿名/引用风格/强制章节——检查脚本读它；形状指标不进）
    ├── blueprint.md            # 论文提纲，随论证变化更新
    ├── content/                # 各节 .md 源
    ├── experiments/            # plan-v1.md（人读）+ plan-v1.json（机读）/ v2…（版本化实验计划包）+ 收到的数据包
    ├── references.json         # 引用清单（cite_key + handle + role: core|supporting + claim + section + needs_human_verify）
    ├── visuals/                # 图表资产台账 manifest.json + 每个资产 <id>.md（spec）
    ├── scripts/                # plot_<名>.py（当场写）
    └── writing.log             # 会话日志（追加，续跑用）
```

文件组织约定

- **三份文件各有用途。** `paper-state.json` 记录章节、图表、实验批次、待办、页数和里程碑。`blueprint.md` 记录总论点、各项贡献和章节安排，并随论证调整。`venue-contract.md` 记录页限、匿名、强制章节和图表等要求。产物即真相，每项操作结束后更新进度记录。
- **文件切分纪律**：section 一文件、数据表一文件。由脚本/数据生成的内容单独成文件，手写的随正文——重生成不碰散文，协作冲突面最小。纯文字小表（符号表、两行对比）可内联。
- **布局以 kit 为准**：主 tex 文件名与目录结构以 op-1 探 authorkit 的结果为准（记进 config.json）；kit 有明确规定时按 kit 来，纪律给模板让路。authorkit 自带的填充 tex/pdf 本身就是 venue 的详细写作规范，op-1 读它并进 `venue-contract.md`。
- **视觉 spec（`_draft/visuals/`）不进正文**：figure 占位（方框+caption+label）/ 表骨架（booktabs，数字留 `--`）随正文本地验证落位；真图真数字由 make-visual / ingest-results 按台账替换。

## 核心纪律

1. **产物即真相，状态即真相**——`paper-state.json` 是论文工程的唯一机读真相源。任何目标干完立即更新；续跑读 state + writing.log 恢复，不靠记忆。
2. **必须等待用户确认的事项。** 提纲初稿及实质更新、每批实验计划、每节写作方案和 PDF、每节图表意图清单、每张图的预览、用实际结果替换占位、定稿时的每项压缩建议、可能改变原意的润色（meaning-risk），以及里程碑。
3. **编译通过后再继续。** 本地编译通过后才能提交。与 Overleaf 同步后，远程编译也必须通过。失败时先修复，再推进。报告失败时只引用日志末尾相关的错误摘要。
4. **协作同步纪律**——每次会话开始、每次 Overleaf 同步前 `git fetch` + 整合（rebase/merge）；push 被拒就 fetch→整合→push 循环重试；本地提交切小、push 集中在关键节点；**同一处冲突即停交用户**，只自动合并不重叠改动。Overleaf 网页端会自动 commit，协作方高频写时提醒用户错峰。
5. **里程碑快照**——用户认可的节点（初稿齐、将实验结果写入论文完、review 改完……）打 git tag + state 记里程碑。写论文反复改，回到上一轮好状态是刚需。
6. **页数与定稿删减。** 提纲记录会议页限和各节的参考分配，各节不用遵守固定页数预算。写作时先写完整，将可删减或移入附录的内容登记到 `compress_candidates`，每次本地验证都报告当前页数。到 finalize 再提出删减、移入附录或压缩表述的方案，由用户逐项确认。保留 teaser、流程图等核心图的尺寸及图内字号。
7. **开始时登记投稿要求。** 初始化时记录目标会议的页限、匿名要求、强制章节及图表规范，写作中据此核对。自动登记需要完成的待办，例如 limitations 节、ethics 声明、checklist 和匿名仓库。
8. **label/\ref 纪律**——节/图/表全带 `\label`，正文引用一律 `\ref`，禁止手写 "Figure 3" 式裸编号。落地检查、audit、submission 三层都查。
9. **由未参与起草的子 agent 检查正文。** 使用 general-purpose，禁用 Explore。
10. **数据图用真实数据和确定性代码绘制。** 用 seaborn 或 matplotlib 编写脚本，加载论文配色，导出 SVG 和 PDF。禁止用生成式 AI 制作数据图。
11. **给起草者提供必要材料。** 每节开始前，将该节指南的选择规则和自查清单、句段与字词写作要求及常见生成式写作问题、已写章节摘要和符号表直接提供给负责起草的 agent。
12. **TaskList 跟目标走**——每个确认的目标建/更新任务，进度可见；不起手建死一张全流程清单（目标是动态来的）。

## 前置材料和交接

- **iterate 论文准备材料 + claims.json**（从零写材料）：总论点 + 创新点清单 + 故事线骨架 + refuted/abandoned + Roadmap 终态 → init-setup 读入、design-story 消费。
- **修改需求清单**（改稿材料）：`writing-paper-response` 产或用户直接给，schema 见 `references/templates/revision-brief-template.json` → 进待办项队列，按类型路由到各目标（见运行模型）。
- **CPE 契约**：plan 版本化（`_draft/experiments/plan-vN.md` 人读 + `plan-vN.json` 机读——CPE 消费的单一读取源，schema 见 `references/templates/paper-experiment-plan-template.json`）；CPE 按批回**实验数据包**（`experiments-actual.json` + `results.json` + `pkg-meta.json`，schema 见 `code-paper-experiment/references/templates/data-pkg-schema.json`）→ ingest-results 按批回填。
- **review**：黑盒，只消费成品 PDF，不读本 skill 任何内部产物。
- **submission**：消费本 skill 产的 `venue-contract.md` + `_draft/config.json` + 成品 PDF；写作时约束已前移，submission 只查只能最后查的 + 填 authorkit 材料。

## 运行模型（目标驱动）

### 论文进度记录

`paper-state.json`（schema：`references/templates/paper-state-template.json`）跟踪：venue（含 deadline、页限）、blueprint_version、**每节状态**（planned/drafting/drafted/needs-data/needs-revision/locked + 页数参考与消耗 + 节摘要）、**数据依赖**（哪节/哪个 claim/哪张表在等哪个实验）、**实验批次**（plan vN 状态）、**待办项队列**、**压缩候选**（写作期登记的可砍/可挪内容，定稿时压缩篇幅用）、**里程碑**。图表资产台账在 `_draft/visuals/manifest.json`。

### 待办项队列（五个来源）

1. **蓝图初始化**——design-story 首次定稿，生成各节写作项 + 首图项。
2. **目标会议要求**——强制章节/声明/checklist/匿名仓库等需要完成的投稿要求，契约产出时自动注册。
3. **用户口述**——随时直接提，进队列。
4. **review/response 清单**——修改需求清单逐项进队列（re-frame → design-story；section重写/局部改 → write-section；补图表 → make-visual；补实验 → design-experiment → CPE → ingest-results）。
5. **数据到达**——一批 CPE 数据到，生成该批的 ingest 项 + 受影响的回填项。

### 目标菜单（八个目标）

| 目标              | 干什么                                                    | 手册                                       |
| ----------------- | --------------------------------------------------------- | ------------------------------------------ |
| init-setup        | 一次性起手：访谈、目标会议要求、Overleaf clone、`_draft/`   | `references/ops/op-1-init-setup.md`        |
| design-story      | 蓝图初建或重新确定提纲（随工作进展更新的文档；重新确定提纲自动生成受影响章节的修改任务）        | `references/ops/op-2-design-story.md`      |
| write-section     | 写/重写/局部改任意一节（提供已写章节的摘要 + 符号表）         | `references/ops/op-3-write-section.md`     |
| design-experiment | 规划或追加一批实验 → plan-vN 给 CPE                       | `references/ops/op-4-design-experiment.md` |
| ingest-results    | 消费一批 CPE 数据：写结果、产数据图、填表、同步更新数字       | `references/ops/op-5-ingest-results.md`    |
| make-visual       | 单个图表详细设计+产出（示意图 HTML；数据可视化脚本；预览图确认）     | `references/ops/op-6-make-visual.md`       |
| audit             | 写作质量检查：一致性/诚实性/润色 + 合规 + label/\ref + 读者测试 | `references/ops/op-7-audit.md`             |
| finalize          | 定稿：用户交付物替换、页数定稿、manifest、交接            | `references/ops/op-8-finalize.md`          |

### 建议机制

每完成一个目标（或每次会话开始），agent 读 state → 给出**带理由的下一步建议**，用户确认或自由输入别的目标。建议按状态推出，例如：「Method 改过，Intro 动机段可能脱节——建议 write-section intro」「plan-v2 的数据到了，实验节主表还空着——建议 ingest-results」「venue 要求 limitations 节，还没写——建议 write-section limitations」。

**deadline 感知**：state 记了 deadline 时，建议按 must/should/nice 加权；临近截稿主动给砍量方案（哪些挪 appendix、哪些 nice-to-have 放弃）。

```mermaid
flowchart TD
    START["会话开始 / 一个目标完成"] --> READ["读 paper-state.json<br/>+ writing.log"]
    READ --> SUGGEST["给出带理由的下一步建议<br/>（deadline 感知加权）"]
    SUGGEST --> PICK{"用户确认目标"}
    PICK --> EXEC["执行目标操作<br/>（读对应 ops/op-N 手册）"]
    EXEC --> UPDATE["更新 state + writing.log<br/>（产物即真相）"]
    UPDATE --> MILE{"到里程碑?"}
    MILE -->|是·用户认可| TAG["git tag + state 记里程碑"] --> SUGGEST
    MILE -->|否| SUGGEST
```

## references 文件列表

**`references/ops/`（八份操作手册——跑哪个目标读哪个）**：见上方目标菜单表。

**`references/sections/`（写哪个 section 读哪个，按角色分派）**：`blueprint-design`（蓝图 schema：人读叙事在前 + 节清单四步程序 + 随工作进展更新的文档规则）、`related-work-writing` / `introduction-writing` / `method-writing`（含符号体系构建）/ `abstract-writing` / `conclusion-writing`（五节指南，refs_v2 实证产物，自带全节自查 checklist）、`experiment-writing-setup` / `experiment-writing-results`（实验章两层：不依赖数据的实验信息 / 依赖数据的结果分析）、`appendix-writing`。这些是**角色指南**——非默认节（Background/Preliminaries 等）按蓝图角色标注借最近角色（见 op-3）。

**`references/craft/`（各节共用的写作和检查方法）**：`visual-design`（图表意图登记 + 示例锚定 + 分类路由 + palette/语义色）、`numerical-display`（数据可视化工艺）、`schematic-figure`（示意图 HTML+CSS+SVG 绘制工艺：图标三级来源/真实样本/预览迭代）、`bibtex-on-the-fly`（当场 bib + 引用 role）、`latex-landing`（论文根=papers/ 下 Overleaf clone + 本地编译验证 + 关键节点 Overleaf 同步 + 探模板 + label/\ref 纪律）、`section-self-audit`（写后自审 + 全文润色 子 agent 协议；audit fan-out 编排在 op-7）、`self-check`（audit 一致性 lens 清单——纯内容一致性）、`sentence-craft`（句段层）+ `word-craft`（字词层）+ `anti-ai-patterns`（AI 禁止模式）、`venue-specs`（官网入口 + 时区规范 + 图尺寸）、`visual-aesthetic-review`（渲染检查）。

**`references/templates/`**：`paper-state-template.json`（论文进度记录 schema）、`paper-experiment-plan-template.md`（实验计划包人读区）+ `.json`（机读 schema）、`revision-brief-template.json`（修改需求清单 schema）、`visuals-manifest-template.json`（图表资产台账 schema）。

**检查脚本**（`scripts/`，skill 预置的确定性检查）：`run_checks.py <论文根> all` 总入口——label/\ref + 裸编号、引用完整性（cite↔bib + references.json 登记与 section 一致性）、AI 腔 + 自我削弱表达硬正则、数字诚实 gate（canonical-values.json 白名单）、venue 硬合规（venue-contract.json）。audit（op-7）与 finalize（op-8）调用；有 FAIL exit 非零。

**绘图脚本**：agent 当场写（`_draft/scripts/plot_<名>.py`），skill 不预置绘图脚本。

## 常见错误

- 不要把目标菜单当线性流程走——顺序是建议不是规则；真实写作里重写 Method 后回改 Intro 是常态。
- 论证有实质变化时，用 design-story 更新提纲。write-section 发现此类变化时立即标「蓝图脱节」，并建议更新提纲。每次 audit 核对提纲与正文是否一致。
- 不要一次定死全部实验——plan v1 只装长周期必做项让 CPE 早跑；写作中冒出的实验需求记进 state，攒成 v2/v3。
- 不要等「最终数据包」——数据按批到、按批 ingest；没有「等全部跑完」这个状态。
- 起草每节前提供已写章节摘要、符号表和提纲。各节沿用一致的术语、符号和数字。
- 不要把 guideline 攒到最后查——目标会议要求起手就产，页数每次本地验证报，需要完成的投稿要求第一天就在队列里。
- 不要每节都 push Overleaf——写作循环走本地编译验证；Overleaf 同步只在关键节点（里程碑/用户要求/协作需要）。每节都 push 会把远端编译 log、同步噪音灌进上下文，agent 漂移。
- 不要各写各的色——palette 锁定后渲染色卡给用户看图确认，全部图用 palette 的 HEX。
- 不要防御性写作——局限一个不少（诚实性红线不动），但写成边界声明不写成道歉；优势满强度主张、摘要引言明说；故事以最有证据支持的贡献组织论证，证据不足以支持优势的维度不作为主要比较维度（语言层见 `word-craft` 原则 4，弱结果决策程序见 `experiment-writing-results`，锚定见 `blueprint-design`）。
- 不要手写 "Figure 3"——一律 `\ref`；节/图/表/公式全带 `\label`。
- 不要把正文堆进主 tex——主文件名随 authorkit（不一定是 main.tex），section 一文件、数据表一文件，主 tex 只做 `\input`。
- 本地编译通过后才提交或推送。同步时还须确认远程编译通过。
- 不要在协作冲突时硬解——同一处冲突即停交用户。
- 不要让 agent 用生图模型产图——示意图统一 HTML+CSS+SVG 手绘（文字精确、确定性迭代）；数据可视化只确定性代码（避免图表出现未经实测的数据）。

## 操作详情（八目标）

跑哪个目标读哪个手册；本表只给触发时机与确认点。

1. **init-setup**（一次性；改稿场景已有论文根则跳过 clone）：访谈收集材料 → 爬官网**日程与政策**产 `venue-contract.md` 初版（deadline 时区双写，确认点：换算说明）→ Overleaf 官方 git 链接 clone 到 `papers/` 下（确认点）→ 建 `_draft/` → **探 authorkit**（格式规范的权威来源：读自带填充 tex 的写作规范进契约定稿 + 主 tex 名记进 config + 注册合规待办项）→ 选题复盘（仅从零写）→ 初始化 `paper-state.json`。详见 `references/ops/op-1-init-setup.md`。
2. **design-story**（新建或更新提纲）。读取论文准备材料或现有正文，写出连贯论证、总论点和贡献清单，每项贡献注明关联的验证依据。按四步确定章节：列出论证任务、按三项判据决定是否独立成节、参照目标会议的模板及同类论文、确认章节安排。写明各节职责、参考页数和首图要传达的信息，逐项请用户确认。更新提纲时对比新旧内容，为受影响章节登记修改任务。详见 `references/ops/op-2-design-story.md`。
3. **write-section**（写/重写/局部改）：八子步循环——方案（确认点）→ 写 .md+bib → 子 agent 自审 → 初稿本地验证 → 交互改（确认点）→ 图表意图登记（确认点）→ 加轻占位 → final 本地验证。提供已写章节的摘要+符号表+页数参考+目标会议要求。定稿后更新节摘要进 state。详见 `references/ops/op-3-write-section.md`。
4. **design-experiment**（首批或追加）：按子论点和待验证维度安排实验，覆盖定性验证，检查有无遗漏或重复→ 标依赖拓扑（**配置未冻结主表不开跑**；decides_config 先行；无依赖并行）→ 独立查漏（reviewer 预演）→ 产 plan-vN（确认点：矩阵+依赖+成本逐项过；配置冻结另设确认点）。详见 `references/ops/op-4-design-experiment.md`。
5. **ingest-results**（一批数据到）：验收 → 按 CPE 实际对齐 → 写结果/分析 → 子 agent 自审 → 产数据图/填表 → 回填 Intro/Abstract 数字 → canonical 值核查 → 本地验证（确认点：用户确认图表中的实际结果准确）。详见 `references/ops/op-5-ingest-results.md`。
6. **make-visual**（单个资产：详细设计+产出）：示例锚定（问用户要参考图优先，没有搜同 venue 论文）→ 根据实际方法、数据和示例详细设计 → 示意图写 HTML 渲预览迭代 / 数据可视化写脚本出快稿 → **确认点：用户看预览图后确认** → 落地替换占位。示意图 agent 只产草稿，终稿用户 PPT 重绘。详见 `references/ops/op-6-make-visual.md`。
7. **audit**（可反复运行）。由未参与起草的子 agent 分别检查一致性、证据与表述是否相符、语言表达。另核对提纲与正文、投稿要求和 label/\ref，并做十分钟读者测试，只读标题、摘要、引言、Figure 1 和图表说明。可能改变原意的改动请用户确认。详见 `references/ops/op-7-audit.md`。
8. **finalize**（定稿）：锁内容（audit）+ 竣工 blueprint → 用户交付（示意图 PPT 终稿 + 正式 bib，确认点）→ 替换 + Overleaf 同步（远程编译通过）→ **定稿时压缩篇幅**（最终版面上一次到位：根据 priority 判断哪些图可移入附录，teaser 和流程图仍留在正文，逐项请用户确认）→ 全局版式回归（压缩后）→ 汇报 + 里程碑 + 交接包清点 → review/submission。详见 `references/ops/op-8-finalize.md`。
