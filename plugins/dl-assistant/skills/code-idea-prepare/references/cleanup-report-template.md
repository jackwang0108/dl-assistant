# 代码整理记录与交接

保存cleanup-report.md与cleanup.json；按实际需要保存方案、检查结果和coverage/operation-paths.md。不强制有质量方案、覆盖采集或训练结果；未发生的工作不补造。报告在执行时逐项更新，保留未采用/失败/撤销和未知，不到最后凭回忆写。

## cleanup-report.md

```markdown
# 本轮代码整理记录
> 日期、目标/授权、项目/组件、上游准备/复现来源与范围。

## 1. 实际结论与选择
采用什么版本/本次diff，保留了哪些用途、批准移除或有意修复了什么；哪些检查有证据、哪些仍未知。
无改动/部分完成/未采用也是结果，不以tag、删除量或单指标接近认证基准。

## 2. 改前状态和保留范围
准确代码commit+原未提交diff、用户已有改动、环境/config/资产身份；所需操作、接口、配置和历史资产及依据。

## 3. 候选调查与覆盖范围
实际引用/配置/注册/外部入口/副作用/保存关系调查，覆盖的命令/配置/输入与工具限制。
候选的保留/移除建议/不确定及理由；未命中不叫死代码，调用记录不叫性能热点。

## 4. 逐项变更—行为—验证表
变更 | 类型/理由/授权 | 保留或有意改变什么 | 实际diff/前后条件 | 检查与依据 | 结果/限制 | 采用/未采用/撤销与原因
类型为preserve_behavior/remove_out_of_scope/behavior_fix，不把故意行为变化叫等价。

## 5. 执行与比较证据
改前/改后各自条件、命令/工作目录/环境、配置/模型/数据/输入、日志/退出状态、实际观察及分析依据。
离散身份/结构、数值、随机过程、接口/保存兼容按实际需要检查；未覆盖项与旧参考失效范围。

## 6. 差异调查与局部撤销
观察、竞争原因/已查证据、仍未知；撤销了哪项本次改动、实际状态及重验范围。
用户原改动和环境/资产是否保留；改前也异常则核前置/旧证据，不直接认证恢复。

## 7. 自查与下一步
执行前和交接前的判断、依据、未知与行动影响；未解决问题、对应责任/成本与实际决定。
给code-reading/执行的准确版本、保留用途、操作路径观察和检查限制，不从hot-path或旧tag推导未来必经/可信度。
```

## cleanup.json

schema_version=2。以下是尚未执行的结构例子，空值和草案状态不是成功。实际按范围增删条目，字段引用必须对应真实材料。

