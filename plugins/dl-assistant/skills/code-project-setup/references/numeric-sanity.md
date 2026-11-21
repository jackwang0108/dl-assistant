# 数值正确性检查（numeric-sanity）

> 三层验证的升级核心：每层不只看"不报错"，还看"数值合理"。主文 SKILL.md 说"加数值 sanity"，
> 这里放每层具体查什么、怎么查、命中红线怎么办。

## 为什么"跑通"不等于"跑对"

setup 最危险的不是报错——报错会停下来，看得见。最危险的是**静默错误**：代码全程不抛异常，
但结果是错的。常见五种，都在 setup 阶段就能拦：

| 静默错误 | 表象（不报错） | 真相 |
| --- | --- | --- |
| checkpoint 半加载 | `load_state_dict(strict=False)` 静默吞掉 | 一半权重是随机初始化，eval 数字莫名其妙 |
| device map 错 | 能跑，慢 | 部分张量在 CPU、部分在 GPU，结果可能对但极慢；或 silently 在错的卡 |
| 预处理 mean/std 错 | forward 正常出数 | 输入分布偏移，输出全错但形状对 |
| NaN 传播 | loss 打印出来是 `nan`，训练"在跑" | 学习率/初始化/数据问题，越跑越烂 |
| 假成功 | eval metric=0.0 或 =1.0 | 数据没真加载 / 全预测同一类 / 标签泄漏，不是真的完美 |

**拦截原则**：每过一层验证，问一句"这个数值如果是错的，它会长什么样？"——对照红线检查。

## Layer 1（import/config）：轻量数值 sanity

import 成功后，确认 CUDA 这条链没静默错位：

```python
import torch
assert torch.cuda.is_available(), "CUDA 不可用——驱动/torch 装错"
print(torch.cuda.get_device_name(0))            # 确认看到的是预期的卡（A100）
print(torch.__version__, torch.version.cuda)    # 与 nvcc 对齐（详见 compile-deps.md）
# 若有编译型算子，import 它并跑一次最小调用，确认不是 undefined symbol
```

红线：`is_available()` 为 False、看到的卡不对、编译算子 import 报 undefined symbol → 回 `compile-deps.md`。

## Layer 2（synthetic smoke）：关键数值 sanity

这是拦截静默错误的主战场。smoke script 调真实组件后，**显式断言数值**，别只看"没抛异常"：

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

## Layer 3（官方命令 smoke run）：强数值 sanity

smoke 真实数据跑几步/一小轮后：

- **loss 趋势对**：smoke train 几步内 loss 应有下降趋势（不是上涨、不是纹丝不动、不是 NaN）。
- **eval metric 不离谱**：tiny subset eval 的 metric **> 0 且不是假满分**。
  - `metric == 0.0` → 数据没真加载 / 预测全错 / 标签对不上，**不是**"小子集太难"就能搪塞的。
  - `metric == 1.0`（或恰好满分）→ 标签泄漏 / 评估了训练样本 / 度量实现 bug，**假成功比失败更危险**。
- **checkpoint 加载完整性**（最高频静默坑）：

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

- **资源足迹**（顺带记）：smoke run 时记开发卡（1×A100）单 step 显存峰值（`torch.cuda.max_memory_allocated()`）和耗时，写进 setup.json 机读区（dev_card_footprint），判断够不够支撑 execution 迭代。

## 命中红线怎么办

- **NaN / 全零 / 梯度断**：是 bug，agent 进 debug 循环（不是停顿点）——查初始化、数据、device、计算图。
- **checkpoint missing keys 异常 / 需要 remap**：**语义改动即停**，把 missing/unexpected 列给用户，解释"这样加载会有层是随机的"，问怎么处理。
- **eval 假满分 / 恰好 0**：是危险信号，agent 自己先排查（数据路径、标签映射、是否评估了训练集），排查不出再上报。
- **量级离谱但有限**：记进 report 的"语义风险"，提示下游 reproduction 重点核对——不一定是 setup 能定的（可能是 repo 本身的预期）。

> 与 baseline-survey 的衔接：survey 的"社区复现"若提到有人报 key mismatch / 复现不出数字，
> 这里的 checkpoint 完整性检查就是验证那个预判——实测 missing keys，把"传闻"坐实或推翻，写进 report。
