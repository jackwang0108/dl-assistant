# idea-seed.json 研究起点模板

本文件说明怎样记录研究起点、用户目标和已知约束，并保存初查得到的证据、判断与下一步要核实的问题。

在 [工作流 Step 1](../research-workflow.md#step-1-核查起点实际检索) 将本文件的 JSON 保存为调研目录下的 `idea-seed.json`。先记用户和已知材料提供了什么，再根据实际查询和阅读更新初查。用户可以只给一个方向或观察，主会话据此确定初查问题。目标会议、资源和时间预算尚未确认时保留未知。

## 可复制模板

```json
{
  "schema_version": 2,
  "date": null,
  "topic": null,
  "starting_point": {
    "kind": null,
    "content": null,
    "sources": []
  },
  "problem": null,
  "user_intuition": null,
  "user_goal": null,
  "familiarity": null,
  "interests": [],
  "observations": [],
  "resources": {
    "available": [],
    "potential": [],
    "unknown": []
  },
  "time_budget": null,
  "target_venue": null,
  "seeds": [],
  "initial_check": {
    "question": null,
    "search_records": [],
    "findings": [],
    "inferences": [],
    "decision": null,
    "next_action": null
  },
  "open_questions": []
}
```

## 字段怎么填

| 字段 | 怎么填 |
| --- | --- |
| `starting_point` | 写用户实际给出的起点。类型可为 `field`、`paper`、`observation`、`hypothesis` 或 `prior_results`。来源可用用户陈述、稳定论文标识或实际文件路径。已有多个入口时，选一个主起点，其他线索写入 `seeds` |
| `problem`、`user_goal`、`user_intuition`、`familiarity`、`interests` | 分开记当前想弄清的问题、用户目标、用户的原有解释和背景。只知道领域时，`problem` 可留空。主会话推断写入 `initial_check.inferences` |
| `observations` | 每项写观测、来源、已知测量条件和核查状态。用户报告的观察可以保留为 `user_reported`，未取得运行记录时说明缺失。证据附对应位置，未报告的设置列为未知 |
| `resources` | 按设备、数据、软件、方法经验等记条件。每项写具体内容和依据。`available` 记已确认可用，`potential` 记可能取得及条件，`unknown` 记影响后续设计的待核问题。形成候选前可先保留未知 |
| `seeds` | 每条写来源、稳定标识或实际路径、线索内容、已核查范围和仍未知的部分。论文卡的阅读建议结合当时的阅读目标理解。只读摘要或拿到搜索片段时如实标注 |
| `initial_check` | 写当前最需要查清的问题。实际查询引用 `literature/search/`，已核原文引用 `literature/papers/` 的笔记及具体位置。分别写已核发现、主会话推断、当前决定及下一步动作 |
| `open_questions` | 列出继续研究最需要澄清的问题。能定向补查时写明要核的原文、运行记录或其他材料 |

未知标量用 `null`，没有记录的列表用 `[]`。当前决定说明已有依据足以进入 Step 2，还是需要先补一项能改变判断的证据。只存初查时的已知情况。后续形成的候选研究问题、假设和筛选理由写入 `candidates/`，用户决定及续做位置写入 `spec.json`。

## 完整填写示例

以下沿用边缘视觉加速案例。论文、路径和观察均为虚构，用来演示 Step 1 初查结束时如何记录。用户给了一个现象，尚未确认目标会议、正式预算和轨迹采集能力。

```json
{
  "schema_version": 2,
  "date": "2025-07-01",
  "topic": "边缘设备上的视觉模型加速",
  "starting_point": {
    "kind": "observation",
    "content": "裁剪后 FLOPs 降了，端到端延迟没降。",
    "sources": ["用户在本次会话中的描述"]
  },
  "problem": "在单张图像请求下，为什么模型裁剪减少了计算量，却没有观察到端到端延迟下降？",
  "user_intuition": null,
  "user_goal": "弄清裁剪收益为何没有体现到实际响应时间，判断下一步优先查模型还是运行时。",
  "familiarity": "有基础推理部署经验",
  "interests": ["单张图像请求的端到端延迟"],
  "observations": [
    {
      "statement": "用户报告裁剪后 FLOPs 下降，端到端延迟未见明显下降。",
      "source": "用户在本次会话中的描述",
      "conditions": "边缘设备上的视觉分类，批大小为 1。",
      "verification": "user_reported",
      "unknown": ["尚未取得原始运行记录", "原版与裁剪版的计时边界是否一致", "运行时是否为两版选择了同一算子实现"]
    }
  ],
  "resources": {
    "available": [
      {
        "kind": "hardware",
        "detail": "用户确认可以使用一台目标设备做延迟测量。",
        "source": "用户在本次会话中的说明"
      }
    ],
    "potential": [
      {
        "kind": "tool",
        "detail": "运行时可能支持算子级轨迹采集。",
        "condition": "先核设备和当前运行时是否开启对应接口，再试采一段基准轨迹。"
      }
    ],
    "unknown": ["轨迹采集是否稳定", "重复测量及正式实验耗时"]
  },
  "time_budget": null,
  "target_venue": null,
  "seeds": [
    {
      "source": "本次初查",
      "ref": "https://example.org/papers/edge-vision-a",
      "point": "论文 A 在同一设备和运行时下对比原模型与裁剪模型。",
      "checked_scope": "v2 §4.1、§4.2 表 2，批大小为 1 的端到端中位延迟。",
      "unknown": "这一测量能否解释用户设备上的延迟表现尚待核实。"
    },
    {
      "source": "本次初查",
      "ref": "https://example.org/papers/edge-vision-b",
      "point": "论文 B 在指定算子库上报告融合子图的吞吐收益。",
      "checked_scope": "v1 §4.2 表 1，设备 B、批大小为 16、子图吞吐量。",
      "unknown": "未核到单张端到端延迟或目标设备上的算子库支持范围。"
    }
  ],
  "initial_check": {
    "question": "已知论文的设备、批大小和计时边界是否与用户观察相近？",
    "search_records": ["literature/search/route-representatives.json"],
    "findings": [
      {
        "statement": "A 测单张端到端延迟，B 测批量子图吞吐。两项证据回答的性能问题不同。",
        "evidence": [
          {"path": "literature/papers/edge-vision-a/edge-vision-a-note.md", "location": "A v2 §4.1、§4.2 表 2"},
          {"path": "literature/papers/edge-vision-b/edge-vision-b-note.md", "location": "B v1 §4.2 表 1"}
        ]
      }
    ],
    "inferences": [
      "计算量下降后，端到端时间仍可能受访存、算子实现或其他环节限制。初查只提供了进一步区分这些解释的线索。"
    ],
    "decision": "可以进入 Step 2。初查足以把问题缩到单张请求的端到端计时，并提出可区分的解释。用户设备上的具体原因仍未知。",
    "next_action": "读取用户已有的原版与裁剪版测量记录，核对计时边界及运行时条件，再写候选问题与假设。若缺少原始记录，将其列为后续需取得的观察。"
  },
  "open_questions": [
    "两次测量是否用了同一设备、运行时版本和计时边界？",
    "裁剪前后的算子实现是否改变？",
    "目标设备能否采到足以区分解释的算子轨迹？"
  ]
}
```
