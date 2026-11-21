# spec.json 模板（调研方案 · 机读 · 会生长 · 承载两次方案呈现）

主会话在 Step1（检索方案）和 Step3（深挖方案）两次方案呈现、用户确认后写入。落盘让方案**可追溯**：事后能复盘「当时为什么这么搜、这么分」。方案呈现是在对话里做给用户看的，文件本身是机读留痕，所以用 json。字段值中文，专有名词保留英文。

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
    "novelty_level": "扫新力度定级（规则见 source-strategy.md 用途×熟悉度加权）",
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
    "axis_rationale": "选这根轴的理由",
    "scale_recommendation": "每子领域深挖多少代表作 + 总量 + 推荐理由",
    "subfields": [
      {
        "name": "子领域1",
        "papers": ["标题 + arXiv key，从 pool.json 划给它"],
        "focus": "按轴的梳理重心（模板见 organizing-axis.md 第七节）",
        "serves_purpose": "让子 agent 知道该把什么写显眼（找研究方向就重点挖 limitation/future work）"
      }
    ]
  }
}
```

- `search_plan` 是 Step1 的第一次方案呈现；`deep_dive_plan` 是 Step3 的第二次方案呈现（并行展开前最后一次拍板）。
- `purpose` 枚举：学习理解 / 找研究方向 / 定位自己的工作 / 选技术方案；`familiarity` 枚举：基本陌生 / 有点了解 / 就在其中做。两个变量独立，别合并成一个。
- 保存目录不进 spec——目录写死 `docs/literature-survey/<日期>-<topic-slug>/`，无需记录。
