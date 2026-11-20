# 论文内部引用与外部检索的分工

## 哪种证据更直接

“这一版正文引用了什么、在哪里引用”优先看 TeX 中实际 cite 命令与键，再结合该版的 bib/bbl/inline bibliography。外部索引可能迟收录、截断或混合版本，不能代替这个版本的引用证据。

但 cite key 是项目内名字，不是 DOI；BibTeX 字段也是作者提供的书目信息，可能缺失、错误或旧于正式发表版本。tex-mcp 负责保留原文记录，paper-search 负责核外部身份、补元数据和查询后续引用者。没有源码本身的引用记录时，不能假装外部引用列表就是该版本完整 bibliography。

## 工具与状态

```python
tex_references(document_id=doc, section="3.3")
tex_references(document_id=doc, keys=["vaswani2017attention"])
tex_reference_lookups(document_id=doc, keys=["vaswani2017attention"])
```

tex_references 默认列正文实际引用或由 nocite 纳入的条目；未使用的 bib 库条目不冒充正文引用。显式 keys 可以查看库中其他条目。每项保留：原始引用键、书目字段/原始文本、来源格式与文件、cited_at（节、命令和位置）、缺失或重复状态，以及原文声明的稳定标识。

bib 使用语法解析器保留字符串宏、花括号和作者名单；bbl/inline 按缺失的引用键补充，不因发现 bib 就忽略它们。解析失败、重复键、缺字段和丢失引用明确报告。不能保证解析所有 BibLaTeX/自定义 bibliography 格式；未识别时查原文件和对应 PDF，不补造条目。

external_identity=unverified 表示尚未核外部身份，status=parsed 只表示取得了书目记录。DOI/arXiv ID 从原文字段或原始引用文本抽取，也只是带出处的待核标识。

## 交给 paper-search v2

tex_reference_lookups 返回可分页的 items：handoff 说明目标工具，reference_lookup 按 key 给 paper_search_inputs。

- 有 DOI/arXiv 等标识：传 resolve_papers(inputs=[{"identifier": ...}])。
- 只有书目信息：传 title/authors/year 候选查询，核对结果；不要接受首条标题命中。
- 只有 bbl 渲染文本、信息不足：保留 insufficient_metadata；读原始引用、抽取可核书目信息后再查，不把整段文本虚构成标题。

这个工具不直接调用外部 API，不自动消耗付费额度，也不把外部查询结果写成论文原文事实。外部核查成功后，下游记录“文档版本＋cite key → 外部稳定标识＋匹配依据＋查询时间”，保留原记录。外部数据库找不到时，原文存在的引用仍然存在，不能删除或改成无引用。

查询“谁引用了这篇论文”仍使用 paper-search 的引用者检索；TeX 中的 bibliography 只能直接提供该版论文引用别人的记录。
