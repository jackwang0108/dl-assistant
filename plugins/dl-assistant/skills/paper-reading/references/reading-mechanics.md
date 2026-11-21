# 读论文的机械操作（Step 1 用）

Step1 的骨架在 SKILL.md（来源判断 + 读取策略一句话 + "不立刻开讲"），这里是操作细节。

## 一、来源与工具（按优先级）

- **用户给 arXiv ID / abs URL 或论文标题** → 标题先用 `resolve_papers` 核对，已有 arXiv ID 直接交给 `tex_open`。取得固定版本后用 `tex_outline` 和 `tex_read`。源码不可用时，用同版本全文或 PDF 走下方 PDF 通道。
- **用户给本地 PDF 路径 / 非 arXiv 的 PDF URL** → 直接用 **pdf-mcp** 读，无需 paper-search，也不走 tex-mcp。
- **用户只粘了摘要/标题** → 先就摘要交流，并告知：要讲方法细节或做实验判断，需要完整论文（arXiv ID 或 PDF）。

## 二、读取策略（按需，绝不一次性读全文）

**tex-mcp 通道（arXiv 论文首选）：**

1. `tex_open` 打开源码，保存实际版本和 `document_id`。后续所有 TeX 读取使用此 ID，按返回游标读完所需范围。
2. `tex_outline` 找到摘要、引言和结论对应的标题，按节调用 `tex_read(document_id, section=...)`，形成整体判断。
3. 后续按需 `tex_read(document_id, section=...)` 读 method/experiment/附录具体节；核对返回的公式源码和引用位置，排版编号按需查原页。
4. **图表是论文信息密度最高的地方**：正文里的浮动体锚点（`[Figure 2 (label=fig:arch)]`）→ `tex_get_object` 拿原图路径用视觉工具看；表直接用节返回里的完整 `tabular` LaTeX，也可用 `tex_get_object` 按精确标签取表，排版需核对时渲染对应 PDF 页。

**pdf-mcp 通道（降级 / 本地 PDF）：**

1. `pdf_open` 取得 `document_id`，再用 `pdf_info` / `pdf_outline` 看页数和目录。
2. 读前 3-5 页（abstract+intro）+ 最后 1-2 页（conclusion），形成整体判断。
3. 后续按需读 method/experiment 具体页码。
4. 看图表用 `pdf_render` 把那一页**整页渲染成 PNG**（图 + caption 一起），用同一份快照的 ID 调用。

## 三、全文获取失败的回退

按序降级，每一级失败再走下一级：

1. **tex-mcp**：`tex_open` 打开固定版本 → 成功即走 tex 通道（见上）。
2. **pdf-mcp**：直接用 `pdf_open` 打开本地 PDF、已核同版本的 HTML/XML 或 PDF URL。需下载时先用 `download_paper_asset` 获取具体版本的 PDF 路径。扫描页可用 `pdf_render` 检查原页，或按该 skill 的说明启用 OCR。
3. 都失败 → 诚实告诉用户"拿不到全文，只能基于摘要/你提供的信息回答"，不硬编。
