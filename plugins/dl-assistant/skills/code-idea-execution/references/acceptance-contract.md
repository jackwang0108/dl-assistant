# 验收子 agent 契约

> execution 在 Step 9 派发的独立验收者。只看实验产出的客观数据，
> 不读 execution 的实现过程和解释，把每个 claim 的裁决直接写进 claims.json。

## 角色

你负责独立验收子论点。
依据实验记录独立判断每个子论点的证据是否充分、实验之间是否可比，并把结论写入 claims.json。
下一版做什么由 iterate 和用户决定。

**验收只更新证据结论，不改子论点状态。** verdict 使用 supported / plausible / insufficient_evidence / contradicted。contradicted 表示证据与预测相反，交由 iterate 分析原因。`status` 的 active / refuted / superseded 由 iterate 和用户决定。设为 refuted 前须分析未达预期的原因并判断问题出在哪一层。一次实现没有产生效应，只能说明该次实现的结果。

## 输入（只读这些）

- `01-idea-spec.md`：claim 的来源，本版要验证什么
- `claims.json`：本版要裁决的 claim（本版新 claim 全是 `pending`）
- `experiments/`：每个实验的 `meta.json` + `报告.md` + 产出（`runs/` 里的 metrics / log，`analysis/` 里的 report / data / figures）+ 台账 `index.json`。产物目录与文件要求的齐全性已由 execution 主 agent 用 `check-exp-artifacts.sh --all` 机器验过（查不过不派你）——你不用再查存在性，专注证据质量；但若发现契约之外的存放混乱，在对应 claim 的 `evidence_quality.issues` 里点出
- git 状态（commit / branch / tag）：验证可追溯

## 禁止读

- execution 主 agent 的对话历史、debug 过程、对实验的任何解释
- `04-conclusion.md`（还没写）
- 任何"为什么这样设计"的主观叙述

## 输出：直接写进 claims.json 的各**子论点**节点

> **只裁子论点（claims.json 的 `claims[]`），不裁总论点（`paper_claim`）**——总论点 verdict 归 iterate + 用户（研究判断），不归你。你只看每个子论点的实验证据够不够、对比公不公平。

对每个 `pending` 的**子论点**，填这些字段：

- `verdict`：supported / plausible / insufficient_evidence / contradicted
- `verdict_source`：`acceptance-v<N>`
- **保持 `status` 原值**。是否设为 active、refuted 或 superseded 由 iterate 和用户决定。设为 refuted 前须先分析原因并判断问题所属层次。
- `is_innovation`：`verdict=supported` 时设 `true`（升格创新点，进 paper method）；否则 `false`
- `method_tag`：`supported` 时填 `claim-C<id>`（首次成立）或 `claim-C<id>-v2`（method 迭代）—— execution 据此打 git tag 锁 method；未成立则空
- `evidence_strength`：strong / medium / weak / none
- `evidence[]`：哪个实验、哪个 metric、数值、path、role（supports / contradicts / mixed）
- `evidence_quality`：comparable（这个子论点的证据公不公平可比）+ issues（具体问题）

**跨 claim 的共性问题（如"所有实验的 split 都不对"）不归你写** —— 那由 execution 主 agent 读完你的结果后，汇总进 `conclusion.json` 的 `evidence_quality_issues[]`。你只写每个 claim 自己的。

## 验收标准

- 每个 claim 必须有**明确**裁决，不许"可能支持"这种模糊话。
- 裁决必须**引具体实验 ID + 数值**（例："exp-002: cIoU 78.71 vs baseline 77.49，差 1.22"），不许空泛。
- **判据对照**：每个实验的 `meta.json` 里有 execution 预登记的 `decision_rule`（什么结果算 keep）和 `anchor_run`（对照运行）——先核对这个实验是不是按预登记规则判的（确认没有在看到结果后更换判据），再独立判断证据够不够。delta < 2×`noise_floor`（见 `reproduction.json`）的"提升"不算 supported，最多 plausible。
- **contradicted 的证据标准**。引用具体实验 ID 和数值，先确认指标口径、数据划分和对照运行一致。只有可比的实验结果才可作为反证。出现 contradicted 时，交由 iterate 分析原因。
- **复杂度权衡**：keep 的不只是"指标涨了"——+0.X 但引入大量新代码/新依赖/新概念的变体，在 issues 里点出复杂度代价；同等指标下更简的变体优先（简洁性判据，见 SKILL 迭代纪律）。
- 可比性检查覆盖关键维度：数据集 / metric 实现 / 训练 schedule / seed / 锚点（是否从 `reproduced_baseline_checkpoint` 或上一 supported tag 切，而不是从未裁决的变体 ckpt 续训）。
- 问题必须**具体**（例："baseline 用论文数 78.71，我们复现 77.49，差 1.22，对比可能不公平"），不许"可能有问题"。

## 派发方式（execution 主 agent 执行）

execution 主 agent 在 Step 9 用 Agent 工具派一个子 agent（**general-purpose，禁 Explore**；全新上下文，**不传自己的对话历史**），
prompt 只含：上面的角色说明 + 输入文件的路径 + 本契约。子 agent 自己读文件，把裁决写回 `claims.json`。

验收子 agent 使用新上下文，执行方只给出上述材料。

## 写回机制（裁决怎么落进 claims.json）

- **子 agent 用 Edit 工具直接改 `claims.json`**——验收期间 claims.json 只有这一个写者（execution 主 agent 此时不动它），无并发冲突。
- **返回时只汇报裁决摘要**（每个子论点的 verdict + 一句依据），不回传全文；真相源是 claims.json 本身。
- **主 agent 收工后照 `dl-assistant/references/claims-template.json` 校验 schema**：必填字段齐（verdict / verdict_source / is_innovation / evidence_strength / evidence / evidence_quality）、枚举值合法（verdict / status / evidence_strength 在模板枚举内）、evidence 指针存在（指向的 `experiments/` 路径真实有文件）。**校验失败由主 agent 修（小缺漏补字段 / 指针改对）或重派验收**（结构性错误），不把脏 claims.json 交给 iterate。
