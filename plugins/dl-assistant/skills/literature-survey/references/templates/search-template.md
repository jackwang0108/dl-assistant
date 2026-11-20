# search 文件：原始查询与筛选记录

每批独立 JSON 文件，文件名不覆盖旧批次。以下为格式版本 2；请求字段如未知用 null，不能捏造完成情况。

```json
{
  "schema_version": 2,
  "query_group": "核心问题组",
  "requests": [
    {
      "source": "arxiv",
      "query": "实际执行的查询",
      "requested_range": null,
      "date_basis": null,
      "sort": null,
      "limit": 100,
      "pages_fetched": [],
      "status": "not_run",
      "complete": false,
      "truncated": null,
      "returned_count": 0,
      "fetched_at": null,
      "raw_path": null,
      "error": null
    }
  ],
  "included": [],
  "excluded": [],
  "pending": []
}
```

请求 status 使用 not_run/success/partial/failed，合法空结果为 success 且 returned_count=0；失败或没执行不能改称空结果。complete 只描述请求范围完成情况，truncated 与分页未知时不保证完整。

每篇条目包含实际已有的 title、authors、arxiv、doi、url（具体论文页）、版本、year、published、source、observed_at、reason、approach、abstract_notes、reading_level 和 evidence_locations。身份未知时 null，至少一个标识或标题可用；作者、版本和相关字段保留用于核对，不按标题直接合并。

`citations` 可为已取得数值，必须带 source 与 observed_at；多个来源观测保留为多条输入记录，合并脚本不会取最大值。原始字段和版本冲突保留在 pool 的 observations/field_conflicts。

included 指按范围纳入候选，不等于证据充分；excluded 必须有实质纳排理由；pending 为边界、资料不足或尚未完成评估。不能把跨查询重复当作内容排除理由。相同身份在不同组结论冲突时脚本放入 pending，主 agent 核查后更正输入并记录依据。

reading_level 使用 metadata/abstract/partial_text/detailed，evidence_locations 记录来源版本与实际章节或页码。`published` 使用明确日期或年月，区分预印本首发和正式发表；最新日期不是覆盖证明。
