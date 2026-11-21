# Reduced 训练配置：快速迭代代理

> **命名约定**：分钟级的链路冒烟叫 **smoke run**（归 `code-project-setup`，验"链路通不通"）；本文的**小时级**迭代代理叫 **reduced setting**（归 `code-paper-reproduction`，验"改动方向对不对"）——两个词不混用。

## 问题

中期的主战场是 method 迭代（`code-idea-execution`），而迭代要求**每一轮 run 控制在可接受的时间内（单轮迭代预算：默认 2-3h，上限 4h）**——每次改动都跑 full 规模（几天）不现实。需要一个**快速迭代代理**：

- **单轮 ≤ 迭代预算**，保持快速试错节奏
- **趋势保真**：改动方向要和 full 规模一致（不要求数值精确）
- **规模外推可预测**：reduced 与 full 之间的 scaling 趋势经过实测验证，不靠信仰
- **有可信 full baseline 托底**：reduced 上的改动只是方向指示，最终验证回 full

## 核心原理：Scaling Law（要验证，不假设）

Reduced 配置的有效性建立在深度学习的 scaling law 之上：**在合理的缩减范围内，模型性能、训练动态、方法改进的相对趋势在不同规模间保持一致**。

- 训练数据量、训练步数、模型大小之间存在可预测的幂律关系
- 方法改进在小规模上的相对提升（如 +2%）往往在大规模上也有类似幅度的提升
- 超参、架构改动对训练曲线的影响（收敛速度、稳定性）在不同规模间趋势一致

但**单点 reduced 无法验证 scaling law 在本任务上成立**——只跑一个数据点，"reduced 的趋势能外推到 full"是信仰不是证据。所以本 skill 的 reduced 交付不是"一个配置"，而是"**一个工作点 + 一条 scaling 验证链**"：沿数据轴从最小到可接受规模跑一串点、拟合、外推预测一个没训过的规模、实跑验证——预测命中，才敢在 reduced 上放心迭代（见「有效性验证」）。

## 设计

Reduced 配置是在 **training 可信度已验证** 之后引入的快速实验代理。它不替代 full 验证，而是在 baseline 已可信的基础上，为 idea 迭代提供一个"几小时 vs 几天"的加速层。

**默认必做**：要重训的 idea 且 full 训练超迭代预算时，reduced 不是可选项——没有它，execution 就没有迭代载体。豁免情形见「何时不适合 Reduced」，豁免时显式告知用户迭代节奏后果，由用户决定迭代方式。

### 核心原则

1. **Reduced 是加速层，不是替代层**
   - Baseline 的 training 可信度必须先验证（分流 B 的 full / 分流 C 的 b+a）
   - Reduced 继承已验证的可信度，只负责快速探索改动方向
   - 有希望的方向最终要回 full 规模验证

2. **趋势保真 > 数值精确**
   - Reduced 上 +1.2 个点不保证 full 上也 +1.2
   - 但如果 reduced 上稳定 +X%，full 上大概率同向（可能幅度不同）
   - 反之，reduced 上稳定 -X% 或持平，也是有效信号

3. **单轮迭代预算：默认 2-3h，上限 4h**
   - 预算靠**数据轴**一条轴凑（见「缩减策略」——模型轴被显式排除）
   - 数据轴压到底还超预算 → **不擅自缩训练计划**，把取舍摆给用户拍板（更慢的迭代 vs 缩计划误杀慢收敛改动的风险）

4. **不缩训练计划**
   - 原文给的训练计划大概率是能收敛的；缩了数据之后，同样的计划依然能收敛
   - **压缩 epoch 会让训练停在未收敛点**——有的改动学得慢但最终性能更高，在未收敛点比较会把这类改动系统性误杀。中期迭代最怕的就是这种误判
   - 保持原 epoch 计划（epoch 数、lr schedule 形状、warmup 位置都不动），让每个改动都有机会收敛到自己的终点

### 缩减策略：只有数据轴（模型容量不许动）

**模型轴被显式排除**，两条理由：

