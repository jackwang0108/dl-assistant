# 实验 报告.md 模板（experiments/<exp_id>/报告.md）

每项实验一份摘要，供用户阅读。均值 ± 标准差、各随机种子的结果和对照判据的判断都记录在 `results.json`。报告直接引用其中的数字，无需新增供程序读取的字段。

**写法要求**。报告限一页，如实记录结果、未达到预期的情况、异常和意外观察。论文中的论述由 `writing-paper` 负责。每项实验完成后，立即编写报告并更新 `results.json`。

**读者视角组织**——打开报告的人按这个顺序问问题：结果是什么 → 为什么跑它 → 怎么跑的 → 细节在哪。模板就按这个顺序排。

---

```markdown
# <exp_id>：<一句话标题>

> **TL;DR**：<用一句话说明做了什么>｜<主指标> <mean±std，n seeds>｜**success / failure / partial**（对照预先设定的判据）

## 为什么跑这个实验

## 怎么做的

## 结果与现象

## 产物
```

## 各节指引

### TL;DR（三行以内，结论先行）

前三行应说明实验内容、主要结果，以及对照预先设定判据的判断。

- 浅（不合格）：「消融模块 A，结果见下文。」。缺少主要结果和判断。
- 深（合格）：「Contribution 1 消融：去模块 A｜mIoU 74.2±0.3（n=3）vs 完整版 76.8±0.2｜**success**（掉 2.6 ≥ 预先设定的判据 1.5，A 是增益来源）。」

### 为什么跑这个实验

原样引用计划中的三个字段。`paper_claim` 说明支撑论文中的哪条论点，`purpose` 说明要回答的问题，`expected_signal` 记录预先设定的成功判据。说明 `depends_on` 记录的依赖和哪些实验依赖本实验。对 `decides_config` 实验，说明其结果决定了哪些实验的配置。

- 浅（不合格）：「消融模块 A。」。缺少消融目的和判据。
- 深（合格）：「验证 Contribution 1：模块 A 是否带来性能增益。预先设定的判据：去掉 A 后主指标掉 ≥ 1.5 视为有效。它是主表 exp-main-A 的对应的消融实验，与其共用同一冻结配置，以保证对比条件一致。」

### 怎么做的

**关键信息自包含**——读者不跳文件也该知道：config 相对 full config 的变动（一句话）、eval 协议（checkpoint 选择规则 val 选 best、eval split、seeds 列表）；main/comparison 实验必写 **fairness 怎么落实**（baseline 超参来源、数据集/预处理/training budget 是否对齐）和 **baseline 来源**（self-run 还是 official 引数）。备查资料（`configs/` 冻结副本、`scripts/` 启动脚本、`experiments/run-spec.json` 本实验条目——完整命令在其中）只作备查，不放正文。

- 浅（不合格）：「配置见 configs/，命令见 run-spec.json。」——读者必须跳文件才知道你干了什么。
- 深（合格）：「full config 仅去模块 A，其余与 exp-main-A 逐字节相同；val 选 best checkpoint、test 只评一次；seeds 0/1/2。完整 config 与命令见 configs/、scripts/。」

### 结果与现象

- **主结果**：mean ± std + n seeds + **各 seed 原始数**（照抄 `results.json`——便于判断结果波动是否主要来自某一个随机种子）；
- **signal 判定**：success / failure / partial + 对照预先设定的判据 的一句话理由。**否定信号如实写**；
- **和 reduced 趋势对照**：方向一致？量级合理？（如有反转，记录故障排查结论）；
- **意外观察**：跑出来的计划外现象（某类样本全错、某个 seed 训练动态异常……）——往往是论文 analysis 节或下个工作的素材，没有就写「无」；
- **异常备注**：resume 记录、失败 seed 及原因（n 不足必须写，判定降置信）。

**qualitative 实验**：本节换成产物描述——产了哪些图（`figures/` 里哪些文件）、用的哪个 checkpoint、选了哪些样本（怎么选的）、对应论文哪个图位（`output_to_paper`）。

### 产物

用一行列出产物路径：「产物齐全（check-run-artifacts.sh 过）：configs/ / scripts/ / runs/seed-{0,1,2}/（train.log、eval.log、metrics.json）/ results.json / meta.json。」**只在缺项时展开写缺哪个、为什么**——详细检查结果见脚本输出，无需逐项复述。