```json
{
  "schema_version": 2,
  "created_at": null,
  "updated_at": null,
  "status": "not_started",
  "goal": null,
  "authorized_scope": null,
  "inherits": {
    "setup": null,
    "reproduction": null,
    "research_spec": null
  },
  "before_state": {
    "components": [],
    "environment_refs": [],
    "config_refs": [],
    "asset_refs": [],
    "user_changes_ref": null
  },
  "retained_uses": [
    {
      "id": "U1",
      "purpose": null,
      "operation_refs": [],
      "interfaces": [],
      "configs": [],
      "historical_assets": [],
      "basis_refs": [],
      "unknowns": []
    }
  ],
  "candidate_investigations": [],
  "observed_paths": [],
  "changes": [
    {
      "id": "CH1",
      "kind": "preserve_behavior",
      "status": "proposed",
      "locations": [],
      "rationale": null,
      "basis_refs": [],
      "retained_use_ids": [
        "U1"
      ],
      "preserved_behavior": null,
      "intentional_change": null,
      "impact_and_unknowns": [],
      "authorization_ref": null,
      "before_refs": [],
      "after_refs": [],
      "diff_path": null,
      "verification_ids": [
        "V1"
      ],
      "revert_scope": null
    }
  ],
  "verification_records": [
    {
      "id": "V1",
      "change_ids": [
        "CH1"
      ],
      "retained_use_ids": [
        "U1"
      ],
      "purpose": null,
      "method_kind": "run",
      "input_conditions": null,
      "expected_behavior": null,
      "basis_refs": [],
      "comparison_method": null,
      "comparison_basis": null,
      "before": {
        "source_result_ref": null,
        "execution_status": "not_started",
        "context_refs": [],
        "command": null,
        "working_directory": null,
        "log_path": null,
        "exit_code": null,
        "result_paths": [],
        "observations": []
      },
      "after": {
        "execution_status": "not_started",
        "context_refs": [],
        "command": null,
        "working_directory": null,
        "log_path": null,
        "exit_code": null,
        "result_paths": [],
        "observations": []
      },
      "comparison_result": "not_assessed",
      "behavior_assessment": "not_checked",
      "finding": null,
      "limitations": [],
      "next_action": null
    }
  ],
  "uncertain_items": [],
  "reversions": [],
  "self_checks": {
    "before_execution": [],
    "before_handoff": []
  },
  "after_state": {
    "components": [],
    "environment_refs": [],
    "config_refs": [],
    "asset_refs": [],
    "user_changes_preserved": null
  },
  "handoff": {
    "selected_state_refs": [],
    "supported_uses": [],
    "unsupported_inferences": [],
    "invalidated_prior_evidence": [],
    "operation_paths_ref": null,
    "remaining_tasks": [],
    "next_skill": null
  },
  "revisions": []
}
```

### 现场、用途与候选

status=not_started/in_progress/completed/partial/blocked/failed/cancelled，只指本次任务完成情况，completed不表示所有输入/未来配置行为相等。goal/authorized_scope记录实际目标及授权，不自行推导全仓库重构权限。

before_state/after_state保存全部实际组件的路径/来源、commit、dirty与diff、环境/config/资产引用，不只记HEAD。user_changes_ref指本次前已有改动记录；user_changes_preserved=true/false/null须有核实依据，不能默认true。不可分离时保留未知/问题并讨论，不自动覆盖。

retained_uses逐项说明当前及已约定用途、所需接口/配置/历史资产、来源与未知。移除既有用途在changes.intentional_change明确，不通过删除本表条目掩盖支持范围缩减。before的已验证范围不自动成为after已验证范围。

candidate_investigations每项含id、位置、调查范围/真实来源、调用/配置/注册/外部入口/副作用/保存兼容关系、覆盖观察和限制、建议(retain/propose_removal/uncertain)及理由。不把静态工具/coverage输出当决定；来源未取得与已查无记录分别写。

observed_paths每项含操作、命令/工作目录/环境、代码/config/输入、执行状态、实际工具/配置、观测路径/结果位置、未观测和工具遗漏。路径记录不表示性能热点或每轮必经；沿用hot-path文件只作历史定位并标注实际含义。

### 变更与对应检查

changes.kind=preserve_behavior/remove_out_of_scope/behavior_fix。status=proposed/applied/kept/reverted/not_adopted，记录实际状态；kept不自动证明验证充分。未验证但保留工作中的改动须明确局限，不交“已确认无影响”的范围。

每变更关联受影响用途、实际位置/diff、来源/理由、意图保留的行为或有意改变部分、授权和局部撤销范围。移除用途说明迁移/文档/历史兼容处理；有意修复说明原问题与新要求、受影响原结论及再验证责任。研究方法或对照变化需研究讨论，用户批准说明授权不证明等价。

verification_records逐项绑定真实改前/改后上下文（实际代码commit+diff、环境/config/输入/数据/模型身份及来源）、预期/比较办法及依据、日志/退出状态/结果和观察。before.source_result_ref可引用真正相关的原结果；条件不适用不能复用，缺对照如实写未执行并说明影响。

method_kind=run/review区分实际运行与文档/diff等审阅；review记录实际审阅材料、时间和结论，不伪造命令。execution_status=not_started/running/completed/failed/blocked/cancelled仅过程状态，退出0不推出检查符合。非运行检查（如文档diff/引用审阅）明确类型、实际审阅依据与结果，命令/exit_code可null，不伪造执行。

