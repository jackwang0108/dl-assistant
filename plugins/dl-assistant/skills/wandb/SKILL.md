---
name: wandb
description: 将官方 W&B skill、SDK 和 MCP 接入 dl-assistant 的内网科研流程；配置或查询实验时核对研究/代码/运行身份、同步与证据交接。通用操作复用官方资料，研究判断仍由科研 skill 负责。
---

# W&B 与 dl-assistant 的接入

这是项目接入说明，通用 W&B 操作复用固定版本的 [官方 wandb-primary](upstream/wandb-primary/SKILL.md) 及其脚本。官方内容保留原文，来源与适配范围见 [官方版本与使用边界](references/official-adaptation.md)。不重新实现通用查询、曲线分析或产物管理。

默认连接用户自己的 W&B 实例，训练和查询不依赖 W&B 云端。SDK 记录实际运行，官方 MCP 查询数据；spec/plan/claims 和研究判断仍保存在项目文件，Git commit+diff 定位代码。横切规范见 dl-assistant。

## 按任务选择官方操作

| 任务 | 官方资料与入口 | dl-assistant 补充规则 |
| --- | --- | --- |
| setup 接入、训练/评测记录 | [官方主说明](upstream/wandb-primary/SKILL.md)、实际 SDK 入口 | [部署与内网验证](references/deployment.md)；检查已有 logger，独立 SDK 写入和 API/MCP 读回，不重复初始化 |
| 查询 run、指标与配置 | [SDK 参考](upstream/wandb-primary/references/WANDB_SDK.md)、`upstream/wandb-primary/scripts/wandb_helpers.py` 或官方 MCP | 先按本地台账确定应纳入集合，核全部尝试、条件、选择和缺失，不只取最高分 |
| 读取运行日志 | [日志参考](upstream/wandb-primary/references/RUN_LOGS.md) | 保留崩溃/恢复段和本地日志，缺异常记录不证明没失败 |
| 产物与来源 | [Artifact 参考](upstream/wandb-primary/references/ARTIFACTS_AND_REGISTRY.md) | 记录精确版本/digest与可取得位置，不仅用可变 best/latest |
| 形成下一轮研究判断 | code-idea-iterate | 官方的机制定位、无限探查和二元单变量实验规则不用于替代本项目研究流程 |

只读当前任务需要的官方章节，脚本路径以本skill目录解析，不照抄上游示例的相对工作目录。通用产品/SDK事实仍按实际版本和官方文档核实。当前仅用 Models，不默认启动 Weave、Agent Lens、ARIA、Launch 或 sweeps，也不改变已批准预算。

## 共同身份与记录

按 [共同记录约定](references/experiment-records.md) 将研究轮次/复现或论文批次、实验、重复、attempt 与 W&B run 双向关联。每个独立执行尝试默认一个 run；重启记录新 attempt/run、恢复源和 checkpoint。代码与配置改变保留当时来源，多卡 rank 不当独立重复。

新代码实验默认启用；人工推导、历史记录或受阻接入明确适用范围、原因和本地证据，不补造历史 run。运行前先登记，SDK config 保存实际身份，meta保存反向关联；密钥只从私有配置注入，不写研究文件或命令参数。

运行、同步、数据有效性分别记录。同步未知不写 synced，上传失败保留本地结果和待同步目录，不重新训练、不自动切云端。独立读回后保存必要快照；synced只说明该范围被读回，不代表全部历史/产物完整或科学结论正确。

## 纳入调用方现有自查

- 开跑：实例、上传范围、本地设计/实际配置与 run 身份是否对应，失败后是否能保留本地结果？
- 交接：全部尝试和同步/缺失是否保留，SDK写入与API/MCP读回分别验证到哪里？
- 解释：查询是否覆盖应纳入集合，可比条件、指标step/选择、采样/分页和原始来源是否核对？

具体记录、快照和调用阶段见共同约定。正式新增测量或可复现分析交 execution/论文实验，研究判断仍按原流程保存。自查不新增逐项审批，也不把官方诊断文本当已证实机制。

```bash
python3 <skill目录>/scripts/check_tracking.py --meta <实验目录>/meta.json
```

execution 和论文实验的原检查器自动检查声明 tracking 的 meta；历史未接入记录不批量重写。退出0仅表示本地声明/文件一致，不证明真实上传、比较公平或科学有效。部署状态与测试范围见 [验证记录](references/validation-report.json)。
