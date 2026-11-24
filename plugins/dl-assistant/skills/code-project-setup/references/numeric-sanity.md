# 组件行为与数值检查

本文件说明怎样根据入口和组件的预期行为设计最小检查，验证实际输入、计算和输出，并在发现异常时定位问题发生在哪一步。

按[运行手册 Step 5](workflow.md#step-5-逐项实跑正式入口复跑受影响的检查)验证已审阅的入口。检查结论限定在实际使用的版本、输入和条件。下游根据需要用完整协议核参考性能。

## 1. 先写清预期和依据

每项检查按以下顺序写。

1. **检查对象。** 写入口编号、要核的组件、参数组、输出或指标，以及本轮为什么需要它。
2. **输入和运行条件。** 写真实样本 ID 或合成规则、最终配置、模型和权重、设备、dtype、训练或推理模式，以及会影响结果的随机性。
3. **预期行为和出处。** 从当前版本的原测试、代码定义、已知答案或可信参考提取可检验条件。缺少依据时记观察和待查项。
4. **实际操作和观察。** 保存工作目录、解释器、命令、日志、退出状态、实际值和输出位置。
5. **结果与范围。** 写明符合哪项预期，验证到哪里，以及还有哪些条件或结果待核。

优先使用能隔离当前问题的最小输入。合成输入适合有明确约束和预期的组件检查。输入必须符合项目的形状、设备、dtype、值域和标注要求。需要真实场景、变长输入或特定分支时，从正式数据取可追溯的样本。

## 2. 按操作选三层检查

| 层次 | 怎么查 | 通过后能说明什么 |
| --- | --- | --- |
| 环境与配置 | 用实际解释器检查项目导入、配置解析、依赖及入口指定的设备。按 CPU、GPU 或其他设备的实际要求验证 | 这套环境可解析配置并访问所需设备 |
| 实际组件 | 调用项目的 loader、预处理、模型、损失或算子，检查其实际输入和输出。作者提供的编译算子在目标设备实调 | 该组件在已测条件下符合检查依据。扩展检查参见[编译型依赖](compile-deps.md#5-逐层验证最终使用的算子) |
| 正式入口 | 用真实数据、权重和具体配置跑到预定输出。按需核样本覆盖、参数更新、指标或测量产物 | 这条命令完成了实际跑过的范围。帮助命令、dry run、合成检查、小样本和全量运行分别记录 |

各入口从下表选择应有的检查。不适用的层或组件说明理由，受阻或未覆盖的必要检查留待处理。

| 入口 | 重点观察 |
| --- | --- |
| 推理 | 真实权重、配置、预处理、目标设备、输出结构和任务定义的数值行为。对可选编译算子核实际走的分支 |
| 训练 | 实际批次、目标和损失定义，预期参与计算的参数组，以及真正发生的优化器更新。依计划核保存或恢复 |
| 评测 | 样本 ID、标签与预测的对应，参与统计的数量或分母，指标输入、聚合和输出单位 |
| 预处理 | 输入输出的身份、数量、标签、划分和单位，实际 loader 能否读取转换产物 |
| 测量或其他实验 | 实际运行路径、所需字段、单位、事件和输出文件。计时按约定起止边界检查 |

权重用[项目实际加载路径](dataset-prep.md#4-权重身份与实际加载)核对身份、加载位置和关键参数覆盖。若发布模型的某个必要组件仍用初始化权重，将该模型对应的推理或评测验收记为不通过。作者要求部分加载或替换组件时，按已确认的目的和条件判断。

## 3. 看数值时先对照任务定义

| 现象 | 先核什么 |
| --- | --- |
| 出现 NaN 或 Inf | 在输入、预处理、算子输出、损失、梯度和指标之间找第一个异常。根据定义对应该有限的位置检查。掩码处按设计使用的 `-inf` 单独处理 |
| 输出全零或量级异常 | 核输入、权重、设备、归一化、掩码和输出定义。同一输入可用项目原测试或已知结果对照。预期为零的输出可以通过 |
| loss 为零、为负或短跑波动 | 核实际损失项、系数、归约和目标，查看优化器是否按计划更新。短跑先记录观察，结合定义和输入判断 |
| 梯度缺失或为零 | 核冻结状态、这批数据触发的分支、是否已经 backward、梯度累积和取样时机。检查应更新的参数，并分别观察梯度和更新 |
| 指标在小样本上为零或满分 | 先查 ID、标签和预测的配对、样本数、分母、指标单位和聚合。结合实际样本解释结果，必要时补一个有已知答案的指标检查 |

### 训练示例 · 检查真正发生的一次更新

先从实际优化器的参数组、冻结配置和样本触发的分支，选出**在这次受控输入下预期会改变**的参数。把以下函数接到检查脚本，`model` 使用实际模型，`expected_to_change` 填已经核对的参数名，`run_update` 调用仓库已有的真实训练路径直到一次预期更新结束。梯度累积时观察在积累完成后更新的那一步，使用 AMP 时记录是否发生溢出并跳过更新。需要看梯度时，在实际 backward 后、清空梯度前取证。 [PyTorch AMP 训练示例](https://docs.pytorch.org/docs/stable/notes/amp_examples.html)

```python
def check_parameter_update(model, expected_to_change, run_update):
    names = tuple(expected_to_change)
    if not names:
        raise ValueError("先确定在本次输入下应改变的参数")
    parameters = dict(model.named_parameters())
    before = {name: parameters[name].detach().clone() for name in names}

    run_update()

    max_abs_delta = {
        name: (parameters[name].detach() - before[name]).abs().max().item()
        for name in names
    }
    print("max_abs_parameter_delta:", max_abs_delta)
    return max_abs_delta
```

按项目的预期解释这些读数，并核结果是否有限。只对有依据的参数和值设验收标准。异常时先核学习率、优化器状态、步数、冻结和实际分支，再定位更新是否发生。

### 评测示例 · 比较样本 ID 和出现次数

`expected_ids` 取本轮固定试跑清单，`observed_ids` 从真正进入指标聚合的记录导出。用一致的 ID 类型。分片或分布式评测时，按实际指标定义在正确的聚合边界核对。下面示例适用每个选中样本应计一次的场景。

```python
from collections import Counter

def compare_metric_coverage(expected_ids, observed_ids):
    expected = Counter(expected_ids)
    observed = Counter(observed_ids)
    return {
        "expected_count": sum(expected.values()),
        "observed_count": sum(observed.values()),
        "missing": dict(expected - observed),
        "extra_or_repeated": dict(observed - expected),
    }
```

同时保存 loader 输出的 ID，便于判断样本是在读取、批处理还是聚合时丢失。指标值另按其输入、分母和单位解释。

## 4. 按需要测耗时和显存

先写清设备、输入规模、batch、精度、预热次数及计时起止。训练按实际要测的阶段决定是否包含取数据、前向、反向和参数更新。推理或测量分别明确预处理、设备同步和结果回传是否在计时内。

下面示例在单个 CUDA 设备上记录一段已确定边界的操作。用入口实际执行的 `run_measured_operation` 替换回调，在计时前按相同配置预热。需要冷启动数据时单独记录。多卡或端侧设备采用其实际同步与测量方式。

```python
from time import perf_counter
import torch

def measure_cuda_operation(device, run_measured_operation):
    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)
    start = perf_counter()
    run_measured_operation()
    torch.cuda.synchronize(device)
    elapsed_s = perf_counter() - start
    peak_allocated_bytes = torch.cuda.max_memory_allocated(device)
    return elapsed_s, peak_allocated_bytes
```

这里记录的是同步后的墙钟时间和 PyTorch 张量分配的峰值。需要比较时保存多次读数、波动及实际运行条件。将测得范围写入报告，适用时同时填写 `setup.json` 的 `dev_card_footprint`。 [设备同步](https://docs.pytorch.org/docs/stable/generated/torch.cuda.synchronize.html) · [峰值统计重置](https://docs.pytorch.org/docs/stable/generated/torch.cuda.memory.reset_peak_memory_stats.html) · [已分配显存峰值](https://docs.pytorch.org/docs/stable/generated/torch.cuda.memory.max_memory_allocated.html)

## 5. 出现异常时怎么定位和记录

1. **先核运行身份。** 对照命令、最终配置、代码与 diff、实际权重、数据及设备。用原条件复现最小失败输入。
2. **找第一个偏离预期的位置。** 先取真实样本、标签和预处理结果，再查实际计算、损失与更新或预测。读到样本后仍有缺口时查批处理、筛选、聚合和落盘。已有同条件的原测试或已知答案时用来缩小范围。
3. **明确接下来能做什么。** 按 workflow 在批准范围内修复并复跑受影响检查。需改训练、评测、加载或研究条件时，带着失败输入、来源、影响和拟复跑方法回 Step 3。保留原结果和修复后结果。
4. **分开记录三个判断。** 进程退出状态记实际退出码。检查结果记符合预期、与预期冲突、待调查、未检查或不适用并说明理由。入口交付只写证据覆盖的范围。保存试跑配置、输入身份、脚本、命令和日志，供下游复查。

## 示例 · edge-vision 评测正常退出但漏了样本

沿用[运行手册](workflow.md#贯穿示例--直接试跑论文仓库)的 E02。试跑固定 17 个验证样本、批大小 8，预期每个 ID 参与统计一次。原命令退出码为 0，生成了指标，但 ID 对照显示只统计了 16 个。

先核配置仍指向同一个验证划分和 17 项清单，再比较 loader 与指标接收的 ID。此例评测路径丢弃了最后一个不满批的样本。说明保留最后一批会改变统计覆盖，回 Step 3 确认最小修复。获准后沿用原权重、同一清单和指标实现复跑，核缺失及额外 ID 均为空。执行报告保留两次日志、配置和修复 diff。结论限定为这 17 个样本的评测路径，完整参考结果交复现阶段核对。
