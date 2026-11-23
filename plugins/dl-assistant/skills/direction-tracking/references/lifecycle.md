# 运行方式和论文来源

## 四种运行方式

### 首次配置（Setup）

1. 询问方向描述、关键词和同义词，以及 2–5 篇种子论文的 arXiv ID。保存根目录固定为 `<项目>/docs/direction-tracking/`。
2. 建立 `track-<slug>/`，写入 `config.yaml`、空的 `seen.jsonl` 和 `library.md`，以及包含 `slug`、`created`、`last_run=null` 的 `meta.json`。
3. 进入首次收集。

### 首次收集（Bootstrap，使用 B 类）

1. 对每篇种子论文调用 `paper-search get_paper_citations`，传入稳定的 arXiv 标识，详见下方 B 类说明。将返回的结果在本地按 `published` 排序，每篇种子默认保留最近约 50 篇引用者，用户可调整。该工具不提供按日期排序的参数。
2. 合并并去重后进入两轮筛选。此时 seen 为空，合并后的候选都是新论文。
3. 所有获取过的论文都保存到 `seen.jsonl`。通过筛选的写入 `library.md` 和 `runs/<日期>.md`。
4. 更新 `meta.last_run = now`。

首次收集的目的是根据已有引用回顾这个方向以前的工作。

### 后续更新（使用 A 和 B 类）

1. **A 类**：按 arXiv 关键词查询从 `last_run → now` 的投稿。为覆盖投稿日期的波动，查询起点向前重叠 2 天，再根据 seen 去重。
2. **B 类**：对每篇种子论文调用 `get_paper_citations`，传稳定的 arXiv 标识，按覆盖情况和预算继续获取。将结果与 seen 比较，找出本次新增的引用者。
3. 合并 A、B 结果并去重，把新 ID 记入 seen。做两轮筛选，再更新 `library.md` 并撰写本次简报。
4. 更新 `meta.last_run = now`。

### 按会议与年份查询（使用 C 类）

用户提供会议名和年份，或直接提供 URL、论文清单。按 `conference-sources.md` 获取，合并去重后进行两轮筛选，再更新 `library.md` 并撰写本次简报。可单独查询会议，也可与后续更新一并执行。仅查询 C 类时保持原有 `last_run`，因为 C 类不参与 A 类的日期范围计算。

## 三类论文来源

### A 类：arXiv 关键词查询

- arXiv API 关键词查询：`(all:"kw1" OR all:"kw2" OR ...) AND submittedDate:[last_run TO now]`。同义词组内和各组之间均使用 OR。
- 使用 `scripts/fetch_arxiv_keywords.py`，按关键词的 OR 组合和提交日期范围查询。返回的论文记录字段与 `fetch_arxiv_daily` 一致，供 R2 复用。主会话先把 `config.yaml` 的同义词组展开成一个关键词列表，因为脚本不处理同义词分组。
- A 类能够及时查到首次提交的新论文。

### B 类：引用种子论文的工作

- 对每篇种子发起一次 `paper-search get_paper_citations` 查询。
- 使用稳定标识，例如 `get_paper_citations(paper_ref="arxiv:…")`。来源需要其他标识时，先用 `get_papers` 或 `resolve_papers` 核实别名。
- 用 `get_query_results` 读完当前快照，必要时用 `extend_query(action="fetch_more")` 继续获取。记录查询失败、因预算截断的结果和未确认的覆盖范围。
- 后续更新不设日期范围，在预算内获取引用者，再与 seen 比较。B 类结果可能较晚出现，用来补充 A 类未检索到的工作。
- 若新增的引用者超过阈值（默认约 100 篇），先报告结果并请用户确认保留上限，再做两轮筛选。

### C 类：会议论文集

- 来源涵盖 11 个会议，各会议的网站及 OpenReview 和 ACM DL 无法访问时的处理方式见 `conference-sources.md`。
- 有 arXiv 版本的论文按 arXiv ID 跨来源去重。没有 arXiv 版本的使用标题哈希或 DOI。

## 根据已有目录选择运行方式

检查固定目录 `docs/direction-tracking/` 下是否已有 `track-<slug>/`。

- 没有对应目录时，先做首次配置。
- 有对应目录时，读取 `config`、`seen` 和 `last_run`，做后续更新。
- 有多个目录或无法确定方向时，请用户确认本次要跟踪哪一个。
