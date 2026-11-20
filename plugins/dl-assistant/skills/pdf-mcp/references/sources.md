# 结构化全文来源与版本

## arXiv

使用明确 revision 的 `https://arxiv.org/html/{id}v{n}`。可直接 pdf_open，不必先下载 PDF。已有 PDF 且知道固定 ID 时，pdf_source_candidates(document_id=doc, arxiv_id="2404.14219v1") 可构造候选，但不访问它，也不证明匹配。

[arXiv 官方说明](https://info.arxiv.org/about/accessible_HTML.html)明确 HTML 在持续补充，并非所有论文都可成功转换；[转换错误说明](https://info.arxiv.org/about/accessibility_html_error_messages.html)说明部分宏/包会导致内容错误。HTTP 成功不能证明无缺失：核标题、作者、revision、所需章节、图表和公式；必要时与同版 TeX/PDF 比对。不能在 v1 HTML 不可得时悄悄换最新版本。

已有完整 HTML 可在本地打开；相对图片资产以原 HTML 所在目录或实际 URL 为基准。原文图像和通过模型重建的内容分别标记，缺少源图保留限制。HTML 保留 MathML 及可用的源码公式 annotation/alttext；这不是从 PDF 猜出的公式。

## PMC 与出版商

[PMC 全文获取说明](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/)及其 OA 服务提供部分文章的结构化全文/可下载包，不是全部收录文章都开放相同下载方式。PMC 标识、PMID、DOI 是不同标识，不能互换；出版版本也不等于 arXiv 预印本。

pdf_source_candidates(document_id=doc, pmcid="PMC123456") 给文章页与 OA 可用性清单地址。清单本身不是文章 XML；应根据官方清单取得允许下载的 JATS/NXML，再 pdf_open 本地文件或直接全文 URL。工具不解包未知归档、不绕过访问限制，也不自动将 BioC 当作无损 JATS。

出版商 HTML/JATS 使用官方全文页面或下载入口，保留身份和版本依据。没有统一可靠的 DOI→同版本 HTML 地址规则，不凭域名猜 URL。工具支持论文 article 容器的 HTML 和 JATS XML，不保证任意商业网页都能按论文结构读取。

## 表述边界

- document_id 固定具体文件内容与当前解析签名；它不认证论文身份，也不能单独用于跨机器交接。
- 跨格式读取保存各自标识、内容校验值、来源、版本依据和位置；HTML 无 PDF 页码时返回空值，不制造页码对应关系。
- 论文级事实优先来自匹配版本原文；跨格式差异应核查，不能把不同来源中最方便的片段直接混成一个版本。
