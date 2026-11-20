# 问题清单与证据结构（schema_version=2）

输出绑定run_id、mode、paper路径/sha256、材料快照、run_sha256、completion、task_statuses、venue、isolation与实际生成来源。problems保留结构化意见，disputes保留争议，dispositions保留原意见如何处理，rechecks保留复查。它是本轮意见记录，不是独立科学事实来源。

## 每条issue/problem

- id：任务内唯一issue ID或最终稳定问题ID。
- description、target_claim、impact：具体问题、影响的主张及影响理由。问题未核清时明确未知。
- finding_status：confirmed/partially_supported/unsupported/unverified，与严重程度分开。
- severity：critical/major/minor/suggestion/undetermined，按实际影响说明，不由类型自动定。
- evidence：证据数组，每项{kind,material_id,location,observation,excerpt?}。kind可为text/figure/table/equation/cross_reference/absence/external/author_response；excerpt可省，不因无逐字原句丢意见。
- text注明实际原文位置；图/表/公式注明可定位对象与观察；跨处矛盾列多项对应位置；absence注明查过的材料/范围及没找到什么（不是证明全项目不存在）；external引用初始声明材料或任务external_sources中的实际来源快照及阅读位置；新取得来源作为本轮审查输出保存，不事后改写初始输入。只有摘要或元数据时明确范围，不能伪称全文已核。
- uncertainty：未决数组；clarification_needed：需要澄清什么；suggested_actions：可选办法数组，可空。不强制唯一修复实验，也不强制reviewer制定作者的最终关闭判据。
- self_check：{status,basis,unknowns,effect}，重要问题形成前的依据/影响核查，不只勾选。
- 综合problem另有source_refs：[{task_id,issue_id}]，保留全部原意见来源。综合者新增问题用自己的issues作为来源，不制造原审稿人说过的话。

问题依据暂不足可以unverified并说明，不直接删除；有明确反证才记unsupported。无任何可定位依据的疑问不能称confirmed，应补核查范围或列未验证问题。所有证据项只是声明，脚本不能确认图像、引用真实性或缺失事实。

## 综合与复查

dispositions每条{task_id,issue_id,outcome,problem_id,reason,evidence}；outcome=included/merged/not_supported/needs_check。每条原issue覆盖一次，纳入/合并/待核查对应problem；不支持也保留原问题和核查理由。

disputes每条{topic,source_refs,judgment,basis,evidence,remaining_unknowns,next_actions}，judgment同finding_status。不存在分歧可空，不强迫制造分歧，也不把同源多数当独立证实。

rechecks每条{prior_problem_id,status,reason,evidence,new_problem_ids}，status=resolved/partially_resolved/unresolved/not_checked。指定范围全部覆盖，缺资料用not_checked；范围外保留未检查，不能悄悄消失。

## 下游接收

response必须用具体路径和论文版本，不取最大round。结合证据、finding_status、severity和impact重判；不能把待核实问题自动当事实、自动决定补实验或把合规疑问直接批准为修改。核心研究未决转iterate；仅表达/已明确补充工作走writing-paper。

旧severity=致命/改进、type=指控成立、verbatim_quote与close_criterion仅历史字段；不自动映射为当前已核实结论。可以保留旧意见重新分析，但不能伪填新证据或复制成新版通过记录。
