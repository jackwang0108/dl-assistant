# VS Code 交互调试

用户选定入口后，按[阅读流程](workflow.md)核对真实环境和启动命令。优先复用真实入口。需要缩短启动过程时，用[局部诊断脚本](diagnostics.md)导入并调用原实现，标明数据、权重、运行模式和覆盖范围。

## 调试时用户和 agent 各自做什么

Agent 准备或复用 `launch.json`，核对解释器、程序或模块、参数、工作目录和所需环境变量。先试跑选定入口或诊断脚本，有调试器时预验首个断点。普通试跑、agent 调试器命中和用户 VS Code 命中分别记录，写明验证到哪一步及未验证的原因。

首轮只给用户启动项、首个断点和一个检查动作。例如让用户按 F5，停在模型构造后的第一条可执行语句，查看 `type(model).__name__`。用户把看到的值或卡点发回来，agent 对照源码解释，再给下一处断点或单步操作。断点未命中时先核实际解释器、加载的文件和调用栈，必要时查子进程或远端路径映射。

### 用 mcp-debugger 预验首站

若当前会话可调用单独安装的 `mcp-debugger`，按同版本上游 skill 操作。使用选定项目的解释器（其中需有 debugpy）、工作目录和参数，在真实源码设置断点。确认会话停在目标文件和符号，检查用于讲解的局部值，继续后确认退出，结束时关闭自己创建的会话。只有实际命中才记为预验通过。MCP 不可用时，可用现有调试器或普通试跑，按实际验证程度交代。

MCP 预验用 agent 自己的会话。用户跟读时操作自己的 VS Code 会话，回报观察结果。上游 IDE 镜像用于查看 agent 会话，单步和继续仍由 agent 控制。

## 1. launch.json：两个用途

按需要选以下配置。已有 `launch.json` 时先核当前配置，再添加需要的入口。

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

> 入口由 `torchrun` 或 `deepspeed` 启动时，先核第 4 节的单进程方式是否适用。

### (b) 单独运行目标模块并逐步讲解

可单独调试仓库或依赖库中的目标类、方法、函数或指标计算，例如 `pycocotools` 的 mAP 计算或 `timm` 某层的 forward。这样可以专注于目标代码，无需经过完整的分布式初始化、registry 解析和配置组装。

按以下优先顺序准备脚本。

- **首选，导入并调用原实现。** 独立脚本通过 `import` 加载仓库或依赖里的目标类或方法，构造最小输入并调用。让 `program` 指向该脚本，在原实现中设置断点后单步执行。
- **无法独立调用时复制相关逻辑。** 原实现依赖共享状态、无法单独运行，或缺少仓库专属环境时，把相关逻辑复制到独立脚本。明确注明脚本只验证复制的逻辑。有真实入口的运行结果时，按 (a) 的结果复核脚本是否一致。

```json
{
  "name": "<项目简称>: dissect <target 类/方法>",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/docs/code-reading/<日期>-<主题>/diagnostics/<harness>.py",
  "console": "integratedTerminal",
  "cwd": "${workspaceFolder}",
  "python": "<setup_report 中的 conda env python 路径>",
  "justMyCode": false,
  "env": { "HF_HUB_OFFLINE": "1", "no_proxy": "...", "HF_ENDPOINT": "..." }
}
```

> 需要步入框架或第三方库时，用 `justMyCode: false`，并核对对应库装在所选环境中。

> 脚本写法见 `diagnostics.md`。能导入原实现时用类一，无法导入时用类二的通用环境独立验证。本节说明如何配置 launch.json、单步运行并解释结果。

## 2. 断点计划（和源码讲解分段对齐）

选定路径后，agent 沿这条路径准备断点计划，和要逐段讲解的位置对齐。首轮只交付首个断点，后续根据用户实际看到的结果逐站给出操作。

```text
这条训练路径的候选断点：
1. train.py:42        入口参数解析 / config 加载
2. builder.py:88      registry build model（看实际构建哪个类）
3. dataset.py:120     __getitem__ 返回（看真实 keys/shape）
4. model.py:155       forward 第一个逻辑块
5. model.py:210       backbone → neck 交界（看 shape 变化）
6. loss.py:60         loss 计算
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

- **每行只看一件事**。结果偏离预期时，先核对配置、进程和实际调用路径，再解释差异。
- 看完一段后把关键结果（形状或类型）告诉 agent，供它解释下一个调用。
- 查看训练阶段的实际值时让断点停在 `model.train()` 路径下：BN 走 batch 统计、dropout 生效，和 eval 模式行为不同。

## 4. 单进程调试分布式 / DeepSpeed

先核脚本和框架是否支持单进程启动。如果目标分支可以在单进程触发，可按项目实际使用的 rank 参数和环境变量改写下面的示例，再试跑确认。如果必须经过原启动器或涉及跨 rank 行为，保留实际启动方式，只在已验证可暂停的范围内观察。

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
