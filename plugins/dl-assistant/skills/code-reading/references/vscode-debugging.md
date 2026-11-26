# VS Code 交互调试

用户选定入口后，按[阅读流程](workflow.md)核对真实环境和启动命令。优先复用真实入口。需要缩短启动过程时，用[局部诊断脚本](diagnostics.md)导入并调用原实现，标明数据、权重、运行模式和覆盖范围。

## 调试时用户和 agent 各自做什么

选定入口后，agent 直接准备或复用 `.vscode/launch.json` 中的启动项，核对解释器、程序或模块、参数、工作目录和所需环境变量。先按该启动项的实际条件试跑，有调试器时预验首个断点。普通试跑、agent 调试器命中和用户 VS Code 命中分别记录，写明验证到哪一步及未验证的原因。

首轮只给用户启动项、首个断点和一个检查动作。例如让用户按 F5，停在模型构造后的第一条可执行语句，查看 `type(model).__name__`。用户把看到的值或卡点发回来，agent 对照源码解释，再给下一处断点或单步操作。断点未命中时先核实际解释器、加载的文件和调用栈，必要时查子进程或远端路径映射。

### 用 mcp-debugger 预验首站

若当前会话可调用单独安装的 `mcp-debugger`，按同版本上游 skill 操作。使用选定项目的解释器（其中需有 debugpy）、工作目录和参数，在真实源码设置断点。确认会话停在目标文件和符号，检查用于讲解的局部值，继续后确认退出，结束时关闭自己创建的会话。只有实际命中才记为预验通过。MCP 不可用时，可用现有调试器或普通试跑，按实际验证程度交代。

MCP 预验在 agent 自己的会话中进行。无论 MCP 是否可用，都准备用户自己的 VS Code 启动项。上游 IDE 镜像可查看 agent 会话，该会话的单步和继续由 agent 控制。

## 最小运行条件

先核目标段需要哪些资源，已有可用的数据、权重和配置继续复用。为缺项准备隔离的运行条件，优先沿用真实入口的配置和参数。

- **缺 GPU。** 使用项目支持的 CPU 和单进程选项。只调整跑到断点所需的设备、精度和分布式设置。碰到 CUDA 专属算子或跨 rank 行为时，确认可在 CPU 上执行到哪一步，再选择同一调用链的可运行前段。
- **缺权重。** 用项目自己的模型构造和初始化流程，关闭预训练权重下载和不适用的 checkpoint 恢复，按需固定随机种子。保留目标模型结构和配置。观察范围以实际运行的路径为准，检查点加载和恢复行为需要可用的检查点。
- **缺数据。** 先查 Dataset 的读盘格式、目录或分片结构、清单、字段、标注和过滤规则。按项目的原始输入格式生成足够组成一个有效 batch 的小样本，保存到本次诊断目录，按需保存可再生成的脚本。用配置指向该数据根或清单，走原有 Dataset、DataLoader、变换和 collate。核对 batch size、采样和 `drop_last`，实际读出首批并检查样本数、字段和形状。禁止替换 `__getitem__`、直接注入组装好的 batch 或跳过原数据管线。

入口原本执行长任务时，使用项目已有的步数或样本限制；需要自写脚本时，只调用到目标段所需的原实现。输出、缓存和检查点定向到本次诊断目录，避免覆盖正式产物。笔记记录启动项、实际设备、权重初始化方式、数据路径、跑到的断点及未经过的分支。CPU、随机初始化和合成数据上的结果用于解释该次执行路径。

## 1. launch.json：两个用途

按选定路径挑一个启动方式。已有适用的 `launch.json` 启动项时直接复用，缺少时新增对应启动项，保留其他配置。

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

独立脚本通过 `import` 加载仓库或依赖里的目标类或方法，用项目提供的构造方式准备必要上下文。涉及数据链时，从落盘输入走项目的读取和组批过程。让 `program` 指向脚本，在原实现中设置断点。目标依赖无法满足时，保留能在同一链路中运行的前段和待恢复条件。

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

> 原实现的局部观察示例见[诊断脚本指南](diagnostics.md)。

## 2. 断点计划（和源码讲解分段对齐）

选定路径后，agent 沿这条路径准备断点计划，和要逐段讲解的位置对齐。首轮只交付首个断点，后续根据用户实际看到的结果逐站给出操作。

要在 Dataset、transform 或 collate 内停住时，优先使用项目支持的 `num_workers=0`，让该段在调试进程中执行。要观察 worker 的专属行为时，保留相应的多 worker 设置并核对调试器可附加的进程。

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

> 单进程只覆盖该进程实际经过的行为。SyncBN 跨卡统计、loss 跨卡归约等需要在相应多进程条件下另行验证。