1. **不需要**：中期 follow 的工作多为高校 8 卡级规模（8×4090 / 8×A100 做得完的那种），模型本身放得下——只缩数据就足以把单轮压进预算。
2. **不可行**：换小模型会让对标的 baseline 直接不成立——容量一变，官方 config / 权重 / 论文数字全部对不上；强行要跑就得改 baseline 的语义，可比性当场报废。不用讨论"方法对容量敏不敏感"，这条轴压根不存在。

因此缩减只有一条轴：

- **数据集等比缩放**：所有用到的数据集**按同一比例**均匀采样缩，固定 seed、保目录结构 / 标注格式 / 类别分布——多数据集混训各自同比例，别让某个数据集被缩没。
- **档位不按百分比拍，按 wall-clock 标定**：先跑一小段训练、等吞吐稳定后实测吞吐量，换算各数据比例的单轮用时，**按目标用时选档**——百分比是标定的结果，用时才是约束。

**训练计划保持原文**：epoch 数、lr schedule 形状、warmup 位置按 epoch 不动。两个工程注意：

- **iteration 锚定的配置项要换算成 epoch 等效位置**——数据缩到 30% 后每 epoch 的 iter 数也缩到 30%，warmup iters / 按 iter 的衰减点不换算就错位（lr decay 锚定的坑见 `trust-traps.md` ⑦）。
- **EMA 按 iter 的衰减窗口按 iter 数等比调整**，保持 EMA 覆盖训练全程的同一比例。

**不改输入分布和优化统计**——降分辨率（改感受野 / 小目标 / anchor 尺度）和减 batch（动 BN 统计）都会破坏趋势保真，**不作为缩减手段**；显存不够时优先 grad accumulation 凑等效 batch（BN 统计仍按单卡真实 batch 算）。

选择缩减档位时优先保持：
- 训练收敛的稳定性（不要缩到完全训不稳）
- 和 full 配置的可比性（优化器类型、增强策略、loss 完全一致）
- 单轮实验压进迭代预算

### 在 Reproduction 里的位置

双轨可信度之后的**默认第三产出**（要重训且 full 超迭代预算时）：

```
spec 审：复现目标 + 分流确认
  ↓
agent 执行复现 → 落双轨可信度判定 ✓
  ↓
要重训且 full 训练 > 迭代预算？→ 默认建 reduced 配置
  ↓
实测吞吐（短训练等稳定后测）→ 按 wall-clock 布 sweep 点
  ↓ 用户拍板 sweep 方案（点数 / 各点用时 / 留验点）
agent 跑 sweep 各点 baseline → 小点拟合 → 外推预测留验点 → 实跑验证
  ↓
趋势保真对照（三选一 + 兜底）+ 标定噪声区间
  ↓
产出 Reproduction 交付目录（含 reduced 设置 + scale_sweep）
```

**分流 C 的接力**：复现走了分流 C（full 训不动）时，若 (b) 的小 setting 只缩了数据（模型与 full 一致），它就是 sweep 的现成已验证点，往往只需补齐中间点 + 留验点；若 (b) 用的是论文自报的小模型 setting（容量变了），它不能进 sweep（轴不同），但可作为 scaling 旁证写进报告。

### 有效性验证：scaling sweep（主）+ 趋势保真对照（辅）

**主验证 = scaling sweep**——回答"从 reduced 外推到更大规模靠不靠谱"：

1. **布点**：沿数据轴按 wall-clock 取 3-4 个点，从最小（趋势仍有意义：loss 正常收敛、metric 脱离随机档）到可接受的最大规模。**具体用时不写死**——按实测吞吐标定；**最大点不超过 4h**（中期快速迭代能接受的极限），少数情况经用户拍板可到 12h，再长不做。
2. **各点跑 baseline**（固定 seed；小点便宜大点贵，sweep 方案用户拍板后才跑）。
3. **拟合 + 留验**：用较小的点拟合 log-log 幂律 → **外推预测一个没训过的更大规模点（留验点）的 metric** → 实跑留验点 → 预测误差在**跑前写死的容差**内 → scaling 成立，`scale_sweep.verdict: scaling_law_confirmed`。
4. **不命中 → 显式降级**（`verdict: degraded`）：写清失配形态（平台期 / 拐点 / 噪声过大），reduced 只用于排方向、重大结论回 full 验证——不把"外推失败"模糊成"应该没问题"。

