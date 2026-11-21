# 训练动态诊断顺序（execution debug 用）

> 实现/smoke/full run 时训练不 work（loss NaN / 不收敛 / 指标纹丝不动）按这个**顺序**定位——前面的命中率远高于后面。
> 管的是"训练动态病态"（工程/优化层）；**机制 work 不 work**（方法假设对不对）归 iterate 分层诊断，不在这查。
> 边界：config 路径/兼容/ImportError 类普通工程 bug 直接修，不用走这流程；这流程管"能跑但不对劲"。
> 机制级 sanity（新方法接入后先验机制对不对）：用 `code-paper-reproduction/references/trust-traps.md` 的「组件级验证手册」（overfit one batch / verify loss @ init / input-independent baseline / 进网络前可视化 / 梯度依赖检查）——单一真相源在那，这里不复制。

## 0. 先 overfit 单 batch（一刀分两界）

用 1 个 batch 关 shuffle、关增强、多步迭代：

- **连 1 个 batch 都 overfit 不了** → **代码/数据有 bug**（前向断链、loss 没真算、标签错位、梯度没通），走 1-3 步查；
- **能 overfit**（loss 稳定降到 ~0）→ 代码链路对，问题在**优化/数据规模**，走 4-6 步查。

这一刀把"代码错"和"优化错"分开，省一半瞎试。

## 1. 查输入数据（静默炸弹高发区）

可视化/打印一个真实 batch：mean/std 对不对、标签和输入对没对位、augmentation 后分布有没有崩。预处理错不报错但全错（`code-project-setup/references/numeric-sanity.md` 同源）。

## 2. 查 loss 构成

分项打印 loss：哪一项是 NaN / 哪一项主导淹没了其他项。除零、log(0)、极端 logit 是常客。

## 3. 查数值稳定性（NaN/Inf 专项）

NaN/Inf 是最高频的训练病态，按这个顺序排：

1. **先判是不是精度问题**：换 **fp32 对照跑**（或关 AMP）——fp32 不炸就是混合精度溢出（fp16 尤其）。解法：换 bf16 / 调 loss scale / 降 lr，不是硬扛。
2. **定位第一个 NaN 出现的位置**：前向 hook 逐层打印激活量级（`code-reading/references/diagnostics.md` 手法 2），NaN 都是**从某一层开始**的——找到起点层，查那层的输入分布和运算（除零 / log(0) / exp 溢出 / softmax 极端 logit）。
3. **查梯度同步病态**：`grad_norm` 爆炸（>1e2）→ clip / 降 lr；消失（~0）→ 断链 / frozen 错 / requires_grad 没开。目标层（你改的那块）梯度要真的流到。
4. **加 epsilon / clamp 是语义微改**：防除零/溢出可以加，但**可能微改数值**——记进实现笔记，验收/复现对齐时盯它（CIP 的教训：这类改动能破坏严格相等）。

## 4. 查 lr / schedule

数量级扫（×0.1 / ×10 各试一个 short run）；warmup 有无、schedule 类型对不对。lr 是"能跑但不对"的头号优化层原因。

## 5. 查初始化 / 权重加载

strict 加载确认（`strict=False` 丢 key = 一半随机初始化，见 `code-paper-reproduction/references/trust-traps.md` ③）；新加模块的初始化（新层默认 init 和 baseline 的分布差太远会早期炸）。

## 6. 逐步放大，定位崩溃点

1 batch → 100 batch → reduced 全量，**哪一步开始崩就是哪层问题**：1 batch 能 overfit、100 batch 崩 → 数据多样性/增强；reduced 崩 → lr/schedule 相对规模不配。

> 连续失败 N 次（默认 3）走 SKILL 的卡死上报，不死磕。
