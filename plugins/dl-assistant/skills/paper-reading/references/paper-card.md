# paper-card.json：判断、证据与阅读进度

所有阅读模式都建立 card，并随讲解增量更新。以下为格式版本 2；旧字段中仍有下游引用的名称保留，但不再把阅读建议当质量或创新性结论。

## 最小记录

```json
{
  "schema_version": 2,
  "arxiv_id": null,
  "doi": null,
  "url": null,
  "title": "待确认标题",
  "authors": [],
  "read_date": "2026-07-09",
  "sources": [],
  "paper_type": null,
  "worth_reading": null,
  "worth_reason": "尚未判断阅读价值",
  "reading_goal": null,
  "core_idea": null,
  "novelty": {
    "status": "unverified",
    "author_claims": [],
    "contribution_types": [],
    "differences": [],
    "checked_sources": [],
    "search_scope": "尚未进行已有工作对比"
  },
  "claim_evidence": [],
  "core_contribution": null,
  "swappable_components": [],
  "key_findings": [],
  "limitations": [],
  "connections": [],
  "reading_progress": {
    "status": "in_progress",
    "coverage": [],
    "minimal_summary": {"status": "not_started", "content": null},
    "topics": [],
    "sequence_adjustments": [],
    "open_questions": [],
    "next_step": null
  },
  "revisions": []
}
```

每次建立最小记录时包含以上字段。未知标量用 null，尚无条目用空数组，不适用的字段在相邻说明或判断理由中注明；不能用 false 表示未知。标题示例是占位说明，实际拿不到标题时记录 null 和已知来源。至少有一个论文标识或本地来源路径；`authors` 未核实时空数组并说明尚未确认，不填示例作者。

## 来源与阅读建议

`sources[]` 每项记录 `source_id`、`kind`（tex/pdf/html/abstract 等）、`location`（URL 或路径）、`version`（未知为 null）、`accessed_at`（带时区）、`read_locations`（实际读到的章节/页码）。来源 ID 供后续证据引用。

`read_date` 为本次记录更新日期，不代表读完。`paper_type` 描述内容类型与讲解重点，不使用内部比喻。`reading_goal` 写用户的本次目标。`worth_reading` 为 true、false 或 null，表示针对该目标是否建议进一步深读，`worth_reason` 说明判断依据和已读范围。false 不能供下游推导成质量差、无创新或研究拥挤；用户要求继续时照常阅读与保存。

`core_idea` 说明核心机制或结论；`core_contribution` 写明确来源与核查范围的贡献概括。字段含义固定，不能将定理写进实验指标字段后省略说明。

## 创新性与贡献类型

`novelty.status`：`unverified`（待核实）、`distinct`（在已查范围有明确差异）、`covered`（所评估的新内容已有工作覆盖）、`not_applicable`（本次未做该类评价且不适用）。整体状态无法概括多个贡献时保持 unverified，并逐项写差异。

`author_claims` 为作者声称的新内容；`contribution_types` 为方法、发现、定理、任务、数据集、评测等类型标签，不是创新等级。`differences[]` 每项注明所评估内容、比较来源及版本、具体差异、重要性与未决事项。`checked_sources[]` 使用标题与 arXiv ID / DOI / URL；`search_scope` 记录检索日期、范围和未覆盖内容。没有比较文献时保持 unverified，不用意外程度替代创新性。

## 主要论点与证据

`claim_evidence[]` 每项：`id`、`statement`、`claim_locations`、`evidence_locations`、`conditions`、`judgment`、`reason`、`open_questions`。位置必须含 `source_id` 和实际章节、公式、图表或页码。

`judgment` 使用 `supported`、`insufficient`、`contradicted`、`unverified`，含义见论点分析参考；理由写清证据限度，作者报告不等于独立复现。对应表与报告由这些记录组织，不能只保留无出处的一句结论。

## 研究线索

`swappable_components[]` 保留 `component`、`current`、`why_swappable`，后者写待验证假设而非保证能改进。不存在合适组件时空数组。

`connections[]` 为讨论过的建议，保留 `direction`（inward/outward，分别指同方向继续或迁移应用）、`kind`、`point`、`anchor_arxiv_ids`，增加 `sources`、`paper_locations`、`main_risk`、`verification_status`。`kind` 沿用下游已有分类：方法上/证据上/边界上/解释上，或搬思想/推结论/借工具/当约束；这些只是分类名，正文用具体说明。

`anchor_arxiv_ids` 只填已核实的 arXiv ID；非 arXiv 来源放 `sources`（标题与 DOI/URL），无已核查外部来源时可为空并标待验证。建议不是已确认研究课题。

## 可恢复的阅读进度

- `status`：in_progress、paused、completed，表示本次约定阅读范围的状态，completed 不等于全文无遗漏。
- `coverage[]`：来源及位置、阅读深度（abstract/skim/detailed）、是否存在未查附录或证明等限制。
- `minimal_summary`：status=not_started/explained/skipped，content保存实际最小提要；跳过写原因，不补造已讲。最小提要不是方法详解。
- `topics[]`：增加kind=prerequisite/paper_content，分别表示已有基础与本文内容；每项记录主题、所需的已介绍概念、实际来源/位置（背景可用独立定义/教学例子与已核查外部来源，不硬填本文Method位置）、讲解状态（not_started/explained/skipped）、理解检查状态（not_checked/user_reported/checked）、练习及反馈（发生时记录）。跳过不等于不理解，讲过不等于已掌握。
- `open_questions[]`：问题、来源、当前解释、待办动作；尚未解决不阻止暂停。
- `sequence_adjustments[]`：仅实际发生时记调整原因、移到哪里、需要补什么及返回位置；用户要求提前讲方法也说明，不用完整自查报告。没有调整则空数组。
- `next_step`：下次从哪个基础概念或本文位置继续、尚缺哪些前提；完成且无后续可为 null。

`revisions[]` 记录版本变更、错误更正或判断变化的日期、原因和受影响条目。读旧 card 时将缺字段视为未知，minimal_summary和主题类别缺失不表示用户没听过或已掌握，继续时结合会话与实际笔记核对，不从头重复；旧 `novelty.level` 只作历史判断，不能不经核查映射为 distinct；旧 worth_reading 也不能成为排除后续研究的依据。仅在实际使用时补记录，不批量重写历史笔记。