**工作点选择**：日常迭代载体 = sweep 中 ≤ 迭代预算的**最大已验证点**（规模越大趋势越贴近 full，能压进预算就选大的），其 baseline 数字落 `baseline_result`。

**辅验证 = 趋势保真对照（三选一 + 兜底）**——sweep 验的是"规模外推可预测"，而 reduced 的真实用途是"改动的 delta 方向保真"，两者正交，这层不省：

1. **baseline 自身对照**：reduced 工作点和 full 的绝对性能比例合理
   - 示例：reduced 72.3 AP vs full 78.5 AP，比例 92%，gap 合理
2. **已知消融对照**：论文消融实验在 reduced 上 delta 方向一致
   - 示例：论文报 "-backbone: -2.1 AP"，reduced 上跑这个消融得 -1.8 AP（同向）
   - **这条最重要**——它直接验"方法改动的趋势"在缩减后是否保真，正是 reduced 的用途
3. **简单 idea 试探**：跑一个简单 baseline 变体，看 delta 符号是否一致
   - 示例：lr × 1.5，reduced 和 full 上都是 -0.x AP（同向）
4. **兜底（无消融无对照可用时）**：机制 sanity + 量级检查——reduced 训练 loss 正常下降、eval metric 量级与 full 同档（不是数量级偏离）、趋势曲线形状与 full 早期一致。三条都过则可用，但**显式标注该 reduced 配置为「弱证据」**（`validity_check.confidence: low`），下游 execution 用它只排方向、重大决策回 full 验证。

### 噪声标定：reduced 上多小的 delta 是信号

有效性验证回答"reduced 能不能用"，噪声标定回答"reduced 上多小的 delta 算信号"——这是 execution 在 reduced 上做 keep/discard 的判据，**必须随 reduced 配置一起交付**：

- **多 seed 测底线**：reduced 工作点便宜，baseline 至少跑 2-3 个 seed，std 直接落 `noise_floor`。
- **已知消融标定**：论文报的已知消融（趋势保真对照第 2 条用的那个）在 reduced 上的 delta 幅度是现成标尺——如论文消融 -2.1 AP、reduced 上 -1.8 AP，则 reduced 上 ±0.4 以内大概率是噪声。
- 标定结论写进 `reduced_setting.noise_floor`（含标定依据），execution 在 reduced 上 delta < 2×std 时不可判，回 full 或多 seed 再判。

### Workflow 集成

**Reproduction 阶段**（本 skill）完整闭环：
- 验证 baseline 的 training 可信度 ✓
- 产出可信的 baseline checkpoint 和 training command ✓
- 要重训且 full 超迭代预算 → 默认建 reduced：实测吞吐 → wall-clock 布点（用户拍板）→ 跑 sweep + 留验点验证 → 趋势保真对照 + 标定噪声 → 写入交付目录
- **交付给 execution 的是 ready-to-use 的 reduced 配置 + 已验证的 scaling 链**，不是建议

**Idea Execution 阶段**（`code-idea-execution`）直接消费：
- 读取 Reproduction 交付目录的 `reduced_setting` 块
- 有 reduced 配置则直接用于快速试错，keep/discard 判据用 `noise_floor`
- `scale_sweep.verdict: degraded` 时只排方向，重大结论回 full
- 有希望的方向回 full 规模验证

### 交付格式

在 `reproduction.json` 加 `reduced_setting` 块：

