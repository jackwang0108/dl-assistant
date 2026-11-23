---
name: dl-assistant
description: 当调用 dl-assistant 科研助手中的任意一个 skill 时触发。dl-assistant 科研 skill 系统的总览与全局地图——全局 skill 流向图（谁调谁、交接什么文件）+ 三阶段划分 + 跨机器模型。想搞清楚系统怎么连、找该用哪个 skill、或看某个 skill 的前后交接时读这个；其他 skill 按名引用本文档看全局图。
---

# DL Assistant 系统总览

## 核心定位

这是 dl-assistant 科研 skill 系统的**总览与全局地图**——一份参考文档，不做路由、不执行具体工作。它讲三件事：

1. **全局 skill 流向图**：系统有哪些 skill、按什么顺序串、之间交接什么文件（见下节）。
2. **三阶段划分**：前期输入 / 中期 coding / 后期产出。
3. **跨机器模型**：产物落哪、怎么协作（见「全局目录布局与跨机器同步」）。

**什么时候读它**：想搞清楚系统怎么连、某个 skill 的前后交接是什么、或想找该用哪个 skill 时。**其他 skill 在自己的局部依赖图里只画相邻 skill，要看全局就按名引用本文档。**

## 共同研究流程

**提出假设 → 设计实验 → 收集数据 → 分析并修订假设 → 提出下一步假设。**

每轮明确「原来相信什么、实际观察到什么、因此改变了什么判断」。`idea-find` 形成首轮研究问题、假设和取证计划，`code-idea-execution` 按计划取得证据并记录实际条件与偏差，`code-idea-iterate` 根据证据修订判断，决定下一轮要减少哪个未知。

### 从实验到论文

- **实验前**，在研究说明中回答「即使做成功，结果会回答什么科学问题，论文能据此提出什么新结论？」在本轮取证方案中写清对照和测量怎样区分可能的解释。
- **实验执行后**，`code-idea-execution` 报告实际执行、测量质量和观察到的结果。论点的证据判断（`evidence_assessment`）说明本轮证据在实际条件下怎样支持或削弱具体命题，并标出仍无法区分的解释。
- **研究判断时**，`code-idea-iterate` 用实际数据重新回答实验前的问题。说明得到的发现改变了什么认识、哪条替代解释仍成立、结论适用于哪里，以及相对最接近的已有工作新增了什么。研究贡献和是否开始写作分别判断。`supported` 的数量、运行成功与代码标签均只提供各自对应的信息。
- **交接论文时**，围绕科学问题、发现、证据、替代解释、适用边界和相对已有工作的新增组织材料。按每项证据在论证中的作用选择实验和图表，说明核心论证还有哪些缺口。`code-idea-iterate` 据此给出写作建议，由用户决定是否启动写作。截稿时间可影响写作安排和主张范围，证据缺口如实保留。

## 核心设计哲学

**人在回路。** Agent 主动搜集证据、分析、筛选并给出有理由的推荐，**放大人的信息处理带宽**，把问题**推进到人可以下判断的临界点**。研究方向、投入和最终主张由人决定。各 skill 在需要用户决定的地方设确认点，并保留供用户核对的报告和可供下游读取的记录。

**产物即真相。** 判断「进行到哪一步」的唯一依据是磁盘上的真实产物——它们不会过期、不会和实现脱节。一切关键结论必须落盘：**可审计**（数字来自真实 run，能追回命令与配置）、**可回溯**（git tag + 版本树锚定每个成功节点）、**可追踪**（产物交接靠显式契约，不靠记忆）。会话可以断、机器可以换，只要产物在，上下文就能重建。

## 所有技能共用的规则

各技能的正文只需用一行引用本节。有专用约定时，例如某个技能需要额外的符号记法，可在对应技能中补充。其他技能中引用的「横切规范」也指本节。

- **符号约定**：会话里给用户看的公式/符号用 Unicode（σ、λ、≥、×10⁻³），写进落盘 markdown 才用 LaTeX。
- **论文标识**：落盘文件和给用户的内容里，论文用 arXiv ID / DOI / URL 标识，并注明已核版本。paper-search v2 调用也使用稳定外部标识，跨机器交接用导出的来源和结果。
- **跨机器交接**：skill 只声明「需要哪个文件」，不规定怎么传——文件不在找用户要，不绑传输工具（详见「全局目录布局与跨机器同步」）。

## 科研三阶段全景

DL Assistant 把一个科研项目划分为三阶段，每阶段对应一组 skill：

| 阶段               | 干什么                                          | skills                                                                                                                           |
| ------------------ | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **前期（输入）**   | 找方向 / 读论文 / 调研 / 想 idea                | arxiv-daily-paper、hf-trending-papers、direction-tracking、paper-reading、literature-survey、idea-find、baseline-survey          |
| **中期（coding）** | 搭环境 / 复现 / idea迭代                        | code-project-setup、code-paper-reproduction、code-idea-prepare、code-reading、code-idea-execution、code-idea-iterate             |
| **后期（产出）**   | 写论文 / 做实验 / 审稿 / 回应 / 投稿 / 代码发布 | writing-paper、writing-paper-review、writing-paper-response、writing-paper-submission、code-paper-experiment、code-paper-release |

