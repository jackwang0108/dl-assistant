# 准备报告、操作证据与机读交接

按任务即时记录实际操作与结果，最终汇总每项操作的范围，不把最终回忆写成执行证据。保存setup-report.md与setup.json，路径尊重用户和项目约定；新任务不覆盖旧报告。

## setup-report.md

```markdown
# 本轮环境与入口准备报告
> 日期、当前目标、项目/机器、来源survey与spec/plan；本次实际检查范围。

## 1. 当前能做什么
操作 | 对应需求/组件 | 已检查的具体条件/范围 | 证据 | 未验证/受阻事项 | 下一步
没有运行的入口不写已验证；少量样本不称全量，部分完成不伪装失败或成功。

## 2. 来源与版本
实际用户决定、上游schema、全部组件/版本/角色；真实代码commit和未提交diff；配置/资产/环境身份。
survey的静态预判与本次实际观察分别写，差异核对版本/条件，不简单以新数字覆盖旧记录。

## 3. 执行前自查和任务记录
目标、预期依据、改动/授权与范围；已知/未知及对执行的影响。
每任务记录对应操作/R需求/survey任务、目的、输入条件、预期行为及依据、实际命令/工作目录/环境、代码/config/数据/权重、日志/退出状态、观察、解释范围、失败/偏差与后续。
进程状态和检查结果分开；没有有依据预期时记观察和待调查。

## 4. 资产、转换与改动
原始与派生数据身份/数量/划分/单位、转换规则与对应检查；权重使用/遗漏/额外/有意初始化；环境与依赖改动。
每改动给原因、影响、验证和实际授权，未决保留；不因让程序执行而改研究设计。

## 5. 实际资源与随机性
测量条件/方式、实际观察、估计依据与未知分开；一次短运行不代表全规模成本。
实际随机性设置与位置、是否修改及授权，不因设seed就声称结果完全可重复。

## 6. 交接前自查与survey任务回应
已检查结论是否有证据、范围是否夸大、改动是否按规则检查、需求/多组件是否遗漏、剩余责任是否明确。
逐个survey实测任务给实际证据、限制、仍未知和后续owner；其他阶段任务只移交，不填本次完成。

## 7. 下一步与恢复
给reproduction的验证目标/协议和未决可信度、给code-reading的实际环境/源码/入口；需要返回选型或研究讨论的具体问题。
已有任务状态、资产完整性/版本、检查复用条件、提交状态与恢复位置；不默认merge/push或重复启动。
```

## setup.json

schema_version=2。以下是尚未执行的结构示例；不把占位、空值或文件存在当作已完成检查。实际只建立本轮需要的操作、环境和检查，允许不同组件用不同环境。

```json
{
  "schema_version": 2,
  "tracking_ref": null,
  "created_at": null,
  "updated_at": null,
  "status": "not_started",
  "goal": null,
  "source_survey": null,
  "source_spec": null,
  "requirements": [],
  "survey_task_responses": [],
  "repo": {
    "name": null,
    "url": null,
    "branch": null,
    "commit": null,
    "dirty": null,
    "diff_path": null
  },
  "repo_role": null,
  "components": [],
  "sources": [],
  "environments": [],
  "conda_env": null,
  "operations": [
    {
      "id": "O1",
      "purpose": null,
      "requirement_ids": [],
      "component_ids": [],
      "status": "not_checked",
      "check_ids": [
        "C1"
      ],
      "supported_scope": null,
      "limitations": [],
      "remaining_tasks": []
    }
  ],
  "checks": [
    {
      "id": "C1",
      "operation_id": "O1",
      "layer": "component",
      "object": null,
      "input_conditions": null,
      "expected_behavior": null,
      "basis_refs": [],
      "context": {
        "component_ids": [],
        "environment_id": null,
        "code_refs": [],
        "config_refs": [],
        "data_refs": [],
        "checkpoint_refs": [],
        "device": null,
        "precision": null,
        "mode": null,
        "randomness": null
      },
      "execution": {
        "status": "not_started",
        "command": null,
        "working_directory": null,
        "started_at": null,
        "ended_at": null,
        "exit_code": null,
        "log_path": null,
        "output_paths": []
      },
      "result": "not_checked",
      "observations": [],
      "interpretation": null,
      "limits": [],
      "follow_up": null
    }
  ],
  "supported_operations": [],
  "ready_commands": {},
  "data": {},
  "checkpoint": {},
  "blocked": [],
  "resource_observations": [],
  "reproducibility": {
    "observed_settings": [],
    "unverified": [],
    "changes": []
  },
  "changes": [],
  "paper_metrics": [],
  "validation_targets": [],
  "self_checks": {
    "before_execution": [],
    "before_handoff": []
  },
  "dataset_report": null,
  "env_export": [],
  "smoke": null,
  "remaining_tasks": [],
  "revisions": []
}
```

