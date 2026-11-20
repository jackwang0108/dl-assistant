# 逐目标复现记录与交接

默认docs/code-paper-reproduction/<实际日期>-<slug>/，尊重用户指定位置。保存spec.md、reproduction.json、report.md、alignment.md、runs/<唯一run-id>/及实际必要产物。失败/未决/部分结果同样保存，新运行不覆盖旧日志或原协议。大资产保留实际位置、身份与可取得条件。

## reproduction.json

新版schema_version=2。以下是未执行结构示例，null/空值不是验证成功；按实际目标增加/删除条目，无关或未知明确说明，不复制示例为真实证据。

```json
{
  "schema_version": 2,
  "tracking_ref": null,
  "created_at": null,
  "updated_at": null,
  "status": "not_started",
  "inherits": {
    "setup_report": null,
    "survey_report": null,
    "source_spec": null
  },
  "components": [],
  "environments": [],
  "sources": [],
  "targets": [
    {
      "id": "T1",
      "requirement_ids": [],
      "survey_task_ids": [],
      "component_ids": [],
      "purpose": null,
      "target_type": "evaluation",
      "requested_scope": "original_conditions",
      "reference": {
        "source_refs": [],
        "location": null,
        "conditions": null,
        "reported_result": null,
        "statistic_definition": null,
        "limitations": []
      },
      "protocol": {
        "id": "P1",
        "version": 1,
        "status": "draft",
        "conditions": null,
        "basis_refs": [],
        "comparison_rule": null,
        "comparison_basis": null,
        "repetition_plan": null,
        "analysis_plan": null,
        "budget": null,
        "approval_ref": null
      },
      "comparability": {
        "status": "unresolved",
        "items": [],
        "limitations": []
      },
      "execution_status": "not_started",
      "run_ids": [],
      "data_validity": "unassessed",
      "uncertainty": {
        "sources": [],
        "design": null,
        "raw_result_refs": [],
        "analysis": null,
        "limitations": []
      },
      "assessment": "not_assessed",
      "finding": null,
      "evidence_refs": [],
      "use_scope": {
        "supported_uses": [],
        "unsupported_inferences": [],
        "remaining_checks": []
      },
      "gap_investigation_ref": null
    }
  ],
  "runs": [
    {
      "id": "RUN1",
      "target_id": "T1",
      "protocol_id": "P1",
      "protocol_version": 1,
      "status": "not_started",
      "code_refs": [],
      "environment_id": null,
      "config_refs": [],
      "data_refs": [],
      "checkpoint_refs": [],
      "randomness": null,
      "selection_rule": null,
      "command": null,
      "working_directory": null,
      "started_at": null,
      "ended_at": null,
      "exit_code": null,
      "log_path": null,
      "result_paths": [],
      "observations": [],
      "resume_from": null,
      "deviations": []
    }
  ],
  "gap_investigations": [],
  "low_cost_configs": [],
  "self_checks": {
    "before_execution": [],
    "before_handoff": []
  },
  "survey_task_responses": [],
  "ready_commands": {},
  "checkpoint": {},
  "resource_observations": [],
  "changes": [],
  "remaining_tasks": [],
  "next_step": null,
  "revisions": []
}
```

### 来源与目标

inherits指实际取得的setup/survey/研究说明路径及版本，缺文件不伪称已读。components/environments引用或保存当前实际身份/commit+diff/配置/资产和环境上下文；不能只继承旧conda_env、repo_role或ready_commands后声称前置全部满足。sources每项含id、类型、URL或实际路径、版本、取得时间与读取/运行范围。

target_type=evaluation/training/behavior；可有多种目标，不强制成对出现。requested_scope=original_conditions/modified_conditions，说明目的：复现报告原条件，还是验证明确修改条件下的参考/行为。reference记录真实出处、位置、原条件、报告的统计量/单位/选择过程和限制；无数值参考不编数字，行为参照写具体定义/答案及出处。

每目标协议记录原条件与实际条件，至少包括相关模型/结构/初始化/权重来源、数据版本/split/样本分组、预处理/采样/排除、指标实现/参数/单位/聚合、训练与保存/选择流程、设备/精度/随机性。按实际目标适用，不要求行为检查填训练参数。源配置与实际展开配置均可追踪，不能只记配置文件名。

