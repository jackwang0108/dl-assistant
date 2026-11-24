---
name: writing-paper-response
description: 根据实际稿件和研究证据处理预审、真实审稿、导师或合作者的意见。制定处理方案、交接获批改稿、核对实际修改并准备可查证的回复。
---

# 核查意见、安排改稿并准备回复

逐项说明对方在问什么、依据支持到哪里、影响哪条主张、准备怎样处理、实际上做到了什么，以及回复中能准确说什么。适用于内部反馈、投稿前预审、会议 rebuttal 和期刊修改回复。

## SKILL 交接关系

```mermaid
flowchart LR
    REVIEW["writing-paper-review 或用户"] -->|"指定稿件与原始意见"| RESP["writing-paper-response"]
    RESP -->|"获批 revision-brief.json"| WRITE["writing-paper"]
    WRITE -->|"revision-result.json、实际稿件及核查证据"| RESP
    RESP -->|"核心研究未决、证据与影响范围"| ITER["code-idea-iterate"]
    ITER -->|"研究判断及证据边界"| RESP
    RESP -->|"回复定稿、稿件版本及未决事项"| SUB["writing-paper-submission"]
```

全局流程见 [dl-assistant](../dl-assistant/SKILL.md)。

## 产出与保存

沿用论文工程和已有回应目录。新建时可用 `<论文根>/response/<response-id>/`，例如按送审轮次或组会主题命名。有新交接就另存一版。仅处理外部稿件时可用用户指定的目录。

```text
response/<response-id>/
├── response-state.json                # 当前工作记录，含意见、关切、行动和回复
├── materials/                         # 按需保存原意见、被评论稿件和官方规则
├── receipts/<return-id>/              # 按批收取 writing-paper 的回传
│   ├── revision-result.json           # 行动 ID、实际改动、核查和未完成项
│   └── <改后稿件与随包证据>              # 按回传索引保存或引用
└── handoffs/<stage>-<N>/
    ├── response-state.json            # 本次阶段记录快照
    ├── response-map.md                # 原意见与关切、决定和行动的对应
    ├── revision-brief.json            # handoff 阶段给写作端的获批行动
    ├── rebuttal-letter.md             # 回复草稿或已核回复
    └── validation.json                # 输入、范围、就绪项和结构检查
```

## 运行流程图

```mermaid
flowchart TD
    S(["开始或续做"]) --> I["固定原意见、被评论稿件和当前稿件<br/>确认范围、目标规则与时限"]
    I --> C["拆分关切并保留原 ID<br/>核原文、实际证据和受影响主张"]
    C --> P["提出推荐、可行方案、成本与未知<br/>相关取舍成组确认"]
    P --> D{"按获批方案处理"}
    D -->|"文字、图表或明确补证"| W["分批交 writing-paper<br/>核实际回传和关闭判据"]
    D -->|"核心科学判断未决"| R["交 iterate<br/>带主张、证据和待回答问题"]
    D -->|"据证回应或保留未决"| A["记录判断、依据及回应范围"]
    W --> X["检查其他意见、回复及稿件是否受影响"]
    R --> X
    A --> X
    X -->|"新证据或范围变化"| C
    X -->|"可以核对回复"| F["按实际结果和版本写回复<br/>核字数、定位、来源与逐项覆盖"]
    F --> G{"达到本阶段要求？"}
    G -->|"还有待核"| H(["保存草稿与续做入口"])
    G -->|"通过"| J(["保存对应稿件的回复定稿"])
```

## 参考资料列表

| 资料 | 何时读 |
| --- | --- |
| [执行流程及示例](references/workflow.md) | 从收意见、确认方案到回传和定稿 |
| [证据核查与处理策略](references/fix-strategy.md) | 判断意见依据、挑选行动、确定关闭判据 |
| [回复写作](references/rebuttal-writing.md) | 核官方要求、组织回复、核字数与定位 |
| [状态字段](references/response-record.md) · [状态模板](references/response-state-template.json) | 保存和恢复工作状态，验证交接 |
| [改稿清单](../writing-paper/references/templates/revision-brief-template.json) · [改稿结果](../writing-paper/references/templates/revision-result-template.json) | 发出批准批次和核对实际回传 |

## 判断与确认

1. 分清稿件写了什么、研究实际做了什么，以及证据支持什么。分别核查原意见、被评论稿件、当前稿件、实际设置与结果。
2. 可以澄清、修改、补明确的证据、据证回应或暂留未决。核心现象、有效性、新颖性、价值或目标条件下的收益仍不明确时，交 iterate 重审。
3. 主会话先查资料并给建议。核心主张变化、争议取舍和新增投入由用户决定。多个关切可共享行动，也可成组确认，保留逐项来源和影响。
4. 区分批准、执行和核查。用实际回传核稿件、改动、证据和关闭判据，再确认完成陈述。回复覆盖不等同于科学问题已解决。
