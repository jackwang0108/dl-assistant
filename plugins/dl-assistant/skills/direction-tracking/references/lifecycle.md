# 入口与三源机制

## 四种入口

### Setup（首次建方向）

1. 问:方向描述 / 关键词(+ 同义词)/ 2-5 篇种子 arxiv ID。保存目录写死 `<项目>/docs/direction-tracking/`,不问用户。
2. 建 `track-<slug>/`:`config.yaml` + 空 `seen.jsonl` + 空 `library.md` + `meta.json`(`slug`/`created`/`last_run=null`)。
3. → 进 Bootstrap。

### Bootstrap（首次跑，走 B）

1. 每个种子:`paper-search get_paper_citations`(传种子的稳定 arXiv 标识,机制见下「三源抓取机制·B」),拉取后**客户端按 `published` 排序截断近 N**(N 防爆,默认 ~50,用户可调;工具本身没有 recency 排序参数,别指望服务端排)。
2. 合并 → seen 空,全是新 → 进漏斗。
3. 通过的 → `library.md` + `runs/<日期>.md`;**所有拉过的** → `seen.jsonl`。
4. `meta.last_run = now`。

> B 在这里不"滞后"——要的就是这份回顾性 corpus,快速建立方向全貌。

### 增量（后续常规跑，A + B）

1. **A**:arxiv 关键词查询,日期窗 `last_run → now`(往前 overlap 2 天,防 arxiv 投稿日期抖动;最终靠 seen 去重)。
2. **B**:每个种子 `get_paper_citations`(传稳定 arXiv 标识并按覆盖和预算续取,机制见下「三源抓取机制·B」),跟 seen diff 出新引用者。
3. A+B 合并去重 → 新 ID 进 seen → 漏斗 → `library.md` / digest。
4. `meta.last_run = now`。

### C（事件驱动，用户给会议 proceedings）

用户给 **会议 + 年份**(或 URL / 清单)→ 按 `conference-sources.md` 抓 → 合并去重 → 漏斗 → `library.md` / digest。可在增量 run 里顺手跑,或单独触发。`last_run` 不因 C 单独变(C 不参与 A 的日期窗)。

---

## 三源抓取机制

### A：arxiv 关键词（及时）

- arxiv API 关键词查询:`(all:"kw1" OR all:"kw2" OR ...) AND submittedDate:[last_run TO now]`。同义词组:每组内 OR、组间再 OR。
- 用本 skill `scripts/fetch_arxiv_keywords.py`(关键词 + submittedDate 窗 OR 查询,paper 字段形状跟 `fetch_arxiv_daily` 一致,好让 R2 复用)。**主会话从 config.yaml 把同义词组展开成扁平关键词列表传给它**(脚本本身不管同义词分组)。
- 只走 A 能 timely 抓 day-1 新论文——这是 A 不可替代的理由。

### B：种子引用（语义）

- `paper-search get_paper_citations`,每种子一次。
- **种子标识**：用 `get_paper_citations(paper_ref="arxiv:…")`。来源需要其他标识时，先用 `get_papers` 或 `resolve_papers` 核实别名。
- **检查覆盖**：用 `get_query_results` 读完当前快照，必要时用 `extend_query(action="fetch_more")` 继续向来源取结果。记录失败、预算截断和未确认的来源覆盖。
- 增量:**在预算内拉取引用者，再与 seen 比较**(不用日期窗)。滞后无所谓——B 的角色就是"事后补 A 漏的"。
- **量爆控量**:种子多了引用者只涨不跌;diff 出的新引用者超阈值(默认 ~100)先报用户、确认 cap 再进漏斗,别整批烧 token。

### C：会议 proceedings（高质量）

- 见 `conference-sources.md`(11 个顶会的 host 映射 + OpenReview/ACM DL 受限类的兜底)。
- 大多数会议论文有 arxiv 版本 → 跨源去重靠 arxiv ID 兜底;少数没有的 → 标题哈希 / DOI。

---

## 入口路由（每次进来先判）

扫固定目录 `docs/direction-tracking/` 下有没有 `track-<slug>/`:

- **没有** → Setup。
- **有** → 续跑(读 `config` + `seen` + `last_run`)。多个夹子 / 歧义 → 问用户跟哪个。
- **拿不准** → 追问,别猜。
