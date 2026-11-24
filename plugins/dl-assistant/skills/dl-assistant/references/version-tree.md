# Idea 版本树规范（链表模型 · git 跟 plan 走）

研究版本按建立顺序登记，分支和实际起点按各轮获批范围选择。本文件说明版本索引、Git 命名及文件位置，供 `code-idea-execution` 和 `code-idea-iterate` 查阅。

> 一个 baseline repo 只跑一条 idea 链、最终发一个 paper，`ideas/` 直接平铺版本目录。与 `idea-tree-template.json`（机读索引）同源，冲突以本文件 + `code-idea-execution/SKILL.md` 为准。版本变更的**操作步骤**（何时切分支、何时打 tag）在 SKILL.md，本文件不重复。

## 核心模型：git 跟 plan 走 + claim 两层

### git 跟 plan（不是 spec）
- **spec 是稳定层**（总论点 claim + Roadmap + 当前子论点 + 文献 + novelty），跨 plan 沿用，**不是 git 节点**。
- **一个 plan = 一个 git 节点**（一个版本 v<N>）。`code-idea-execution` 根据一份 plan 执行（方法已由 idea-find/iterate 设计好）→ 实现 + 实验 → conclusion。
- 用户确认建立下一轮版本后，才建版本节点。新版本可以只核准备条件或进行获批的诊断。现有材料复查、准备写作或暂停等决定保存在决定目录。
- 执行结果、测量有效性和命题证据见本轮结论及命题快照。需要回查实现时，用实际 commit 或项目约定的代码标签定位。

### claim 两层 + 创新点
- **总论点 claim**：paper 的总主张（1 个，稳定）。如「我们的方法提升 X」。
- **子论点 claim**：总论点拆成的可验证命题（pending → supported / plausible / insufficient_evidence / contradicted）。如「组件 A 提升 X 的某方面」。
- **科学贡献**由 iterate 和用户结合科学问题、实际发现、替代解释、适用边界和相对已有工作的新增判断。
- 方法实现从实际 commit、代码映射和运行记录回查。有代码标签时可一并引用。

详见 `claims-template.json`。

## 链表模型

```
plan-1 → plan-2 → plan-3 → … → plan-N（当前最新）
```

- **每个获确认的研究版本保存对应 plan**。v1 由 `idea-find` 给出，v2+ 由 `code-idea-iterate` 根据相关证据和用户决定交接。
- **保留历史节点。** 按实际进度更新状态。提前停止的计划和有效反证分别引用对应决定与证据。
- **`ideas/` 目录是完整累积集**：v1 到 vN 的所有版本目录平铺在 `ideas/` 下，随时看清"一共有哪些 plan、每个收获什么"。也是 `code-paper-release` 干净抽取的前提。
- **研究上一轮和代码起点分别记录。** 例如研究继续跟进 v4 的观察，同时从 v2 的已核实现建立新的 v5 分支。用 `00-from-previous-version.json` 记录实际关系。

## 命名（三者同源，从 v<N>-<slug> 派生）

| 命名空间 | 形式 | 例 |
|---|---|---|
| 目录 | `ideas/v<N>-<slug>/` | `ideas/v2-diagnostic/` |
| git 分支 | `idea/v<N>-<slug>` | `idea/v2-diagnostic` |
| git tag（按需） | `claim-C<id>[-v<k>]` | `claim-C1` / `claim-C1-v2` |

> 研究版本号通过分支名和 `idea_tree.json` 追踪。可选标签用于定位具体实现。

### 版本号 v<N>-<slug>
- **v<N>**：从 1 线性递增，不复用不回退（v3 证伪，下一个仍 v4）。
- **slug**：plan 的语义名（这版方法/诊断做啥，如 `attention-refill`、`diagnostic`）。

## 分支怎么切

- **v1**：从 baseline repo 的可信 baseline tag 切——`code-idea-prepare` 成功时打的 `baseline-prepared`（CIP 全退或经评估后被跳过则 `baseline-reproduced`）。
  ```bash
  git checkout -b idea/v1-<slug> baseline-prepared
  ```