通常前期在本地机器、中期在 GPU 机器、后期写作线在本地 + 实验线在 GPU 机器；各 skill 产各自的产物，靠下方「全局目录布局与跨机器同步」做跨机器协作。

## 配套 skill

下列 MCP 配套技能在各阶段均可按需使用。

| skill                                    | MCP server       | 干什么                                                                                                                                   |
| ---------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [paper-search](../paper-search/SKILL.md) | paper-search-mcp | 论文检索（搜索 / 详情 / 引用追踪 / 作者·机构）                                                                                           |
| [tex-mcp](../tex-mcp/SKILL.md)           | tex-mcp          | 读 arXiv 论文源码（章节正文 / 图 / 表 / 参考文献）——**arXiv 论文内容读取的首选通道**，用 `tex_open` 打开固定版本，源码不可用时用 pdf-mcp |
| [pdf-mcp](../pdf-mcp/SKILL.md)           | pdf-mcp          | PDF 文件操作（提取文字·图片 / 搜索 / 渲染页面）——本地/成品 PDF 专用 + tex-mcp 的兜底                                                     |
| [overleaf-mcp](../overleaf-mcp/SKILL.md) | overleaf-mcp     | 绑定本地 Git 仓库、远端编译、查日志与 PDF。正文编辑和同步走 Git CLI。                                                                    |

- [W&B](../wandb/SKILL.md) 提供可选的实验记录和查询支持。
- [research-presentation](../research-presentation/SKILL.md) 用于制作汇报幻灯片。

上表的操作按各 MCP v2 说明执行。TeX 和 PDF 打开后以返回的 `document_id` 继续读，Overleaf 用同一轮的 `compile_id` 查日志和产物。

## 全局 skill 流向图（skill 间顺序依赖）

下图展示科研流程中各技能的执行顺序。箭头标明需要交接的材料。各技能运行内部的流程图需要查看对应的技能，这里只显示技能之间的交接关系。

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
    PKG[("论文材料（paper-package.md）与代码仓库")]
    EPLAN[("实验计划包")]
    EDATA[("实验数据包")]
    PDF[/论文 PDF/]
    REPO[/release repo/]

    AD -.->|关注的论文| IF
    HF -.->|关注的论文| IF
    PR -.->|精读笔记| IF
    LS -.->|领域地图| IF
    DT -.->|累积库| IF
    IF -->|研究说明草稿（候选代码仓库线索及研究设想类型）| BS
    IF -.->|研究说明、首轮取证方案与初始论点记录| EX
    BS --> DOCS
    DOCS --> CPS
    CPS -->|setup report| CPR
    CPS -.->|setup.json| CR
    CPR -->|reproduction report| CIP
    CIP -->|prepared baseline repo| CR
    CR -->|读懂 baseline 再动手| EX
    CPR -.->|评估后跳过代码清理（记录理由）| CR
    EX -->|实际观察、证据判断与适用边界| IT
    IT -->|继续迭代，交接研究说明、本轮取证方案和论点记录| EX
    IT -->|进入论文写作与补充实验阶段| PKG

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
- 中期由 `code-idea-execution` 执行实验，`code-idea-iterate` 分析证据后与用户决定是否继续迭代。进入论文阶段后，`code-idea-iterate` 生成 `paper-package.md`，记录科学问题、主要发现、支撑证据、替代解释、结论边界、相对已有工作的新增和剩余论证缺口。写作和论文实验均从 `code-idea-iterate` 接收该文件及对应的代码仓库。
- 中期主线依次包括环境准备、复现、代码清理、代码阅读和方案实现。**代码阅读（`code-reading`）是必经步骤**。实现研究方案之前，先带用户读懂基线代码（见「核心设计哲学」）。
- `baseline-survey` 按用途选择代码仓库。**用于比较的基线代码**适用于改进直接前驱方法的研究。**用于分析实验的代码仓库**适用于组合已有研究发现或先做分析的研究，这类研究没有直接前驱仓库，第一版用分析实验检验假设。后一种情况下，`code-paper-reproduction` 以仓库自己报告的参考结果为复现目标，核查这套代码能否用于后续测量。
- 复现后通常先做代码清理，再进入代码阅读。复现交接时，根据仓库规模、未使用代码和消融实验残留的多少、方案涉及的改动范围，以及预计的迭代次数，判断是否需要清理。仓库较小、代码整洁且只涉及局部改动时，**记录理由后可跳过清理，直接进入代码阅读**。判断标准见 `code-paper-reproduction` SKILL.md「下游交接」。
- 后期 `writing-paper → review → response → writing-paper`（改论文）来回箭头。
- 后期写作和论文实验分别在本地与 GPU 服务器上进行。实验计划包由写作交给论文实验，实验数据包由论文实验交回写作。
- **前期文献库不直接交给论文写作技能**。前期调研报告和精读笔记供用户了解领域、判断研究价值。论文写作时，围绕具体论点选取参考文献，包括研究方案所基于的核心论文，以及需要比较的相关工作。因此，图中前期调研与论文写作之间没有交接箭头。

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
    ├── idea-find/             # idea-find：idea 文件夹（研究说明草稿 + 实验计划 + 初始论点记录）
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
