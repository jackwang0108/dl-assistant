# paper-card.json 格式（paper-reading）

每篇论文生成一份 `paper-card.json`。对话中每步得出判断时补充相应字段，结束时补齐。文件保存在固定目录 `docs/paper-reading/<日期>-<paper-slug>/`，供用户复查，也供 `idea-find` 读取 `swappable_components` 和 `connections` 寻找研究线索。`worth_reading:false` 的记录可帮助了解已有研究的密度与局限。

每篇论文都保存卡片。不值得精读时保存精简版。卡片和 arxiv-daily-paper 的 `trend-snapshot.json` 一样，都是已完成工作的记录文件，不用于集中维护全局进度。

## 模板（完整版 · 值得读的）

```json
{
  "arxiv_id": "2506.12345",
  "title": "...",
  "authors": ["..."],
  "read_date": "2026-07-09",
  "paper_type": "提出新方法，以验证实验为证据",
  "worth_reading": true,
  "worth_reason": "在已有研究较多的方向上做了增量改进，消融设计有参考价值",

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
  "worth_reason": "在已有研究较多的方向上只做了小幅改进，对比基线只到 ResNet",
  "core_idea": "一句话（即使不值得读也记它是什么）"
}
```

## 字段说明

| 字段 | 完整版 | 精简版 | 含义 / 来源 |
| --- | --- | --- | --- |
| `arxiv_id` / `title` / `authors` | 是 | 是 | 论文标识（Step1） |
| `read_date` | 是 | 是 | 读完日期 |
| `paper_type` | 是 | 否 | **论证块**：自由文本，"论证类型与重点贡献；证据是 Y"（Step3 三步判断；各块的填法见 `argument-playbook.md`） |
| `worth_reading` | 是 | 是 | 值不值得深读（Step3 判断） |
| `worth_reason` | 是 | 是 | 一句理由 |
| `core_idea` | 是 | 是 | 一句话精髓·逻辑链（Step3） |
| `novelty` | 是 | 否 | novelty 程度 + 类型（Step3/4） |
| `core_contribution` | 是 | 否 | 不可替换的核心贡献（Step4） |
| `swappable_components` | 是 | 否 | **替换点**：Step 4 记录的现有组件及可替换的理由，供后续选题参考 |
| `key_findings` | 是 | 否 | 反直觉结果/失败案例（Step5） |
| `limitations` | 是 | 否 | 证据不足之处（Step4/5） |
| `connections` | 是 | 否 | **后续研究建议**（Step 6），供选题参考。记录 0–3 条建议，没有合适的建议时留空。每条一个条目（不合并）：`direction`（inward/outward）+ `kind`（内向=方法上/证据上/边界上/解释上，外向=搬思想/推结论/借工具/当约束）+ `point` + 已核实的文献依据 arxiv_id |

> `idea-find` 用 `swappable_components` 查找可改进的组件，用 `connections` 查找延伸建议，并可按 `kind` 选择。`connections[].anchor_arxiv_ids` 填写通过 paper-search 核实的 arXiv ID。上表的 `kind` 取值供其他技能直接读取。

> **字段按块填，不适用就留空**——发现块论文 `swappable_components` 可空（可迁移的 probe 设计记 `connections`）；`novelty` 枚举套不上就换主线块对应维度（发现块记"发现的意外程度"）。具体填写方式见 `argument-playbook.md` 第五节。