- **v2+**：从本轮选定并核实的 commit 切。按 [iterate 运行手册 Step 5](../../code-idea-iterate/references/workflow.md#step-5-准备并交接下一轮取证版本)检查工作区与实际起点。
  ```bash
  git switch -c "$branch" "$verified_start"
  ```

> `baseline-prepared` 由 `code-idea-prepare` 打（CIP 成功 merge 时）。CIP 全退或经评估后被跳过则用 `code-paper-reproduction` 的 `baseline-reproduced`。execution 上来要问 cleanup 目录在不在，确认从哪个 tag 切。

## 用标签定位实现

按项目约定和已有授权使用 `claim-C<id>` 或 `claim-C<id>-v<k>` 定位已有实测证据的实现。创建新研究版本以确认的 commit 和批准范围为依据。

### 标签、实现与证据的对应关系

```
git tag: claim-C<id>
   ↕
method 代码: 该 commit 的实现（这版 method = 这个子论点的实现）
   ↕
conclusion: ideas/v<N>-<slug>/04-conclusion.md（实际比较、条件和证据出处）
```

**tag 的 commit message 必须写**：claim ID + 子论点 + 关键 metric + run 路径。
```bash
git tag -a claim-C1 -m "C1: <子论点白话> supported. metric: <关键数字>. run: experiments/exp-XXX/runs/"
```

git 历史、method 代码、conclusion 三方对齐，任何一处能追溯另两处。

### method 迭代（同子论点改进 method）

命题含义不变时沿用 ID，保留旧实现、实测条件和结论边界。新实现按本轮批准的比较取证，结论引用实际比较所用的基准 commit、运行和配置。命题含义发生实质变化时使用新 ID，记录与旧命题的关系。

## 文件目录

整个 `ideas/` 长这样：

```
ideas/
├── PROJECT_CONTEXT.md                # 项目级稳定背景（session 开头读）
├── idea_tree.json                    # 版本机读索引，保留历次已建节点
├── decisions/
│   └── <decision-id>/
│       └── research-assessment.md    # 研究决定与批准范围
├── paper-package.md                  # iterate 在决定进入论文阶段时生成，记录总论点、创新点和论证顺序，交给写作和论文实验技能
└── v<N>-<slug>/                      # 一个 plan 节点（一个版本）
    ├── 00-from-previous-version.md   # iterate 产（v2+）：上轮证据与本轮选择
    ├── 00-from-previous-version.json # iterate 产（v2+）：实际版本起点、变更和交接引用
    ├── 01-idea-spec.md               # 稳定层：总论点+Roadmap+当前子论点+文献+novelty
    ├── 02-research-plan.md           # 本 plan：方法设计+claim×实验+原理+代码指引
    ├── 03-claim-code-map.md          # execution 产：claim×代码×验证逻辑地图（叙述关填）
    ├── 04-conclusion.md              # 本 plan 结果：发现+裁决（人读叙事）
    ├── conclusion.json               # 机读交接（iterate/release/writing-paper 读）
    ├── claims.json                   # claim 树快照（两层，验收写裁决）
    ├── scripts/                      # 版本级 utility（按需建）
    ├── scratch/                      # debug 草稿区（按需建）
    └── experiments/
        ├── index.json                # 实验台账：每轮一行（execution 维护，验收/iterate 读）
        └── exp-XXX-<name>/
            ├── meta.json
            ├── scripts/
            ├── runs/                 # 训练产出（按 seed，不进 git）
            └── analysis/             # 诊断产出
```

### 每个版本目录的固定文件

| 文件 | 谁产出 | 作用 |
|---|---|---|
| [`00-from-previous-version.md`](../../code-idea-iterate/references/from-previous-version-template.md) | iterate（v2+） | 写上轮实际观察、判断变化、本轮选择、批准范围和继承条件 |
| [`00-from-previous-version.json`](../../code-idea-iterate/references/from-previous-version-template.json) | iterate（v2+） | 记录研究上一轮、实际代码起点、命题变更及 plan 修订和批准引用 |
| `01-idea-spec.md` | idea-find（v1）/ iterate（v2+） | 研究问题、研究价值、假设、与已有工作的差异及结论边界 |
| `02-research-plan.md` | idea-find（v1）/ iterate（v2+） | 按获批范围写各项取证设计、比较、测量、解释、预算和停止点 |
| `03-claim-code-map.md` | execution | claim×代码×验证逻辑地图（叙述关填；plan 只读，地图落这里） |
| `04-conclusion.md` | execution | 本 plan 结果：发现 + claim 裁决（从 claims.json 渲染）+ 版本结论 + 可复现 |
| `conclusion.json` | execution | 机读交接（status/outcome/golden_metrics/key_insights/scale_risks/evidence_quality_issues） |
| `claims.json` | execution（建 v1 + 验收后记录判断）/ iterate（演化） | 记录本轮的总论点和子论点，供各阶段查阅 |

> spec/plan/from-previous 归 idea-find/iterate 产（方法设计是研究决策，execution 只读）；conclusion + claim-code-map + claims 裁决归 execution（纯执行引擎）。execution 按 spec 和 plan 执行，并记录 conclusion。编号固定不重排——下游 skill（iterate/release/writing）按编号找文件。

### experiments/ 与 checkpoint（不进 git）
- `experiments/index.json` 是版本级**实验台账**：每轮一行（实验 ID / claim / 锚点 / 关键数字 / keep 还是 discard / 一句话原因），execution 维护，验收/iterate 读。
- `experiments/exp-XXX-<name>/`，每个实验含 `meta.json`（含预登记 `decision_rule` / `anchor_run` / `scale_risk`）+ `报告.md`（人读封面）+ `configs/`（config 冻结副本）+ `scripts/`（可复现脚本，内嵌完整命令行）+ `runs/seed-X/`（train.log/eval.log/metrics.json/checkpoints）或 `analysis/`（诊断）。齐全性由 `code-idea-execution/scripts/check-exp-artifacts.sh` 机器验收。
- 可复现脚本进 `experiments/<exp>/scripts/`；debug 脚本进版本级 `scratch/`；禁 `/tmp`（重启归零）。
- checkpoint 数 GB 留服务器，不进 git；靠 conclusion 可复现信息（tag/commit/命令）+ tag message 的 run 路径反查。

### 跨机器交接
- 代码分支 + tag：`git push --follow-tags`（不是裸 push，否则 tag 不上传）。
- 实验数字/产出（runs/analysis）：**需要时找用户要，不绑传输方式**——不在 spec/命令里写死 ssh/scp/rsync，机器怎么连、文件怎么传由用户定。
