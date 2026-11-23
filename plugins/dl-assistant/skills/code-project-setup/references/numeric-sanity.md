# 数值正确性检查（numeric-sanity）

> 三层验证都要达到各自的通过条件。下面列出需要检查的数值、异常表现和处理方式。

## 为什么"跑通"不等于"跑对"

命令未报错时，程序也可能没有加载预期的权重、使用了不正确的设备映射，或采用了错误的预处理。以下现象需要在准备阶段排查。

| 问题 | 可观察到的现象 | 对结果的影响 |
| --- | --- | --- |
| checkpoint 只加载了部分权重 | `load_state_dict(strict=False)` 允许权重键缺失或多出，调用仍可能完成 | 未加载的层可能仍使用初始化权重，评测结果不可信 |
| device map 错 | 能跑，慢 | 部分张量在 CPU、部分在 GPU，结果可能对但极慢；或实际使用的显卡与预期不一致 |
| 预处理 mean/std 错 | forward 正常出数 | 输入分布偏移，输出全错但形状对 |
| NaN 传播 | loss 打印出来是 `nan`，训练"在跑" | 学习率/初始化/数据问题，训练继续执行也不会消除 NaN |
| 评测指标恰好为零或满分 | eval metric=0.0 或 =1.0 | 可能未实际加载数据、模型总预测同一类或存在标签泄漏 |

每一层都按下面的判据检查异常表现。

## Layer 1（import/config）：轻量数值正确性检查

import 成功后确认 PyTorch、运行时和编译型算子使用的 CUDA 版本兼容。

```python
import torch
assert torch.cuda.is_available(), "CUDA 不可用——驱动/torch 装错"
print(torch.cuda.get_device_name(0))            # 确认看到的是预期的卡（A100）
print(torch.__version__, torch.version.cuda)    # 与 nvcc 对齐（详见 compile-deps.md）
# 若有编译型算子，import 它并跑一次最小调用，确认不是 undefined symbol
```

红线：`is_available()` 为 False、看到的卡不对、编译算子 import 报 undefined symbol → 回 `compile-deps.md`。

## Layer 2（synthetic smoke）：关键数值正确性检查

运行 smoke script 调用真实组件后，显式检查并断言下列数值条件。

```python
# forward 输出
out = model(dummy_batch)
assert torch.isfinite(out).all(), "输出含 NaN/Inf —— 初始化或前向有问题"
assert out.abs().sum() > 0, "输出全零 —— 权重没加载 / 前向断链"
assert out.shape == expected_shape, f"形状不符：{out.shape} vs {expected_shape}"

# loss
loss = criterion(out, dummy_target)
assert torch.isfinite(loss), "loss 是 NaN/Inf"
assert loss.item() > 0, "loss 恰为 0 —— target 退化 / loss 没真算"
print(f"smoke loss = {loss.item():.4f}")   # 人工瞄一眼量级是否合理（交叉熵初始 ~ln(类别数)）

# backward：梯度真的流动
loss.backward()
grad_norm = sum(p.grad.abs().sum() for p in model.parameters() if p.grad is not None)
assert grad_norm > 0, "梯度全零 —— 计算图断了 / requires_grad 没开"
```

> **量级直觉**（瞄一眼用，不强卡）：N 类分类交叉熵初始 loss 约 `ln(N)`（10 类 ≈ 2.3）；
> 检测/分割的初始 loss 看 repo 文档预期。明显偏离（如 1e6 或 1e-8）是信号。

## Layer 3（官方命令 smoke run）：强数值正确性检查

smoke 真实数据跑几步/一小轮后：

- **损失呈下降趋势**：smoke train 几步内 loss 应有下降趋势（不是上涨、不是纹丝不动、不是 NaN）。
- **评测指标数值合理**：tiny subset eval 的 metric **> 0 且已排除异常满分**。
  - `metric == 0.0` → 数据没真加载 / 预测全错 / 标签对不上，**不是**"小子集太难"就能搪塞的。
  - `metric == 1.0`（或恰好满分）→ 标签泄漏 / 评估了训练样本 / 度量实现 bug，应排查这些原因。
- **checkpoint 加载完整性**（常见的未报错错误）：

```python
ckpt = torch.load(path, map_location='cpu')
sd = ckpt.get('state_dict', ckpt)
missing, unexpected = model.load_state_dict(sd, strict=False)
print(f"missing keys: {len(missing)}", missing[:10])       # 模型要、ckpt 没给 → 这些层是随机初始化！
print(f"unexpected keys: {len(unexpected)}", unexpected[:10])  # ckpt 有、模型不要 → 可能 key 命名没对上
```
  - `missing` 非空且非预期（不是 head 这种本就要重训的层）→ **权重没真加载进去**，eval 数字不可信。
  - 大量 `unexpected` → 多半是 `module.` 前缀（DataParallel 存的）/ 命名规范不一致，需要 key remap。
  - **注意**：`strict=False` 本身、以及任何 key remap，都是**语义改动即停点**——停下问用户，别在工程执行区悄悄做。

- **单步显存峰值和耗时**（顺带记）：smoke run 时记开发卡（1×A100）单 step 显存峰值（`torch.cuda.max_memory_allocated()`）和耗时，写进 setup.json 机读区（dev_card_footprint），判断够不够支撑 execution 迭代。

## 发现异常时的处理方式

- **NaN / 全零 / 梯度未正常传递**：是 bug，agent 进 debug 循环（不是停顿点）——查初始化、数据、device、计算图。
- **checkpoint missing keys 异常 / 需要 remap**：**语义改动即停**，把 missing/unexpected 列给用户，解释"这样加载会有层是随机的"，问怎么处理。
- **eval 异常满分 / 恰好 0**：是危险信号，agent 自己先排查（数据路径、标签映射、是否评估了训练集），排查不出再上报。
- **数值有限但量级异常**：记进 report 的"语义风险"，提示下游 reproduction 重点核对——不一定是 setup 能定的（可能是 repo 本身的预期）。

> 与 baseline-survey 的衔接：survey 的"社区复现"若提到有人报 key mismatch / 复现不出数字，
> 这里的 checkpoint 完整性检查就是验证那个预判——实测 missing keys，核对社区报告的问题能否重现，写进 report。
