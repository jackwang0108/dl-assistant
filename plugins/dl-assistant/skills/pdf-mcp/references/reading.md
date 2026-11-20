# 调用、模型和续读

## 主要调用

```python
pdf_capabilities()
pdf_open(source="/path/to/paper.pdf")
pdf_open(source="https://arxiv.org/html/2404.14219v1")
pdf_open(source="/path/to/article.nxml", source_format="xml")
# 后续使用实际返回值：
pdf_info(document_id=doc)
pdf_outline(document_id=doc)
pdf_page_info(document_id=doc, pages="1-3")
pdf_read(document_id=doc, pages="3-5", max_chars=24000)
pdf_read(document_id=doc, section="S2")  # HTML 源码章节 ID，先核 outline
pdf_read(document_id=doc, pages="3", bbox=[40,80,300,500])
pdf_search(document_id=doc, query="attention", pages="3-5")
pdf_search(document_id=doc, query="alpha beta", mode="and", section="Methods")
pdf_objects(document_id=doc, kind="table", pages="4")
pdf_get_object(document_id=doc, object_id=object_id, view="image")
pdf_render(document_id=doc, pages="4", bbox=[80,100,500,350], dpi=200)
pdf_references(document_id=doc)
pdf_links(document_id=doc, pages="1-3")
pdf_diagnostics(document_id=doc)
pdf_cache_stats()
pdf_cache_clear(expired_only=True, ttl_hours=24)
```

这共 17 个工具；实际参数以当前 MCP schema 为准。普通 PDF 读取保留文字块位置，文字顺序未认证。区域读取直接选择 PDF 文字层，不与 parse_id 组合。原生 PDF 书签章节包含共享边界页，可能带入下一节开头，需要核准确位置。

图片源对象 view=image 可以下载其明确引用的源图；不访问任意正文链接。失败逐项报告。PDF 中 figure/table/equation 的原页裁剪与 embedded bitmap 提取不同，后者可能没有图注、矢量线条和子图关系。

## 按需解析

```python
pdf_parse(document_id=doc, pages="3-5", timeout=120)
# 保留返回的 parse_id：
pdf_outline(document_id=doc, parse_id=parse_id)
pdf_read(document_id=doc, parse_id=parse_id, section=section_id)
pdf_objects(document_id=doc, parse_id=parse_id, kind="figure")
pdf_get_object(document_id=doc, parse_id=parse_id, object_id=object_id, view="image")
# 确实需要时：
pdf_parse(document_id=doc, pages="3", ocr=True, timeout=180)
pdf_parse(document_id=doc, pages="3", formulas=True, timeout=180)
```

第一次模型准备必须显式设置 allow_model_download=true；复杂模型准备可能超过默认 120 秒，可在授权范围内使用最多 600 秒。默认禁止解析进程发起网络连接，并配置 HF/Transformers 离线模式；外部推理服务始终关闭。启用下载时也只准备本地模型，不自动使用付费 OCR/API。

Docling 为可选依赖 `pdf-mcp[structure]`，可安装到 MCP 环境，也可用 `PDF_MCP_STRUCTURE_PYTHON` 指向单独准备的 Python。`PDF_MCP_MODEL_CACHE` 指定 Hugging Face 模型目录；OCR 后端还可能需要系统能力或其模型，按实际诊断准备。普通操作不导入 Docling，也不要求安装这些依赖。

论文默认不 OCR；没有文字层时再评估 OCR。formulas=false 时可能只检测公式区域、没有公式文本；formulas=true 使用识别模型，保留未经核对状态。公式识别的裁剪扩展已设为零，减少邻栏文字混入，仍不能保证符号正确。原页核查必不可少。

每个新解析任务使用隔离工作进程，有真实总超时；已保存结果直接读取。实测中复用同一常驻 converter 的纯解析约 0.24–0.32 秒/样本页，但新 MCP 工作进程还包含初始化，不能把这个数当作每次工具调用延迟。模型准备、OCR和公式识别成本分别记录，见仓库测试报告。

## 续读与限制

```python
pdf_read(document_id=doc, pages="3-5", max_chars=24000, cursor=next_cursor)
```

续读保持范围、section、parse_id、bbox、预算等参数一致。record_fragment 是一条 JSON 记录的字符串片段，按 record_index 和 offset 连接 text，final=true 时解析；不要把每段单独当完整对象。

普通读取/搜索最多选择 500 页；页面诊断与原生对象检测最多 50 页；结构识别最多 20 页；单次渲染最多 10 页。超限明确报错，不静默返回前几页。输出可分页；搜索还有正则与总耗时限制。DPI 为 36–400，每张渲染图最多 3000 万像素。bbox 越界会取实际交集并返回，完全出界、反向、非有限坐标报错。

所有位置指所保存文档，不是用户后来覆写的文件。缓存内容和派生图片被改动时检测或重建。新缓存使用 documents-v2.sqlite3 / sources-v2 / images-v2 / jobs-v2，旧库不迁移；清理缓存不删除用户原文件或模型权重，过期清理按显式调用执行。

## 网络代理

本机 Clash 可配置 `PDF_MCP_PROXY_URL=http://127.0.0.1:7890`。下载和显式模型准备均通过此代理；模型的离线解析不联网。代理模式将域名解析/连接交给明确配置的可信代理，适配 Clash fake-IP DNS；目的地址的网络访问策略需由代理执行。默认直连则检查并固定公共 DNS 地址，每次重定向重新核查，二者的网络依据分别记录，不混称。
