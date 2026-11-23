# 训练动态诊断顺序（execution debug 用）

> 实现、短时测试或全量训练时，若 loss 出现 NaN、训练不收敛或指标没有变化，按下面的顺序排查。
> 这里排查代码接入与优化过程。方法假设是否成立由 iterate 分析。
> 边界：config 路径/兼容/ImportError 类普通工程 bug 直接修，不用走这流程；这流程管"能跑但不对劲"。
> 实现机制的基础验证（新方法接入后先验机制对不对）：用 `code-paper-reproduction/references/trust-traps.md` 的「组件级验证手册」（overfit one batch / verify loss @ init / input-independent baseline / 进网络前可视化 / 梯度依赖检查）——单一真相源在那，这里不复制。

## 0. 先检查模型能否拟合单个批次

用 1 个 batch 训练多步，关闭数据打乱与增强：

- **连 1 个 batch 都 overfit 不了** → **代码/数据有 bug**（前向计算不完整、未实际计算损失、输入与标签不对应，或梯度未传到目标层），走 1-3 步查；
- **能 overfit**（loss 稳定降到 ~0）→ 代码链路对，问题在**优化/数据规模**，走 4-6 步查。

根据单个批次的拟合结果，优先排查代码和数据，或转到优化设置和数据规模。

## 1. 查输入数据（检查未报错的数据问题）

可视化或打印一个真实 batch，核对 mean/std、输入与标签是否一一对应，以及增强后的分布。错误的预处理可能在没有报错的情况下改变结果（`code-project-setup/references/numeric-sanity.md` 同源）。

## 2. 查 loss 构成

分项打印 loss：哪一项是 NaN / 哪一项量级远大于其他项。检查除零、log(0) 和极端 logit。

## 3. 查数值稳定性（NaN/Inf 专项）

出现 NaN 或 Inf 时，按以下顺序排查。

1. **先判是不是精度问题**：换 **fp32 对照跑**（或关 AMP）——fp32 下未出现 NaN 或 Inf 时，按混合精度溢出排查（fp16 尤其）。解法：换 bf16 / 调 loss scale / 降 lr，按原因处理。
2. **定位第一个 NaN 出现的位置**：前向 hook 逐层打印激活量级（`code-reading/references/diagnostics.md` 手法 2），NaN 都是**从某一层开始**的——找到起点层，查那层的输入分布和运算（除零 / log(0) / exp 溢出 / softmax 极端 logit）。
3. **检查梯度及其同步。** `grad_norm` 过大（>1e2）时尝试裁剪梯度或降低学习率。接近零（~0）时检查计算图是否中断、是否误冻结参数、requires_grad 是否启用，以及目标层能否收到梯度。
4. **加 epsilon / clamp 是语义微改**：防除零/溢出可以加，但**可能微改数值**——记进实现笔记，验收/复现对齐时盯它（CIP 的教训：这类改动能破坏严格相等）。

## 4. 查 lr / schedule

数量级扫（×0.1 / ×10 各试一个 short run）；warmup 有无、schedule 类型对不对。lr 是"能跑但不对"的头号优化层原因。

## 5. 查初始化 / 权重加载

strict 加载确认（`strict=False` 丢 key = 一半随机初始化，见 `code-paper-reproduction/references/trust-traps.md` ③）；新加模块的初始化（新层默认 init 和 baseline 的分布差太远会早期炸）。

## 6. 逐步放大，找出训练开始失败的规模

按 1 batch、100 batch、完整 reduced 配置的顺序扩大测试。能拟合 1 batch 但在 100 batch 时失败，先查数据多样性和增强。完整 reduced 配置失败时，检查学习率和训练计划是否适合该规模。

> 连续失败 N 次（默认 3）时，按 SKILL 中的规则向用户报告，再由用户决定下一步。
