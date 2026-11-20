# 本轮证据与研究判断交接

保存 `04-conclusion.md` 和 `conclusion.json`。不把阳性当执行成功，也不把部分完成、阻塞或无显著结果写成证伪。字段定义为schema_version=2，旧消费者需核对后再使用。

## 人读报告

```markdown
# {版本} 实验交接
- 当前研究问题、假设及批准计划版本。
- 原来相信什么：先验与本轮未知，本项目原有数据与文献分开。
- 实际观察到什么：执行完成数、失败/阻塞/取消、数据与具体来源。
- 观察支持到哪一步：逐命题证据、条件、替代解释与不确定性。
- 哪些仍未知：资料、数据有效性、设计识别和未完成实验分别说明。
- 计划偏差与全部尝试：改动、批准范围及其影响，探索/事后解释标明。
- 意外观察与建议：有依据的技术诊断和待研究解释，不宣布根因或自动改题。
- 可复现与审阅：代码/模型/数据/配置/命令、设计快照、review与用户代码审阅。
- 自查：pre_run/handoff记录路径、对应输入、剩余缺陷和对交接的影响；不代替独立review。
- 下一轮待决定：修订假设、补取证、重评价值或停止的理由；决定归iterate与用户。
```

## conclusion.json

```json
{
  "schema_version": 2,
  "version": null,
  "status": "partial",
  "data_validity": "unassessed",
  "outcome": "pending",
  "node_type": "research_round",
  "claims_json": "claims.json",
  "self_checks": [],
  "review_path": null,
  "review_status": "not_reviewed",
  "method_tag": null,
  "round_record": {"prior_beliefs": [], "observations": [], "evidence_updates": [], "unknowns": []},
  "experiment_counts": {"planned": 0, "completed": 0, "failed": 0, "blocked": 0, "cancelled": 0, "unfinished": 0},
  "deviations": [],
  "unexpected_observations": [],
  "key_insights": [],
  "scale_risks": [],
  "evidence_quality_issues": [],
  "golden_metrics": [],
  "remaining_tasks": [],
  "recommendations": [],
  "handoff": {"next": "iterate", "design_change_approval_required": true}
}
```

status=completed/partial/blocked/failed/cancelled，只表示本轮执行；有效阴性且计划全部执行可为completed，部分未跑为partial，不写partially_refuted代替。data_validity=unassessed/valid/limited/invalid，聚合时列影响范围，不能将局部坏数据推广全部。

outcome=pending/supported/contradicted/mixed/insufficient_evidence/not_identifiable/invalid_data，表示本轮已核查命题的证据概览，不替代逐项claims，也不自动修改总假设研究状态。执行完成但无法区分解释可以completed+not_identifiable。

round_record逐项引用原始路径、实验ID和条件；evidence_updates记录本轮证据评价，不预先替iterate决定新方向。review_status=not_reviewed/partial/completed，不可由文件存在推断完成。

golden_metrics保留旧字段名但默认空，仅在之后明确选择论文/发行版结果时填写含完整来源的条目；supported不自动选入。method_tag可沿用历史定位，版本追踪不依赖它。旧success/failure节点不自动映射新版科学结果；未知项保留，不补猜。

## 研究条件核对（与本轮用途有关时）

引用条件记录的路径和版本，写明目标与实际条件、必须保留项的代码/配置/数据位置及检查证据、未知/偏差、所查范围和不能外推的内容。记录下一次目标条件验证的触发点或不适用理由。按本 skill 职责分别说明静态调查、准备、阅读或实际运行，不能将尚待检查项写成已落实；条件或假设变化后重新核对。
