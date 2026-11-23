# 检索来源与使用方式（Step 2 和 Step 4）

检索分别使用以下两类工具。

1. **paper-search MCP**——用 `search_papers` 检索。每条 `queries` 指定文本和已启用的来源。引文追踪用 `get_paper_citations` / `get_paper_references`，传稳定标识。详见 [调用示例](../../paper-search/references/tools-and-examples.md)。
2. **hf CLI**（`hf papers`）——HuggingFace 论文库，独立命令行工具。**不是 `search_papers` 的 sources 之一**，命令用法见 `references/hf-papers.md`。

> hf-papers 通过 CLI 单独调用。调用 paper-search MCP 时，只指定其已支持的来源。

根据各来源擅长的任务，结合调研用途和用户熟悉度安排检索。

> 配套：query 怎么设计、沿引用关系补查、survey 优先、时间配比、去重，见 `search-strategy.md`；这里只管"用哪个来源、为什么"。

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
- **自由文本 query 会被 MCP 自动转写成 `all:"词" AND all:"词" ...` 字段式查询**（2026-08 修复：此前自由文本原样透传、arXiv 松散匹配导致主题过滤失效，日期窗检索近期论文返回大量无关论文）——所以宽词 + 日期窗现在能同时成立，直接写自然语言关键词即可；带引号的短语会保持整短语匹配。但关键词匹配的固有短板仍在：**同义变体、替代术语召回差**（靠 hf 语义搜索补，见下节）；**常见词区分度低**（如 query 里带 "learning"，会放进摘要顺带提及的论文）——使用更具体的关键词可提高准确性，宽泛的概念查询用语义搜索补充。
- **Scholar 只支持到年**；Semantic Scholar 支持发表日期或年份。要核 arXiv 首次提交日期用 arXiv 来源（各来源日期粒度的说明见 `paper-search/references/date-filtering.md`，以它为准）。
- Scholar 只返回摘要片段，Semantic Scholar 和 arXiv 提供完整摘要。需要确认分类或深入分析时，优先查阅完整摘要。
- Semantic Scholar、Scholar 和 OpenAlex 提供引用数，识别奠基作和里程碑时可作参考。arXiv 不提供引用数。
- **沿引用关系补查（`get_paper_citations` / `get_paper_references`）主力是 semantic_scholar**（提供较完整的引用关系）。

---

## 二、hf CLI（并列的第二工具）

- **hf-papers 是 arxiv 的社区策展子集**（社区提交/讨论的 arxiv 论文），**不是全量 arxiv**——不能替代 arxiv 检索近期论文。
- 但 HF 对收录文章做过 AI 解析（`ai_keywords` / `ai_summary`），**`hf papers search` 是语义搜索、召回质量明显好于 arxiv 的关键词匹配**——同义变体、替代术语召得回，正好补上 arxiv 检索近期论文的最大短板。
- 还带 **upvotes / github_stars / organization** 社区信号。
- `search` 无日期过滤，要近期按返回的 `published_at` 后筛。**补查近期工作 = 一组定向 `search`（按子方向各查询一次）+ 后筛**；`ls --month/--week` 实测硬上限 100 篇且无分页，不适合按特定主题补查历史论文，`ls --date` 只适合看近几天日报（细节见 `references/hf-papers.md`）。
- 命令速查（安装 / `--format json` / 日期限制 / 失败处理）见 **`references/hf-papers.md`**。

---

## 三、按职能分配（不是按轮次）

五种**职能**，按需调用（前四个走 paper-search MCP，最后一个走 hf CLI）：

- **语义查全（主力）= semantic_scholar + scholar**：第一轮广泛检索的主力，负责召回率，带回引用数。宽泛、模糊的方向描述用它们。
- 第一轮用 arXiv 的 `cat:`、关键词和近期日期范围准确查找新投稿，加入候选清单。范围宽泛的语义查询使用其他来源。
- 第一轮用 hf CLI 的 `hf papers search "<核心概念>"` 查找相关论文。补查近期工作时，为各子方向分别发起一次定向 `search`，再按 `published_at` 筛选。`ls --month` 最多返回 100 篇且无分页。
- **沿引用关系补查 = semantic_scholar**：贯穿两轮，从核心论文往外滚（见 `search-strategy.md`）。
- **补充机构和作者信息 = openalex**：需要补充机构或作者信息时使用。

> 第一轮同时使用 arXiv 和 hf CLI，让近期工作也进入候选清单，参与 Step 3 的分类。Semantic Scholar 和 Scholar 扩大覆盖，arXiv 按关键词和日期查新，hf CLI 补充同义表述及各子方向的近期论文。

---

## 四、按用途和熟悉度调整检索范围

分别确定近期检索力度和整体覆盖范围。

- **所有用途均查找近期工作**。用 arXiv 日期范围和 hf 定向 `search`。学习理解时可以只查近 3-6 个月，将结果纳入候选但不深入分析。寻找研究方向时覆盖近 1-2 年并深入分析。
- **整体覆盖范围按用途调整**。寻找研究方向时必须沿引用关系补查、扩大时间范围，并严格检查 Step 5 的覆盖情况。遗漏关键新工作可能导致 `idea-find` 重复研究已解决的问题。其他用途可以适当放宽覆盖范围。

| 用途 | SS/scholar 语义查全 | 检索近期论文（arxiv + hf） | 说明 |
| --- | --- | --- | --- |
| 学习理解 | 重 | **必做**（窗可短：近 3-6 月） | 重奠基作和综述，但最新进展也得知道 |
| 找研究方向 | 重 | **必做（重：近 1-2 年 + 深入分析）** | 最前沿直接决定方向新鲜度；**全+新双高** |
| 定位自己的工作 | 重 | **必做**（中：近 1 年） | 要全也要不漏掉近期竞品 |
| 选技术方案 | 重 | **必做**（中：近 1 年） | 解法空间要含最新方案 |

**熟悉度修正**（与用途正交，叠加生效）：

- 用户**基本陌生**时，优先覆盖奠基作和综述。
- 用户**就在其中做**时，更注重近期进展。

---

## 五、两轮各自怎么用来源

- **第一轮 · Step2 广泛检索**：paper-search MCP 的 SS + scholar 做语义查全（每组 query 一个检索子 agent）；同时**必做检索近期论文**（力度按用途加权）：arxiv 近期日期范围检索近期论文（MCP）+ hf `search` 语义召回 + hf 定向 `search` 补查近期工作（CLI）。所有结果一起进候选论文清单、一起参与 Step3 确定分类方式。
- **第二轮（Step 4）**。子 agent 主要阅读分给该子领域的论文 PDF。需补查时，用 arXiv 的 `cat:`、关键词和日期范围查找该子领域的最新或遗漏工作。不清楚是否有同义表述时，可再做一次 hf `search`。

---

## 六、检索来源失败时的处理

- paper-search MCP：检查返回里的 `sources_failed`，某来源失败就记录、切其他来源继续，**不中断整个流程**。
- `scholar` 依赖 SERPAPI_KEY、`openalex` 依赖 OPENALEX_API_KEY——没配置会失败或返回空，此时退回 SS + arxiv 也能跑。
- hf CLI：装不上 / 限流就记录后继续（**arxiv 检索近期论文必须保住**），并在 `survey.json` 的 `coverage_notes` 注明 hf 源缺失（详见 `references/hf-papers.md`）。
- 全部来源都失败，才提示用户调关键词 / 检查配置。
