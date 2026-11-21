# paper-card.json 格式（paper-reading）

`paper-card.json` 是 paper-reading 的**结构化判断卡**：每读一篇论文产一张，对话中每个 step 得出结论时**增量填**、最后完成。每篇存进 `docs/paper-reading/` 下自己的文件夹（`<日期>-<paper-slug>/`，目录写死，契约见 SKILL.md「产出与保存」），逐篇累积后保存目录就**隐性沉淀成一个论文判断库**——idea-find 会扫 `docs/paper-reading/*/paper-card.json`：`swappable_components`（替换点）和 `connections`（连接点）是 idea 种子池，`worth_reading:false` 的卡是避坑/红海信号。

**所有文章都产**（包括不值得读的精简版）。和 AD 的 `trend-snapshot.json` 一样，它是落盘产物、不是状态中枢。

## 模板（完整版 · 值得读的）

```json
{
  "arxiv_id": "2506.12345",
  "title": "...",
  "authors": ["..."],
  "read_date": "2026-07-09",
  "paper_type": "卖方法 · 证据是验证实验",
  "worth_reading": true,
  "worth_reason": "红海里的增量，但消融设计有参考价值",

  "core_idea": "一句话精髓（逻辑链：发现X→insight→机制→为什么有效）",
  "novelty": {"level": "incremental|novel|new_task|new_benchmark|new_paradigm", "note": "..."},

  "core_contribution": "这篇不可替换的核心贡献组件",
  "swappable_components": [
    {"component": "中间特征融合", "current": "朴素 concat", "why_swappable": "这子问题有专门优化文献线"}
  ],

  "key_findings": ["反直觉结果X", "失败案例Y"],
  "limitations": ["假设太强Z", "消融缺关键组件W"],

  "connections": [
    {"direction": "inward", "kind": "方法上", "point": "把方法族A换进组件B", "anchor_arxiv_ids": ["2401.xxxx"]},
    {"direction": "outward", "kind": "搬思想", "point": "把核心insight迁到任务C", "anchor_arxiv_ids": ["2402.yyyy"]}
  ]
}
```

## 精简版（不值得读的）

```json
{
  "arxiv_id": "...",
  "title": "...",
  "read_date": "...",
  "worth_reading": false,
  "worth_reason": "红海里的小增量，baseline 只比到 ResNet",
  "core_idea": "一句话（即使不值得读也记它是什么）"
}
```

## 字段说明

| 字段 | 完整版 | 精简版 | 含义 / 来源 |
| --- | --- | --- | --- |
| `arxiv_id` / `title` / `authors` | 是 | 是 | 论文标识（Step1） |
| `read_date` | 是 | 是 | 读完日期 |
| `paper_type` | 是 | 否 | **论证块**：自由文本，"原子组合 + 主战场；证据是 Y"（Step3 三步判断；各块的填法见 `argument-playbook.md`） |
| `worth_reading` | 是 | 是 | 值不值得深读（Step3 判断） |
| `worth_reason` | 是 | 是 | 一句理由 |
| `core_idea` | 是 | 是 | 一句话精髓·逻辑链（Step3） |
| `novelty` | 是 | 否 | novelty 程度 + 类型（Step3/4） |
| `core_contribution` | 是 | 否 | 不可替换的核心贡献（Step4） |
| `swappable_components` | 是 | 否 | **替换点**：拿来即用·可替换的组件（Step4 埋）—— **idea 种子** |
| `key_findings` | 是 | 否 | 反直觉结果/失败案例（Step5） |
| `limitations` | 是 | 否 | 不 solid 处（Step4/5） |
| `connections` | 是 | 否 | **自然的延伸**（Step6）—— **idea 种子**。宁缺毋滥：0-3 条封顶，没有自然的延伸就留空，不硬凑。每条一个条目（不合并）：`direction`（inward/outward）+ `kind`（内向=方法上/证据上/边界上/解释上，外向=搬思想/推结论/借工具/当约束）+ `point` + 真实锚点 arxiv_id |

> **`swappable_components` + `connections` 是这张卡的灵魂**——未来 idea-find 扫目录，这俩字段就是"可改进点池"和"跨域 idea 种子池"。`connections[].anchor_arxiv_ids` 必须是 paper-search 查证的真实 arXiv ID，不瞎编；`kind` 用四分类词汇（内向=方法上/证据上/边界上/解释上，外向=搬思想/推结论/借工具/当约束），idea-find 可按 kind 挑种子。

> **字段按块填，不适用就留空**——发现块论文 `swappable_components` 可空（可迁移的 probe 设计记 `connections`）；`novelty` 枚举套不上就换主线块对应维度（发现块记"发现的意外程度"）。不留空硬凑。分流细则见 `argument-playbook.md` 第五节。
