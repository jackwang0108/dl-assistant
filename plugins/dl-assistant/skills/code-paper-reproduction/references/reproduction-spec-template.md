# Reproduction Spec 模板（code-paper-reproduction）

> spec 定 what / why：复现什么、为什么这么分流、风险在哪、怎么算对齐。Step 2 产出，**用户审过才进 Step 3**。
> spec 落盘是"当初决定复现什么、为什么这么分流"的证据——写够决策所需的信息，不写成 repo 介绍流水账。
> 每节给了「具体填写要求」，照它判断写到什么程度算够。

````markdown
# Reproduction Spec: <repo-name>

> Step 2 产出，用户审过才进 Step 3。机读初稿来自 setup.json 的 paper_metrics（若有），本 spec 回论文核对后定稿。

## 1. 复现目标
- **repo 角色**：用于比较的基线代码 / 用于分析实验的代码仓库（baseline-survey clone 卡标，经 setup.json `repo_role` 原样传递）
- **论文**：<title / arxiv id>（仓库用于分析实验时：仓库维护者报告的参考结果的出处——README / model zoo / 技术报告）
- **目标表格行**：Table X 第 N 行 + 该行的 setting（backbone / 输入尺寸 / schedule）（仓库用于分析实验时：哪个模型 @ 哪个 benchmark = 多少）
- **数据集 + split**：<dataset> / <val|test>（论文报的是哪个集）
- **metric 精确定义**：<如 mAP@[.5:.95] (pycocotools 官方 eval)>
- **论文数 + 容差范围**：<41.2> / 容差来源（优先使用论文报告的标准差，否则使用默认容差）

> 具体填写要求：明确论文的表号、行号和该行使用的设置（trust-traps ⑤）；metric 写到能据此去源码核对的精度——`mAP` 不合格，`mAP@[.5:.95] (pycocotools)` 合格（trust-traps ①）。

## 2. idea 类型与分流建议
- **idea 类型**：training-free / 要重训（一句话依据）
- **训练规模估算**：dev_card_footprint 单步耗时 × 论文 iter ≈ <X 小时/天>
- **选定分流**：A / B / C + 理由；若 C，小 setting 用哪个（论文自报小 setting 优先）

> 具体填写要求：分流理由要落到数字上（"开发卡 full ≈ 14h，训得动，走 B"），不是"感觉规模不大"。

## 3. 执行方案
- **eval 命令**：<来自 setup.json ready_commands，注明>
- **train 命令**：<同上>
- **checkpoint / config**：<路径 + 待核对的训练来源和版本（EMA? best/last?）>
- **预估时间**：eval <X> / train <X> / 多 seed 计划（≥2-3 seed 测 noise_floor）
- **预期产出分流产物**：runs/ 下会有哪几个 run-slug

## 4. 已知问题和待验证风险
- **确定要处理的**：<setup.json 标的语义风险 / 仓库已有的问题记录（survey、issue）>
- **存疑待验证的**：<按排查手册列出待核对项：metric 自实现？checkpoint 的训练来源与版本不明？协议含 TTA？>

> 具体填写要求：分别列出已确认的问题和待验证的风险。逐项说明判断依据和核验办法。如果还无法说清怎么核验，回到仓库继续检查。

## 5. 验证标准（可判定）
- **eval_判定 = reproduced 的条件**：<数字 + band，如 "official eval ≥ 40.7（41.2 − 0.5）">
- **training_判定 = 通过的条件**：<按分流写：B = full 训练数在容差范围内 + ≥2-3 seed std 记录到 noise_floor；C = b 小 setting 对齐 + a 趋势吻合>
- **什么情况降级**：<开发卡 full 训不动 → 各项验证能支持的结论第 2 级；b+a 也不够 → 第 3 级组件级验证>
````

## 模板使用说明

- **先探索再开口**：spec 里的每个字段都应该有论文 / repo / setup.json 的出处，不在信息不足时写 spec 问用户。
- **可判定是硬要求**：第 5 节写不出具体数字条件，说明第 1 节的目标没明确并固定，回去补。
- **spec 审是确认点**：写完停下给用户审，确认才进 Step 3；用户改动的分歧点在 spec 里改定，不口头约定。
