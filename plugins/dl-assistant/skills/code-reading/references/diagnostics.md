# 诊断脚本指南（code-reading）

这些脚本用于 agent 预验运行时的张量形状、registry 构造结果和模块状态，也可作为 [VS Code](vscode-debugging.md) 启动项调用原实现的最小入口。先按[阅读流程](workflow.md)确定要观察的问题，只采集回答该问题所需的信息。

## 选择运行环境

- 要观察项目行为，使用仓库的环境、配置和原实现。缺 GPU、权重或数据时，按[最小运行条件](vscode-debugging.md#最小运行条件)准备对应替代资源，先跑到目标断点或同一链路可达的前段。
- 要核通用库的算子行为，可单独在对应版本上调用该算子，记录输入和结果。结论覆盖这次独立运行，项目调用链的观察由仓库运行提供。

## 两类诊断及其做法

### 类一：使用仓库环境做诊断

导入仓库模块，使用项目的构造方式、数据管线和可用权重或随机初始化。在用户的 VS Code 会话中也可用 Debug Console 做同样的观察。

**手法 1 · 读取首批并打印结构**（查看 keys、shape、dtype 和对象类型）

```python
"""
Diagnostic: 验项目 DataLoader 产出的首批结构. [code-reading · <章节>]
从磁盘读取样本并通过项目原有读取和组批逻辑，打印 keys 和 shape。
"""
import os, sys
REPO_ROOT = "<repo 绝对路径>"          # 显式指定，别靠 __file__ 相对推算（脚本在 docs/code-reading/ 下）
sys.path.insert(0, REPO_ROOT)
os.environ["HF_HUB_OFFLINE"] = "1"     # 按需；其他 env 按 setup report（no_proxy / HF_ENDPOINT 等）

import torch
# ... 用 repo 的 build/config 从真实或合成样本路径构造 loader ...

batch = next(iter(loader))
for k, v in batch.items():
    if torch.is_tensor(v):
        print(f"{k:20s} {tuple(v.shape)} {v.dtype}")
    else:
        print(f"{k:20s} {type(v).__name__}")
```

**手法 2 · 非侵入 forward hook（看真实 forward 的层输入输出，不改源码）**

用这类脚本检查实际运行中某层的输出形状或模块类型。用 `register_forward_hook` 从脚本注册 hook，脚本结束后不再生效。运行权限按实际影响判断。

```python
"""
Diagnostic: hook <module 路径> 看真实 forward 的 in/out shape. [code-reading · <章节>]
外挂 forward hook，不改模型源码；跑 1-2 个 batch 打印后即移除。
"""
import os, sys
REPO_ROOT = "<repo 绝对路径>"
sys.path.insert(0, REPO_ROOT)
os.environ["HF_HUB_OFFLINE"] = "1"

import torch
# ... 用 repo 代码 build 出 model，从 repo 的 DataLoader 读取一个 batch ...

records = []
def make_hook(name):
    def hook(module, inputs, output):          # inputs 是 tuple，output 是该模块返回值
        def shape_of(x):
            return tuple(x.shape) if torch.is_tensor(x) else type(x).__name__
        records.append((name, type(module).__name__,
                        [shape_of(i) for i in inputs], shape_of(output)))
    return hook

handles = []
for name, module in model.named_modules():
    if name in {"backbone.layer4", "neck", "bbox_head.cls"}:   # ← 换成这次要追的层
        handles.append(module.register_forward_hook(make_hook(name)))

model.eval()
with torch.no_grad():
    _ = model(batch)                           # 真实 forward，钩子自动触发

for name, cls, ins, out in records:
    print(f"{name:24s} {cls:18s} in={ins} -> out={out}")

for h in handles:                              # 用完移除
    h.remove()
```

要点：

- **按名字精确挂**关心的几层，别 `for all modules` 全挂——输出爆炸又拖慢。先 `print([n for n,_ in model.named_modules()])` 找准名字。
- 上例观察推理。追训练时把 hook 挂到训练入口构造的模型，复用项目实际的输入适配、调用方式、训练模式和梯度上下文。
- hook 里**只读不改**：只记录/打印，**不要改 output**，并记录观察影响。

**手法 3 · 读 buffer / backward hook（看权重、running stats、梯度）**

- 看 BN 真实统计：直接读 `module.running_mean` / `running_var` / `momentum`，判它是 `SyncBatchNorm` 还是普通 `BatchNorm2d`。
- 看梯度：`module.register_full_backward_hook(fn)`，在 `loss.backward()` 后拿 grad 的 shape/范数。

### 类二：通用库的局部观察

直接调用通用库，用一个小输入观察算子行为。

```python
"""
Diagnostic: 观察 torch.flatten 和 Tensor.transpose 的维度变化。
"""
import torch

B, C, H, W = 2, 256, 32, 32
x = torch.randn(B, C, H, W)
out = x.flatten(2).transpose(1, 2)             # [B, C, H, W] -> [B, H*W, C]
print(out.shape)                               # 对照源码注释/论文期望
```

## 通用原则（两类都遵守）

- 优先从源码之外观察。运行前检查文件、设备和状态影响，临时改动及恢复按[阅读流程](workflow.md)。
- **授权按实际影响核对。** 记录脚本会访问哪些数据、状态和设备。超出当前授权时，先说明具体影响和恢复方式。
- **运行后把实际结果用于讲解当前段。** 记录脚本、输入、当前状态和输出范围。
- **环境**：类一用与目标入口、配置和资产对应且实际可用的仓库环境。类二用匹配该段逻辑的独立环境。
- **产出位置**：支持讲解的脚本放在本次笔记目录下的 `diagnostics/`。`sys.path` 显式指 repo 绝对路径，别靠 `__file__` 相对推算。
