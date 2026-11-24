# 诊断脚本指南（code-reading）

> code-reading 读源码时，**「这个 tensor 运行时实际什么 shape」「registry 实际构建哪个类」「BN 跑的什么统计」这类运行时事实，静态读看不到。**
> 本手册给出独立脚本的操作示例。先按[阅读流程](workflow.md)明确需要核实的运行时问题，再按所需环境选手法。
> 只采集回答当前问题所需的信息。运行前先核实际副作用，必要证据随笔记保留。
>
> **想交互式地在断点里看同样的实际观察值**→ 见 `vscode-debugging.md`：在 VSCode debug console 的 REPL 里逐行敲，比脚本更顺手，且在真实运行上下文里看。本手册是它的补充——agent 自己要先验才能讲的事、或要隔离复现某段逻辑时，写脚本跑。

## 决策：要验一个运行时事实，先问「需要什么环境」

```
我要确认的这件事……
├─ 需要 repo 的专属环境（import repo 模块 / 用它的 build / dataloader / checkpoint / 配好的依赖）
│     例：dataset.__getitem__ 实际返回哪些键、registry 按 config 实际构建哪个类、
│         load_state_dict 后哪些 key 没对上、它的 model 真实 forward 的层输出 shape
│   → 实际具备仓库运行条件时才做。条件不足时标明推断和缺项。
│
├─ 只需通用 python+torch 环境（自包含、不依赖 repo 的专属依赖/数据/权重）
│     例：一段 reshape/permute/view 的 shape 变换、einops rearrange、
│         一个只用到 torch 标准层的自包含 nn.Module 的 forward、读 config 文件解析成什么 dict
│   → 写独立小脚本验。有可用环境且值得核查时运行。
│
└─ 什么都不用跑（讲代码结构 / 职责 / 意图 / 调用关系）
      → 静态读，不写脚本。
```

**两个常被误判的点：**

- **「环境没配」≠「什么都不能验」。** repo 专属环境没配，不代表通用 torch 环境也没有。自包含的 shape 逻辑、单个标准模块、算子行为，通用环境就能验——可按问题用独立脚本局部验证。
- **「能跑 repo」≠「什么都该跑脚本」。** 讲清结构、职责、意图靠读源码就够，别为了讲一个一眼能看懂的函数去起脚本。脚本只用在「静态读确实定不下来」的运行时事实上。

### 缺少仓库运行条件

只有仓库环境能回答的问题，条件不足时按以下方式记录。

- 把 shape/值明确标成 **「源码推断，待实际运行确认」**，不写成观测到的事实。
- 独立脚本只能验证其中复制或抽取的逻辑，例如用合成张量检查一段 reshape。说明检查范围，并核对脚本是否忠实于源代码。

## 两类诊断及其做法

### 类一：使用仓库环境做诊断

import repo 的模块、用它的 build/dataloader/权重，看**真实**运行时值。下面三个手法写成脚本由 agent 跑；同样这些实际观察值想交互式看，用 `vscode-debugging.md` 的 debug console。

**手法 1 · import + 构造 + print 静态结构**（最常用，看 keys/shape/dtype/对象类型）

```python
"""
Diagnostic: 验 dataset.__getitem__ 实际输出结构. [code-reading · <章节>]
import 项目代码构造一个样本，打印 keys 和 shape，不改任何文件。
"""
import os, sys
REPO_ROOT = "<repo 绝对路径>"          # 显式指定，别靠 __file__ 相对推算（脚本在 docs/code-reading/ 下）
sys.path.insert(0, REPO_ROOT)
os.environ["HF_HUB_OFFLINE"] = "1"     # 按需；其他 env 按 setup report（no_proxy / HF_ENDPOINT 等）

import torch
# ... 用 repo 的 build/config 构造 dataset ...

sample = dataset[0]
for k, v in sample.items():
    print(f"{k:20s} {tuple(v.shape) if torch.is_tensor(v) else type(v).__name__}")
```

**手法 2 · 非侵入 forward hook（看真实 forward 的层输入输出，不改源码）**

用这类脚本检查实际运行中某层的输出形状或模块类型。用 `register_forward_hook` 从脚本注册 hook，脚本结束后不再生效。此做法无需申请修改源码，首次运行诊断脚本仍按下文的授权规则处理。

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
# ... 用 repo 代码 build 出 model、拿一个真实 batch（复用 repo 的 build/dataloader，别自己造假数据）...

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

model.eval()                                   # 追训练链行为时改 model.train()，BN/dropout 行为不同
with torch.no_grad():
    _ = model(batch)                           # 真实 forward，钩子自动触发

for name, cls, ins, out in records:
    print(f"{name:24s} {cls:18s} in={ins} -> out={out}")

for h in handles:                              # 用完移除
    h.remove()
```

要点：

- **按名字精确挂**关心的几层，别 `for all modules` 全挂——输出爆炸又拖慢。先 `print([n for n,_ in model.named_modules()])` 找准名字。
- 追**训练链**实际观察值时 `model.train()` 跑——BN 走 batch 统计并更新 running stats、dropout 生效，和 eval 模式不同；这正是要看的（也是 reproduction 追训练链伪对齐时「眼见为实」要的）。
- hook 里**只读不改**：只记录/打印，**不要改 output**，并记录观察影响。

**手法 3 · 读 buffer / backward hook（看权重、running stats、梯度）**

- 看 BN 真实统计：直接读 `module.running_mean` / `running_var` / `momentum`，判它是 `SyncBatchNorm` 还是普通 `BatchNorm2d`。
- 看梯度：`module.register_full_backward_hook(fn)`，在 `loss.backward()` 后拿 grad 的 shape/范数。

### 类二：通用环境独立诊断（通用 PyTorch 环境）

不 import repo，把要验的**自包含逻辑抽出来**用 dummy tensor 跑。专治「B 没配 repo 环境，但这事其实通用环境就能验」。

```python
"""
Diagnostic: 验 <某函数> 的 reshape 逻辑 shape 是否如源码推断. [code-reading · <章节>]
独立复现源码里的那段形状变换，不 import repo。验的是「抽取的逻辑」，非 repo 真跑。
"""
import torch

B, C, H, W = 2, 256, 32, 32
x = torch.randn(B, C, H, W)
# —— 照抄源码 line <N> 那段（标清来源）——
out = x.flatten(2).transpose(1, 2)             # [B, C, H, W] -> [B, H*W, C]
print(out.shape)                               # 对照源码注释/论文期望
```

## 通用原则（两类都遵守）

- 优先从源码之外观察。运行前检查文件、设备和状态影响，临时改动及恢复按[阅读流程](workflow.md)。
- **授权按实际影响核对。** 记录脚本会访问哪些数据、状态和设备。超出当前授权时，先说明具体影响和恢复方式。
- **运行后把实际结果用于讲解当前段。** 记录脚本、输入、当前状态和输出范围。
- **环境**：类一用与目标入口、配置和资产对应且实际可用的仓库环境。类二用匹配该段逻辑的独立环境。
- **产出位置**：支持讲解的脚本放在本次笔记目录下的 `diagnostics/`。`sys.path` 显式指 repo 绝对路径，别靠 `__file__` 相对推算。

> 想用 VSCode 调试器（断点 + debug console REPL）交互式看这些实际观察值，而不是跑 standalone 脚本 → `vscode-debugging.md`。launch.json 模板、单进程调试分布式训练，都在那。
