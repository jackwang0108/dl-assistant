# literature.json 研究问题证据模板

本文件说明怎样复用已有文献调研，把与当前研究问题相关的证据关联到具体假设，并记录仍需补查的问题及其对研究判断的影响。

主会话在 [工作流 Step 3](../research-workflow.md#step-3-深入查新对照最接近的工作并讨论是否继续) 更新 `literature/literature.json`。范围由当前问题和假设决定。已有 `literature-survey` 时，引用目标条目、已核证据与覆盖说明，领域分类、完整论文池和报告在上游文件中回查。没有可复用的结果时，使用当前问题的定向检索和原文笔记填写同一结构。

## 可复制模板

```json
{
  "schema_version": 2,
  "topic": null,
  "problem_ids": [],
  "seed_sources": [],
  "request_records": [],
  "evidence": [],
  "closest_assessment": [],
  "hypothesis_evidence": [],
  "new_questions": [],
  "unresolved_identity_or_evidence": [],
  "coverage_notes": []
}
```

## 字段怎么填

| 字段 | 怎么填 |
| --- | --- |
| `problem_ids` | 引用 `spec.json` 中实际涉及的 Q 编号。关联假设时用对应的 H 编号 |
| `seed_sources` | 写复用产物路径、引用条目、主题相关性、覆盖截至日期及局限。可引用 `survey.json` 的论文、比较和待验证问题，以及覆盖记录、论文卡或笔记 |
| `request_records` | 引用本轮追加的 `literature/search/` 批次和实际查询，说明为什么补查以及查询结果。没有新增查询时留空 |
| `evidence` | 为需要复查的证据给局部编号。保留稳定论文标识、所读版本、章节或图表、核查深度、原文支持的事实、实际条件、证据边界与记录路径。同一条证据可以供多个命题引用 |
| `closest_assessment` | 按问题比较最接近工作的实际贡献、验证范围和剩余差异，给证据编号。只改变数据、设备或场景时，交代会怎样改变解释或实践决策 |
| `hypothesis_evidence` | 写 H 编号、具体预测、证据关联及原因。可用 `supports`、`challenges`、`inconclusive` 或 `not_yet_checked`。先说明条件是否可比，再说明它支持、削弱或暂时无法区分哪步推断 |
| `new_questions` | 写文献比较或反面证据引出的新问题、出处和下一步可核查的线索。需要推进时写入对应候选记录 |
| `unresolved_identity_or_evidence` | 分别记录身份、版本、材料或关键对照缺口，注明当下会限制哪项判断及续查入口 |
| `coverage_notes` | 区分上游已核覆盖、本轮新增覆盖及未完成范围。未命中说明实际查过什么。失败、截断或未执行分别记录。实际查询截至日期和最新命中日期分别使用 |

优先核对会改变研究判断的证据。来源内容冲突时保留各自版本、条件和出处。文献中报告的现象只在相应条件下支持判断，本项目的实验结果留待实际取证后记录。问题修订、研究价值和用户决定写入 `spec.json`，证据记录为这些判断提供可复查的依据。未取得材料时照实留缺口。

## 完整填写示例

沿用边缘视觉加速案例。上游调研已经核查过 C 的组合部署，接入 `idea-find` 时直接引用该证据。本轮定向补查分项消融和运行时实现，示例中的论文、路径及查询结果均为虚构。

```json
{
  "schema_version": 2,
  "topic": "边缘设备上的视觉模型加速",
  "problem_ids": ["Q1", "Q2"],
  "seed_sources": [
    {
      "kind": "literature_survey",
      "path": "docs/literature-survey/2025-07-01-edge-vision/survey.json",
      "coverage_path": "docs/literature-survey/2025-07-01-edge-vision/coverage-review.md",
      "as_of": "2025-06-30",
      "entries": ["papers: p00003", "comparisons: comparison-1", "gaps: gap-2"],
      "used_for": "定位组合部署的先例、可比条件和独立贡献的待核问题。",
      "limitations": "arXiv 初次提交日期窗口已查，OpenAlex 正式发表补查失败。"
    }
  ],
  "request_records": [
    {
      "path": "literature/search/ablation-runtime-01.json",
      "source": "arxiv",
      "as_of": "2025-06-30",
      "status": "success",
      "reason": "在已知组合部署后，定向查压缩与融合的分项对照，以及关于算子实现切换的证据。",
      "outcome": "本次查询及筛读范围内，未核到可分离两种解释的对照。"
    }
  ],
  "evidence": [
    {
      "id": "E1",
      "paper_ref": "https://example.org/papers/edge-vision-c",
      "version": "v1",
      "location": "§4.1、§4.3 表 3，PDF 第 7 页，附录 B",
      "reading_level": "detailed",
      "source_record": {
        "path": "docs/literature-survey/2025-07-01-edge-vision/notes/model-optimization.md",
        "entry": "p00003 / C-E1"
      },
      "finding": "同一设备和运行时中，同时开启压缩与融合，端到端中位延迟从 24 ms 降至 14 ms。",
      "conditions": "设备 C，运行时 R，模型 M，D 验证集，批大小 1。基线同时关闭两项改动。",
      "limitation": "正文表 3 只给组合对照，未分别测压缩和融合，分项消融的补充材料未取得。"
    }
  ],
  "closest_assessment": [
    {
      "problem_id": "Q1",
      "evidence_ids": ["E1"],
      "existing_result": "C 已在单张请求场景验证压缩与融合的组合部署。",
      "implication": "撤回「首次组合」的预期新增，更新 spec.json 中 Q1 到 Q2 的修订。",
      "remaining_difference": "组合在什么条件下获益，以及两种机制能解释多少，仍需额外证据。"
    }
  ],
  "hypothesis_evidence": [
    {
      "hypothesis_id": "H2",
      "prediction": "算子实现固定时，组合收益随中间张量写回量的下降而变化。",
      "evidence_ids": ["E1"],
      "relation": "inconclusive",
      "comparability": "同样关注单张请求的延迟，原文未控制算子实现，也未报告写回量。",
      "reason": "组合结果可以支持继续追问机制，当前对照无法判断访存解释。"
    },
    {
      "hypothesis_id": "H3",
      "prediction": "写回量相近时，延迟差异主要随运行时选择的算子实现变化。",
      "evidence_ids": ["E1"],
      "relation": "inconclusive",
      "comparability": "原文未报告对照组间的实现选择及写回量。",
      "reason": "两项改动同时切换，无法判断是否发生了实现切换或归因给该机制。"
    }
  ],
  "new_questions": [
    {
      "problem_id": "Q2",
      "question": "单张请求下，哪些条件能解释并预测压缩与融合的组合收益？",
      "evidence_ids": ["E1"],
      "next_check": "先确认补充材料有无同版本的分项对照，以及能否取得区分访存和实现选择的轨迹。"
    }
  ],
  "unresolved_identity_or_evidence": [
    {
      "kind": "missing_material",
      "evidence_id": "E1",
      "missing": "C v1 的单组件消融及轨迹。",
      "impact": "当前不能归因。如果补充材料已给出同条件的机制证据，要重新判断 Q2 的新增。",
      "next_action": "核 C v1 §4.3 指向的补充材料。仍未取得时，在取证设计中写清需要测的对照、轨迹和解释边界。"
    }
  ],
  "coverage_notes": [
    "上游 arXiv 近期覆盖截至 2025-06-30，OpenAlex 正式发表补查失败。",
    "本轮补查限于压缩加融合的分项消融与运行时实现，原始查询见 literature/search/ablation-runtime-01.json。"
  ]
}
```