### 状态与需求映射

- 顶层status=not_started/in_progress/completed/partial/blocked/failed/cancelled，只描述本次约定准备工作的执行情况。completed也不表示全部仓库链路或科学可信。
- requirements引用survey/研究设计的R编号及条件；独立任务可自行建明确需求。survey_task_responses每项含原task_id/owner、对应operation/check、实际状态、证据、回答了什么、仍未知与下一步owner。要移交的任务不填完成。
- operations.status=not_checked/in_progress/checked/partial/blocked/failed/not_applicable，分别保存范围与限制。checked必须有本轮必要检查的实际证据；失败/未查/部分操作不能用一条命令无异常代替。not_applicable需理由，不替代未完成。
- checks.result=matches_expected/investigate/conflicts_with_expectation/not_checked/not_applicable，与execution.status（not_started/running/completed/failed/blocked/cancelled）分别记录。退出0不推导符合预期；有与预期冲突/需调查/未执行的必要项时，不把受影响操作列为已支持。
- execution.status=completed表示过程已结束且对应运行记录完整，不认证行为正确；命令执行失败应failed，缺退出状态先核实，不能当still running。输入不符合测试约束也需说明，不能把测试缺陷写成原模型错误。

### 实际身份与运行上下文

repo保留主要仓库兼容入口；components列全部实际组件，含id、survey candidate_id、roles、路径、来源/revision、实际commit与dirty/diff、配置/资产关联和改动。没有主要仓库可null，不虚构一个repo。环境/权重/数据身份变化后核受影响检查，历史结果仍保留来源。

environments每项含id、kind（conda/venv/container/system/other）、实际激活/调用方式、运行目录、解释器与依赖版本、平台、必要设备/驱动/运行库、构建工具（需要时）、导出/构建记录及来源。容器额外记镜像来源/digest、必要挂载与运行条件；conda_env只存主要conda环境名，不适用为null，不改作容器名。env_export只列实际存在的相关导出记录，不要求五件套。

sources条目含id、类型、实际URL/路径、版本、读取/运行时间、范围，给basis_refs和原文/代码位置引用。paper_metrics保留来源声明和条件，调查/准备核对了哪部分写明；不是setup已复现。validation_targets关联实际组件、协议/参考来源、已核对范围和交reproduction的未知，不由repo_role决定。

每项check的context绑定实际代码commit+diff（如有）、配置文件/值与版本或内容校验、数据/权重版本/校验和样本ID、环境/设备/精度/模式等与操作相关条件。无关条件可null但说明不适用，未知不能填示例规格。command、working_directory、环境选择、实际覆盖样本/步数、日志、退出码和输出路径保存到execution；当时未提交的代码要保留diff，不能只记HEAD。修改后的条件不继承旧通过。

检查阶段的配置另存，不能覆盖正式实验参数；--help、dry-run、合成输入、小样本和完整运行的范围明确区分。自造教学输入不充当真实数据记录。检查时异常/失败、尝试过程和批准修改保存到changes或任务记录，不只保留最终成功配置。

