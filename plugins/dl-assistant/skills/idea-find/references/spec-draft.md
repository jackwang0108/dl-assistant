# 产草稿（Step 15-17）：准 spec + plan + 初始 claim 树（两层）

讨论②一起打磨出方法后，主会话（本阶段不派子 agent）跟用户定稿，产**三个文件**：

- `specs/<方向slug>-idea-spec-draft.md`（准 spec）
- `specs/<方向slug>-idea-plan-draft.md`（准 plan，**方法设计**）
- `specs/<方向slug>-claim-tree-draft.json`（初始 claim 树，**两层**）

一方向一份，集中放 `specs/`。

## 产草稿流程（三个确认点·共同打磨）

讨论②收敛方法路线后，主会话（本阶段不派子 agent）跟用户**逐文件共同打磨**，每个文件用户拍板才写下一个——这阶段产研究决策产物，方向/设计错了 execution 接手就跑偏。

### Step 15 写 spec → 确认点：用户确认

按 spec-template 写 spec（§0 总论点+Roadmap+当前子论点 / §1 问题 / §2 文献 / §3 novelty / §4 失败解读表初稿）。摆给用户审：总论点立得住吗、Roadmap 第一个创新点（当前子论点）对不对、novelty 够不够目标会议、解读条目覆盖了各方案的主要失败情形吗、**每条的三问讲得通吗**（验什么 / 阈值来历或「无先验」标注 / 命中支持哪种解读+嫌疑层+后路——光写结论不讲推导，用户没法审）。**用户确认才写 plan**。

### Step 16 写 plan（共同打磨实验设计）→ 确认点：用户拍板

按 plan-template 写 plan——**核心是和用户共同打磨实验设计**（讨论②只定了方法路线，实验怎么验是这阶段细化）：

- 出实验总览 + 方案设计 + 每实验原理初稿。
- **给用户讲懂每个实验**（回答什么 / 为什么这样设计 + 机制 / 预期成功·失败信号）。
- 用户质疑/调整 → 查文献（paper-search）+ 证据补充 → 更新。
- 循环到用户拍板。**plan 确认才写 claim**。

> 共同打磨手法见 SKILL「怎么跟用户协作」（边查边讲 / 按需展开 / 一起打磨不做选择题）。文献用 paper-search 取真实数据，禁止编造。

### Step 17 写初始 claim 树（两层，跟着 plan 定）

plan 拍板后，claim 树跟着定（总论点 = spec §0，子论点 = plan 的方法派生）——不单独停顿，是 spec+plan 的结构化沉淀。

## 这一阶段的定位（重要）

idea-find 的产物是**中期 `code-idea-execution` 的输入**。execution 是**纯执行引擎**——吃 spec+plan → 实现 + 实验 + 验收 + conclusion，**不设计方法**（方法设计是研究决策，归 idea-find v1 / iterate v2+）。所以 v1 方案必须在这里**定到可执行**，不能只产 spec 草稿把设计推给 execution。

但"定到可执行"的范围是 **v1 最小实验方案**，不是完整方法：

> 纪律：plan 把 **v1 最小实现 + 实验设计**定到能执行（实验总览聚焦首个验证实验 + 核心假设对应的验证及判据、方案设计只写验证核心假设所需的实现、每实验原理）。**不许基于"实验会成功"的预定假设预设计完整方法形态 / 完整实验矩阵**——实验结果不确定，预设的完整方案一旦与结果不符就整体作废；后续版本（加组件、扩 ablation、收敛成论文方法）是 iterate 基于每版实验证据演化的，事先铺排违背"在验证中迭代"。Roadmap 里 v1 之后的创新点只列**方向假设**（要验证什么假设 / 什么结果说明假设不成立），不设计。

**IF 必须产（不留空）**：

- **spec**（§0 总论点 + Roadmap + 当前子论点 / §1 问题 / §2 文献 / §3 novelty / §4 失败解读表初稿 / 附录代码锚点**概要**）
- **plan**（v1 实验总览 + v1 最小方案设计 + **每实验原理** + 代码指引概要 + 运行命令 + DoD）
- **初始 claim 树**（两层：总论点 + 子论点）

