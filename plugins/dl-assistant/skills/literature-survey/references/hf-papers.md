# hf-papers 用法（Step 2 扫新：语义召回主力 + 近期兜底）

hf-papers（官方 `hf` CLI 的 `hf papers` 子命令）在 LS 里的角色：**强语义搜索源 + 近期扫新兜底**。它和 arxiv 互补，不可互替：

- **arxiv**：全量、次日收录，但搜索是关键词匹配（title/abs）——同义变体、换皮叫法召回差，查询词设计必然有限；
- **hf-papers**：HF 论文库对收录的 arxiv 文章做过 AI 解析（`ai_keywords` / `ai_summary`），**`search` 是语义搜索，召回质量明显好于 arxiv 关键词**；但它是社区策展子集（漏掉没被社区提交的），且 `search` 无日期过滤。

所以第一轮扫新两手并用：**hf `search` 保语义召回**（同义变体不漏，也兼作近期兜底——按子方向各发一发 + `published_at` 后筛）、arxiv 日期范围扫新保关键词全量。`ls` 不再是兜底手段（截断坑见下文 `ls` 节）。用法完整文档见 <https://huggingface.co/docs/huggingface_hub/guides/cli>。

## 命令速查

**安装**（任选其一；匿名即可用只读命令）：

- `curl -LsSf https://hf.co/cli/install.sh | bash`（macOS / Linux 推荐）
- `pip install -U huggingface_hub`
- 免装临时跑：`uvx hf papers ...`（需先装 `uv`）

**输出**：一律显式加 `--format json`（结构化、便于解析；`-q` 只输出 ID 适合管道）。命令不存在 → 提示用户安装；限流/报错要登录 → `hf auth login`。

### search — 语义搜索（主题召回主力）

```
hf papers search "<query>" [--limit N] --format json
```

- **无日期过滤**：按返回的 `published_at` 后筛（如保留近 6 个月 / 近 1 年，按用途定的时间窗）。
- query 可以写**自然语言概念描述**（语义搜索），不只堆关键词——"looped transformer" 和 "weight-shared recurrent depth" 这类同义表述都能召回。
- 返回字段：`id`（arXiv ID）、`title`、`authors`、`summary`、`upvotes`、`published_at` 等。

### ls — 日报 / trending（近期兜底）

```
hf papers ls [--date today|YYYY-MM-DD] [--week YYYY-Www] [--month YYYY-MM]
             [--sort trending|publishedAt] [--limit N] --format json
```

- 列的是当期 HF **全部**论文（日报），**不带主题过滤**——窄主题得自己筛标题/摘要。
- **实测坑（2026-08）**：`--limit` 默认 50、硬上限 100（`--limit >100` 直接报错）且**无分页参数**，而一个月的日报有几百篇——`ls --month/--week` 对窄主题回填**无效**，别再这么用。它只保留一个用途：`--date` 看最近几天的日报。
- **近期兜底改走 `search`**：把方向拆成几个子方向，各发一发定向 `search` + 按 `published_at` 后筛（实测精确 query 精度很高）。
- **日期边界坑**：`--date today` 常因 HF 日报未更新而报 `"date" must be less than or equal to "<最新日期>"`——不是故障，取错误里的 `<最新日期>` 改用，或退 `--sort trending`。

### info — 单篇结构化详情（可选）

```
hf papers info <arxiv_id> --format json
```

额外返回 `ai_keywords`（**可拿来扩 query 同义变体**，喂给 arxiv/SS 检索组）、`ai_summary`、`github_repo` + `github_stars`。

## 在 LS 流程里怎么用

- **Step2 第一轮**：核心概念组的 query 除了走 paper-search MCP（SS/scholar/arxiv），检索子 agent 同时跑 `hf papers search`（按用途定的时间窗后筛）；**近期兜底 = 把方向拆成几个子方向，各发一发定向 `search` + 后筛**（实测精确 query 精度很高）。
- 结果与 arxiv 扫新**同等待遇**：进候选池、参与 Step3 定轴。
- **Step2 汇报时 hf 命中单列**（见 SKILL.md Step2 的扫新覆盖行）——没跑就是 0，露馅。
- 失败兜底：CLI 装不上/限流，记录后继续（arxiv 扫新必须保住），并在 `survey.json` 的 `coverage_notes` 注明 hf 源缺失。