comparison_result=no_difference_observed/difference_observed/insufficient_evidence/not_assessed/not_applicable。no_difference_observed只表示已查范围未发现差异，不证明所有行为等价；单一指标相同不能替代需要检查的输出、接口或保存兼容。容差/随机性解释须有依据，不能统一±0.1%或旧noise_floor裁决。

behavior_assessment=matches_expected/conflicts_with_expectation/investigate/not_checked/not_applicable，表示实际行为是否符合有依据的要求。有意修复/移除功能时新旧可能应当不同，要验证新要求及保留用途，不强求比较结果无差异。只是检查指标接近不能填behavior_assessment=matches_expected概括全部行为。

findings、limitations和next_action说明实际证据与解释边界；不足/未执行/有冲突的必要检查不能被汇总成整个项目“等价通过”。差异也不自动证明某次删改错误，核条件、预期和实际影响。

### 差异、撤销、自查与交接

uncertain_items每项记录位置/用途、为何不确定、来源和遗漏、已选择保留/待调查的处理及后续责任，不自动称潜伏bug。

reversions每项含相关change_id、调查依据、仅本次可撤销范围、保护用户已有改动/资产的办法、实际操作与前后状态、重验结果及未决。无法分离时不操作，不因回旧commit或撤销完本次补丁就声称环境/原证据已恢复。原状态也异常时记录返回setup/reproduction的条件。

self_checks.before_execution/before_handoff每项含check、status(clear/limited/needs_revision)、finding、证据/版本、unknowns与effect。主文件必查项在实际流程位置完成；已有材料可引用，不新增独立自查JSON/脚本、不要求用户每项重新批准。needs_revision先处理，不为了交接改成通过。

handoff.selected_state_refs绑定实际选择的代码/config/环境/资产；supported_uses每项含retained_use_id、具体条件/范围、verification_ids和限制。没有相关证据、存在未解决冲突或检查未执行时不把受影响用途列为已支持，仍可交真实部分结果与待办。没有代码改动可保留相关原检查范围与来源，但不能升级原证据。

unsupported_inferences明确不能认证的用途/条件，invalidated_prior_evidence说明哪些上游结果因本次变化不再直接适用及原因。remaining_tasks含具体问题/owner和下一步建议/用户决定；需要再验证或研究设计的交对应skill，不一律留给以后execution。

operation_paths_ref指真实操作路径记录（按需生成），不认证热点。next_skill通常是code-reading或待解决问题的责任方；code-reading仍必经，execution需按当前批准研究设计和关键代码审阅实施。不能由已清理推导新方法有效或有创新性。

revisions保留时间、旧状态、变化原因、新证据和影响，不覆盖原判断。分支/tag仅定位实际代码，是否提交/merge/push按实际规则与授权，不是行为已验证证据。

## 旧格式与消费者

旧score/classification、performance.in_band、iteration_verified、protected_iteration_infra、hot_path与tag不自动映射为新用途支持/行为等价结论。旧原始读数或调用证据可按具体条件核对使用，不能恢复统一阈值或scaling设施认证。

code-reading已按实际用途/变更/观察范围接收；后期skills按实际来源和验证范围接收，历史项目记录仍须核对。交接明确schema_version=2、retained_uses/changes/verification_records和selected_state_refs；旧消费者不理解时先核对，不能忽略影响/未覆盖项后回退到“prepared=true”。历史项目原文件不批量迁移。

## 研究条件核对（与本轮用途有关时）

引用条件记录的路径和版本，写明目标与实际条件、必须保留项的代码/配置/数据位置及检查证据、未知/偏差、所查范围和不能外推的内容。记录下一次目标条件验证的触发点或不适用理由。按本 skill 职责分别说明静态调查、准备、阅读或实际运行，不能将尚待检查项写成已落实；条件或假设变化后重新核对。