**待补齐（留空，execution 读代码后填，不拍脑袋）**：

- **claim×代码地图 file:line**（execution 读代码理解接入点后填——叙述关落 `03-claim-code-map.md`；IF 还没碰真实 baseline 代码，填不了精确位置）
- baseline / 选择用于分析实验的代码仓库：**标 idea 形态**（前驱改进型 / 组合 insight 分析先行型）+ 候选 repo / 权重 / 数据集**只列线索 URL，不下判断**；分析先行型另写**载体需求**（分析实验需要长在什么任务 / 数据 / 模型上）——选哪个交 `baseline-survey` 尽调（它按形态走选择用于比较的 baseline或选择用于分析实验的代码仓库）
- 版本号（进 `ideas/` 时 execution 分配 v1）

## spec 草稿（按 spec-template）

按 `dl-assistant/references/spec-template.md` 骨架产（单一真相源、不誊抄）。各节内容来自哪：

- §0 总论点 + Roadmap（创新点状态表，第一个创新点 = 当前子论点；**v1 之后的创新点只列方向假设——要验证什么假设 / 什么结果说明假设不成立，不设计**）+ 当前子论点 ← 讨论②定的 v1 方案 + 找方向阶段的方向
- §0 候选方案节（每方案三要素：要验证什么假设 / 为什么值得验证 / 什么结果说明假设不成立，结构见 spec-template）← 选定路线为方案 A；挑错中通过检查、 用户也想试的其他路线可作方案 B/C 一起比较（2-4 个，排除法定）
- §1 问题定义 ← 找方向阶段的核心问题 + 挖方法阶段深读的"为什么现有方案不够"
- §2 文献基础 ← `papers/` 里选定方向的必读论文
- §3 novelty ← 挖方法阶段选定路线 + 独立检查
- §4 失败解读表（初稿：每个方案的主要失败情形 → 观察模式 + 解读 + 嫌疑层 + 后路，与用户共同打磨，**每条带判据三问**：验什么假设 / 阈值来历（无先验须标注）/ 命中支持哪种解读+嫌疑层+后路；命中不判死 claim，只触发解读 + iterate 分析实验未达预期的流程；iterate 写 spec 时随版本演化）← 讨论②的证伪条件 + Step 16 实验设计的预期失败信号
- 附录 A 代码锚点**概要**（模块级，如"改 backbone 的 neck"——精确 file:line 留 execution）标「待补齐」

> spec-template 没有的 idea-find 额外节：**目标会议**（项目级，后续进 `PROJECT_CONTEXT.md` 的研究框架）：

| 会议 | CCF 等级 | 预计截止 | 备注 |
| --- | --- | --- | --- |
| {匹配领域的会议} | A | {日期} | {征稿状态} |

## plan 草稿（按 plan-template，方法设计——本阶段核心）

按 `dl-assistant/references/plan-template.md` + `plan-writing-principles.md` 骨架产。**这是 v1 最小实验方案**，挖方法阶段一起打磨的路线落地成可执行 plan：

- **实验总览**：v1 范围内每个子论点 / 判据对应哪些实验验证——聚焦首个验证实验 + 核心假设对应的验证及判据（先过这张表再设计实验）
- **方案设计**：挖方法阶段选定路线的 **v1 最小实现**——机制 / 公式 / 架构改动只写验证核心假设所需的部分 + 预期工作原理 + 接入点概要
- **每实验原理**：回答什么 / 为什么这样设计 + 机制 / 预期成功·失败信号（含判据三问：验什么假设 / 阈值来历 / 命中意味着什么——让 execution 能看懂每个实验在干啥，让用户能审）
- **代码指引概要**：改哪个模块（模块级，精确 file:line 留 execution 读代码落 `03-claim-code-map.md`）
- **Phase 分组 + 共享对照协议 + 运行命令 + DoD**

