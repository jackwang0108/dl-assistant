# hf-trending-papers 使用的 hf CLI 命令

本技能使用 `huggingface_hub` 提供的官方 `hf` CLI。这里列出会用到的命令和参数。完整文档见 <https://huggingface.co/docs/huggingface_hub/guides/cli>。

## 安装

任选其一：

- 推荐（macOS / Linux）：`curl -LsSf https://hf.co/cli/install.sh | bash`
- pip：`pip install -U huggingface_hub`
- Homebrew：`brew install hf`
- 临时运行：`uvx hf papers ls ...`（需先装 `uv`）

升级：`hf update`。

## 认证

- `hf auth login`：登录（浏览器流程，或 `--token $HF_TOKEN` 直接传 token）
- `hf auth whoami`：查看登录状态
- `hf auth logout`：登出

> `hf papers` 的只读命令（`ls` / `search` / `info`）大多**匿名可用**，只在限流或报错时才需要 `hf auth login`。

## 全局输出格式参数

| 参数 | 作用 |
| --- | --- |
| `--format json`（或 `--json`） | 本技能使用结构化 JSON 分析论文和趋势 |
| `--format agent` | 输出完整 TSV。CLI 检测到由 AI agent 调用时，`auto` 会选择此格式 |
| `-q` / `--quiet` | 只输出 ID，一行一个（适合管道串命令） |
| `--no-truncate` | 在 `human` 表格中完整显示较长的值 |

默认格式 `auto` 在交互终端使用 `human`（彩色表格），在 agent 调用时使用 `agent`。本技能统一显式指定 `--format json`，以便按字段读取数据。

## hf papers 子命令

### ls — 列出每日论文或热门论文

```
hf papers ls [--date today|YYYY-MM-DD] [--week YYYY-Www] [--month YYYY-MM]
             [--sort trending|publishedAt] [--submitter <user>] [--limit N] --format json
```

此前核对过的返回字段（随排序方式变化）：默认（publishedAt 排序）有 `id`（arXiv ID）、`title`、`authors`、`summary`、`upvotes`、`comments`、`published_at`、`submitted_at`、`submitted_by` / `submitted_by_name`、`discussion_id`；`--sort trending` 额外有 `organization`（可为 `null`）。

> **返回数量上限（2026-08 实测）**。`--limit` 默认为 50，最多 100，`--limit >100` 会报错。命令没有分页参数，一个月的日报可能有几百篇，`--month/--week` 最多返回排名前 100 篇，适合查看热门论文。完整列出投稿或按特定主题补查历史论文需要其他查询方式。按主题查新时，使用 `search`，再根据 `published_at` 筛选。

### search — 按关键词搜索论文

```
hf papers search "<query>" [--limit N] --format json
```

返回字段比 `ls` 少：无 `organization`、无 `submitted_by` / `submitted_by_name`（实测），其余同日报 `ls`。

### info — 查询单篇详情及额外字段

```
hf papers info <arxiv_id> --format json
```

额外返回：`ai_keywords`（用于按话题分组，只有 HF 已处理的论文有值，近期论文常为 `null` 或缺失）、`ai_summary`、`github_repo` + `github_stars`（代码热度）、`linked_models` / `linked_datasets` / `num_total_models`（关联模型、数据集及模型总数）。

### read — 全文 markdown

```
hf papers read <arxiv_id>
```

> 需要精读全文时，交给 `paper-reading`。本技能通常不调用 `read`。

## 当天日报尚未发布时的处理

如果本机日期晚于 HF 最新日报日期，`--date today` 可能返回：

```
Bad request: "date" must be less than or equal to "<最新日期>"
```

HF 日报常在下午更新，周末可能没有日报。用提示中的 `<最新日期>` 重试，即 `--date <最新日期>`，或改用 `ls --sort trending` 查看近期热门论文。
