# v2 阅读、续读与对象核查

## 固定版本与入口

```python
tex_capabilities()
tex_open(source="1706.03762v7")
tex_open(source="/path/to/source", main_tex="main.tex")
# 取得真实 document_id 后：
tex_outline(document_id=doc)
tex_read(document_id=doc, section="3.3")
tex_read(document_id=doc, section="3.3", cursor=next_cursor)
```

无版本 arXiv 请求先核实际 revision，再下载该 revision；显式版本缓存命中时先核文件清单，不把 v1 当 v2。refresh=true 强制重新获取；本地源码每次重新打开按内容生成快照。多个入口不自动猜，依据 MAIN_AMBIGUOUS 的 candidates 明确 main_tex。失败/未完成的解包不会作为已完成记录。

源码与解析结果固定保存在 documents-v2.sqlite3 / documents/。数据库不迁移旧缓存。解析器代码/依赖签名、文件内容、版本与入口共同决定文档标识，变更后不继续使用旧解析结果证明新内容。旧快照仍可读，缓存被修改则报 CACHE_CHANGED。

## 读取范围

```python
tex_read(document_id=doc, section="Method", include_nested=True,
         include_referenced=True, asset_mode="images", max_chars=24000)
tex_read(document_id=doc, section="3.3", view="source")
tex_read_file(document_id=doc, path="sections/method.tex", start_line=20, end_line=80)
tex_search(document_id=doc, query="contrastive", mode="literal")
tex_diagnostics(document_id=doc)
```

section=None 顺序读正文，不重复遍历父子节；include_nested=false 只读所选节到首个子节前。默认附件只沿直接关系取得，不递归读取其他章节或下载所有外部论文。附件图注中的引用文献也可一并取得，但不因此展开无限引用链。

游标绑定文档、范围、视图、图像模式和预算。续读时保持其他参数一致。大条目使用 record_fragment，需要按 record_index/part 顺序连接 text 后按 JSON 解码；不要丢弃非 body 类型内容。

## 对象与实际图像

```python
tex_objects(document_id=doc, kind="figure")
tex_get_object(document_id=doc, object_ref="fig:model-arch", asset_mode="images", dpi=200)
tex_get_object(document_id=doc, object_ref="equation:1", asset_mode="metadata")
```

label 和 object_id 都要求唯一；重复 label 会明确报歧义。object_id 是此快照的源码顺序标识，不是经过编译核实的图号。读取正文时保留原始 ref 命令，不用推算编号替换成确定的论文编号。

资源路径有 resolved/missing/ambiguous 等状态；图像有 ready/invalid_image/rasterization_failed/unsupported_format 等状态。PDF 源图按指定 DPI 栅格化，缓存绑定源文件和 DPI；多页源图当前默认展示第一页并报告页数，不能把第一页当全部子图。PNG/JPEG 原始文件按实际尺寸提供。EPS/SVG 等无法直接处理时明确返回限制。

## PDF 核对和隔离重建

```python
tex_attach_pdf(document_id=doc, path="/path/to/same-version.pdf",
               identity_basis="已核标题、版本和来源")
tex_render_object(document_id=doc, object_ref="fig:model-arch", method="pdf",
                  pdf_ref=pdf_ref, page=3, bbox=[20, 80, 400, 500], dpi=160)
```

bbox 为 PDF 页面坐标点，page 从 1 开始，区域必须在页面内。绑定记录保留 identity_status=unverified：工具不会将用户/agent 给出的身份依据认证成事实。先核对应版本再使用。

isolated_tex 需要可用 Docker 与已在本地的、带 sha256 digest 的 TEX_MCP_RENDER_IMAGE；不自动拉取镜像。容器无网络、只读根文件系统、源码只读，并有限制内存、进程与运行时长。检查编译退出码及新 PDF，不接受上次残留结果。当前运行环境未实测配置好的 TeX 镜像时，报告此能力未做真实环境验证；不将命令模拟测试称为真实容器编译成功。

## 版本比较

```python
tex_compare(left_document_id=old_doc, right_document_id=new_doc)
```

按结构 ID、对象标签/顺序和引用键比较，返回实际差异并分页。章节重排、标签变更可能表现为新增、删除或改变，不据此直接判断论文贡献变化。需要时回到两侧原始位置和 PDF 核查。