protocol.status=draft/approved/amended，approval_ref指实际授权/确认，已有授权可复用。条件或规则变化保留旧协议和run的对应版本，在changes/revisions写原因/影响/授权；不能看结果后覆盖旧比较界限或预期。fields为空的示例不是可直接执行的计划。

### 可比性、执行与判断分开

comparability.status=matched/different/unresolved/not_applicable；items逐项写原参考、实际设置、same/different/unresolved/not_applicable、来源与影响。not_applicable须说明原因，不用来跳过必要条件。matched只是所核条件相符，不证明所有实现行为相同。

顶层status与targets.execution_status可用not_started/in_progress/completed/partial/blocked/failed/cancelled，指执行/分析任务是否按本轮范围完成，不表示参考结果已复现。runs.status用not_started/running/completed/failed/blocked/cancelled记录实际运行。退出0不自动完成目标分析，缺退出码先核实际状态，不据其断言任务仍运行。

data_validity=unassessed/valid/limited/invalid，写具体问题和影响范围。不能由命令退出0或格式齐全自动填valid，也不能把局部异常推广全仓库。

assessment：
- consistent_with_reference：在声明条件、有效证据和有依据的比较办法下与参考一致；不认证整体实现或跨规模推广。
- discrepant：有效且可比的证据显示与参考不一致，说明差距、规则与范围；原因可以未知，不等于假设错误。
- insufficient_evidence：信息/重复/参考不足，或有效范围不足以作目标判断；说明具体缺口。
- not_comparable：条件不同或未知使当前目标无法直接比较，不能用近似数值或放宽界限宣称原条件已复现。
- not_assessed：尚未判断；not_applicable仅目标不适用，说明原因，不代替未完成。

原条件目标若实际条件有实质差异，不填consistent作为“原条件复现”。改条件结果若有自己的有效参照，建立对应modified_conditions目标并保留原目标的未决，不更名掩盖差异。无有效数据不能填consistent/discrepant；有限数据需明确它是否足以支持本目标、不能推广哪些范围。

findings、assessment与evidence_refs要对应实际run/来源。use_scope记录当前证据支持的具体用途、不能推断内容及所需补验；不是无限授权后续方法比较。偏弱或条件不明的实现不能仅靠“报告了限制”就用来宣称研究提升，需iterate/用户结合公平比较与设计决定。

### 运行、随机性和选择过程

runs保留全部相关尝试，精确绑定代码commit及未提交diff、环境、实际配置、模型/数据版本或内容校验、采样/seed、日志/退出状态、结果路径及恢复来源。每次重启保留独立记录或attempt，不覆盖原输出。不知道身份/条件就说明，不能补示例设备、性能和路径。

observations逐项给实际读数/行为、单位、分母或样本/分组范围、结果来源；原论文值和本次观测分开。选择最佳checkpoint、平均权重、按验证集选择等流程写selection_rule与实际执行，不能只留下最好seed或最接近参考的运行。

uncertainty分别记录数值误差、训练随机性、评测随机性、数据抽样/分组等实际来源、设计/重复单位、逐次读数引用、分析办法/依据和限制。未测标准差就未知；有标准差也不转成固定复现容差或未来差值裁决。已有参考仅报最佳值/统计含义不明时保留限制，不凭任务名套band。

resource_observations绑定实际run/模型/输入/设备/精度、测量方式与范围，实测与估计分开。批准预算、实际消耗和剩余任务可查，不把短检查估计写成确定全训练耗时。

### 差距调查、自查与低成本配置

gap_investigations每项含id/target_id、观察与来源、competing_explanations（主张、支持/反对、未知和区分办法）、checked_items（检查范围/已排除或受限解释）、next_check（信息价值、成本/授权或选择不做）、current_finding/unknowns与对use_scope影响。可引用alignment.md具体位置，不强写唯一根因。

