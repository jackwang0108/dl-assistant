# Experiment Writing — Setup（实验章·不依赖真实结果的部分）

`writing-paper` 写实验章节 setup 部分的规则。Experiment 是三位一体的**「证明」面**——针对总论点设计实验，证明方法满足它。每个实验都要能回扣到总论点或子论点（contribution）。

> 本文件管**不依赖真实结果就能写**的部分：总 setup（数据集 / baseline / metric / 实现 / 训练细节）+ 每个实验的目的与设置，**不写结果/分析**——结果/分析见 `experiment-writing-results.md`，由 **ingest-results** 在数据批到了之后写。本文件通常由 **write-section** 写。setup 源读 `_draft/experiments/plan-vN.json`（实验计划包机读区，版本化递增）。
> 实验章为什么按数据可用性分两块写、各自职责见 `SKILL.md`。

## 从总论点拆可验证维度（先对齐再写）

起点是**总论点**（`blueprint.md` 的 paper_claim），不是散的 contribution。拆成可验证维度，每个维度一组实验：

| 维度 | 回答什么 | 挂 claim | 实验 |
|---|---|---|---|
| 主性能 | 方法整体满足总论点吗 | C1 | 主表 Table 1 |
| 组件必要性 | 各核心改动 part 要不要 | C2,C3 | 消融 Table 2 |
| 机制理解 | 方法为什么/怎么/边界 | 分析子论点 | 分析图/表 |

- 没有证据的维度不能在实验章节强说；不服务任何维度的实验 → 移 appendix；负结果可保留（说明边界/诚实）；缺关键实验 → 产**实验计划包**触发 `code-paper-experiment` 补。

## 默认结构 = goal 1（组织）+ goal 2（Setup，含训练细节）

实验章 5 个 goal 按**数据可用性**切两块：**本文件写 goal 1+2 + 每实验目的/设置**（不依赖真实结果就能写）；goal 3/4/5 见 `experiment-writing-results.md`，数据批到了之后写。

| goal | 作者在想什么 | 何时写 |
|---|---|---|
| 1. 组织实验 | 怎么把实验对齐到总论点（RQ/维度/路线图） | 数据可用前（write-section） |
| 2. Setup | 数据/baseline/metric/实现怎么写清楚又公平 | 数据可用前（write-section） |
| 3. 报主结果 | 数字怎么报可信（防过度宣称） | 数据批到后（ingest-results） |
| 4. 消融 | 怎么证明组件必要性（防戏剧化） | 数据批到后（ingest-results） |
| 5. 分析 | 怎么解释机制为什么/边界 | 数据批到后（ingest-results） |

**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。** 篇幅紧时优先：setup、主性能、核心消融、一个最有解释力的分析。

## 逐 goal 写作技法

### goal 1：组织实验 —— 怎么把实验对齐到总论点

**选择逻辑**：怎么给读者一张实验地图？
- 多维度 → RQ 驱动整章（RQ1/RQ2...）
- 多组件 → 消融小节按 `Effect of X` 平行命名（与方法模块一一对应）
- 复杂 → 章首路线图（`We first... Next... Finally... (Sec. X.Y)`）

- ✓ **do：用研究问题（RQ）驱动整章**——开头把要回答的 RQ 编号列出，后续每个子节对应一个 RQ，让每个实验都回答一个预设的可证伪问题。
- ✓ **do：章首路线图预告各子节顺序与目的**（`We evaluate X through: (1) comparison..., (2) ablation..., (3) analysis...`），评估维度编号与子节一一对应。
- ✓ **do：子节标题写成问句或加粗论断句**（`MoR improves retrieval performance.` / `How well do ...?`），让目录即 take-away。

### goal 2：Setup —— 数据/baseline/metric/实现怎么写清楚又公平

**选择逻辑**：怎么让 setup 可复现又显公平？
- 密集信息 → 加粗 run-in 标签切分（`Datasets./Baselines./Metrics./Implementation Details.`）
- 公平性质疑 → `For fair comparison` 前置声明对齐了什么

- ✓ **do：加粗 run-in 标签切分 setup**（`Datasets. NAVSIM is a large-scale...`），把数据/基线/指标/实现物理隔离成可扫读小段。
- ✓ **do：`For fair comparison` 主动声明对齐了哪些变量**（等量采样、官方权重、统一 backbone/算力、沿用前作协议），把"比较是否公平"预先堵死。
- ✓ **do：数据集/baseline 用统一模板逐条列举**（`名称[ref]: 任务+规模(样本/类别)+选择理由` / baseline 按范式分组+角色标签），让选型意图与覆盖面可审查。
- ✓ **do：实现细节一次性给全数值**（GPU 型号数量、optimizer、lr、batch、epoch、耗时），`Following [前作]` 挂靠协议默认可信化。

### 训练细节（reviewer 复现 checklist）

超参 / optimizer / lr schedule / 训练时长（epoch、wall-clock）/ 实现细节数值——**从 Method 挪出来，统一放这里**（Method 只讲方法本身，见 `method-writing.md` 的「不收什么」）。这些不是点缀：它们是 **reviewer 复现 checklist 的一部分**，reviewer 判断"给我这份论文我能不能复现"时逐条对的就是这块。写法沿用 goal 2：一次性给全数值（GPU 型号数量、optimizer + lr + schedule、batch、epoch、耗时），`Following [前作]` 挂靠协议的部分可压缩但要点名。细节多到一个段落装不下 → 正文给关键值、全表进 appendix，指针写清楚。

## 每个实验的「目的 + 设置」skeleton

write-section 写到每个实验子节时，先写它的**目的 + 设置**（结果/分析留空待数据批回填）：

- **目的**：答哪个 RQ？支撑哪个 claim（C-ID）？
- **设置**：这个实验特有的配置（复用 goal 2 总 setup，只写差异：特定数据子集/baseline 子集/metric/超参）。
- **占位**：留一句 `> 结果与分析待 ingest-results 按 CPE 报告写`，结构先搭好、内容等数据。

## 全节自查（反模式信号清单 · setup 相关）

写完逐条勾：

- [ ] baseline 是否够新且公平？metric 是否领域标准？
- [ ] 主实验覆盖 ≥2 setting？三必须维度（主性能/消融/分析）都有规划？
- [ ] 涉及效率是否报对比？显著性/方差/多 seed 是否说明？
- [ ] data leakage 风险（训练/测试污染）是否排除？
- [ ] 每个实验是否回扣 RQ / claim（C-ID）？

> 结果/分析部分的反模式（全胜宣言 / trade-off 否认 / 戏剧化渲染 / 外推 / 消融戏剧叙事）见 `experiment-writing-results.md`。

## 与全文协同（三位一体）

- 每个实验回扣总论点的一个维度（ref C-ID）。
- 消融组件名 = Method 的核心 part = Introduction 的 named-abstraction（术语全篇一致）。

## 文风 lint

写完按句段、字词和常见生成式写作问题三类写作要求 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# 实验章 setup 写作计划（数据可用前）
## 1. 总论点 → 可验证维度拆解（RQ）
## 2. 总 Setup（数据/baseline/metric/实现/训练细节/fairness）
## 3. 每个实验 | 目的(RQ/claim) | 设置 | （结果待 ingest-results 占位）|
## 4. setup 自查逐条勾
```
