# 定向文献检索记录模板

本文件说明怎样记录围绕当前研究问题执行的定向检索，保留实际查询、来源与筛选依据，并说明结果对当前假设有什么影响。

用于[初查](../research-workflow.md#step-1-核查起点实际检索)和[定向补查](../research-workflow.md#step-3-深入查新对照最接近的工作并讨论是否继续)。先核对已有调研实际覆盖了什么，能复用的证据引用原记录。将本轮查询按实际任务保存为 `literature/search/<批次>.json`。近作、最接近工作与反面证据是按问题选择的查询任务，可在一个批次完成。不同调用、重试和后续补查保留记录。

## 通用检索字段

`query_group`、`requests`、`included`、`excluded` 和 `pending` 沿用 [literature-survey 检索记录模板](../../../literature-survey/references/templates/search-template.md)。按该模板保存真实调用参数、日期口径、获取时间、查询和结果快照、分页及来源和覆盖记录。用 [paper-search](../../../paper-search/SKILL.md) 查看当前 MCP 接口。需要使用 HF 时，保留实际命令和日期后筛字段及结果。

- 请求成功且实际零命中时，`returned_count` 填 `0`。请求失败且没有可用结果，或未执行时，填 `null`。部分结果写实际已返回数及限制。
- 有相关结果、但核查后发现它们缺关键对照时，仍记录实际返回数。把缺什么证据写在核查结果里。来源失败、分页或时间窗不完整时，保留受限范围。
- 每条命中按本批筛选决定放入一个数组，说明理由。主题相关但证据不足的论文可纳入，并标明已读程度及缺口。身份或范围待核的放 `pending`。跨批重复发现保留原始来源，主会话用稳定标识或已核互链合并。仅标题相似时保留待核。已知 DOI、arXiv ID 或已核链接都可用于回查。

## 本轮研究问题专用字段

| 字段 | 怎么填 |
| --- | --- |
| `research_focus` | 写实际关联的 Q/H 编号、待核问题和为什么需要补查。还在初查且编号未形成时，可引用 `idea-seed.json` 的初查问题 |
| `reused_sources` | 引用上游调研、笔记、证据条目及覆盖位置，写清哪些已知事实从这里承接 |
| `observations` | 只记已核事实及条件，注明论文稳定标识、版本、原文位置和读文深度。写对哪项预测有影响，以及仍缺什么依据 |
| `new_questions_or_explanations` | 从观察推导的新问题、竞争解释或后续核查线索。标明所依据的观察和未验证的前提 |
| `limitations` | 写实际查过的范围、待取材料和仍不能作出的判断。找到相关论文但缺少能区分解释的证据时指出具体缺口 |

主会话核对原始调用、论文身份和证据条件后，把会影响当前命题的事实及其关系汇总到 `literature/literature.json`。按[研究问题证据模板](question-evidence.md)引用批次位置。涉及候选推荐或问题修订时，更新候选记录和 `spec.json`。

## 可复制模板

```json
{
  "schema_version": 2,
  "query_group": null,
  "research_focus": {
    "problem_ids": [],
    "hypothesis_ids": [],
    "question": null,
    "reason_for_search": null
  },
  "reused_sources": [],
  "requests": [],
  "included": [],
  "excluded": [],
  "pending": [],
  "observations": [],
  "new_questions_or_explanations": [],
  "limitations": []
}
```

## 完整填写示例

以下为[研究问题证据示例](question-evidence.md#完整填写示例)引用的 `literature/search/ablation-runtime-01.json`。论文、查询快照和结果均为虚构。C 已由上游调查核查，本轮聚焦分项消融和运行时实现。查询返回两条，筛读后仍缺能区分机制的对照。

```json
{
  "schema_version": 2,
  "query_group": "分项消融和运行时实现",
  "research_focus": {
    "problem_ids": ["Q2"],
    "hypothesis_ids": ["H2", "H3"],
    "question": "是否有可比的分项对照，能区分中间张量写回量与运行时算子实现对组合收益的影响？",
    "reason_for_search": "已有文献验证组合部署，但两项改动同时切换，独立贡献不清楚。"
  },
  "reused_sources": [
    {
      "path": "docs/literature-survey/2025-07-01-edge-vision/survey.json",
      "entries": ["papers: p00003", "gaps: gap-2"],
      "coverage_path": "docs/literature-survey/2025-07-01-edge-vision/coverage-review.md",
      "note": "已有记录覆盖至 2025-06-30，并已核查论文 C 的组合部署。"
    }
  ],
  "requests": [
    {
      "tool": "search_papers",
      "params": {
        "queries": [
          {
            "text": "edge vision model compression operator fusion ablation",
            "sources": ["arxiv"]
          }
        ],
        "filters": {
          "date_range": {"date_type": "first_submitted", "start": "2025-05-01", "end": "2025-06-30"}
        },
        "sort": "relevance",
        "budget": {"max_requests": 2, "max_items": 10, "max_seconds": 20},
        "cache": "prefer"
      },
      "query_id": "example-ablation-query",
      "snapshot_id": "example-ablation-snapshot",
      "fetched_at": "2025-06-30T09:00:00Z",
      "status": "success",
      "returned_count": 2,
      "next_cursor": null,
      "source_reports": [
        {
          "source": "arxiv",
          "status": "ok",
          "actual_query": {
            "search_query": "(all:\"edge\" AND all:\"vision\" AND all:\"model\" AND all:\"compression\" AND all:\"operator\" AND all:\"fusion\" AND all:\"ablation\") AND submittedDate:[202505010000 TO 202506302359]",
            "start": 0,
            "max_results": 10,
            "sortBy": "relevance",
            "sortOrder": "descending"
          },
          "fetched_count": 2,
          "upstream_has_more": false,
          "limitations": []
        }
      ],
      "coverage": {
        "local_has_more": false,
        "upstream_has_more": false,
        "truncated": false,
        "limitations": ["仅表示此查询完成。"]
      },
      "usage": {"requests": 1, "items": 2, "seconds": 2.1, "download_bytes": 0}
    }
  ],
  "included": [
    {
      "title": "近期论文 C",
      "arxiv": null,
      "doi": null,
      "url": "https://example.org/papers/edge-vision-c",
      "reason": "命中已知组合部署先例，与本轮归因问题直接相关。沿用上游身份及读文记录。",
      "reading_level": "detailed",
      "mcp_item": {"paper_ref": "example:edge-vision-c", "version": "v1"}
    }
  ],
  "excluded": [
    {
      "title": "论文 E",
      "arxiv": null,
      "doi": null,
      "url": "https://example.org/papers/edge-preprocessing",
      "reason": "初筛摘要仅讨论预处理缓冲时延，不涉及压缩与融合的分项对照。",
      "reading_level": "abstract",
      "mcp_item": {"paper_ref": "example:edge-preprocessing", "version": "v1"}
    }
  ],
  "pending": [],
  "observations": [
    {
      "paper_ref": "https://example.org/papers/edge-vision-c",
      "version": "v1",
      "location": "§4.1、§4.3 表 3，PDF 第 7 页，附录 B",
      "reading_level": "detailed",
      "note_path": "literature/papers/edge-vision-c/edge-vision-c-note.md",
      "finding": "设备 C、运行时 R、批大小 1。基线同时关闭模型压缩与算子融合，组合收益不能分别归因。",
      "hypothesis_ids": ["H2", "H3"],
      "implication": "已核证据无法区分两种解释。补充材料及运行轨迹尚未取得。"
    }
  ],
  "new_questions_or_explanations": [
    {
      "question": "相同输入下能否在保持算子实现时观测不同写回量，或在写回量相近时比较不同实现？",
      "basis": "表 3 同时切换两个组件，改动可能改变写回量及运行时实现选择。",
      "next_check": "核同版本补充材料。若仍缺，先确定目标设备上的轨迹与隔离条件能否获取。"
    }
  ],
  "limitations": [
    "本轮只补查 arXiv 首次提交日期 2025-05-01 至 2025-06-30 的记录。",
    "本轮返回两条记录。按当前查询与已读范围，仍未找到能区分 H2、H3 的对照。"
  ]
}
```

示例中的 `mcp_item` 只演示字段位置。实际记录按[通用检索模板](../../../literature-survey/references/templates/search-template.md)保留原始条目。汇报给主会话时，附批次路径、主要观察及限制，例如「查询返回两条，C 的组合比较相关，但所需分项消融仍未核到」。
