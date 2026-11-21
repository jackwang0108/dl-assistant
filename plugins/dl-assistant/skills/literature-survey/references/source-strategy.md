# 检索来源策略（Step 2 检索、Step 4 深挖现搜时都用）

**检索的工具面有两个，并列关系**：

1. **paper-search MCP**——用 `search_papers` 检索。每条 `queries` 指定文本和已启用的来源。引文追踪用 `get_paper_citations` / `get_paper_references`，传稳定标识。详见 [调用示例](../../paper-search/references/tools-and-examples.md)。
2. **hf CLI**（`hf papers`）——HuggingFace 论文库，独立命令行工具。**不是 `search_papers` 的 sources 之一**，命令用法见 `references/hf-papers.md`。

> 注意，最容易犯的错：把 hf-papers 当成 paper-search 的一个 source 去调——它不在 MCP 里，这么调它永远不会执行，扫新就静默缺了一块。两个工具面各调各的。

**来源不按"轮次"切，按"职能"分配，再用用途 × 熟悉度加权。** 下面定清楚每个来源干什么、什么时候用。

> 配套：query 怎么设计、滚雪球、survey 优先、时间配比、去重，见 `search-strategy.md`；这里只管"用哪个来源、为什么"。

---

## 一、paper-search MCP 四来源职能表

| 来源 | 语义召回 | 时效 | 精确查询 | 引用数 | 摘要 | 引文图谱 |
| --- | --- | --- | --- | --- | --- | --- |
| **semantic_scholar** | 强 | 慢（批量收录，数天~两周） | 否 | 有 | 有，全文摘要 | 有，citations / references |
| **scholar**（经 SerpAPI） | 强 | 中 | 否 | 有 | 受限，只有 snippet 片段 | 受限，经 SerpAPI |
| **arxiv** | 弱（关键词匹配 title/abs） | **快（次日收录）** | 有，`cat:`/`ti:`/`abs:` + 日期范围，服务端过滤 | 无 | 有，全文摘要 | 无 |
| **openalex** | 中 | 中 | 否 | 有 | 部分 | 有，引用 |

会影响决策的细节：

- **用 arXiv 按首次提交日期查新论文**。在 `filters.date_range` 中设 `date_type="first_submitted"`、`start` 和 `end`，另传 `sort="date_desc"`。核对来源报告和检索覆盖。
- **自由文本 query 会被 MCP 自动转写成 `all:"词" AND all:"词" ...` 字段式查询**（2026-08 修复：此前自由文本原样透传、arXiv 松散匹配导致主题过滤失效，日期窗扫新返回全是噪声）——所以宽词 + 日期窗现在能同时成立，直接写自然语言关键词即可；带引号的短语会保持整短语匹配。但关键词匹配的固有短板仍在：**同义变体、换皮叫法召回差**（靠 hf 语义搜索补，见下节）；**常见词区分度低**（如 query 里带 "learning"，会放进摘要顺带提及的论文）——特化词越多越精确，宽召回别指望它。
- **Scholar 只支持到年**；Semantic Scholar 支持发表日期或年份。要核 arXiv 首次提交日期用 arXiv 来源（各来源日期粒度的单一真相源是 `paper-search/references/date-filtering.md`，以它为准）。
- **scholar 的摘要只是 snippet 片段**；SS、arxiv 是全文摘要——做 taxonomy / 深挖时 SS、arxiv 的料更足。
- **引用数只有 SS / scholar / openalex 有，arxiv 没有**——判断奠基作 / 里程碑靠引用数，别指望 arxiv。
- **引文链滚雪球（`get_paper_citations` / `get_paper_references`）主力是 semantic_scholar**（图谱最干净）。

---

## 二、hf CLI（并列的第二工具面）

- **hf-papers 是 arxiv 的社区策展子集**（社区提交/讨论的 arxiv 论文），**不是全量 arxiv**——不能替代 arxiv 扫新。
- 但 HF 对收录文章做过 AI 解析（`ai_keywords` / `ai_summary`），**`hf papers search` 是语义搜索、召回质量明显好于 arxiv 的关键词匹配**——同义变体、换皮叫法召得回，正好补上 arxiv 扫新的最大短板。
- 还带 **upvotes / github_stars / organization** 社区信号。
- `search` 无日期过滤，要近期按返回的 `published_at` 后筛。**近期兜底 = 一组定向 `search`（按子方向各发一发）+ 后筛**；`ls --month/--week` 实测硬上限 100 篇且无分页，窄主题回填无效，`ls --date` 只适合看近几天日报（细节见 `references/hf-papers.md`）。
- 命令速查（安装 / `--format json` / 日期边界坑 / 失败处理）见 **`references/hf-papers.md`**。

---

