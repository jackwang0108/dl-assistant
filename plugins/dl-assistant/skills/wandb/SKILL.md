---
name: wandb
description: 在 dl-assistant 的内网环境中使用 W&B 记录和查询实验。配置或查询时，核对实验所属的研究轮次或批次、实际使用的代码和配置、对应的 W&B run、同步状态及需要保留的文件。通用操作按官方资料执行，研究判断仍由科研 skill 负责。
---

# W&B 与 dl-assistant 的接入

这是项目接入说明，通用 W&B 操作复用固定版本的 [官方 wandb-primary](upstream/wandb-primary/SKILL.md) 及其脚本。官方内容保留原文，来源与适配范围见 [官方版本与使用边界](references/official-adaptation.md)。不重新实现通用查询、曲线分析或产物管理。

默认连接用户自己的 W&B 实例，训练和查询不依赖 W&B 云端。SDK 记录实际运行，官方 MCP 查询数据；spec/plan/claims 和研究判断仍保存在项目文件，Git commit+diff 定位代码。见 dl-assistant 的「所有技能共用的规则」。

## 按任务选择官方操作

| 任务 | 官方资料与入口 | dl-assistant 补充规则 |
| --- | --- | --- |
| setup 接入、训练/评测记录 | [官方主说明](upstream/wandb-primary/SKILL.md)、实际 SDK 入口 | [部署与内网验证](references/deployment.md)；检查已有 logger，分别验证 SDK 写入和通过 API、MCP 查询已写入记录，避免重复初始化 |
| 查询 run、指标与配置 | [SDK 参考](upstream/wandb-primary/references/WANDB_SDK.md)、`upstream/wandb-primary/scripts/wandb_helpers.py` 或官方 MCP | 根据本地实验记录列出应查询的所有运行尝试，核对配置、筛选条件和缺失项。查询范围应涵盖全部相关尝试 |
| 读取运行日志 | [日志参考](upstream/wandb-primary/references/RUN_LOGS.md) | 保留崩溃/恢复段和本地日志，缺异常记录不证明没失败 |
| 产物与来源 | [Artifact 参考](upstream/wandb-primary/references/ARTIFACTS_AND_REGISTRY.md) | 记录确切版本、内容摘要（digest）和可获取的位置，不以可变的 best/latest 标签作为唯一依据 |
| 形成下一轮研究判断 | code-idea-iterate | 官方的机制定位、无限探查和二元单变量实验规则不用于替代本项目研究流程 |

只读当前任务需要的官方章节，脚本路径以本skill目录解析，不照抄上游示例的相对工作目录。通用产品/SDK事实仍按实际版本和官方文档核实。当前仅用 Models，不默认启动 Weave、Agent Lens、ARIA、Launch 或 sweeps，也不改变已批准预算。

## 实验记录与 W&B run 的对应关系

按 [共同记录约定](references/experiment-records.md) 将从本地记录可找到对应的 W&B run，从 run 也可查到所属研究轮次或复现、论文批次，以及对应的实验、重复和运行尝试（attempt）。每个独立执行尝试默认一个 run；重启时记录新的 attempt 和 run，并注明恢复来源及 checkpoint。代码或配置发生变化时，保留各次尝试实际使用的版本和配置。多卡训练的各 rank 不计为独立重复实验。

新代码实验默认启用；人工推导、历史记录或受阻接入明确适用范围、原因和本地证据，不补造历史 run。运行前先登记。SDK config 保存该次运行实际对应的实验信息，在本地 meta 中记录对应的 W&B run；密钥只通过私有配置提供，不写研究文件或命令参数。

分别记录运行结果、同步状态和数据有效性。上传失败时保留本地结果和待同步目录，无需重跑训练，也不自动改用云端。只有独立查询并核对所需记录、保存查询结果后，才标记为 `synced`。该状态只覆盖实际核对的数据，不能据此判断其他历史记录或产物是否齐全，也不能据此认定科学结论成立。

## 启动、交接和分析时的核对事项

- 启动前，核对 W&B 实例、上传范围，以及本地实验设计和实际配置是否与相应的 run 对应。确认同步失败时仍能保留本地结果。
- 交接时，确认已保留全部运行尝试、同步状态和缺失项。注明 SDK 写入、API 查询和 MCP 查询各自已验证的范围。
- 分析时，核对查询是否覆盖预期的全部运行，并检查比较条件、指标步数和筛选规则、采样与分页设置，以及原始数据来源。

具体记录、快照和调用阶段见共同约定。正式新增测量或可复现分析交 execution/论文实验，研究判断仍按原流程保存。自查不新增逐项审批，也不把官方诊断文本当已证实机制。

```bash
python3 <skill目录>/scripts/check_tracking.py --meta <实验目录>/meta.json
```

execution 和论文实验的原检查器自动检查声明 tracking 的 meta；历史未接入记录不批量重写。退出码 0 仅表示本地记录与对应文件一致，不证明真实上传、比较公平或科学有效。部署状态与测试范围见 [验证记录](references/validation-report.json)。