self_checks.before_execution/before_handoff按主文件必查项记录check、status(clear/limited/needs_revision)、finding、证据/版本、unknowns与effect。已有材料直接引用，不另写自查JSON或脚本；需要修正时保存实际问题和受阻目标，不把它改成通过以完成流程。

low_cost_configs可为空；有需求时每项含id、用途、状态(proposed/executed)、原target/protocol、实际配置/差异、run/结果引用、支持范围、不能推断内容、预算/批准及未决。详见reduced-setting.md；不填scale_sweep、scaling_law_confirmed或任何由baseline拟合得出的新方法外推认证。未运行的建议不列可直接使用入口。

survey_task_responses逐条映射原任务/owner、target/run、实际观察、回答的未知、限制和剩余责任。不属于本轮执行的科学实验/准备任务只移交，不写本次已完成。

ready_commands/checkpoint保留定位入口，分别指实际run和资产身份/条件。命令字符串无环境/工作目录/协议/范围就不够用；少量样本运行不能冒充完整训练命令已验证。自训权重不是所有后续微调的强制起点，来源选择由问题和批准设计决定，保留公平比较及选择过程。

changes/revisions保留协议/代码/资产/解释的变化原因、前后版本、实际授权与受影响目标。next_step说明继续验证/返回准备或研究讨论/暂停等实际建议与用户决定，不能自动推到后期。旧记录历史保留，未取得来源保持未知。

## report.md

```markdown
# 本轮复现与验证报告
> 日期、实际目标与范围、来源、当前协议/代码/config/环境和资产身份。

## 1. 逐目标结论与用途
目标/原条件或改条件 | 实际证据 | 可比性 | 有效范围 | 参考判断及依据 | 支持/不支持哪些用途 | 未决/下一步
部分完成、受阻和差距同样交付，不用整体可信布尔值概括。

## 2. 协议、参考和实际条件
原文/发布身份及位置、统计量含义；版本化协议、实际差异/未知和影响。

## 3. 运行与分析记录
目的、原预期/比较依据、实际命令/上下文、逐次读数/选择、日志/退出、数据有效范围、随机性/抽样及分析限制。
已有材料可引用，但必要结论要让读者能理解，不禁止正文出现关键数值。

## 4. 差距调查
观察、竞争解释、支持/反对、已排除/仍未知、最有信息且成本合理的下一项检查或不继续的理由；详见alignment。

## 5. 低成本配置（仅实际讨论/执行时）
用途、condition_review_ref 与条件记录版本、目标和实际条件差异、必须保留项的落实证据/未知、当前结果/成本、解释范围及目标验证触发点；不写自动规模外推认证。

## 6. 自查、变更与交接
执行前与交接前自查的具体依据和行动影响，全部相关偏差/失败、版本修订和survey任务回应。
给prepare/reading/execution的具体入口、条件、用途与限制；旧消费者需核对的新语义。
需要继续研究的关键验证不因规模或机器转成论文补实验。用户代码阅读仍必经，清理按实际需要。
```

## alignment.md

按目标写参考条件—实际条件—证据—差异/未知—影响的对应表，再记录竞争解释和后续查证。它是调查记录，不要求最后每项都“查明根因”。来源或实际条件改变时留修订，旧推断不升级成事实。

## 旧字段和消费者

旧eval_判定/training_判定、trustworthy_for_delta、evidence_strength、frozen/mutable组件列表、noise_floor、reduced_setting.scale_sweep及里程碑tag都不能自动转换成新版结论。历史原数据/日志可按实际条件重新核，但旧标签不认证实现、比较公平或跨规模推广；不批量迁移原项目。

prepare与code-reading已按保留用途/实际变更与证据范围接收；后期消费者仍将在各自审查时同步。交接说明schema_version=2和具体target/run/use_scope；不认识新格式时先核对，不回退一个整体布尔值，也不把新协议/检查范围压成旧双轨认证。

## W&B 来源与同步交接

tracking_ref 指向项目的非敏感配置及版本；按 [共同记录](../../wandb/references/experiment-records.md) 保存实例、SDK/MCP验证范围及运行身份。执行、同步和有效性分别报告；保留所有尝试、本地关键结果、实际查询快照与校验值，缺失不补造，不写凭证。