### 资产和检查结果

data和checkpoint以资产ID为键，每项记录来源身份、实际路径、配置/版本、状态和对应检查。可用status=not_obtained/partial/obtained/checked/blocked，检查范围另列；obtained不表示读取/加载已验证，checked不表示数据全部正确或科学有效。完整性依据、原始/派生关系、转换脚本、样本计数/划分/单位、实际权重覆盖与遗漏另附细节/来源。

supported_operations每项记录operation_id、具体范围、所依据check_ids、代码/环境/资产条件和限制，**不是一组宽泛“ready”布尔值**。仅在必要检查符合预期、无未解决关键冲突且条件对应时填写；调查未决可交部分结果，不支持其受影响范围。

ready_commands只保留旧消费者定位用的命令字符串映射，每条都必须指向对应的supported_operation和实际入口check；详细工作目录/环境/配置见checks。仅import、--help或组件检查通过不能填完整eval/train入口。train_smoke只表示当时短运行范围，不外推正式训练；没有已检查入口就空对象，不补造可运行命令。

blocked每项说明受影响operation/asset、原因、实际证据、解除条件与owner；无关事项可另记剩余任务，不把本轮未包含的大训练自动归为失败。

### 资源、改动、自查与恢复

resource_observations每项记录对应check/运行、设备、模型/输入/batch/精度、训练或推理、测量方式/预热/范围、实测显存/耗时等实际数据及限制；估计另标并给依据。不能将短运行结果填成完整训练能力，CPU任务不虚构开发卡。

reproducibility.observed_settings记录实际设置与代码/config位置（seed、采样/worker等适用内容），未知用null或unverified，不以“未设”代替未查。changes保存设置变更及依据/授权，不自动强改确定性。

changes每项含时间、对象、前后版本、原因、对数据/计算/比较影响、批准范围/实际授权、验证与限制。self_checks.before_execution/before_handoff每项含check、status(clear/limited/needs_revision)、finding、证据/版本、unknowns和effect；已有证据直接引用，不新增自查JSON/脚本。needs_revision先处理或如实交受阻事项，不能同时给“已就绪”结论。

dataset_report、env_export、smoke/检查脚本只引用实际生成的文件；无需时null/空数组并说明。不要求每次有图像或数据样本导出。revisions保存旧结论、变化证据、原因与影响，不批量覆盖历史。

恢复时核正在运行任务、环境/代码/config/资产与记录版本、完整性和检查范围，再决定复用或重跑；文件存在不代表完成，报告也不是不需核查的事实。人读报告与JSON即时对应，实际执行有新证据时保留原预期与修订，不把事后观察改写为原本预期。

## 旧消费者与边界

reproduction、prepare与code-reading已按实际目标/用途和行为证据接收新版；当前后期skills按实际来源与检查范围接收；历史项目中的conda_env、ready_commands、data/checkpoint或smoke仅作为定位入口。交接明确schema_version=2、主要入口与全部组件、检查范围及未决；接收方先核对语义，不认识字段时不能忽略多环境/多组件或将checked读成研究可信。旧JSON缺信息是未知，不假装已迁移；旧字段仅帮助定位，不恢复旧的统一数值判据。

## 研究条件核对（与本轮用途有关时）

引用条件记录的路径和版本，写明目标与实际条件、必须保留项的代码/配置/数据位置及检查证据、未知/偏差、所查范围和不能外推的内容。记录下一次目标条件验证的触发点或不适用理由。按本 skill 职责分别说明静态调查、准备、阅读或实际运行，不能将尚待检查项写成已落实；条件或假设变化后重新核对。

## W&B 来源与同步交接

tracking_ref 指向项目的非敏感配置及版本；按 [共同记录](../../wandb/references/experiment-records.md) 保存实例、SDK/MCP验证范围及运行身份。执行、同步和有效性分别报告；保留所有尝试、本地关键结果、实际查询快照与校验值，缺失不补造，不写凭证。
