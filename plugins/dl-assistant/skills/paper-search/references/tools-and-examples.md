# v2 工具参数与示例

以下为 Python 风格的 MCP 参数示例，实际以工具 schema 为准。返回中的 `items` 是本次快照首批结果；每个来源的分页状态独立保存。`get_papers` 的批量返回位于 `results`，不要与检索 `items` 混用。

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
get_query_results(query_id=snapshot_id, page_size=20)
get_query_results(query_id=query_id, cursor=next_cursor, page_size=20)
extend_query(query_id=query_id, action="fetch_more")
extend_query(query_id=query_id, action="retry_failed", sources=["semantic_scholar"])
extend_query(query_id=query_id, action="add_queries",
             queries=[{"text": "video synthesis diffusion", "sources": ["openalex"]}])
extend_query(query_id=query_id, action="refresh")
```

默认 `syntax="text"`；arXiv 将词/引号短语转换为明确的 AND 查询，不自动扩展同义词。`source_native` 只能指定一个支持该语法的来源。agent 自己设计查询变体，记录采用的表述。

游标固定到生成时的快照。`extend_query` 产生同一 query_id 下的新快照，不修改旧快照；返回 `changes` 中的新命中、变化和本轮未观察项。未观察项可能来自分页或排序变化，不等于论文被删除。查询/引用/实体各类型只支持适用操作：`add_queries` 仅适用于论文检索；无上游分页的推荐不伪造游标。

## 引用与相关推荐

```python
get_paper_citations(paper_ref="arxiv:1706.03762", sources=["semantic_scholar"])
get_paper_references(paper_ref="arxiv:1706.03762", sources=["semantic_scholar"])
find_related_papers(paper_refs=["arxiv:1706.03762", "arxiv:1810.04805"],
                    method="shared_references", match="all")
find_related_papers(paper_refs=["arxiv:1706.03762"],
                    method="provider_recommendations", sources=["semantic_scholar"])
```

共同关系方法为 `shared_references`、`shared_citations`，`match="all"` 要求当前证据关联全部种子，`any` 要求至少一个；所有种子的覆盖限制都需要检查。继续获取后重新计算共同结果。来源推荐目前使用 Semantic Scholar 的 `all-cs` 候选集合，不能当作全学科推荐或完整相似论文集合。

引用查询不会按标题首条结果补绑来源 ID。优先使用来源能够直接接受的标识，或先 `get_papers` / `resolve_papers` 取得已确认的别名。Scholar 引用使用 `scholar_cites:…`，不是 `scholar:…` 的 result_id。引用查询的额外过滤目前不提供；传非空 filters 会明确拒绝，不能沿用搜索接口过滤能力。

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
export_records(query_id=snapshot_id, format="json")
export_records(paper_refs=["arxiv:1706.03762"], format="bibtex")
```

显式 revision 选择使用 arXiv 标识和 `vN`。资源返回 `asset_ref`，可限定下载某项；不接受任意未发现 URL。PDF 验证可解析、非加密且有页面；源码目前只验证 tar 格式、不解压，其他源码格式明确返回不可用。缓存命中也复核校验值和格式，损坏缓存会按策略重新获取。返回 `identity_status` 区分来源关联和原文内容核查，不能将它改写成“论文版本已完全认证”。

导出只读本地已取得记录，不自动花费额外 API 请求补书目信息。JSON 导出实际快照、来源报告和限制；BibTeX 用 misc 条目保存已核字段，缺失单列，不猜会议名、年份、DOI。
