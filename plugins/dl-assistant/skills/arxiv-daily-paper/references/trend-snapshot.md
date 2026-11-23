# trend-snapshot.json 格式（arxiv-daily-paper）

每次运行结束时，把 `trend-snapshot.json` 保存到当天的产出目录。下一次运行时读取历史快照，用于跨日比较。它与 `raw.json` 和第 2 轮的评估记录一样，都是每次运行保存的文件。全局运行状态不在这里维护。

第 5 步撰写简报时，按话题整理的每组论文对应 `clusters` 中的一项。

## 模板

```json
{
  "date": "2026-07-09",
  "categories": ["cs.CV"],
  "clusters": [
    {"name": "文档解析 OCR-VLM", "keywords": ["document parsing", "OCR", "VLM"], "top_ids": ["2507.12345"]}
  ],
  "orgs": {"DeepSeek": 3, "Google": 2}
}
```

## 字段说明

| 字段 | 必填 | 含义 / 来源 |
| --- | --- | --- |
| `date` | 是 | 当天日期（YYYY-MM-DD） |
| `categories` | 是 | 开场确认的 arXiv 分类，用来选择同分类的历史快照 |
| `clusters[]` | 是 | 当天的话题分组，撰写简报时一并记录 |
| `clusters[].name` | 是 | 用于展示的话题名称，跨日比较时忽略该字段 |
| `clusters[].keywords` | 是 | 从该组论文标题或摘要提炼的英文关键词，是跨日比较的主要依据 |
| `clusters[].top_ids` | 是 | 从通过第 2 轮的论文中选择代表论文的 arXiv ID，用作判断话题重叠的辅助依据 |
| `orgs` | 否 | 各机构对应的论文篇数。arXiv 没有专门的机构字段，仅在 comment 或摘要中可直接取得时填写，否则省略 |

> 跨日比较话题时，使用 `keywords` 和 `top_ids` 的重叠情况。例如，「Agent 自进化」和「LLM Agent」可能对应同一组论文。`orgs` 是可选补充信息。
