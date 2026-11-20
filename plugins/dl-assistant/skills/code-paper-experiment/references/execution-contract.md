# 共同实验记录、重复、汇总与交接

## 目录与来源

按项目约定使用唯一批次目录，例如experiments/<batch_id>/，保存plan.json、run-spec.json、experiments/exp-<id>/及必要文件。不同批次/修订不共用一个可变run-spec；旧批次保留，恢复同尝试与新尝试分别记录。包里路径相对包根，实验记录内路径相对实验目录；指针核真实文件/校验值，不只检查字符串包含configs。

run-spec：schema_version=2、batch_id、plan_ref:{path,sha256}、experiments。计划副本schema2且有批准记录；experiments[].exp_id唯一，计划集合与执行集合一致。每项type为实际操作（training/evaluation/diagnostic/ablation/analysis/probe/theory），design_mode明确；plan的execution_type优先，type可保留论文角色（main/comparison/efficiency/qualitative等），不按论文角色推断训练。

每项另有design_record:{path,sha256}，与实际meta一致并核设计副本内容版本；每项另有expected_replicates:[{id,seed}]（seed可null，无随机重复也可有main一次操作）、source_snapshots:[{path,sha256,role}]、condition_review_ref:{path,sha256}、approval:{status,basis}、purpose、depends_on。明确入口/完整命令、资源和停止/调整规则写在设计副本中，不由检查器执行命令。

plan和run-spec全部输入版本须真实；增加/改科学设计保存新批准计划与批次来源关系，不把旧计划改成从来如此。

## 实验meta与复用检查

meta.json沿用code-idea-execution schema2的purpose/type/design_mode/status/status_reason、设计副本、commit/diff、attempts、required_artifacts、data_validity和inference_status等字段；报告与设计可独立于训练。实际data/model来源、解析配置和实现语义仍需人读核查。纯人工理论核查可明确execution_basis=manual，不补假git commit；真实代码执行仍需实际代码版本。共享检查器在完整run中核全部声明产物，在包中只核记录/设计/报告，声明产物由包清单逐项核。

扩展batch_id、condition_review_ref、source_snapshots（与本项run-spec完全相同的不可变来源）、replicates、paper_self_checks。

replicates每项{id,seed,status,selected_attempt_id,selection_reason,metrics_ref}。每个批准重复都列，未完成也列原因；selected_attempt_id仅指该重复的真实成功尝试，不是新seed。metrics_ref可null（纯图/理论等无数值读数），否则{path,sha256}。

attempts在共享字段上明确attempt_id、replicate_id、status、exit_code、command、resume_from；ID唯一，恢复源须是本实验更早的真实尝试。completed代码尝试需exit_code=0；明确execution_basis=manual的人工理论核查不填进程退出码，使用manual_record_ref:{path,sha256}记录实际推导/核查。其他状态明确原因/实际退出；全部尝试和实际代码/配置/数据上下文保存，不只选中尝试。各attempt保存source_refs指向该次实际来源快照，不按旧commit假定没变。与本批批准source_snapshots不同的工程调整需deviation_ref，对应deviation的id、approval:{status:approved,basis}和changes_scientific_design=false；旧尝试仍引用其原文件，不覆盖成新配置。科学设计变化另立新版批准计划/批次，保留旧批来源关系。

paper_self_checks含acceptance、pre_run、handoff，值为{status:clear/limited/needs_revision,basis,unknowns,effect}。已启动才强制pre_run，交接前核handoff；当前needs_revision可交待解决记录，但检查结果标未完成。每项影响条件的deviation另含condition_check同结构。自查不另设逐项批准或独立agent。

## results.json与有限复算

结果含schema_version=2、batch_id、exp_id、status/data_validity/inference_status（与meta一致）、replicate_ids、n_replicates、metrics、summary_checks、observations、limitations。replicate_ids是实际选中完成操作的精确ID集合，不按目录数量或seed数猜；n_seeds仅旧字段，若提供则必须对应实际成功seed数。

