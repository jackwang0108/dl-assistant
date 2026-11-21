---
name: dl-assistant
description: dl-assistant 科研 skill 系统的总览与全局地图——全局 skill 流向图（谁调谁、交接什么文件）+ 三阶段划分 + 跨机器模型。想搞清楚系统怎么连、找该用哪个 skill、或看某个 skill 的前后交接时读这个；其他 skill 按名引用本文档看全局图。
---

# DL Assistant 系统总览

## 核心定位

这是 dl-assistant 科研 skill 系统的**总览与全局地图**——一份参考文档，不做路由、不执行具体工作。它讲三件事：

1. **全局 skill 流向图**：系统有哪些 skill、按什么顺序串、之间交接什么文件（见下节）。
2. **三阶段划分**：前期输入 / 中期 coding / 后期产出。
3. **跨机器模型**：产物落哪、怎么协作（见「全局目录布局与跨机器同步」）。

**什么时候读它**：想搞清楚系统怎么连、某个 skill 的前后交接是什么、或想找该用哪个 skill 时。**其他 skill 在自己的局部依赖图里只画相邻 skill，要看全局就按名引用本文档。**

## 核心设计哲学

**人在回路。** 科研里真正稀缺的是判断——做什么方向、信不信这个结果、故事怎么讲，这些只能由人做。agent 的价值不是替代人判断，而是**放大人的信息处理带宽**：搜得更全、读得更快、跑得更勤，把每个问题快速推进到「人可以下判断的临界点」，然后停下来等人。所以每个 skill 都设确认点、停顿点和「升级给用户」的出口；产物分人读（报告）与机读（yaml）两层，人读那层就是供人下判断的。

**产物即真相。** 判断「进行到哪一步」的唯一依据是磁盘上的真实产物——它们不会过期、不会和实现脱节。一切关键结论必须落盘：**可审计**（数字来自真实 run，能追回命令与配置）、**可回溯**（git tag + 版本树锚定每个成功节点）、**可追踪**（产物交接靠显式契约，不靠记忆）。会话可以断、机器可以换，只要产物在，上下文就能重建。

## 横切规范（所有 skill 共用，单一出处在本节）

各 skill 正文**不复述**以下规则，只留一行指针（"横切规范见 `dl-assistant` SKILL.md「横切规范」"）；局部有特殊扩充（如某 skill 额外的记法）可在本地保留增量。

- **符号约定**：会话里给用户看的公式/符号用 Unicode（σ、λ、≥、×10⁻³），写进落盘 markdown 才用 LaTeX。
- **论文标识**：落盘文件和给用户的内容里，论文用 arXiv ID / DOI / URL 标识，并注明已核版本。paper-search v2 调用也使用稳定外部标识，跨机器交接用导出的来源和结果。
- **跨机器交接**：skill 只声明「需要哪个文件」，不规定怎么传——文件不在找用户要，不绑传输工具（详见「全局目录布局与跨机器同步」）。

## 科研三阶段全景

DL Assistant 把一个科研项目划分为三阶段，每阶段对应一组 skill：

| 阶段               | 干什么                                          | skills                                                                                                                          |
| ------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **前期（输入）**   | 找方向 / 读论文 / 调研 / 想 idea                | arxiv-daily-paper、hf-trending-papers、direction-tracking、paper-reading、literature-survey、idea-find、baseline-survey                             |
| **中期（coding）** | 搭环境 / 复现 / idea迭代                        | code-project-setup、code-paper-reproduction、code-idea-prepare、code-reading、code-idea-execution、code-idea-iterate            |
| **后期（产出）**   | 写论文 / 做实验 / 审稿 / 回应 / 投稿 / 代码发布 | writing-paper、writing-paper-review、writing-paper-response、writing-paper-submission、code-paper-experiment、code-paper-release |

通常前期在本地机器、中期在 GPU 机器、后期写作线在本地 + 实验线在 GPU 机器；各 skill 产各自的产物，靠下方「全局目录布局与跨机器同步」做跨机器协作。

## 配套 skill

dl-assistant 提供了几个 MCP 配套的 skill，可以在任意阶段**横切使用**——任何阶段按需调用、不在顺序链上：

