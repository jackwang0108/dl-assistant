# Reproduction Spec 模板（code-paper-reproduction）

> spec 定 what / why：复现什么、为什么这么分流、风险在哪、怎么算对齐。Step 2 产出，**用户审过才进 Step 3**。
> spec 落盘是"当初决定复现什么、为什么这么分流"的证据——写够决策所需的信息，不写成 repo 介绍流水账。
> 每节给了「深度标尺」，照它判断写到什么程度算够。

````markdown
# Reproduction Spec: <repo-name>

> Step 2 产出，用户审过才进 Step 3。机读初稿来自 setup.json 的 paper_metrics（若有），本 spec 回论文核对后定稿。

## 1. 复现目标
- **repo 角色**：对打 baseline / 实验基座（baseline-survey clone 卡标，经 setup.json `repo_role` 透传）
- **论文**：<title / arxiv id>（基座模式：基座自报参考数字的出处——README / model zoo / 技术报告）
- **目标表格行**：Table X 第 N 行 + 该行的 setting（backbone / 输入尺寸 / schedule）（基座模式：哪个模型 @ 哪个 benchmark = 多少）
- **数据集 + split**：<dataset> / <val|test>（论文报的是哪个集）
- **metric 精确定义**：<如 mAP@[.5:.95] (pycocotools 官方 eval)>
- **论文数 + 容差 band**：<41.2> / band 来源（论文自报 std 优先，否则默认 band）

> 深度标尺：表格行钉死到"换一行 setting 就全错"的精度（trust-traps ⑤）；metric 写到能据此去源码核对的精度——`mAP` 不合格，`mAP@[.5:.95] (pycocotools)` 合格（trust-traps ①）。

## 2. idea 类型与分流建议
- **idea 类型**：training-free / 要重训（一句话依据）
- **训练规模估算**：dev_card_footprint 单步耗时 × 论文 iter ≈ <X 小时/天>
- **选定分流**：A / B / C + 理由；若 C，小 setting 用哪个（论文自报小 setting 优先）

> 深度标尺：分流理由要落到数字上（"开发卡 full ≈ 14h，训得动，走 B"），不是"感觉规模不大"。

## 3. 执行方案
- **eval 命令**：<来自 setup.json ready_commands，注明>
- **train 命令**：<同上>
- **checkpoint / config**：<路径 + 血缘预判（EMA? best/last?）>
- **预估时间**：eval <X> / train <X> / 多 seed 计划（≥2-3 seed 测 noise_floor）
- **预期产出分流产物**：runs/ 下会有哪几个 run-slug

## 4. 风险与地雷
- **确定要处理的**：<setup.json 标的语义风险 / 本 repo 已知坑（survey、issue）>
- **存疑待验证的**：<预判 trust-traps 命中点：metric 自实现？ckpt 血缘不明？协议含 TTA？>

> 深度标尺：地雷分两档，每档每条写"为什么觉得是雷 + 怎么验证"；写不出验证方法的地雷是没探索够，回 repo 再查。

## 5. 验证标准（可判定）
- **eval_判定 = reproduced 的条件**：<数字 + band，如 "official eval ≥ 40.7（41.2 − 0.5）">
- **training_判定 = 通过的条件**：<按分流写：B = full 训练数在 band 内 + ≥2-3 seed std 落 noise_floor；C = b 小 setting 对齐 + a 趋势吻合>
- **什么情况降级**：<开发卡 full 训不动 → 证据阶梯第 2 级；b+a 也不够 → 第 3 级组件级验证>
````

## 模板使用说明

- **先探索再开口**：spec 里的每个字段都应该有论文 / repo / setup.json 的出处，不在信息不足时写 spec 问用户。
- **可判定是硬要求**：第 5 节写不出具体数字条件，说明第 1 节的目标没钉死，回去补。
- **spec 审是确认点**：写完停下给用户审，确认才进 Step 3；用户改动的分歧点在 spec 里改定，不口头约定。
