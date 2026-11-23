# 用 hf-papers 查找相关论文和近期工作

hf-papers 是官方 `hf` CLI 的 `hf papers` 子命令，在本技能中用于语义搜索和补查近期工作。

- **arxiv**：全量、次日收录，但搜索是关键词匹配（title/abs）——同义变体、替代术语召回差，查询词设计必然有限；
- **hf-papers**：HF 论文库对收录的 arxiv 文章做过 AI 解析（`ai_keywords` / `ai_summary`），**`search` 是语义搜索，召回质量明显好于 arxiv 关键词**；但它是社区策展子集（漏掉没被社区提交的），且 `search` 无日期过滤。

第一轮同时用 arXiv 按关键词和日期查新，并用 hf `search` 补充同义表述。补查近期工作时，为每个子方向查询一次，再按 `published_at` 筛选。查看最近几天的日报可用 `ls`。完整命令文档见 <https://huggingface.co/docs/huggingface_hub/guides/cli>。

## 命令速查

**安装**（任选其一；匿名即可用只读命令）：

- `curl -LsSf https://hf.co/cli/install.sh | bash`（macOS / Linux 推荐）
- `pip install -U huggingface_hub`
- 临时运行：`uvx hf papers ...`（需先装 `uv`）

**输出**：一律显式加 `--format json`（结构化、便于解析；`-q` 只输出 ID 适合管道）。命令不存在 → 提示用户安装；限流/报错要登录 → `hf auth login`。

### search — 语义搜索（主题召回主力）

```
hf papers search "<query>" [--limit N] --format json
```

- **无日期过滤**：按返回的 `published_at` 后筛（如保留近 6 个月 / 近 1 年，按用途定的时间窗）。
- query 可以写**自然语言概念描述**（语义搜索），不只堆关键词——"looped transformer" 和 "weight-shared recurrent depth" 这类同义表述都能召回。
- 返回字段：`id`（arXiv ID）、`title`、`authors`、`summary`、`upvotes`、`published_at` 等。

### ls — 查看日报或热门论文

```
hf papers ls [--date today|YYYY-MM-DD] [--week YYYY-Www] [--month YYYY-MM]
             [--sort trending|publishedAt] [--limit N] --format json
```

- 列的是当期 HF **全部**论文（日报），**不带主题过滤**——窄主题得自己筛标题/摘要。
- **返回数量上限（2026-08 实测）**。`--limit` 默认 50，最多 100，`--limit >100` 会报错，且无分页。一月的日报可能有几百篇，`ls --month/--week` 不用于按细分主题补查历史论文。本流程只用 `--date` 查看最近几天的日报。
- **补查近期工作改走 `search`**：把方向拆成几个子方向，各查询一次定向 `search` + 按 `published_at` 后筛（实测精确 query 精度很高）。
- **日报尚未发布**。`--date today` 可能返回 `"date" must be less than or equal to "<最新日期>"`。改用提示中的 `<最新日期>`，或使用 `--sort trending`。

### info — 单篇结构化详情（可选）

```
hf papers info <arxiv_id> --format json
```

额外返回 `ai_keywords`、`ai_summary`、`github_repo` 和 `github_stars`。可用 `ai_keywords` 扩充 arXiv 和 Semantic Scholar 检索组的同义词。

## 文献调研中的用法

- **Step2 第一轮**：核心概念组的 query 除了走 paper-search MCP（SS/scholar/arxiv），检索子 agent 同时跑 `hf papers search`（按用途定的时间窗后筛）；**补查近期工作 = 把方向拆成几个子方向，各查询一次定向 `search` + 后筛**（实测精确 query 精度很高）。
- 结果与 arxiv 检索近期论文**同等待遇**：进候选论文清单、参与 Step3 确定分类方式。
- Step 2 单独报告 hf 命中数量。没有运行 hf 检索时，报告 0。
- CLI 安装失败或受限流时，记录原因并继续 arXiv 近期检索，在 `survey.json` 的 `coverage_notes` 中注明缺少 hf 来源。