每个metrics内数值通过summary_checks声明核对，未覆盖的数值标待核查。每项{id,reported,operation,inputs,replicate_ids,decimals,ddof}：
- reported为本results中/metrics/...的JSON Pointer；输入每项{path,sha256,json_pointer}，来源不能是results本身。mean/std/sum/count/direct为有限支持的运算，std明确ddof。
- mean/std等对应重复读数时，inputs与replicate_ids一一对应，引用被选中重复的metrics_ref，种子/尝试和源字段不能偷换。标量复合分析可用direct引用实际分析输出；它只核输出一致，不认证分析方法，保留脚本和数据依据。
- decimals是明确展示精度，按十进制ROUND_HALF_UP核对；原始分母、单位、选择与不确定性仍需语义核查。不用通用容差掩盖计算差异。
- 不支持的分析不能伪装mean或success；保留实际输出并说明未自动复算范围。n=1不填样本std=0，按设计说明不可估计/不适用。

completed需有结果记录但metrics可空；未执行/失败不强造数值。结果只是观察与推断范围，不要求阳性。

## 包级三份索引与来源

保留experiments-actual.json、results.json、pkg-meta.json三名；均有schema_version=2、batch_id、同一plan_ref与run_spec_ref:{path,sha256}，包内保存对应不可变快照。

- actual.experiments_actual逐项列exp_id/status/data_validity/inference_status/reason/meta_ref/results_ref，覆盖所有计划ID。not_started/blocked/cancelled可无实验目录但必须如实说明；不把未开始写成运行失败。
- 包级results.experiments保存实际results.json对象，与actual.results_ref文件和meta逐项一致；无结果项可不出现在results集合，不能多出未登记结果。所有副本/状态/计划引用双向对账，重复ID不按集合去重吞掉。
- pkg-meta.experiments列exp_id/status，与actual一致；resources记录实际CPU/GPU/时间/存储等适用资源，未知写未知，不统一填GPU-hours或0。
- artifact_manifest每项{exp_id,artifact_path,path,sha256,format,disposition,availability,purpose,required_for_interpretation,missing_effect}。artifact_path为原实验目录内逻辑文件；disposition=copy/reference，copy实际路径须在包内，reference可为外部真实位置。availability=accessible/unavailable/not_checked。缺失/未知保留影响，不能把指针当已取到；关键小型证据优先复制，权重/完整log按用途和授权决定。

包中meta/design/报告及代码diff等小型记录保留于experiments/<exp_id>/；required_artifacts按当前状态逐项被manifest覆盖。来源配置、原始指标等可在包内或通过manifest外部引用解析；文件缺失导致检查未完成，不隐瞒或重跑填齐。包应在接收机器再次核可用性，GPU上可访问不代表本地可访问。

## 退出与下游

0为所声明记录检查完成（可以含failed/blocked记录）；1为错配/结构/汇总错误；2为用法错误；3为部分记录/来源/复算未完成。输出同时说明执行状态，不把0称全实验成功。模板只是字段说明，不是完整JSON Schema或科学质量认证。

writing-paper按具体批次/版本接收，更新证据表与数值来源；核心发现变化返回iterate。release核具体结果、条件、代码和所需资产，不自动继承一个全规模或平均性能标签。旧格式要明确核查/转换，不改写历史读数和原设计。

## W&B 关联

启用时meta.tracking和各attempt.wandb按 [共同记录](../../wandb/references/experiment-records.md)；scope_id为batch_id，experiment_id为exp_id，重复与恢复仍按本契约核对。共享检查器会验证声明的tracking及本地快照。交接时configuration_ref、dirty diff及snapshot_ref指向的小型文件随包保留实际相对路径并纳入artifact_manifest，快照的config身份/哈希不可重写；synced不代替包可移植性、原始读数复核或数据有效性。原始W&B恢复目录可留服务器，记录recovery_ref；接收端未取得时为UNCHECKED/退出3，不能因未同步而改成执行失败。在源服务器核恢复目录时仍使用严格的单实验检查。
