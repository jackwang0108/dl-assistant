# tex-mcp v2

读取固定版本的论文源码，按章节返回正文以及直接引用的图片、表格、公式与参考文献。旧接口与数据库不兼容；保留原文位置、转换依据及未解析部分，避免将处理后的文本误当作完整编译结果。

## 安装和运行

```bash
cd mcp-servers/tex-mcp
uv sync --extra dev
uv run python -m tex_mcp
```

入口命令为 `tex-mcp` 或 `python -m tex_mcp`。更新后重启 MCP 进程，确认 tex_capabilities 返回 api_version=2，且暴露下列 14 个工具。使用说明见 [tex-mcp skill](../../plugins/dl-assistant/skills/tex-mcp/SKILL.md)。

`TEX_MCP_CACHE_DIR` 默认 `~/.cache/tex-mcp`，使用 documents-v2.sqlite3、documents/、renders/ 和 pdf/。旧目录不迁移或读取。document_id 与游标依赖缓存；跨机器交接还需固定论文标识/版本、入口、文件清单与位置。

## 工具

| 工具 | 用途 |
|---|---|
| tex_capabilities | 支持范围和渲染配置 |
| tex_open | arXiv/本地源码导入，固定版本和入口 |
| tex_outline | 结构目录与原始位置 |
| tex_read | 章节正文＋本节/直接引用的图表、公式、文献 |
| tex_search | 有超时的搜索、来源定位与可交给 tex_read 的 match_ref |
| tex_objects | 按类型或定义所在节列对象 |
| tex_get_object | 按唯一 label/object_id 取对象及图像 |
| tex_references | 版本内书目、引用键、引用位置和缺失项 |
| tex_reference_lookups | 准备 paper-search.resolve_papers 输入，不发外部请求 |
| tex_read_file | 按行读取原始清单文件 |
| tex_diagnostics | 解析缺失、未知定义/分支等 |
| tex_compare | 两个固定快照的实际差异 |
| tex_attach_pdf | 以校验值绑定 PDF，保留身份依据 |
| tex_render_object | 明确 PDF 裁剪或配置好的隔离 TeX 重建 |

参数以 MCP schema 为准，具体示例与限制见 skill 的 references。

## 内部实现

- acquire.py：先将无版本 ID 解析成实际 revision，再有限额下载和逐文件解包。拒绝路径越界、链接和特殊文件；普通目录中的合法相对路径可以在根目录内解析。
- storage.py：SQLite 保存固定解析记录，文件内容、入口、版本和解析器代码/依赖签名决定 ID。显式版本可复用已验证清单；latest 先核实际版本。refresh=true 强制获取。本地源码变化或删除文件形成新快照，不靠最大 mtime 判定。
- syntax.py：以 pylatexenc 节点处理注释、原样区域、文件展开和有顺序/作用范围的有限宏展开。保留来源片段，未知条件和定义明确诊断，不执行 TeX。
- document.py：构建章节、对象、标签和引用边。章节可附定义在其他文件/章节的对象；结构编号不认证 PDF 编号。缺失或歧义不自动选择第一项。
- bibliography.py：使用 pybtex 解析 bib，bbl/inline 按缺失键补充。原文引用存在、字段解析成功、外部论文身份确认是不同状态。
- service.py：固定文档读取、正文位置、对象附件、整体 JSON 预算、续读、诊断与比较。比较图像资源时纳入文件校验值。过大记录明确分片。
- images.py：来源图像、按 DPI 绑定的缓存、显式原始 PDF 裁剪。TeX 编译只走配置的无网络 Docker，不调用宿主 pdflatex。
- server.py：14 个薄接口与结构化错误。

## 阅读与图像

先 tex_open，再 tex_outline，然后 tex_read(document_id=..., section="3.3")。默认 items 中包括 object 附件、reference 和 body。如果 truncated=true，跟随 next_cursor 获取后续内容。正文块附原文位置。关闭 include_referenced 时，仍保留本节的直接引文。source 模式查看处理范围对应的原文件片段，tex_read_file 获取精确原始行。

查证某个局部说法时，用 tex_search 找到相关命中，再将 match_ref 交给同一 document_id 的 tex_read。context_chars 控制命中前后各取的字符数。局部阅读沿用分页和附件选项。

figure 资源可能缺失、歧义或无法栅格化；可解析路径不等于已取得图片。source_asset 也不等于含子图标注、旋转裁剪和覆盖文字的完整排版图。自动生成图像可通过对应 PDF 的明确 page/bbox 核查；不按图号猜 PDF 页码。

可选重建需要已在本地的 digest-pinned `TEX_MCP_RENDER_IMAGE`。工具不自动下载镜像；Docker 配置无网络、只读根文件系统、只读源码、有限 CPU/内存/进程和超时，检查新产物及退出码。重建输出不认证为原始排版。未配置环境时报告不可用，不静默回退宿主编译。

## 测试

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
# 显式联网，仅 arXiv，不运行下载的 TeX：
TEX_MCP_RUN_LIVE=1 uv run pytest tests/test_v2_live.py -q
```

单元测试覆盖引用、宏顺序/作用范围、循环与重复输入、原样区域、bibliography 补充及解包边界。集成测试使用真实 SQLite、源图/PDF 与受控 HTTP，检查 3.3 节的跨文件图片附件、续读预算、版本缓存、DPI、PDF 裁剪和渲染失败。e2e 通过 FastMCP 协议测试全工具列表和完整流程，启动真实 stdio 子进程，并验证引用记录交给 paper-search 的协议调用。

真实 arXiv 测试使用 Attention v7 与 ResNet v1，检查版本、引用对象、可查看图片和文献记录。隔离 TeX 编译的测试会验证命令约束和失败处理；没有配置真实镜像时不声称完成真实容器编译。
