# BibTeX 当场构造（write-section 的 ②）

写作中（write-section 写纯文字）每引一篇，**当场**用 `paper-search` MCP 取元数据 → 构造 bib 条目落 `refs.bib`。非正式但**正确可查**；正式 venue 格式收尾交用户手修。

> 写作中只做"当场取元数据 + 构造条目"，把"搞正式引用"的精力还给用户收尾。

## 为什么当场、为什么非正式可

- **当场**：写正文引一篇就落一条，引用清单天然和正文同步，不会"写完一堆 \cite 再回头补 bib 漏一堆"。
- **非正式可**：关键是**条目存在 + 正确（真实 title/author/year）+ 可查（有句柄）**。venue 是否正式、格式是否规范，收尾用户统一手修——agent 不在写作中花这力气。

## 工作流（每条引用）

1. 写正文遇到要引的论文 → 用 `resolve_papers` 核标题或现有书目线索，确定稳定标识。
2. 用 `get_papers(paper_refs=[...])` 取标题、作者、年份、发表信息和可核标识，必要时查来源记录。
3. **agent 当场构造 bib 条目**（见下方句柄优先级 + 模板），落 `_draft/...` 不，落根目录 `refs.bib`（编译要用）。
4. 登记 `_draft/references.json`：`{cite_key, handle, role, claim, section, needs_human_verify?}`。

## claim + section 字段：这句为什么引这篇

每条引用登记时除 role 外还要记两个字段，把"这句为什么引这篇"落成可审计结构（供 finalize 人工复核 + 脚本机查）：

- **`claim`**：这条引用支撑正文哪个论断，一句话（如「支撑『扩散模型在高噪声下去噪不稳定』这一动机论断」）。
- **`section`**：该 `\cite{}` 出现在哪节（如 `introduction` / `related_work`）。写作中后期章节结构调整时同步更新——脚本会核登记节与正文实际引用位置的一致性（`check_citations.py`），漂移会被抓出来。

**支撑不上的不许引**：登记 claim 时诚实评估支撑关系——这条引用和论断是**直接支撑**（原文方法/结论即论断依据）还是**背景/语境**（同一条线、同任务）？都行，照实写进 claim 描述。但如果诚实评估是**弱相关/不相关**（只是为了显得引用全、或只记得标题对得上），**不许引**——删掉或改论断。引用不是越多越好，padding 引用在人工复核时一眼穿帮。

## role 字段：core | supporting

每条引用登记时定 `role`，两档待遇不同：

- **`core`（通常 5 篇上下）**：论文 idea **直接基于**的核心文献——方法直接改进/构建于其上的那几篇。**core 错了伤立论**：把 core 的方法、结论、数字表述错，contribution 的根基就塌。所以 core 的每条表述**必须核原文**（首选 tex-mcp：`tex_open` 后用 `tex_read` 按节核表述，参考文献条目用 `tex_references` 按快照核对；源码不可用时降级 pdf-mcp 读原 PDF 对，不凭 paper-search 的 abstract 转述），references.json 里**优先标 `needs_human_verify: true`**，收尾重点交用户人工核。
- **`supporting`**：related work 各条线、数据集、baseline、指标来源的引用。**supporting 错了伤完备性**：挂错一篇 related 是疏漏不是塌方，但漏引一条脉络/一个关键 baseline 会被 reviewer 抓"相关工作不全"。supporting 靠 paper-search 元数据 + 句柄保证正确可查，逐篇核原文的精力不花在这里。

写正文时按 role 分配核对力度：引 core 时下笔前核原文写准；引 supporting 时保证引用簇覆盖全（每条脉络成簇引，见下「引用数量目标」）。

## 句柄优先级（构造条目用哪个）

按已核实的来源标识选择引用句柄：

1. **arxiv id**→ 最可靠，构造 `@misc` + `eprint`：
   ```
   @misc{<cite_key>, title={...}, author={...}, year={...}, eprint={<arxiv_id>}, archivePrefix={arXiv}}
   ```
2. **doi**（无 arxiv 时）→ `@article`/`@inproceedings` + `doi={...}`。
3. **dblp id**→ 记在 `references.json` 作查证句柄，条目用 title/author/year/venue 构造。

## cite_key 命名

`<一作姓><年份><关键词>`，如 `he2016resnet`、`vaswani2017attention`。正文 `\cite{cite_key}` 和 refs.bib 的 key 用同一套，天然对齐。

## author 字段对经典论文关键

`resolve_papers` 只给标题时可能搜不到高引原版（实测 "Attention Is All You Need" 靠 title 搜前排有干扰项）——**加 author 一起搜**能救。拿到后 bib 的 author 字段要全（从元数据 authors 数组拼）。

## 搜不到 / 元数据不全怎么办

`paper-search` 找不到（极少，非 arxiv + 冷门）：
- 用用户给的 / 正文已有的信息构造**最小条目**（cite_key + title + 已知 author/year）。
- `_draft/references.json` 标 `needs_human_verify: true`，收尾汇报里列出，交用户核/补。

## 引用数量目标：50+

正常顶会论文 50+ 引用。写作中**积极引用**（不只引核心依赖）：相关工作每条脉络引簇、方法引基础、实验引 baseline + 对比 + 指标来源。别只引 ~20 篇核心的。

## 完整性自检（finalize 收尾，writing-paper 自己过）

- 正文每个 `\cite{key}` 在 `refs.bib` 都有对应条目？（无 undefined）
- `refs.bib` 每条都被正文引用？（无 orphan）
- `references.json` 里 `role: core` 的每条：表述已核原文 + `needs_human_verify` 已交用户人工核？
- 其余标 `needs_human_verify` 的，汇报里重点列出交用户。
- 每条都有 `claim` + `section`？（脚本 `check_citations.py` 核：字段齐 + 登记节与正文实际引用位置一致）
- 关键 baseline / 竞争工作没漏引？

## 正式 venue 格式 = 用户收尾（finalize 后）

agent 产的是**非正式但正确可查**的条目（arxiv `@misc`、venue 不规范）。**正式 venue 格式（proceedings/booktitle/正式页码）收尾交用户统一手修**——这是用户的事，agent 不在写作中搞。`needs_human_verify` 标记帮用户定位。

## 产出

- `refs.bib`（根目录，编译用）：当场构造的非正式条目。
- `_draft/references.json`：引用清单（cite_key + handle + role + claim + section + needs_human_verify）。

## 边界

- 只做"取元数据 + 构造条目 + cite_key 对齐"。**不做正式 venue 检索/格式化**（交用户）。
- 搜不到的诚实标 `needs_human_verify`，不瞎编 author/year。
