# 规划范围明确的补充实验

先读研究交接、证据表、已有实验和实际待办。每项需求说明要减少哪个未知、可能结果对核心判断的影响及已有证据能否复用。核心现象、有效性、贡献意义或目标条件下关键收益仍未知，交 iterate 设计、execution 执行，不按规模/seed/主表名称分工。

1. 核 [研究条件](../../../dl-assistant/references/research-conditions.md)：问题/假设版本、目标与本轮条件、必须保留/可缩减/未知、实际检查与解释范围。低成本配置无永久认证；短训练不替代后期现象。
2. 按需要选比较、测量、分析、可视化或稳健性任务，不强制消融、两个数据集、性能提高或固定 seed 数。必要对照和样本/重复由问题与不确定性决定，不填通用成功百分比。
3. 每实验说明 exploration/confirmation、目的、实际配置/数据版本、比较与公平性、读数/统计、可能结果与解释规则、界限依据或未知、所需产物、预算依据及暂停条件。探索不强求方向性预测；事后发现不能伪填预登记。
4. 设置依赖和可复用结果。配置会影响比较时在相关运行前明确冻结版本，修改需记录；不是所有论文都要先扫参数或逐组件去掉。调参使用预先允许的数据，不能根据测试结果反复选配置。
5. 对“能否回答该补充问题、关键条件是否保留、各种结果如何解释、投入是否批准”作具体自查。已有授权直接沿用；新投入或科学比较变化将具体计划交用户确认。
6. 保存递增版本 plan-vN.md/json，旧计划不覆盖；两份表达相同实际设计，差异先修正再交 CPE。不要自动传输或重复启动实验。

保留用于定位的字段：保留 exp_id/type/paper_claim/claim_cids/priority/decides_config/depends_on/config/purpose/expected_signal/fairness/expected_cost/output_to_paper，扩充 design_mode、analysis_plan、interpretation_plan、condition_review_ref、required_artifacts 和 approval。expected_signal 是解释规则摘要，不是保证阳性；当前CPE按下述schema2接收；历史记录或旧运行进程不支持时先核对接口，不能压成“训练+多seed+success”继续运行。

## 交新版code-paper-experiment

计划schema2明确execution_type（实际操作）与type/paper_role（论文用途），expected_replicates的真实ID及seed或null，研究条件、依赖/资源、允许调整与批准记录。无随机重复可是一项main操作，不强制训练、多seed或搜索。执行者将真实入口/源快照/设计副本绑定到唯一batch_id的run-spec，不在原计划上悄改。

接收不齐全/失败记录时判断具体证据范围，不为让包通过而要求重跑到成功；must表示原计划重要性，缺失后的科学影响和下一步需实际判断。