```json
"reduced_setting": {
  "enabled": true,
  "scale_method": {
    "data": "各数据集等比采样（seed=42 固定抽样；目录/格式/分布一致；档位按 wall-clock 标定，见 scale_sweep）",
    "schedule": "保持原文 100 epoch 计划（warmup/衰减点 epoch 位置不动；iteration 锚定项已换算，EMA 窗口按 iter 数等比调）"
  },
  "baseline_result": { "metric": "AP", "value": 72.3, "std": 0.2 },
  "scale_sweep": {
    "axis": "data（唯一缩减轴，模型容量不动）",
    "points": [
      { "data": "3%", "wall_clock": "12min", "value": 61.2 },
      { "data": "10%", "wall_clock": "40min", "value": 67.8 },
      { "data": "30%", "wall_clock": "2.5h", "value": 72.3 }
    ],
    "fit": "log-log 幂律（前 3 点拟合）",
    "holdout": { "data": "60%", "wall_clock": "4h", "predicted": 74.8, "actual": 74.5, "tolerance": "±0.5（跑前写死）", "hit": true },
    "verdict": "scaling_law_confirmed"
  },
  "noise_floor": {
    "metric": "AP",
    "std": 0.2,
    "calibration": "论文消融 -backbone 在 reduced 上 -1.8 AP（同向）；±0.4 以内视为噪声"
  },
  "config": "configs/faster_rcnn_r50_fpn_1x_coco_reduced.py",
  "command": "bash scripts/train_reduced.sh",
  "footprint": { "time": "2.5h", "gpu_memory": "10GB", "disk": "5GB" },
  "validity_check": {
    "method": "ablation_contrast",
    "evidence": "论文消融 -backbone 在 reduced 上 -1.8 AP，方向一致；reduced 72.3 AP vs full 78.5 AP",
    "confidence": "medium"
  }
}
```

字段说明（json 写不下注释，统一在这里）：

- `scale_method`：怎么缩的——`data` 轴的标定方式 + `schedule` 保持原文的确认（含 iteration 锚定项换算说明）。后期回全量跑（CPE full-scale）的依据。**没有 `model` 字段——模型容量不许动**（动容量 = 改 baseline 语义）。
- `baseline_result`：工作点（日常迭代载体）的 baseline 数字；`std` 多 seed 才填。
- `scale_sweep`：scaling 验证链——`points` 各点的数据比例 / wall-clock / metric 值；`fit` 拟合方式；`holdout` 留验点的预测 vs 实测 + 跑前写死的容差；`verdict` ∈ `scaling_law_confirmed` / `degraded`（degraded 时 execution 只排方向、重大结论回 full）。
- `noise_floor.calibration`：噪声区间的标定依据（多 seed std + 已知消融幅度），execution 的 keep/discard 判据。
- `validity_check.method`：`baseline_self_contrast` / `ablation_contrast`（优先）/ `simple_idea_probe` / `mechanism_sanity`（弱证据兜底）。
- `validity_check.confidence`：`low` / `medium` / `high`；`low` 时 execution 只用它排方向，重大决策回 full。

## 何时不适合 Reduced

- **训练够快的任务**（full 单轮本就在迭代预算内）：不需要代理，直接在 full 上迭代
- **training-free 的 idea**：不重训，迭代代理无意义
- **高度非线性的任务**（RL、对抗训练）：缩减后趋势可能失真
- **数据轴压到底仍超预算**（数据缩到趋势失真的下限还超）：不擅自缩训练计划，把取舍摆给用户拍板
- **最终投稿阶段**：此时应该全上 full 规模，不再用 reduced

命中「不适合」时：显式告知用户迭代节奏后果（每轮要多久），由用户决定迭代方式——不静默降级。

## 与其他概念的区别

| 概念 | 目的 | 时机 | 可信度要求 |
|-----|------|------|-----------|
| **缩规模等价复现（b）** | 验证训练链在开发卡上跑通 | Reproduction 阶段（训练链未验证） | 需同步做 full 规模趋势外推（a）互证 |
| **Reduced 配置** | 加速 idea 迭代（单轮 ≤ 迭代预算） | Reproduction 阶段（训练链已可信后） | 继承已验证的 baseline 可信度 + scaling sweep 实证外推可预测 |
| **smoke run（CPS）** | 验证链路能跑通、数机械上合理 | Setup 阶段（环境就绪验证） | 不对照论文、不验趋势，分钟级 |

**不要混淆**：
- 缩规模等价复现（b）是在**不确定训练链能否跑通**时的诊断手段，必须搭配趋势外推（a）互证才能判可信；它的小 setting 若只缩了数据，则是 sweep 的现成已验证点（接力见上）
- Reduced 配置是在**训练链已可信**后的工程加速，目的是快速试错而非验证可信度——但它的有效性本身要靠 scaling sweep 实证，不靠 scaling law 信仰
- smoke run 是 setup 的就绪验证，既不验可信度也不服务迭代——三个概念的时间尺度（分钟 / 小时 / 天）和目的完全不同
