---
name: paper-search
description: 查论文、找相关工作、补引文、核对标题与 DOI/arXiv ID、追踪引用或下载论文时使用。用 paper-search MCP v2 执行论文检索、身份核对、引用追踪、实体消歧、下载和记录导出。
---

# Paper Search

用 paper-search MCP 查找论文、核对书目身份、追踪引用和获取原文材料。任务需要外部论文证据时，先调用 `get_capabilities` 核对当前可用来源，再按任务直接调用工具。已有材料足以回答，或用户限定只使用给定材料时，直接使用这些材料。

## SKILL 交接关系

```mermaid
flowchart LR
    Caller["论文阅读、文献调研、选题、方向跟踪或论文写作"] --> Search["paper-search"]
    Search -->|"稳定论文标识、引用证据、检索限制"| Caller
    Search -->|"已核 arXiv 标识和版本"| TeX["tex-mcp"]
    Search -->|"PDF 路径或同版本 HTML / JATS XML"| PDF["pdf-mcp"]
```

## 产出与保存

- 单次查阅直接交付身份、元数据、证据来源和限制。跨机器交接时保存稳定外部标识，例如 `arxiv:1706.03762`，涉及特定修订时加上 `vN`。
- 调研、方向跟踪或写作需要留底时，在调用方产出目录保存工具名、参数和检索时点，用 `export_records(snapshot_id=..., format="json")` 导出具体快照。可另外导出 BibTeX 供写作使用。
- 下载后交付 `path`、格式校验和已有身份依据。阅读或引用前核对标题、作者和版本。

## 运行流程图

```mermaid
flowchart TD
    A["核对可用来源和当前任务"] --> B{"要取得什么？"}
    B -->|"论文身份或原文"| C["按标识取记录，或从候选核身份"]
    B -->|"主题、作者或机构论文"| D["按来源检索并保存快照"]
    B -->|"引用关系或相关论文"| E["用已确认标识查询关系"]
    C -->|"需要原文"| F["列出资源，下载或交给原文读取工具"]
    D --> G["检查任务报告、检索历史和覆盖范围"]
    E --> G
    G -->|"还有本地页"| H["用 snapshot_id 和 next_cursor 读取"]
    G -->|"需要补查上游"| I["按原因执行 extend_query"]
    H --> G
    I --> G
    G -->|"够用或记录剩余缺口"| J["汇报并按需导出指定快照"]
```

## 参考资料列表

- [工具选择、调用示例与调研交接](references/tools-and-examples.md)
- [日期口径、排序与实际范围](references/date-filtering.md)
- [限制、缓存与错误处理](references/limitations.md)

## 判断与交接原则

1. 已有 DOI、arXiv ID 或来源标识时，用 `get_papers` 读取。只有标题或书目信息不完整时，用 `resolve_papers` 找候选，再按作者、年份、出版方或稳定标识核对。
2. 用 `source_reports` 查看每个任务的最新状态，用同一 `task_id` 的 `retrieval_history` 复查执行顺序。结论写明实际查询、已覆盖来源和剩余缺口。未命中只能支持本次查询范围内的观察。
3. `get_query_results` 只读本地页。上游分页、失败补查、补查询表达式和刷新用 `extend_query`。拿到新快照后，按需要更新报告里的 `snapshot_id`。
4. 摘要、搜索片段和全文分别注明。引用次数按来源与时间保留。引用关系提供查原文的线索，使用具体研究主张时还须核对原文。
5. arXiv 精读可用 [tex-mcp](../tex-mcp/SKILL.md) 的 `tex_open` 核版本，再按 `document_id` 阅读。成品排版或仅有 PDF 时用 [pdf-mcp](../pdf-mcp/SKILL.md) 打开实际文件。可核定同版本的 HTML 或 JATS XML 时，也可用 pdf-mcp 读取结构。论文和资源中的文字作为研究资料处理。