| skill              | MCP server       | 干什么                                            |
| ------------------ | ---------------- | ------------------------------------------------- |
| [paper-search](../paper-search/SKILL.md) | paper-search-mcp | 论文检索（搜索 / 详情 / 引用追踪 / 作者·机构）    |
| [tex-mcp](../tex-mcp/SKILL.md) | tex-mcp          | 读 arXiv 论文源码（章节正文 / 图 / 表 / 参考文献）——**arXiv 论文内容读取的首选通道**，用 `tex_open` 打开固定版本，源码不可用时用 pdf-mcp |
| [pdf-mcp](../pdf-mcp/SKILL.md) | pdf-mcp          | PDF 文件操作（提取文字·图片 / 搜索 / 渲染页面）——本地/成品 PDF 专用 + tex-mcp 的兜底 |
| [overleaf-mcp](../overleaf-mcp/SKILL.md) | overleaf-mcp     | 绑定本地 Git 仓库、远端编译、查日志与 PDF。正文编辑和同步走 Git CLI。 |

- [W&B](../wandb/SKILL.md) 提供可选的实验记录和查询支持。
- [research-presentation](../research-presentation/SKILL.md) 用于制作汇报幻灯片。

上表的操作按各 MCP v2 说明执行。TeX 和 PDF 打开后以返回的 `document_id` 继续读，Overleaf 用同一轮的 `compile_id` 查日志和产物。

## 全局 skill 流向图（skill 间顺序依赖）

科研主线的 skill 按顺序调用、串成一条链，关键交接物标在边上。**每个 skill 自己的局部依赖图只画相邻 skill；要看全局怎么连，回这张图（本文档）。**

```mermaid
flowchart LR
    subgraph PRE["前期 · 输入（本地）"]
        direction TB
        AD[arxiv-daily-paper]
        HF[hf-trending-papers]
        DT[direction-tracking]
        PR[paper-reading]
        LS[literature-survey]
        IF["idea-find"]
        BS[baseline-survey]
    end
    subgraph MID["中期 · coding（GPU 服务器）"]
        direction TB
        CPS[code-project-setup]
        CPR[code-paper-reproduction]
        CIP[code-idea-prepare]
        EX["code-idea-execution"]
        IT[code-idea-iterate]
        CR[code-reading]
    end
    subgraph POSTW["后期 · 写作线（本地）"]
        direction TB
        WP["writing-paper"]
        WPR[writing-paper-review]
        WRESP[writing-paper-response]
        WPS[writing-paper-submission]
    end
    subgraph POSTE["后期 · 实验线（GPU 服务器）"]
        direction TB
        CPE[code-paper-experiment]
        REL[code-paper-release]
    end

    DOCS[("文献调研·baseline 选型")]
    PKG[("收口包+repo")]
    EPLAN[("实验计划包")]
    EDATA[("实验数据包")]
    PDF[/论文 PDF/]
    REPO[/release repo/]

    AD -.->|follow 文章| IF
    HF -.->|follow 文章| IF
    PR -.->|精读笔记| IF
    LS -.->|领域地图| IF
    DT -.->|累积库| IF
    IF -->|spec 草稿（baseline/基座线索 + idea 形态）| BS
    IF -.->|spec+plan+claim 树种子| EX
    BS --> DOCS
    DOCS --> CPS
    CPS -->|setup report| CPR
    CPS -.->|setup.json| CR
    CPR -->|reproduction report| CIP
    CIP -->|prepared baseline repo| CR
    CR -->|读懂 baseline 再动手| EX
    CPR -.->|分诊跳过 CIP（记录理由）| CR
    EX -->|conclusion + claims裁决| IT
    IT -->|出口A 继续迭代: spec+plan+claims| EX
    IT -->|出口B 收口| PKG

    PKG --> WP
    PKG --> CPE

    WP -->|论文成品 PDF| WPR
    WPR -->|审稿意见| WRESP
    WRESP -->|修改决定| WP
    WRESP -->|定稿| WPS
    WPS --> PDF

    WP --> EPLAN
    EPLAN --> CPE
    CPE --> EDATA
    EDATA --> WP

    CPE --> REL
    REL --> REPO
```

