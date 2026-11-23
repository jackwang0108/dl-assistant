# 复现策略、容差判据和证据不足时的处理

> SKILL 的决策树决定使用哪条分支。本文件说明各分支如何运行、如何用容差和多个随机种子判定差异，以及无法完成复现时如何记录验证范围。
> 可信度陷阱排查见 `trust-traps.md`（①-⑦ + 组件级验证手册），reduced 配置见 `reduced-setting.md`。
>
> 所有分支先用官方 checkpoint 核对推理、权重加载与评测流程。是否继续验证训练取决于构想类型和训练规模。

## 所有分支先用官方 checkpoint 跑评测

用 official checkpoint 跑推理（eval 命令从 `setup.json` 的 ready_commands 拿），对齐论文数：

- **对齐了** → 推理链对，要重训时训出的 gap 能干净归因到训练链（查 trust-traps ⑦）
- **不对齐** → 推理链本身坏了，按 trust-traps ①-⑥ 排（metric 定义 / split / checkpoint 的训练来源与版本 / 协议 / 表格行 / 噪声），修推理链再往下
- 落 `eval_判定`：reproduced / partially_reproduced / not_reproduced_diagnosable / not_trustworthy

长 eval 走 tmux detach 托管（见 `dl-assistant/references/long-run-ops.md`），不用 `run_in_background`。

---

## 分流 A：training-free（只验推理链）

- idea 只改推理 / 后处理，不重训 → 所有分支都要先做的评测验证（official eval）做完即结论
- `training_判定 = NA`，`trustworthy_for_delta` 看 `eval_判定`
- 打 tag `eval-aligned` 后即可交付（跳过 `training-reproduced`）

## 分流 B：要重训 · 规模不大（开发卡 full 训得动）

- 开发卡 full training，完整对齐论文数
- 推理链已校准，训练出的 gap 干净归因训练链 → 查 trust-traps ⑦（BN / loss 归约 / 等效 batch / lr 缩放 / 增强 / warmup-EMA）
- **默认 ≥2-3 个 seed**（full 太贵时至少 2 个并写明）——既是判差异是否超出随机波动的依据，也是给 execution 的 `noise_floor` 契约字段
- 落 `training_判定`：full_reproduced / partial / not_trustworthy
- 打 tag `training-reproduced`

## 分流 C：要重训 · 规模大（开发卡 full 训不动）

**两个都做，缺一不可**：

- **(b) 缩规模等价复现**：用论文报的小 setting，开发卡完整训到它的论文数 ，核对训练结果能否复现该配置的报告值
- **(a) 大规模趋势外推**：大规模 short-schedule，验 loss 曲线形状 + 早期 metric 落论文外推线上 ，用于核对大规模训练的早期趋势
- 单独 a 可能趋势对但终点偏；单独 b 可能小 setting 和大规模训练链不完全同路——**两个一起才敢说训练链可信**
- (b) 的小 setting 同样 ≥2-3 seed（setting 小、便宜，不该省），落 `noise_floor`
- full 规模完整对齐 → 标 `blocked-需运行卡`（归运行服务器）
- 落 `training_判定`：b_plus_a_confirmed / partial / blocked_需运行卡 / not_trustworthy
- 打 tag `training-reproduced`（b + a 确认后）

---

## 无法完成 b 和 a 时的补充验证

SKILL「各项验证能支持的结论」定了 5 级框架，本节讲 3-5 级怎么操作。**前提：每降一级，`reproduction.json` 的 `evidence_strength` 降一档，并写清下游使用约束。**

### 第 3 级：组件级证据（不跑完整训练，验训练链语义）

按 `trust-traps.md`「组件级验证手册」逐项过：overfit 单批 / loss 初值 / input-independent baseline / 进网络前可视化 / 梯度依赖检查。**全过 = 训练链语义正确，只是数值没验到**——`training_判定` 落 `partial`，`evidence_strength: low`，报告里逐项留证据（命令 + 观察到的数值/图）。

### 第 4 级：外部旁证

- 查 repo issue / paperswithcode / 第三方复现博客：多人复现到类似数 → 训练链可信的 prior 高；复现失败潮 → 在 `known_pitfalls` 记一笔并降低结论强度。
- 官方若放出多个 checkpoint（不同 seed / 不同 schedule），用其间 variance 校准噪声 band——比默认 band 表更贴合本任务。

### 第 5 级：记录已验证项、未验证项和使用限制

- `reproduction.json` 记 `full_scale_alignment: deferred_to_running_server`——由运行服务器上的 `code-paper-experiment` 完成全量数值验证。
- 报告里写清**哪些组件验过、哪些没验过**（组件级清单逐项打勾），execution 在上面的 delta 带着这个风险认知，重大结论回 full 验证。

---

## 容差与多 seed 判据（判差异是否超出随机波动）

容差范围表见 **`trust-traps.md` 的「容差范围」节**（论文自报 std 优先，否则按任务类型默认：分类 ±0.3% / 检测分割 ±0.5 mAP/mIoU 等）。判据流程：

1. **单 seed，gap 在容差范围内** → 判对齐（倾向噪声），落 reproduced
2. **单 seed，gap 超出容差范围但 < 2×band** → 跑 **3 个 seed** 看 std：
   - 论文数落在 [mean − std, mean + std] 内 → 对齐（噪声）
   - 落在区间外 → 真差，查 trust-traps
3. **单 seed，gap ≥ 2×band** → 多半真差，直接查 trust-traps（不必先跑多 seed）
4. **卡数 / batch 不同导致的系统性差** → 记"setting 差异"（可解释），非"不可信"

> **eval 侧**多 seed 不是默认跑——只在 gap 超出容差范围但不大时跑 3 个定 std，盲目多 seed 烧算力。
> **training 侧相反**——分流 B/C 默认 ≥2-3 seed：`noise_floor` 是 execution keep/discard 判据的契约字段，这笔钱不能省（见 SKILL「核心纪律 · 面向 method 迭代的交付纪律」）。
> 对照 `setup.json` 的 `reproducibility` 块（seed / cudnn 设在哪、固没固定）：determinism 没固定时，band 内 gap 大概率噪声。

---

## 不要做的事

- 不要为追论文数做大规模超参搜索 —— 复现不是调参。
- 不要把 official checkpoint eval 当 training-free 专属 —— 所有分支都要先用官方权重完成评测验证。
- 不要规模大时只做 a 或只做 b —— 同时核对小规模完整训练结果和大规模早期趋势。
- 不要把单 seed 小 gap 当真差 —— 先按上面判据走（band 内倾向噪声）。
- 不要训练侧只跑单 seed 就交付 —— `noise_floor` 是契约字段，分流 B/C 默认 ≥2-3 seed。
- 不要把"训不动"模糊成"应该没问题" —— 沿各项验证能支持的结论降级，每级显式标证据强度。
- 不要为压迭代预算压缩训练计划 —— 停在未收敛点会系统性错误放弃"学得慢但终点高"的改动；预算靠缩数据凑（模型容量不许动——动容量 = 改 baseline 语义；见 `reduced-setting.md`）。
- 不要在 reproduction 阶段做 idea 实验 —— reduced 只验有效性（跑 baseline），不是试 idea。
