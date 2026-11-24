# v2 工具参数与示例

以下为 Python 风格的 MCP 参数示例，实际以工具 schema 为准。返回中的 `items` 是本次快照首批结果；每个来源的分页状态独立保存。`get_papers` 的批量返回位于 `results`，不要与检索 `items` 混用。

| 任务 | 调用顺序 |
|---|---|
| 已有 DOI、arXiv ID 或来源标识 | `get_papers` → 按需核来源或具体修订 |
| 只有标题或不完整的书目 | `resolve_papers` → 核候选身份 → `get_papers` |
| 主题调研 | `search_papers` → 检查报告 → 读本地页或补查上游 → 导出快照 |
| 查引用或共同关系 | 确认种子标识 → `get_paper_citations`、`get_paper_references` 或 `find_related_papers` → 检查各任务状态 |
| 查作者或机构的论文 | `search_authors` 或 `search_institutions` → 核实体标识 → `get_entity_papers` |
| 查证或取得原文 | `list_paper_assets` → 按版本选择资源 → `download_paper_asset` 或交给原文工具 |

## 身份与信息

```python
get_capabilities()
# Publisher / OpenReview URLs are resolved through providers that accept exact URL lookup.
# No supported match produces not_found/unavailable; it does not silently become a title match.
resolve_papers(inputs=[{"identifier": "https://arxiv.org/abs/1706.03762"}],
               sources=["arxiv"])
resolve_papers(inputs=[{"title": "Attention Is All You Need", "year": 2017}])
get_papers(paper_refs=["arxiv:1706.03762"], cache="prefer")
get_papers(paper_refs=["arxiv:1706.03762"], view="sources", cache="only")
get_papers(paper_refs=["arxiv:1706.03762"], view="versions", cache="only")
get_papers(paper_refs=["arxiv:1706.03762v1"], cache="refresh")
```

`fields` 可以选择返回记录中实际可用的字段，如 `title`、`authors`、`abstract`、`snippet`、`dates`、`citation_counts`、`assets`；基本身份与出处仍保留。没有该字段或字段名拼错会明确报错，不自动猜字段。`sources` 视图提供独立观测记录；`versions` 只列已实际取得的版本，不能据缺失认定没有其他版本。

## 检索、浏览与补查

```python
search_papers(
    queries=[
        {"text": "video generation diffusion", "sources": ["semantic_scholar", "scholar"]},
        {"text": 'cat:cs.CV AND abs:diffusion AND abs:video',
         "sources": ["arxiv"], "syntax": "source_native"},
    ],
    budget={"max_requests": 6, "max_items": 40, "max_seconds": 45},
)
# 从真实返回中取得 query_id / snapshot_id，不使用下面的符号占位作为真实 ID。
get_query_results(snapshot_id=snapshot_id, page_size=20)
get_query_results(snapshot_id=snapshot_id, cursor=next_cursor, page_size=20)
extend_query(query_id=query_id, action="fetch_more")
extend_query(query_id=query_id, action="retry_failed", sources=["semantic_scholar"])
extend_query(query_id=query_id, action="add_queries",
             queries=[{"text": "video synthesis diffusion", "sources": ["openalex"]}])
extend_query(query_id=query_id, action="refresh")
```

默认 `syntax="text"`；arXiv 将词/引号短语转换为明确的 AND 查询，不自动扩展同义词。`source_native` 只能指定一个支持该语法的来源。agent 自己设计查询变体，记录采用的表述。

游标固定到生成时的快照。`extend_query` 产生同一 query_id 下的新快照，不修改旧快照；返回 `changes` 中的新命中、变化和本轮未观察项。未观察项可能来自分页或排序变化，不等于论文被删除。查询/引用/实体各类型只支持适用操作：`add_queries` 仅适用于论文检索；无上游分页的推荐不伪造游标。

每条 `source_reports` 对应一个查询任务。同一来源有多个表达式时，用 `task_id` 定位。按该 ID 在 `retrieval_history` 查看同一查询历次执行的状态、实际查询（来源调用返回时）、偏移变化和请求数。用 `query_id` 读取最新快照，用 `snapshot_id` 精确读取或导出；需复查时保存具体快照 ID。

## 引用与相关推荐

```python
get_paper_citations(paper_ref="arxiv:1706.03762", sources=["semantic_scholar"])
get_paper_citations(paper_ref=confirmed_doi, sources=["openalex", "semantic_scholar"],
                    publication_year_range={"start": 2024, "end": 2025})
get_paper_references(paper_ref="arxiv:1706.03762", sources=["semantic_scholar"])
find_related_papers(paper_refs=["arxiv:1706.03762", "arxiv:1810.04805"],
                    method="shared_references", match="all")
find_related_papers(paper_refs=["arxiv:1706.03762"],
                    method="provider_recommendations", sources=["semantic_scholar"])
```