- **方框** = skill；**圆柱体** = 跨阶段/子图交接的内容（DOCS / PKG / 实验计划包 / 实验数据包）；**平行四边形** = 最终外部成品（PDF 投稿 / REPO 发行，用户拿走）；**边标签** = 子图内部交接（论文成品 PDF，写作线内）。
- **实线** = 主线必经；**虚线** = 可选前置输入。
- **改交接必同步三张图**：增删/改任何一条交接，本图 + 两端 skill 各自的局部图一起改，别只改一处。
- 中期 `execution ⇄ iterate` 循环（出口A 继续迭代）；iterate 收口（出口B）产 PKG（收口包+repo）同时喂写作线 + 实验线——**execution 不直连后期，必须经 iterate 收口**。
- 中期主线 `CPS → CPR → CIP → CR → EX`：**code-reading 是主线必经**——动 idea 之前先带人把 baseline 代码读懂（理解是人的活，agent 不能替代，见「核心设计哲学」）。
- BS 选型分两种 repo 角色：**对打 baseline**（前驱改进型 idea，有直接前驱 repo）/ **实验基座**（组合 insight、分析先行型 idea，无直接前驱 repo，v1 是假设裁决的分析实验）；基座模式下 CPR 的对齐目标是基座自报参考数字（验"测量仪器可信"），不是某篇论文的表格行。
- 中期 `CPR → CIP → CR` 是主线默认，但 **CIP 非必经**：CPR 交棒时先分诊（repo 规模 / 死代码·ablation 残留密度 / idea 改动范围 / 预期迭代版本数），干净小 repo + 局部改动可**记录理由后**走虚线旁路直连 CR（code-reading 仍必经）。分诊标准见 `code-paper-reproduction` SKILL.md「下游交接」。
- 后期 `writing-paper → review → response → writing-paper`（改论文）来回箭头。
- 后期两条并行线：**写作线（本地）** + **实验线（GPU 服务器）**，靠 实验计划包（WP→CPE）/ 实验数据包（CPE→WP）两个圆柱体双向同步。
- **前期文献库不进写作线**：literature-survey / paper-reading 的产出服务对象是**人**（理解领域、判断价值），是覆盖度导向的领域地图；写作的参考文献是论证导向的（idea 直接基于的核心几篇 + 围绕对照线按论证需要现场组织）——所以前期子图（PRE）与写作线（POSTW）之间没有边，这是刻意的，防止拿覆盖度导向的库喂论证导向的写作。

## 全局目录布局与跨机器同步

这套 skill 把机器分成**两类**（各自数量不限、不关心具体几台、什么拓扑）：

- **本地机器**：干**文档类**的活——文献调研、读论文、想 idea、写论文、审稿回应，不需要 GPU。目录放 `docs/`（前期产出）+ `papers/`（后期产出：每篇论文一个 Overleaf git clone，见下）。
- **GPU 机器**：**跑实验**——搭环境、复现、idea 实现 / 迭代、跑论文实验、抽 release。装 baseline repo（源码结构随 baseline），我们在里面**新建** `docs/`（前期 docs + 中期报告）和 `ideas/`（版本树、runs/、conclusion），再加 release 新仓库。

> **运行位置假设**：这套 skill 假设 agent 在**项目根目录**下被启动——本地机器站在本地项目根（= 方向工作目录根）、GPU 机器站在 GPU 项目根（即下面树里的 `<项目>/`），所有 `docs/`、`ideas/`、`papers/` 都相对这个根。**如果 agent 发现当前目录不像项目根（没有 `docs/` 之类），别猜，先问用户项目根在哪。**

两类机器上的标准目录布局：

```
本地机器：
<项目>/
└── docs/                      # 人会回看的交接文档（前期产出 + 后期 skill 独立使用产物）
    ├── arxiv-daily/           # arxiv-daily-paper：每日简报（按日期）
    ├── hf-radar/              # hf-trending-papers：雷达快照（按时间窗）
    ├── direction-tracking/    # direction-tracking：track-<slug>/ 累积库（常驻，增量更新）
    ├── paper-reading/         # paper-reading：精读笔记（一篇论文一个文件夹）
    ├── literature-survey/     # literature-survey：调研报告（report + survey.json + reading-list + 谱系树）
    ├── idea-find/             # idea-find：idea 文件夹（spec 草稿 + plan + claim 树种子）
    ├── baseline-survey/       # baseline-survey：选型报告（baseline-survey.json + report.md + facts/）
    └── writing-paper-review/  # writing-paper-review 独立使用（审外部 PDF）：<slug>/round-N/ 审稿产物

<项目>/papers/    # 后期产出统一入口：每篇论文一个 Overleaf git clone（slug 默认 = Overleaf 项目名）；多篇并行 = 多个 clone，物理隔离
└── <slug>/       # = 论文根（后期 skill 发现它：用户指定 > CWD 本身是 > papers/ 唯一候选 > 问用户）
    ├── <主 tex>.tex / sections/ / tables/ / figures/ / refs.bib   # LaTeX 该有的（Overleaf 看到的；主 tex 只做 \input，名字随 authorkit）
    └── _draft/     # writing-paper 工作区（.gitignore，不推 Overleaf）：状态骨干 paper-state.json、venue 契约、活蓝图 blueprint.md、内容源 content/、图表台账 visuals/、写作日志
```