## 三、按职能分配（不是按轮次）

五种**职能**，按需调用（前四个走 paper-search MCP，最后一个走 hf CLI）：

- **语义查全（主力）= semantic_scholar + scholar**：第一轮广撒的主力，负责召回率，带回引用数。宽泛、模糊的方向描述用它们。
- **时效 + 精确扫描 = arxiv**：**第一轮就用**，但不拿它做宽泛语义搜（它弱）。用 `cat:` + 近期日期范围做一次"新文章精确扫描"，把最新工作捞进候选池。
- **语义召回 + 近期兜底 = hf-papers（hf CLI）**：**第一轮就用**。`hf papers search "<核心概念>"` 做语义召回（同义变体不漏）；近期兜底 = **按子方向各发一发定向 `search` + `published_at` 后筛**（不用 `ls --month`：硬上限 100 篇、无分页，回填无效）。
- **引文链滚雪球 = semantic_scholar**：贯穿两轮，从核心论文往外滚（见 `search-strategy.md`）。
- **机构/作者补充 = openalex**：需要时用（机构搜索依赖它），非主力。

> **为什么 arxiv + hf 必须在第一轮、不能只放第二轮**：如果它们只在深挖（Step4）才用，最新论文要等领域地图画完、轴定死之后才进来——没机会进候选池、参与定轴，只能被硬塞进已冻结的子领域。而"找最新"的需求恰恰最需要新文章参与定轴。所以第一轮两者就和 SS/scholar 并肩，只是分工不同：**SS/scholar 查全、arxiv 扫新（全量关键词）、hf 召回（语义）+ 兜底（定向 search）**。

---

## 四、用途 × 熟悉度加权（扫新是全用途硬要求，力度随用途变）

**"新"和"全"分开定级**：

- **新（扫新）= 全用途硬要求，不可跳**。arxiv 日期范围扫新 + hf 定向 `search`，任何用途必做——差别只在**时间窗和深度**：学习理解可以只扫近 3-6 个月、进池不深挖；找研究方向要扫足近 1-2 年并深挖。
- **全（查全率）= 按用途分级**。**找研究方向要"全且新"**（滚雪球必做、时间范围放宽、Step5 独立查漏覆盖度从严）——这份 survey 是 idea-find 的 gap 输入，漏一篇关键新工作，IF 的方向就可能建在已被填掉的 gap 上；其他用途查全可适当放宽。

| 用途 | SS/scholar 语义查全 | 扫新（arxiv + hf） | 说明 |
| --- | --- | --- | --- |
| 学习理解 | 重 | **必做**（窗可短：近 3-6 月） | 重奠基作和综述，但最新进展也得知道 |
| 找研究方向 | 重 | **必做（重：近 1-2 年 + 深挖）** | 最前沿直接决定方向新鲜度；**全+新双高** |
| 定位自己的工作 | 重 | **必做**（中：近 1 年） | 要全也要不漏掉近期竞品 |
| 选技术方案 | 重 | **必做**（中：近 1 年） | 解法空间要含最新方案 |

**熟悉度修正**（与用途正交，叠加生效）：

- 用户**基本陌生** → 奠基作 / 综述权重升（先打地基）；
- 用户**就在其中做** → 扫新权重升（要的是更新，不是地基）。

---

## 五、两轮各自怎么用来源

- **第一轮 · Step2 广撒**：paper-search MCP 的 SS + scholar 做语义查全（每组 query 一个检索子 agent）；同时**必做扫新**（力度按用途加权）：arxiv 近期日期范围扫新（MCP）+ hf `search` 语义召回 + hf 定向 `search` 近期兜底（CLI）。所有结果一起进候选池、一起参与 Step3 定轴。
- **第二轮 · Step4 深挖**：深挖子 agent 主要读已划给它的论文 PDF。**要现搜补料时**，优先用 **arxiv 精确查询**（`cat:` + 关键词 + 日期）补这个子领域的最新进展和漏网工作——此时已知道子领域边界，精确查询比宽泛语义搜更合适；同义变体拿不准时顺手补一发 hf `search`。

---

## 六、来源失败的兜底

- paper-search MCP：检查返回里的 `sources_failed`，某来源失败就记录、切其他来源继续，**不中断整个流程**。
- `scholar` 依赖 SERPAPI_KEY、`openalex` 依赖 OPENALEX_API_KEY——没配置会失败或返回空，此时退回 SS + arxiv 也能跑。
- hf CLI：装不上 / 限流就记录后继续（**arxiv 扫新必须保住**），并在 `survey.json` 的 `coverage_notes` 注明 hf 源缺失（详见 `references/hf-papers.md`）。
- 全部来源都失败，才提示用户调关键词 / 检查配置。
