# Idea 版本树规范（链表模型 · git 跟 plan 走）

idea 的代码演进是一条**线性链表**：plan-1 → plan-2 → … → plan-N。每个 plan 是一个 git 节点（一个版本）。本文件是版本树的**规范说明**——心智模型、git 实现（命名/tag/切分支）、目录结构。`code-idea-execution` 和 `code-idea-iterate` 维护版本树时遵守，开新 plan、打 tag 前必读。

> 一个 baseline repo 只跑一条 idea 链、最终发一个 paper，`ideas/` 直接平铺版本目录。与 `idea-tree-template.json`（机读索引）同源，冲突以本文件 + `code-idea-execution/SKILL.md` 为准。版本变更的**操作步骤**（何时切分支、何时打 tag）在 SKILL.md，本文件不重复。

## 核心模型：git 跟 plan 走 + claim 两层

### git 跟 plan（不是 spec）
- **spec 是稳定层**（总论点 claim + Roadmap + 当前子论点 + 文献 + novelty），跨 plan 沿用，**不是 git 节点**。
- **一个 plan = 一个 git 节点**（一个版本 v<N>）。`code-idea-execution` 根据一份 plan 执行（方法已由 idea-find/iterate 设计好）→ 实现 + 实验 → conclusion。
- 一个 plan 节点两种结局：
  - **成功**：核心子论点 supported（升格创新点）→ 打 tag
  - **失败**：核心子论点 refuted / 效果不好 → 不打 tag

> 诊断（分析未达预期的原因或进行探查实验）不形成独立版本节点——它在 iterate Step 5 会话内就地完成，结论落 `autopsy.md`；版本节点只对应验 claim 的方法版（改进 method / 新创新点 / 演化）。

### claim 两层 + 创新点
- **总论点 claim**：paper 的总主张（1 个，稳定）。如「我们的方法提升 X」。
- **子论点 claim**：总论点拆成的可验证命题（pending → supported / plausible / insufficient_evidence / contradicted）。如「组件 A 提升 X 的某方面」。
- **创新点 = supported 的子论点**（升格为 paper 贡献；非 supported 不算创新点）。
- **method** = 一个子论点的代码实现，**锁定在成立 tag**。
- 关系：总论点 ←（拆成）← 子论点；子论点 supported → 升格创新点 → 进 paper method。

详见 `claims-template.json`。

## 链表模型

```
plan-1 → plan-2 → plan-3 → … → plan-N（当前最新）
```

- **每个 plan = 一个版本**。v1 的 plan 由 `idea-find` 给出（含方法设计）；v2+ 的 plan 由 `code-idea-iterate` 基于上一版 conclusion 给出。
- **链只追加，不删除**。失败/证伪的 plan 标 `status: abandoned`，但仍留链上——是探索过程的完整记录，写 Related Work / rebuttal 时要回看。
- **`ideas/` 目录是完整累积集**：v1 到 vN 的所有版本目录平铺在 `ideas/` 下，随时看清"一共有哪些 plan、每个收获什么"。也是 `code-paper-release` 干净抽取的前提。
- **没有分支选择**。每次迭代从当前最新版继续。想"回到 v2 试另一条路"——那条路就是 v(k+1)，不开分支。

## 命名（三者同源，从 v<N>-<slug> 派生）

| 命名空间 | 形式 | 例 |
|---|---|---|
| 目录 | `ideas/v<N>-<slug>/` | `ideas/v2-diagnostic/` |
| git 分支 | `idea/v<N>-<slug>` | `idea/v2-diagnostic` |
| git tag | `claim-C<id>[-v<k>]`（**只在成功节点**）| `claim-C1` / `claim-C1-v2` |

> **取消版本 tag `v<N>`**。tag 只剩 `claim-C<id>[-v<k>]`（成功锚点，锁 method 代码）。版本号在分支名 + commit message + `idea_tree.json` 追踪，不单独打 git tag。

### 版本号 v<N>-<slug>
- **v<N>**：从 1 线性递增，不复用不回退（v3 证伪，下一个仍 v4）。
- **slug**：plan 的语义名（这版方法/诊断做啥，如 `attention-refill`、`diagnostic`）。

## 分支怎么切（从最新 commit，不靠 tag）

- **v1**：从 baseline repo 的可信 baseline tag 切——`code-idea-prepare` 成功时打的 `baseline-prepared`（CIP 全退或经评估后被跳过则 `baseline-reproduced`）。
  ```bash
  git checkout -b idea/v1-<slug> baseline-prepared
  ```
- **v2+**：从最新 commit（HEAD）切，不依赖 tag。
  ```bash
  git checkout -b idea/v<N>-<slug>
  ```
- 失败节点虽无 tag，commit 在链上，下版照常从它切。

> `baseline-prepared` 由 `code-idea-prepare` 打（CIP 成功 merge 时）。CIP 全退或经评估后被跳过则用 `code-paper-reproduction` 的 `baseline-reproduced`。execution 上来要问 cleanup 目录在不在，确认从哪个 tag 切。

## tag 规矩（只在成功节点打）

- **成功节点**（核心子论点 supported）→ 打 `claim-C<id>`（首次成立）或 `claim-C<id>-v<k>`（method 迭代新锚点）。
- **失败节点**（refuted / 效果不好）→ 不打 tag。
- claim tag **锁定该子论点的 method 代码**（可回查对比的锚点）。

### tag 三方绑定（成功节点）

```
git tag: claim-C<id>
   ↕
method 代码: 该 commit 的实现（这版 method = 这个子论点的实现）
   ↕
conclusion: ideas/v<N>-<slug>/04-conclusion.md（裁决 supported + evidence 指针）
```

**tag 的 commit message 必须写**：claim ID + 子论点 + 关键 metric + run 路径。
```bash
git tag -a claim-C1 -m "C1: <子论点白话> supported. metric: <关键数字>. run: experiments/exp-XXX/runs/"
```

git 历史、method 代码、conclusion 三方对齐，任何一处能追溯另两处。

### method 迭代（同子论点改进 method）

子论点已 supported 后，还想改进它的 method：
- **子论点 claim 不变**（仍 supported），只动 method。
- 从最新 commit 切新 plan，改进 method，跑实验，打 `claim-C<id>-v2`。
- conclusion 对比基线 = `claim-C<id>`（上一版 method），不是和别的 claim 比。
- method 迭代显著改进才打新锚点（`claim-C<id>-v2` / `-v3`），每个 method 版本一个可回查点。

## 文件目录

整个 `ideas/` 长这样：

```
ideas/
├── PROJECT_CONTEXT.md                # 项目级稳定背景（session 开头读）
├── idea_tree.json                    # 版本链表机读索引（所有节点：成功/失败）
├── paper-package.md                  # iterate 在决定进入论文阶段时生成，记录总论点、创新点和论证顺序，交给写作和论文实验技能
└── v<N>-<slug>/                      # 一个 plan 节点（一个版本）
    ├── 00-from-previous-version.md   # iterate 产（仅 v2+）：上版→这版叙事链
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
| `00-from-previous-version.md` | iterate（仅 v2+） | 上版→这版叙事链（目标→结果→裁决意义→浮出问题→这版做什么）+ 末尾机读变更摘要 |
| `01-idea-spec.md` | idea-find（v1）/ iterate（v2+） | 稳定层：总论点 claim + Roadmap（已成立子论点=创新点）+ 当前子论点 + 文献 + novelty |
| `02-research-plan.md` | idea-find（v1）/ iterate（v2+） | 本 plan 的方法设计 + 实验总览 + 每实验原理 + 代码指引 + 运行命令 + DoD |
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