> plan-template 的「代码指引」节——IF 只写模块级概要，精确 file:line 和 claim×代码地图由 execution 落 `03-claim-code-map.md`。

## claim-tree-draft.json（初始两层 claim 树）

claim 树记录各项研究论点，供构想设计、实验执行、结果验收、后续迭代和论文写作使用。这里先写两层草稿，execution 在 Step 2 将它复制到 `ideas/v1-<slug>/claims.json`，作为该版本的正式记录。

- **路径**：`specs/<方向slug>-claim-tree-draft.json`。
- **schema 直接用 `dl-assistant/references/claims-template.json`**（两层：总论点 paper_claim + 子论点 claims[]），三处不同：`verdict` 全 `pending`、`evidence[]` 空、`version`/`snapshot_date` 留空。
- **两层**：
  - **总论点 paper_claim**（1 个）：spec §0 的总主张（如「我们的方法提升 X」）。
  - **子论点 claims[]**：总论点拆成的可验证命题。创新点1（= 当前子论点 C1，spec §0 核心假设）+ 几条机制/性能子论点（挖方法阶段派生，每个关键组件/机制一条）。**ID 一旦分配不变义**（C1/C2…，后面证伪留 ID、拆分/新增另起 ID）。
- **谁产谁消**：idea-find 产 draft（全 pending）→ execution 起手（Step 2）拷成 v1 `claims.json` → 验收填裁决 → iterate 演化。

## 保存位置

- `<方向slug>-idea-spec-draft.md` + `<方向slug>-idea-plan-draft.md` + `<方向slug>-claim-tree-draft.json`，都放 `specs/`（可同时放多个方向）。idea-find 只产草稿，版本树（`ideas/`）由 execution/iterate 建。
- 正式 `01-idea-spec.md` + `02-research-plan.md` + `claims.json` 由 execution 起手结合 baseline 现实（读代码填 claim×代码地图）后，**从这三份草稿就地升级**进 `ideas/v1-<slug>/`。

## 结束语（显式交接）

> **以上是这个方向的准 spec + plan + 初始 claim 树（两层），已存到 idea 文件夹的 specs/ 目录。**
>
> 下一步（前期收尾）：用 `baseline-survey` 对候选 baseline 做工程尽调——核查候选 repo 的代码质量、权重可得性、数据集版本、社区复现报告，选定用哪个。它会先按草稿里的形态标注判定走**选择用于比较的 baseline**还是**选择用于分析实验的代码仓库**（组合 insight / 分析先行型没有直接前驱 repo，选的是跑分析实验的载体），最终以「clone 卡」给出"去服务器 clone 哪个 repo、什么角色、带什么坑"。它也在本地跑；产出的选型报告和这份草稿一起作为跨机器交接物，需要时找用户弄到目标机器（通用规范见 `dl-assistant` SKILL.md「所有技能共用的规则」）。
>
> 然后（进中期）：把草稿 + 选型报告放到服务器 baseline repo，按主线准备 baseline——`code-project-setup`（环境就绪）→ `code-paper-reproduction`（复现验证）→ 需要时 `code-idea-prepare`（分诊：要不要先清理/优化 baseline）→ `code-reading`（读懂 baseline，必经）——然后把草稿交给 `code-idea-execution`。它起手结合 baseline 代码 + setup/reproduction 报告**确认 spec+plan**，**读代码填 claim×代码地图**（落 `03-claim-code-map.md`），草稿就地升级为正式 spec+plan；同时把 claim-tree-draft.json 拷成 `claims.json`，实现第一版。
>
> 之后每跑完一版实验，用 `code-idea-iterate` 基于实验证据迭代下一版 idea。
>
> 提示：想做这个 idea 文件夹里的**另一个方向**？直接再触发 idea-find、指向这个文件夹——已有产物（`literature.json` 台账、`papers/` 里的 PDF 和笔记、方向文件）直接复用，对新方向开挖方法即可。
>
> 祝研究顺利！
