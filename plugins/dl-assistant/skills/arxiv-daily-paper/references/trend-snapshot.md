# trend-snapshot.json 格式（arxiv-daily-paper）

`trend-snapshot.json` 是 arxiv-daily-paper **跨日连续性**的数据源：**每次运行结束时写一个**（落当天产出目录），**下次运行做跨日对比时读历史的**。它和 raw.json / round2 卡片一样是落盘产物、不是状态中枢。

`clusters` 在 Step5 digest 归簇时同步产出——digest 按话题分组，每组即一簇。

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
| `categories` | 是 | 开场定的 arXiv 类目（跨日只比同分类，靠它筛） |
| `clusters[]` | 是 | 当天话题簇（digest 归簇时同步产出） |
| `clusters[].name` | 是 | 簇名，**仅给人读**——跨日对比**不用它**（名字不稳定） |
| `clusters[].keywords` | 是 | 该簇核心方向关键词（英文，从该组论文标题/摘要提炼）——**跨日话题对比的主依据** |
| `clusters[].top_ids` | 是 | 该簇代表篇 arxiv_id（取 round2 通过的）——重叠判断辅助依据 |
| `orgs` | 否 | 机构→篇数。arXiv 无现成 org 字段，只从 comment/摘要里能零成本解析到时才写；拿不到就**省略，不强求、不瞎编** |

> **跨日对比只信 `keywords` + `top_ids` 的重叠**，不信簇名（今天"Agent 自进化"、昨天"LLM Agent"可能是同一簇）。`orgs` 是加分项不是核心。