共同关系方法为 `shared_references`、`shared_citations`，`match="all"` 要求当前证据关联全部种子，`any` 要求至少一个；所有种子的覆盖限制都需要检查。继续获取后重新计算共同结果。来源推荐目前使用 Semantic Scholar 的 `all-cs` 候选集合，不能当作全学科推荐或完整相似论文集合。

OpenAlex 缺少 W ID 时，可以用传入或缓存中唯一可确认的 DOI 进行精确补查。补查和后续引用请求共用预算。查看 `identifier_resolution`，区分直接提供（`provided`）、缓存别名（`cached_alias`）、本次解析成功（`resolved`）、索引未找到（`not_indexed`）、缺少可用标识（`missing_identifier`）和补查失败（`failed`）。Scholar 引用使用 `scholar_cites:…`，可从已核记录取得。引用源使用稳定标识关联。

`publication_year_range` 的边界含首尾，只对已获取的引用者做本地后筛。用 `year_filter` 检查纳入、窗外和待核数量。边界口径和证据来源见 [日期规则](date-filtering.md)。

## 作者与机构

```python
search_authors(name="Ashish Vaswani", sources=["semantic_scholar", "openalex"])
search_institutions(name="Massachusetts Institute of Technology", country="US")
get_entity_papers(entity_ref=confirmed_entity_ref)
```

作者实体形如 `s2:author:…` / `openalex:author:A…`，机构形如 `openalex:institution:I…`。不要将论文标识或姓名填成实体标识。作者 affiliation/topic 是帮助人工或 agent 判断的提示，未作为强制过滤。SS 作者论文目前不支持搜索端的日期、其他过滤及日期排序；需要这些能力时核 OpenAlex 实体，不能强行把不同来源作者 ID 混用。

## 资源与导出

```python
list_paper_assets(paper_ref="arxiv:1706.03762", version="v1")
download_paper_asset(paper_ref="arxiv:1706.03762", asset_type="pdf", version="v1",
                     budget={"max_requests": 3, "max_seconds": 40,
                             "max_download_bytes": 10000000})
export_records(snapshot_id=snapshot_id, format="json")
export_records(paper_refs=["arxiv:1706.03762v1"], format="bibtex")
```

显式 revision 选择使用 arXiv 标识和 `vN`。资源返回 `asset_ref`，可限定下载某项；不接受任意未发现 URL。PDF 验证可解析、非加密且有页面；源码目前只验证 tar 格式、不解压，其他源码格式明确返回不可用。缓存命中也复核校验值和格式，损坏缓存会按策略重新获取。返回 `identity_status` 区分来源关联和原文内容核查，不能将它改写成“论文版本已完全认证”。

导出只读本地已取得记录，不自动花费额外 API 请求补书目信息。JSON 导出实际快照、来源报告和限制；BibTeX 用 misc 条目保存已核字段，缺失单列，不猜会议名、年份、DOI。

显式带 `vN` 的论文导出只用相同修订的观测，缺失时查看 `version_not_in_cache`。JSON 快照导出包含本地所有符合条件的记录，`coverage.local_has_more` 为 `false`，同时保留 `coverage.upstream_has_more` 的实际状态。

## 文献调研交接示例

假设调研需要补查 2025 年的扩散视频生成工作。以下结果用于解释如何操作，实际状态以工具返回为准。

1. 调用 `get_capabilities()` 核对来源，再执行下面的检索。逐条记录检索表达式及日期口径。

```python
params = {
    "queries": [{"text": "diffusion video generation",
                 "sources": ["semantic_scholar", "openalex"]}],
    "filters": {"date_range": {"date_type": "published",
                              "start": "2025-01-01", "end": "2025-12-31"}},
    "sort": "relevance",
    "budget": {"max_requests": 4, "max_items": 40},
}
first = search_papers(**params)
```

2. 假设 Semantic Scholar 已取首批且还有上游页，OpenAlex 返回权限错误。保留首轮两条 `source_reports`。若已有可用配置，再用下面的 `retry_failed` 专补 OpenAlex。若权限问题持续，保留失败并按调研方案改用其他来源。需要继续取 Semantic Scholar 时，只翻它的上游页。

```python
retried = extend_query(query_id=first["query_id"], action="retry_failed",
                       sources=["openalex"])
latest = extend_query(query_id=retried["query_id"], action="fetch_more",
                      sources=["semantic_scholar"])
if latest["next_cursor"]:
    next_page = get_query_results(snapshot_id=latest["snapshot_id"],
                                  cursor=latest["next_cursor"])
bundle = export_records(snapshot_id=latest["snapshot_id"], format="json")
```

3. 把 `bundle.content` 存为 JSON。按 [调研检索批次模板](../../literature-survey/references/templates/search-template.md) 记录每次调用、对应快照、实际 `returned_count`、来源报告和覆盖。用导出中的稳定论文标识做身份核对，再按调研标准分到纳入、排除和待核。若 OpenAlex 仍失败或 Semantic Scholar 还有上游页，在覆盖说明中分别写明其状态与影响。
