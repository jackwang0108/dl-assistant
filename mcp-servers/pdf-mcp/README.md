# pdf-mcp v2

读取固定快照的 PDF、论文 HTML 和 JATS XML。优先利用已存在的原文结构；PDF 的快速页面操作与按需结构识别分别执行。接口和数据库不兼容 v1。

## 运行

```bash
cd mcp-servers/pdf-mcp
uv sync --extra dev
uv run python -m pdf_mcp
```

可选结构识别：`uv sync --extra dev --extra structure`，或将 `PDF_MCP_STRUCTURE_PYTHON` 指向独立准备的 Docling Python。未安装 Docling 时，基本 PDF/HTML/XML 功能仍可使用。

本机 Clash：`PDF_MCP_PROXY_URL=http://127.0.0.1:7890`。这也是显式模型下载时使用的代理。默认直连会核查并固定公共 DNS 地址；显式代理模式将域名解析和目标网络策略交给可信代理，支持 Clash fake-IP DNS，不宣称仍进行了直接地址固定。

更新后重启 MCP，确认 pdf_capabilities 返回 api_version=2。使用说明见 [pdf-mcp skill](../../plugins/dl-assistant/skills/pdf-mcp/SKILL.md)。

## 解析方案与成本

- TeX 交给 tex-mcp；可取得的同版本论文 HTML/JATS XML直接读取结构。arXiv HTML 有明确 revision URL，但不保证所有版本可用或无转换错误。PMC/出版商全文另核身份和下载范围。
- PyMuPDF 负责 PDF 文字坐标、原页渲染、裁剪、位图和基础表格检测；其文字顺序不认证为正确阅读顺序。
- Docling 负责显式选页的结构识别。默认关闭 OCR/公式识别，不下载模型；首次模型准备需 allow_model_download=true。外部推理服务关闭，不调用付费 API。
- 每个新解析任务在工作进程中运行，并执行真实总超时。成功结果按文档、页码、选项、解析器版本和 worker 签名保存。相同任务读取已有结果。
- 模型准备、首次解析、进程初始化、已准备模型的转换与结果缓存命中是不同成本。小样本实测见 [验证报告](tests/validation-report.json)，不能推断所有论文的速度或准确率排名。

## 17 个工具

| 工具 | 用途 |
|---|---|
| pdf_capabilities | 格式、运行方式和限制 |
| pdf_open | 校验并保存本地/URL 原文快照 |
| pdf_info | 来源、元数据、校验值、页数 |
| pdf_page_info | 页面几何、标签、文字层与可读性提示 |
| pdf_outline | 原始书签、源码或模型章节及边界依据 |
| pdf_read | 按页、章节、区域、解析记录或搜索命中读取，支持续读 |
| pdf_search | 搜索文字块，报告页面覆盖和用于局部查证的 match_ref |
| pdf_objects | 图、表、公式或原生位图与检测状态 |
| pdf_get_object | 对象内容、图注及可选图像 |
| pdf_render | 原始 PDF 整页/区域渲染 |
| pdf_parse | 指定页的本地 Docling 解析、可选 OCR/公式识别 |
| pdf_diagnostics | 转换/识别问题及限制 |
| pdf_references | 结构化全文的书目证据，保留身份未核状态 |
| pdf_links | PDF 内部/外部链接位置，不自动访问 |
| pdf_source_candidates | 固定 arXiv revision / PMC 全文发现候选，不认证对应关系 |
| pdf_cache_stats | v2 缓存统计 |
| pdf_cache_clear | 显式按有效期或全部清理缓存，不删原文件和模型 |

参数以实际 MCP schema 为准。页码从 1 开始，页面标签单列；bbox 统一为左上原点、PDF 点单位的 `[x0,y0,x1,y1]`，与 tex-mcp 的 PDF 裁剪一致。

## 结果与可靠性

读取结果采用 items、truncated 和 next_cursor。max_chars 限制整个 JSON；大表格、书目或长正文可分 record_fragment，按 record_index/offset 连接 text 后 JSON 解码。超出页数、时间、像素限制会明确报错，不静默返回前几项。

document_id 绑定文件内容和解析代码/依赖签名；parse_id 绑定具体识别结果。缓存源文件与派生图片校验内容。HTML 本地基准目录/远端 URL 会影响相对资源，因此纳入文档标识。跨机器交接同时保存原始标识、版本依据和文件校验值，不只交本地句柄。

模型输出不是作者源码；公式识别、表格数字、推断章节和图注关系需核原页。ResNet 实测中默认公式裁剪扩展引入了邻近内容；目前关闭该扩展，并对每条识别公式返回待视觉核查诊断。关闭公式识别时只检测到区域且没有文本，也明确报告。

HTML/XML 可按显式链接附跨章节对象和书目；PDF 中不承诺恢复完整交叉引用关系。内嵌位图不等于完整逻辑图，源图也不等于编译后带子图标记/叠字的论文图。HTML/XML 没有认证的 PDF 页码对应时，不生成伪页码。

缓存默认 `~/.cache/pdf-mcp`，可用 PDF_MCP_CACHE_DIR 覆盖；新库为 documents-v2.sqlite3，文件目录 sources-v2 / images-v2 / jobs-v2。模型目录由 PDF_MCP_MODEL_CACHE 指定。旧缓存不迁移，过期清理按显式调用执行。

## 验证

```bash
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
# 已准备模型的真实验证：
PDF_MCP_PROXY_URL=http://127.0.0.1:7890 \
PDF_MCP_STRUCTURE_PYTHON=/path/to/docling/python \
PDF_MCP_MODEL_CACHE=/path/to/huggingface \
PDF_MCP_RUN_LIVE=1 PDF_MCP_RUN_MODEL_LIVE=1 uv run pytest tests/test_v2_live.py -q
```

单元测试检查页码、整包预算、续读、下载限制、代理与 DNS、缓存及 HTML/JATS。集成测试使用真实 PDF/SQLite/渲染、图像覆写、表格失败、同页章节、扫描页，以及真实工作进程的超时和部分结果。e2e 通过 FastMCP 协议与真实 stdio 子进程检查完整流程；真实联网/模型测试另行显式运行。

[benchmark_parser.py](scripts/benchmark_parser.py) 在对应解析器环境中复现选页转换，示例：

```bash
HF_HOME=/path/to/prepared/huggingface python scripts/benchmark_parser.py docling paper.pdf --page 3 --repeat 3 --output /tmp/docling-result.json
# Marker 在单独安装的环境中运行，将 docling 改为 marker。
```

报告中已有模型准备的测量不等于全新机器的冷启动；基准脚本默认离线，不用于自动下载模型或作全量准确率排名。
