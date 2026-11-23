# spec.json 模板（检索方案和子领域分析方案）

主会话分别在 Step 1 和 Step 3 向用户说明检索方案和子领域分析方案，确认后写入 JSON，便于日后核查检索和分类依据。字段值用中文，专有名词保留英文。

```json
{
  "topic": "视频生成中的扩散模型",
  "created": "2026-06-29",

  "search_plan": {
    "_comment": "Step1 产出，用户确认后写入",
    "purpose": "定位自己的工作",
    "familiarity": "有点了解",
    "time_range": "近 3-5 年",
    "seed_papers": ["有就列标题/arXiv ID；无则空数组，从关键词出发"],
    "novelty_level": "近期检索的力度（规则见 source-strategy.md 用途×熟悉度加权）",
    "query_groups": [
      {
        "name": "核心概念组",
        "queries": ["query 词1", "query 词2"],
        "rationale": "为什么这么设计（给用户看的，方案呈现时讲的就是它）"
      }
    ]
  },

  "deep_dive_plan": {
    "_comment": "Step3 产出，用户确认后冻结",
    "axis": "按方法",
    "axis_rationale": "选择该分类维度的理由",
    "scale_recommendation": "每子领域深入分析多少代表作 + 总量 + 推荐理由",
    "subfields": [
      {
        "name": "子领域1",
        "papers": ["标题 + arXiv key，从 pool.json 划给它"],
        "focus": "按分类维度确定的分析重点（模板见 organizing-axis.md 第七节）",
        "serves_purpose": "让子 agent 知道该把什么写显眼（找研究方向就重点挖 limitation/future work）"
      }
    ]
  }
}
```

- `search_plan` 保存 Step 1 确认的检索方案，`deep_dive_plan` 保存 Step 3 并行分析开始前确认的方案。
- `purpose` 枚举：学习理解 / 找研究方向 / 定位自己的工作 / 选技术方案；`familiarity` 枚举：基本陌生 / 有点了解 / 就在其中做。两个变量独立，别合并成一个。
- 保存目录不进 spec——目录固定为 `docs/literature-survey/<日期>-<topic-slug>/`，无需记录。
