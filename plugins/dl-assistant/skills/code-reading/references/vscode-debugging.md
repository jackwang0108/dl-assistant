# VSCode 交互调试（code-reading · A 模式 offered 默认 track）

> A 模式（有 setup report、环境配好）默认和你的 VSCode 调试工作流融合——你在断点里用 debug console 的 REPL 看运行时真值，比看 agent 跑 standalone 脚本的 stdout 更顺手，而且是在**真实运行上下文**里看（不用自己重建 model/batch）。
> 这是 A 的 **offered 默认交互 track，不强制**；不在 VSCode 里调（或不想调）时退回 standalone 脚本（见 `diagnostics.md`）。

## 导师制分工：agent 看不到你的 debug console

**关键约束**：agent 没法读你 VSCode debug console 的输出。所以融合不是「agent 接管你的调试器」，而是：

> **agent 备脚手架（launch.json + 断点计划 + 该敲的命令）+ 预测「你会看到什么」+ 讲解为什么；你 F5、敲命令、亲眼看、印证或打脸。**

这恰恰是导师制最自然的形态——老师说「你在这停下，敲这个，你会看到 `[B,256,32,32]`，因为上一跳做了 stride-2」，你跑出来验证。

**一条防退化纪律**：agent 自己能用 standalone 脚本验证的事（要先验才能讲的），**就自己跑、自己看、自己讲**，别全推给你「你去跑了告诉我」。调试器是给你 hands-on 探索 + agent 的「你会看到」预测，不是 agent 偷懒的借口。

## 1. launch.json：两个用途

A 模式选定路径后，agent 直接写好 launch.json。两类用途是**正交**的，不是一个东西的两种写法：

- **(a) 保真**——步进 repo 真实入口，在真实噪声里看真值（真 config / 真数据 / 真 model，你只是停下来看）。
- **(b) 剥噪求明**——把核心逻辑从真实程序的 boilerplate 里剥出来单独跑、单步走、边调边讲。

(a) 可信但被 boilerplate / 分布式 setup / registry 间接淹着，读着易迷；(b) 一眼可读但要守保真护栏。两者互补。

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

### (b) 剥离核心逻辑 + 现场教学

**目的不是「跑个探针」**，是把目标——repo（或某个核心依赖库，如 `pycocotools` 的 mAP 计算、`timm` 某 layer 的 forward）的某个**类 / 方法 / 函数 / 指标计算**——从真实程序的噪声里**剥出来**，单独跑、单步走、一边讲。真实入口里 boilerplate、分布式 setup、registry 间接、config 拼装一大堆，读着迷；剥出核心逻辑后清晰明了。在此基础上还支持**现场教学**：对着这段核心逻辑一边单步、一边讲它每步在干嘛。

**两种剥法，保真度天差地别——默认走第一种：**

- **首选 · import 真方法 + 喂最小输入**：harness 只负责剥掉环境噪声，`import` repo（或依赖库）的真类/真方法，构造最小输入直接调它——**跑的还是真代码，保真不丢**。`program` 指向这个 harness，在真方法里下断点单步。
- **退路 · 誊抄核心逻辑**：真方法没法单独隔离（和一堆状态耦合死）、或没 repo 环境（B 模式）时，才把那段逻辑誊抄进新脚本跑。**这是剥离版、非真跑**——必须标清，且对着 (a) 真实运行校一眼，别誊错了还当真相。

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

> harness / 誊抄脚本**怎么写**见 `diagnostics.md`（首选 = 类一 import repo；退路 = 类二 通用环境独立复现）；本节管的是 launch.json + 单步 + 边调边讲这层。

## 2. 断点计划（和 Stage 2 分段对齐）

选定路径后，agent 沿这条路径标几个**值得断的位置**，和 Stage 2 要逐段走的段对齐：

```text
这条训练路径，建议先在这 6 处下断点，我们一段段来：
1. train.py:42        入口参数解析 / config 加载
2. builder.py:88      registry build model（看真 build 出哪个类）
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
- 看完一段告诉 agent 关键结果（shape/类型），agent 据此讲下一跳——你是 agent 的「眼睛」。
- 追**训练链**真值时让断点停在 `model.train()` 路径下：BN 走 batch 统计、dropout 生效，和 eval 模式行为不同。

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

> 单进程只能看「单卡视角」的真值——跨卡行为（SyncBN 跨卡统计、loss 跨卡归约）单进程下看不全，那类要靠读源码 + `diagnostics.md` 的独立诊断补判。
