# VSCode 交互调试（code-reading · A 模式 默认建议的交互方式）

> A 模式（有 setup report、环境配好）默认建议结合 VSCode 调试。停在断点后，可直接在 debug console 查看当前配置、模型和 batch 的实际值。
> 这是 A 的 **默认建议的交互方式，不强制**；不在 VSCode 里调（或不想调）时改用独立诊断脚本（见 `diagnostics.md`）。

## 调试时用户和 agent 各自做什么

agent 无法读取你的 VSCode debug console 输出。

> agent 准备 launch.json、断点计划和检查命令，说明预计结果和原因。你按 F5 启动，执行检查命令并查看结果。

例如，agent 会指出在哪里停下、输入什么命令，以及为什么上一层使用 stride-2 后预计能看到 `[B,256,32,32]`。你运行命令核对。

讲解前需要确认、又能独立运行的内容，由 agent 使用诊断脚本验证并解释结果。

## 1. launch.json：两个用途

A 模式选定路径后由 agent 编写 launch.json。按需要使用以下两类配置。

- **(a) 沿仓库入口单步执行**。观察这次运行实际加载的配置、数据和模型。
- **(b) 单独运行目标模块**。用最小输入调用目标函数或类，再逐步解释运行过程。

沿入口运行可以核对完整上下文。单独运行有助于聚焦某段逻辑，解释时要说明脚本覆盖的范围。

### (a) 步进真实入口（选定路径的 train.py / test.py）

让你 F5 就进训练/推理主流程，逐段停下来看：

```json
{
  "name": "<项目简称>: step through <entry>",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/<entry script>.py",
  "args": ["<config 路径>", "...其他参数..."],
  "console": "integratedTerminal",
  "cwd": "${workspaceFolder}",
  "python": "<setup_report 中的 conda env python 路径>",
  "justMyCode": false,
  "env": { "HF_HUB_OFFLINE": "1", "no_proxy": "...", "HF_ENDPOINT": "..." }
}
```

> 入口是 `torchrun`/`deepspeed` 起的分布式脚本 → 用下面第 4 节的单进程配置，那份就是步进真实分布式入口的。

### (b) 单独运行目标模块并逐步讲解

可单独调试仓库或依赖库中的目标类、方法、函数或指标计算，例如 `pycocotools` 的 mAP 计算或 `timm` 某层的 forward。这样可以专注于目标代码，无需经过完整的分布式初始化、registry 解析和配置组装。

按以下优先顺序准备脚本。

- **首选，导入并调用原实现。** 独立脚本通过 `import` 加载仓库或依赖里的目标类或方法，构造最小输入并调用。让 `program` 指向该脚本，在原实现中设置断点后单步执行。
- **无法独立调用时复制相关逻辑。** 原实现依赖共享状态、无法单独运行，或缺少仓库专属环境（B 模式）时，把相关逻辑复制到独立脚本。明确注明脚本只验证复制的逻辑。有真实入口的运行结果时，按 (a) 的结果复核脚本是否一致。

```json
{
  "name": "<项目简称>: dissect <target 类/方法>",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/docs/code-reading/diagnostics/<harness>.py",
  "console": "integratedTerminal",
  "cwd": "${workspaceFolder}",
  "python": "<setup_report 中的 conda env python 路径>",
  "justMyCode": false,
  "env": { "HF_HUB_OFFLINE": "1", "no_proxy": "...", "HF_ENDPOINT": "..." }
}
```

> **`justMyCode: false` 必须**——否则断点进不去 repo 和第三方库代码，框架机制、依赖库内部就看不到。教依赖库的方法时，该库得装在这个 env 里。

> 脚本写法见 `diagnostics.md`。能导入原实现时用类一，无法导入时用类二的通用环境独立验证。本节说明如何配置 launch.json、单步运行并解释结果。

## 2. 断点计划（和 Stage 2 分段对齐）

选定路径后，agent 沿这条路径标几个**适合设置断点的位置**，和 Stage 2 要逐段走的段对齐：

```text
这条训练路径，建议先在这 6 处下断点，我们一段段来：
1. train.py:42        入口参数解析 / config 加载
2. builder.py:88      registry build model（看实际构建哪个类）
3. dataset.py:120     __getitem__ 返回（看真实 keys/shape）
4. model.py:155       forward 第一个逻辑块
5. model.py:210       backbone → neck 交界（看 shape 变化）
6. loss.py:60         loss 计算
停在每处时我告诉你 debug console 敲什么、会看到什么。
```

## 3. debug console REPL：停在断点敲什么

停在某断点后，在 debug console 的 REPL 里逐行敲。agent 给的是「停在 X → 敲 Y → 你会看到 Z（+ 为什么）」的**预测 + 解释**：

```python
# 停在 forward 里：
x.shape                                  # 当前 tensor 真实形状
type(self.backbone)                      # registry 真 build 出的类
[(n, tuple(p.shape)) for n, p in self.named_parameters()][:5]
{k: (v.shape if hasattr(v, "shape") else type(v)) for k, v in batch.items()}
self.bn1.running_mean[:5]                # BN 真实统计（追训练链伪对齐时）
isinstance(self.bn1, torch.nn.SyncBatchNorm)   # 是不是同步 BN
```

要点：

- **每行只看一件事**，对照 agent 的预测印证；不一致就是读出了 bug 或盲点，正是学习点。
- 看完一段后把关键结果（形状或类型）告诉 agent，供它解释下一个调用。
- 查看训练阶段的实际值时让断点停在 `model.train()` 路径下：BN 走 batch 统计、dropout 生效，和 eval 模式行为不同。

## 4. 单进程调试分布式 / DeepSpeed

分布式训练脚本通常难直接 debug。设这些 env，accelerate / DeepSpeed 会自动初始化单进程 dist，**不需要 deepspeed/torchrun 启动器**就能 F5 步进真实分布式入口：

```json
{
  "name": "debug <train_script> (single-process)",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/train.py",
  "console": "integratedTerminal",
  "cwd": "${workspaceFolder}",
  "python": "<setup_report 中的 conda env python 路径>",
  "justMyCode": false,
  "args": ["--local_rank=0", "...其他参数..."],
  "env": {
    "WORLD_SIZE": "1",
    "RANK": "0",
    "LOCAL_RANK": "0",
    "MASTER_ADDR": "127.0.0.1",
    "MASTER_PORT": "29501",
    "CUDA_VISIBLE_DEVICES": "0"
  }
}
```

> 单进程只能看「单卡视角」的实际观察值——跨卡行为（SyncBN 跨卡统计、loss 跨卡归约）单进程下看不全，那类要靠读源码 + `diagnostics.md` 的独立诊断补判。
