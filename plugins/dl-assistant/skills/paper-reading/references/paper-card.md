# paper-card.json：判断、证据与阅读进度

本文件说明什么时候建立论文卡片、每一步需要记下什么，以及下次如何凭卡片续读或复查证据。论文身份可确认时，在该论文的阅读目录建立 `paper-card.json`，随阅读和讲解更新。以下为格式版本 2。

## 最小记录

```json
{
  "schema_version": 2,
  "arxiv_id": null,
  "doi": null,
  "url": null,
  "title": null,
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

每次建立最小记录时包含以上字段。未知标量用 null，尚无条目用空数组，不适用的字段在相邻说明或判断理由中注明；不能用 false 表示未知。拿不到标题时记录 null 和已知来源。至少有一个论文标识或本地来源路径；`authors` 未核实时空数组并说明尚未确认，不填示例作者。

## 来源与阅读建议

`sources[]` 每项记录 `source_id`、`kind`（tex/pdf/html/abstract 等）、`location`（URL 或路径）、`version`（未知为 null）、`accessed_at`（带时区）。来源 ID 供阅读范围和原文证据引用。材料出处只在 `sources` 写一次，实际读到哪里写在 `reading_progress.coverage`，讲过什么写在 `reading_progress.topics`。

`read_date` 为本次记录更新日期，不代表读完。`paper_type` 描述内容类型与讲解重点，不使用内部比喻。`reading_goal` 写用户的本次目标。`worth_reading` 为 true、false 或 null，表示针对该目标是否建议进一步深读，`worth_reason` 说明判断依据和已读范围。false 不能供下游推导成质量差、无创新或研究拥挤；用户要求继续时照常阅读与保存。

`core_idea` 说明核心机制或结论；`core_contribution` 写明确来源与核查范围的贡献概括。字段含义固定，不能将定理写进实验指标字段后省略说明。

## 创新性与贡献类型

`novelty.status`：`unverified`（待核实）、`distinct`（在已查范围有明确差异）、`covered`（所评估的新内容已有工作覆盖）、`not_applicable`（本次未做该类评价且不适用）。整体状态无法概括多个贡献时保持 unverified，并逐项写差异。

`author_claims` 为作者声称的新内容；`contribution_types` 为方法、发现、定理、任务、数据集、评测等类型标签，不是创新等级。`differences[]` 每项注明所评估内容、比较来源及版本、具体差异、重要性与未决事项。`checked_sources[]` 使用标题与 arXiv ID / DOI / URL；`search_scope` 记录检索日期、范围和未覆盖内容。没有比较文献时保持 unverified，不用意外程度替代创新性。

## 主要论点与证据

`claim_evidence[]` 每项：`id`、`statement`、`claim_locations`、`evidence_locations`、`conditions`、`judgment`、`reason`、`open_questions`。位置使用 `{source_id, location}`，标明实际章节、公式、图表或页码。尚未找到证据时保留空数组并说明原因。

`judgment` 使用 `supported`、`insufficient`、`contradicted`、`unverified`，含义见论点分析参考；理由写清证据限度，作者报告不等于独立复现。对应表与报告由这些记录组织，不能只保留无出处的一句结论。

## 研究线索

`swappable_components[]` 保留 `component`、`current`、`why_swappable`，后者写待验证假设而非保证能改进。不存在合适组件时空数组。

`connections[]` 为讨论过的建议，保留 `direction`（inward/outward，分别指同方向继续或迁移应用）、`kind`、`point`、`anchor_arxiv_ids`，增加 `sources`、`paper_locations`、`main_risk`、`verification_status`。`kind` 沿用下游已有分类：方法上/证据上/边界上/解释上，或搬思想/推结论/借工具/当约束；这些只是分类名，正文用具体说明。

`anchor_arxiv_ids` 只填已核实的 arXiv ID；非 arXiv 来源放 `sources`（标题与 DOI/URL），无已核查外部来源时可为空并标待验证。建议不是已确认研究课题。

## 可恢复的阅读进度

- `status` 使用 `in_progress`、`paused`、`completed`，表示本次约定范围的状态。只读摘要也可以完成快速判断。用户暂停精读时用 `paused`。
- `coverage[]` 每项填写 `source_id`、`locations`、`depth`（`abstract` / `skim` / `detailed`）及 `limits`，只记录实际读取的位置。
- `minimal_summary`：status=not_started/explained/skipped，content保存实际最小提要；跳过写原因，不补造已讲。最小提要不是方法详解。
- `topics[]`：增加kind=prerequisite/paper_content，分别表示已有基础与本文内容；每项填写 `topic`、`kind`、`status`（`not_started` / `explained` / `skipped`）和 `understanding`（`not_checked` / `user_reported` / `checked`）。按实际情况补上原文位置、依赖的概念或反馈。前置知识可注明使用的独立定义、教学例子或已核查来源。用户说自己理解时可记 `user_reported`；实际核对过复述或答题后用 `checked`，并记录判断依据。跳过不等于不理解，讲过不等于已掌握。
- `open_questions[]`：问题、来源、当前解释、待办动作；尚未解决不阻止暂停。
- `sequence_adjustments[]`：仅实际发生时记调整原因、移到哪里、需要补什么及返回位置；用户要求提前讲方法也说明，不用完整自查报告。没有调整则空数组。
- `next_step`：下次从哪个基础概念或本文位置继续、尚缺哪些前提；完成且无后续可为 null。

`revisions[]` 记录版本变更、错误更正或判断变化的日期、原因和受影响条目。读旧 card 时将缺字段视为未知，minimal_summary和主题类别缺失不表示用户没听过或已掌握，继续时结合会话与实际笔记核对，不从头重复；旧 `novelty.level` 只作历史判断，不能不经核查映射为 distinct；旧 worth_reading 也不能成为排除后续研究的依据。仅在实际使用时补记录，不批量重写历史笔记。


## 按步骤填写的示例

以下使用同一篇虚构论文《轻量特征融合》。路径、版本和数值仅用于演示。每个代码块只展示当步变化的字段，写入时只更新示例列出的字段，保留同一对象的其他字段。数组中已有同一来源、论点或主题时更新原条目。

### 1. 核对身份后建卡

以最小模板为起点。用户给了本地 PDF，已从首页核对标题和版本，但还没读正文。先保存来源和阅读目标，`worth_reading` 保持 `null`，进度为 `in_progress`。缺少 DOI 或 arXiv ID 时留空。

```json
{
  "title": "轻量特征融合",
  "reading_goal": "判断论文是否值得为低延迟推理精读",
  "sources": [
    {
      "source_id": "pdf-v2",
      "kind": "pdf",
      "location": "papers/example-v2.pdf",
      "version": "v2",
      "accessed_at": "2026-07-09T10:00:00+08:00"
    }
  ]
}
```

### 2. 快速判断后记录建议

读了摘要就明确只根据摘要判断。若本次只约定做快速判断，此时可以记为 `completed`，创新性仍为 `unverified`。

```json
{
  "worth_reading": true,
  "worth_reason": "摘要声称用更少参数达到相近精度，值得继续核对模型开销和推理延迟。",
  "reading_progress": {
    "status": "completed",
    "coverage": [
      {"source_id": "pdf-v2", "locations": ["摘要"], "depth": "abstract", "limits": ["尚未核对正文和实验表"]}
    ],
    "next_step": "用户选择精读时，从方法与实验设计开始"
  }
}
```

### 3. 继续精读时补证据和讲解记录

用户选择精读后，将进度改为 `in_progress`。如取得同版本 TeX，新增 `tex-v2` 来源。按实际读取更新 `coverage`，例如 TeX 第 3 节和 PDF 文件第 6 页表 2。为影响判断的论点写一项 `claim_evidence`。实际给过的最小提要写入 `minimal_summary`；用户复述后保存反馈。

```json
{
  "claim_evidence": [
    {
      "id": "C1",
      "statement": "新融合模块可以降低推理延迟",
      "claim_locations": [{"source_id": "tex-v2", "location": "第 3 节末段"}],
      "evidence_locations": [{"source_id": "pdf-v2", "location": "文件第 6 页，表 2"}],
      "conditions": ["同一数据集和模型设置"],
      "judgment": "insufficient",
      "reason": "表 2 报告了参数量和精度，未报告实际推理延迟。",
      "open_questions": ["附录是否提供同硬件、同批大小的延迟测量？"]
    }
  ],
  "reading_progress": {
    "status": "in_progress",
    "coverage": [
      {"source_id": "pdf-v2", "locations": ["摘要"], "depth": "abstract", "limits": []},
      {"source_id": "tex-v2", "locations": ["第 3 节"], "depth": "detailed", "limits": []},
      {"source_id": "pdf-v2", "locations": ["文件第 6 页，表 2"], "depth": "detailed", "limits": ["尚未核对附录"]}
    ],
    "minimal_summary": {
      "status": "explained",
      "content": "论文想减少特征融合的计算开销，作者尝试用更小的模块保留输入特征。"
    },
    "next_step": "核查附录的推理延迟测量",
    "topics": [
      {
        "topic": "参数量和推理延迟的区别",
        "kind": "prerequisite",
        "status": "explained",
        "understanding": "checked",
        "feedback": "用户复述时区分了模型参数量与硬件上的实际运行时间。"
      },
      {
        "topic": "表 2 能支持哪些结论",
        "kind": "paper_content",
        "status": "explained",
        "understanding": "not_checked"
      }
    ]
  }
}
```

### 4. 暂停、续读或完成

若用户在核查附录前暂停，将状态记为 `paused`，保存未决问题和具体续读位置。下次先核对来源版本，再从该处开始。完成本次约定的精读范围后改为 `completed`，保存精读笔记；没有后续步骤时 `next_step` 填 `null`。用户另行选择讨论后续研究时，再补 `connections`。

```json
{
  "reading_progress": {
    "status": "paused",
    "open_questions": ["附录是否提供同硬件、同批大小的延迟测量？"],
    "next_step": "核对 v2 附录的延迟实验，再更新 C1 的证据判断。"
  }
}
```