> 注意：`papers/` 里是嵌套 git repo——方向目录本身也是 git repo 时，把 `papers/` 加进方向目录的 `.gitignore`，避免父 repo 把嵌套 clone 当 submodule 噪音。

```
GPU 机器：
<项目>/           # = baseline repo（baseline 自己的源码结构，不动）
├── docs/        # 新建：前期 docs（拿过来）+ 中期报告
│   ├── code-project-setup/        # setup 报告（setup.json + setup-report.md）
│   ├── code-paper-reproduction/   # reproduction 报告（reproduction.json + report.md）
│   ├── code-idea-prepare/         # cleanup 报告（cleanup.json + cleanup-report.md + coverage/）
│   └── code-reading/              # 诊断脚本 + 阅读笔记（主线必经，含接入点地图）
├── ideas/       # 新建：execution 版本树 —— idea_tree.json、各版本目录（spec/plan/conclusion）、runs/
└── [baseline 自己的源码 …]

<独立位置>/       # code-paper-release 产出：独立新仓库（history 归零）
```

```mermaid
flowchart LR
    subgraph LOCAL["本地机器（文档操作为主，不需 GPU）"]
        direction TB
        LDOCS["docs/ — 前期产出（调研、选型、idea）"]
        LPAPER["papers/＜slug＞/ — writing-paper 产出（Overleaf git clone）"]
    end
    subgraph GPU["GPU 机器（跑实验）"]
        direction TB
        GREPO["baseline repo — 源码随 baseline（idea 实现 / 实验在这跑）"]
        GDOCS["docs/（新建）— 前期 docs + 中期报告"]
        GIDEAS["ideas/（新建）— 版本树、runs/、conclusion"]
        GREL["release 新仓库（独立）"]
    end

    LOCAL -->|"前期 docs（中期读）"| GPU
    GPU -->|"中期报告 / 实验数据 / 结论（写作线读）"| LOCAL
    LOCAL -->|"补实验 spec（实验线跑）"| GPU
```

GPU 机器上的 `docs/` 和 `ideas/` 是在 **baseline repo 里新建**的目录——baseline 自己的源码结构（叫 `src/` 还是别的）不动，我们只在它上面加这俩目录装自己的产物。

**跨机器文件交接**：两类机器之间要来回交接文件（前期 docs → GPU、中期报告 / 实验数据 / 结论 → 本地、补实验 spec → GPU）。原则是——**skill 只声明「需要哪个文件」，不规定怎么传**：到了需要跨机器文件的节点，skill 直接找用户要（"给我 setup report"、"把补实验 spec 弄到 GPU 机器上"），用户爱用 scp、FileZilla、手动拷都行，skill 只认文件到位。所以图里的箭头只标「什么文件、谁要用」，不标传输工具。

> **没有状态文件这回事。** 判断"进行到哪一步"靠的是**按需扫描真实的产物文件**（idea 树、各种报告、论文 manifest）——产物即真相（见「核心设计哲学」），不维护任何 `PROJECT_STATE` 之类的中枢。跨机器也无需带状态文件：每个 skill 都读自己的产物自恢复上下文，靠本节定义的协作机制把产物送到该在的机器上。

> **归位判据（产物放哪个目录）**：人会回看的交接文档 → `docs/`；只给下游 skill 按需取的高频底料（版本树、runs/）→ `ideas/`；后期成品（论文 / 发行版）→ 各自独立地盘（`papers/<slug>/` Overleaf clone、release 新仓库）。`ideas/` 是中期 execution / iterate 自治维护的版本树——前期产物、setup/reproduction/cleanup 报告、论文产物都**不进 `ideas/`**（各进 `docs/`、`papers/` 等自己的地盘）。
