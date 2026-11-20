# 研究版本与代码追踪

每轮版本对应一次批准的研究设计，可为方法实现、探索、测量、分析或理论检查。执行完成、数据可信和假设支持程度分别记录；反证和未决也是研究过程的一部分，不分类为只值得丢弃的失败版本。

## 目录与编号

`ideas/v<N>-<slug>/` 按轮次递增；分支通常为 `idea/v<N>-<slug>`。保留 spec、plan、claims、代码映射、conclusion 和 experiments；假设改变分配新ID和血缘，不覆写旧命题。`idea_tree.json` 是索引，完整证据仍在版本文件和实际产物中。

首次代码起点按准备/复现报告的实际组件、commit/diff、配置与使用范围定位；baseline-prepared、baseline-reproduced等历史tag可辅助定位但不是必需认证。已有评测模型或其他实验实现按实际来源与检查范围使用。后续实现起点由批准设计决定，可引用历史commit/权重，不强迫从最近未证实的实现继续；记录implementation_parent_commit与研究上上一轮版本的区别。

在切分支前检查工作区、当前分支和用户改动，不覆盖或自动回退用户代码。代码/配置/脚本/统计与设计记录进git，未提交改动保留diff，权重和大数据按项目存储约定保存并记录校验/路径。不能把整个experiments目录统一忽略而丢掉配置和记录。

## 记录与tag

每轮记录代码commit、实际配置、数据与模型版本、命令/脚本及结果路径。阳性、阴性、未决、部分完成和取消同等追踪。完整记录不表示科学解释或创新性已通过。

可以按需要使用中性的 `round-v<N>` tag 定位完成或暂停时的快照，tag注释说明状态和conclusion路径，不覆盖既有tag。旧 `claim-C<id>` 保留为历史实现定位，不自动保证创新、性能或可发布。GitHub等远端push及发布按用户授权，不默认执行。

## 假设、创新性与论文交接

claims记录总假设与子命题的证据。supported只表示条件内有支持，不自动is_innovation=true；创新性需比较已有工作，研究价值还需单独判断。method_tag可空，理论/分析没有方法checkpoint也能追查。

conclusion分别记录执行status、data_validity和outcome；node_type=research_round不按阳性分success/failure。格式见共享JSON模板和execution结论模板，部分完成不写成partially_refuted。无新实验的研究讨论只保存决定，不强行创建版本节点。

诊断和探索如果属于本轮已批准范围，可作为独立实验登记；研究设计改变后作为新实验或新轮次并明确批准，不让未记录probe直接变成确认性证据。所有尝试在台账可见。

进入论文阶段由iterate和用户按 [五项研究判断](research-transition.md) 决定，核心贡献仍靠未来实验成立时继续研究；停止投入与进入写作不同。`paper-package.md`只整理已确认内容及限制，不能直接把所有supported命题当论文贡献。发行版的golden_metrics需后续明确选择与验证，不从节点标签推断。

## 旧消费者

当前后期skills不按success/failure、keep率或supported即创新来判断；历史项目记录可能仍带有这些旧含义。接收新版schema_version=2时先核对语义，不能静默转旧值；原历史记录保留，实际用到时说明缺失信息与不确定性，不批量伪造迁移。

## W&B 运行关联

已接入W&B的代码实验按 [共同记录](../../wandb/references/experiment-records.md) 保留原研究轮次/实验/重复/attempt与Git定位，W&B只补充运行日志、配置和产物查询。每次独立尝试默认一个run，身份双向保存；重启/恢复不覆盖旧尝试，同步成功不等于运行成功或证据有效。复现与论文批次可独立记录，不强行创建idea轮次。研究决定仍由原文件保存，实例/run身份和必要查询快照随证据交接。
