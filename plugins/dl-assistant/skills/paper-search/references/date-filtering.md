# 日期、排序与实际范围

使用 `date_range` 时，指定日期类型和至少一个边界。无时间窗的检索可以省略 `date_range`。分别记录首次提交、修订和发表的日期口径。日期采用 ISO 日历日期。arXiv 边界按 API 使用的 UTC 日处理。相对日期先结合用户时区转换成明确边界，再调用工具。

```python
search_papers(
    queries=[{"text": "diffusion", "sources": ["arxiv"]}],
    filters={"date_range": {"date_type": "first_submitted",
                             "start": "2025-01-01", "end": "2025-12-31"}},
    sort="date_desc",
)
```

| 来源 | 当前日期支持 | 需要注意 |
|---|---|---|
| arXiv | first_submitted / updated | 使用对应服务端日期字段；保留返回的 published/updated，不用 year 代替 |
| Semantic Scholar | published | 发送 publicationDateOrYear；上游可能用年份处理无精确日期记录，返回仍可能为未知日期 |
| Scholar | 发表年份范围 | 精确到日的范围默认拒绝；允许 report 时只作年份过滤并注明日期未完全落实 |
| OpenAlex | published | 使用服务端发表日期过滤；它不是 arXiv 首次提交日期 |

只传 start 时 arXiv 的上界是本次查询的 UTC 日期，不再加未来 30 天；只传 end 时用合理历史下界。日期颠倒、无起止边界或无效日期在执行前拒绝。

`sort` 可用 relevance、date_desc、date_asc、citations_desc，具体来源支持由 get_capabilities 给出。排序失败不自动改成另一种排序并宣称等价；失败按来源报告。多来源组合没有统一相关性或引用数排序。

`unsupported="error"` 是默认：条件不支持时不执行该来源。`unsupported="report"` 需要明确选择：允许取更宽候选，同时返回未生效项，后续据实际字段核查；日期未知不能填成 1 月 1 日冒充已核日期。即使某个来源声称执行了过滤，关键历史截点仍应检查论文版本和原始时间证据。

精确日期筛选和有限分页是两回事：时间窗有效不代表窗内所有论文已取得。始终结合 coverage、逐来源状态和预算说明范围。

## 引用者的发表年份

`get_paper_citations(publication_year_range={"start": 2024, "end": 2025}, ...)` 会对快照已取得的引用者做本地后筛。两端都包含，至少给一端。年份依据 Semantic Scholar 的 `year` 和 OpenAlex 的 `publication_year`。arXiv 首次提交年和 Scholar 片段提取的年份可以作为人工核查线索。

- `items` 返回窗内候选，`publication_year_evidence` 记录采用的年份和来源。
- `year_filter` 汇总已取得、窗内、窗外和待核数量。`unknown_items` 列出年份缺失或来源冲突的论文标识和现有证据，可按标识继续核查。
- `source_reports` 与 `coverage.upstream_has_more` 仍反映原引用请求的进度。首批窗内结果为零时，依据任务需要和上游状态决定是否 `fetch_more`。
