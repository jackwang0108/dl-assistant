# hf CLI 用法参考（hf-trending-papers 用）

本 skill 底层全走官方 `hf` CLI（`huggingface_hub` 自带）。这里是本 skill 会用到的命令与 flag 速查；完整文档见 <https://huggingface.co/docs/huggingface_hub/guides/cli>。

## 安装

任选其一：

- 推荐（macOS / Linux）：`curl -LsSf https://hf.co/cli/install.sh | bash`
- pip：`pip install -U huggingface_hub`
- Homebrew：`brew install hf`
- 免装临时跑：`uvx hf papers ls ...`（需先装 `uv`）

升级：`hf update`。

## 认证

- `hf auth login`：登录（浏览器流程，或 `--token $HF_TOKEN` 直接传 token）
- `hf auth whoami`：查登录态
- `hf auth logout`：登出

> `hf papers` 的只读命令（`ls` / `search` / `info`）大多**匿名可用**，只在限流或报错时才需要 `hf auth login`。

## 全局输出格式 flag（所有命令通用）

| flag | 作用 |
| --- | --- |
| `--format json`（或 `--json`） | 结构化 JSON，**本 skill 默认用这个**做雷达分析 |
| `--format agent` | TSV 不截断；CLI 检测到被 AI agent 调用时 `auto` 会自动选它 |
| `-q` / `--quiet` | 只输出 ID，一行一个（适合管道串命令） |
| `--no-truncate` | human 表格不截断长值 |

`auto`（默认）= 交互终端用 `human`（带色表格），被 agent 调用用 `agent`。本 skill 统一**显式加 `--format json`**，字段明确、便于解析。

## hf papers 子命令

### ls — 列日报 / trending

```
hf papers ls [--date today|YYYY-MM-DD] [--week YYYY-Www] [--month YYYY-MM]
             [--sort trending|publishedAt] [--submitter <user>] [--limit N] --format json
```

返回字段（实测口径，随排序方式不同）：默认（publishedAt 排序）有 `id`（arXiv ID）、`title`、`authors`、`summary`、`upvotes`、`comments`、`published_at`、`submitted_at`、`submitted_by` / `submitted_by_name`、`discussion_id`；`--sort trending` 额外有 `organization`（可为 `null`）。

> **截断坑（2026-08 实测）**：`--limit` 默认 50、硬上限 100（`--limit >100` 直接报错）且**无分页参数**，而一个月的日报有几百篇——`--month/--week` 只能拿到 top 100。做趋势雷达（看最火的）够用；**窄主题回填/全量枚举别用它**，主题定向查新走 `search` + 按 `published_at` 后筛。

### search — 关键词搜 HF 论文库

```
hf papers search "<query>" [--limit N] --format json
```

返回字段比 `ls` 少：无 `organization`、无 `submitted_by` / `submitted_by_name`（实测），其余同日报 `ls`。

### info — 单篇结构化详情（雷达金矿）

```
hf papers info <arxiv_id> --format json
```

额外返回：`ai_keywords`（聚类信号——仅 HF 已处理的较老论文有值，新鲜论文常为 `null` 或缺键）、`ai_summary`、`github_repo` + `github_stars`（代码热度）、`linked_models` / `linked_datasets` / `num_total_models`（生态落地度）。

### read — 全文 markdown

```
hf papers read <arxiv_id>
```

> 深读不在本 skill 做——交给 `paper-reading`。本 skill 一般用不到 `read`。

## 日期边界（高频坑）

`--date today` 常因本机日期跑在 HF 最新数据之前而报：

```
Bad request: "date" must be less than or equal to "<最新日期>"
```

这不是故障——HF 日报常下午才更新、周末可能空。取错误里的 `<最新日期>` 改用 `--date <最新日期>`，或退一步 `ls --sort trending`（近期热门）。
