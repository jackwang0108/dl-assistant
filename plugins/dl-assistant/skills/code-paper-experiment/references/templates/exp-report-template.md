# 实验 报告.md 模板（experiments/<exp_id>/报告.md）

每个实验一份，**人读**——你（用户）随时打开就能看明白这个实验。机读字段（mean±std / seed 明细 / signal 判定）在 `results.json`，本文件是它的「人读封面」：数字照抄 `results.json`，不另造机读字段。

**写法要求**：一页以内；陈述事实，不 storytelling（怎么叙述是 writing-paper 的事）；否定信号、异常、意外观察如实写。每跑完一个实验就和 `results.json` 一起增量写好，别攒到最后。

**读者视角组织**——打开报告的人按这个顺序问问题：结果是什么 → 为什么跑它 → 怎么跑的 → 细节在哪。模板就按这个顺序排。

---

```markdown
# <exp_id>：<一句话标题>

> **TL;DR**：<干了啥，一句话>｜<主指标> <mean±std，n seeds>｜**success / failure / partial**（对照预注册 bar）

## 为什么跑这个实验

## 怎么做的

## 结果与现象

## 产物
```

## 各节指引

### TL;DR（三行以内，结论先行）

读者只看这三行也该知道：这个实验干了什么、核心数字、对照预注册 bar 的判定。

- 浅（不合格）：「消融模块 A，结果见下文。」——零信息，读者还是得翻全文。
- 深（合格）：「Contribution 1 消融：去模块 A｜mIoU 74.2±0.3（n=3）vs 完整版 76.8±0.2｜**success**（掉 2.6 ≥ 预注册 bar 1.5，A 是增益来源）。」

### 为什么跑这个实验

两样：**plan 三样原样带**（paper_claim——支撑论文哪条 claim；purpose——回答什么问题；expected_signal——预注册 success bar）+ **批内位置**（depends_on 谁、谁依赖它；尤其 decides_config 实验：它的结果定了哪些实验的配置）。

- 浅（不合格）：「消融模块 A。」——只是名字复读，读者不知道为什么要消融、判据是什么。
- 深（合格）：「验证 Contribution 1：模块 A 是性能增益的来源而非装饰。预注册 bar：去掉 A 后主指标掉 ≥ 1.5 视为有效。它是主表 exp-main-A 的消融臂，与其共用同一冻结配置（否则对比被污染）。」

### 怎么做的

**关键信息自包含**——读者不跳文件也该知道：config 相对 full config 的变动（一句话）、eval 协议（checkpoint 选择规则 val 选 best、eval split、seeds 列表）；main/comparison 实验必写 **fairness 怎么落实**（baseline 超参来源、数据集/预处理/training budget 是否对齐）和 **baseline 来源**（self-run 还是 official 引数）。指针（`configs/` 冻结副本、`scripts/` 启动脚本、`experiments/run-spec.json` 本实验条目——完整命令在其中）只作备查，不放正文。

- 浅（不合格）：「配置见 configs/，命令见 run-spec.json。」——读者必须跳文件才知道你干了什么。
- 深（合格）：「full config 仅去模块 A，其余与 exp-main-A 逐字节相同；val 选 best checkpoint、test 只评一次；seeds 0/1/2。完整 config 与命令见 configs/、scripts/。」

### 结果与现象

- **主结果**：mean ± std + n seeds + **各 seed 原始数**（照抄 `results.json`——让人能看出方差是不是某一个 seed 撑起来的）；
- **signal 判定**：success / failure / partial + 对照预注册 bar 的一句话理由。**否定信号如实写**；
- **和 reduced 趋势对照**：方向一致？量级合理？（反转的，这里写查 bug 的结论）；
- **意外观察**：跑出来的计划外现象（某类样本全错、某个 seed 训练动态异常……）——往往是论文 analysis 节或下个工作的素材，没有就写「无」；
- **异常备注**：resume 记录、失败 seed 及原因（n 不足必须写，判定降置信）。

**qualitative 实验**：本节换成产物描述——产了哪些图（`figures/` 里哪些文件）、用的哪个 checkpoint、选了哪些样本（怎么选的）、对应论文哪个图位（`output_to_paper`）。

### 产物

一行指针：「产物齐全（check-run-artifacts.sh 过）：configs/ / scripts/ / runs/seed-{0,1,2}/（train.log、eval.log、metrics.json）/ results.json / meta.json。」**只在缺项时展开写缺哪个、为什么**——机器已逐项查过，人读报告不重复审计清单。
