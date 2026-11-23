# 产出约定

本文件说明每项研究记录保存在哪里、由谁写，以及怎样从已有证据和决定继续工作。[运行手册](research-workflow.md) 说明各步的判断和确认点。

## 目录和文件分工

默认使用 `<项目>/docs/idea-find/<日期>-<topic-slug>/`，用户指定位置时使用该位置。同日开展另一项独立工作时，可在目录名加可区分的后缀。下列目录按实际进展创建，暂停或仍在补证时保留已完成的记录即可。

```text
<日期>-<topic-slug>/
├── spec.json
├── idea-seed.json
├── candidates/
│   ├── candidate-1-edge-vision.md
│   └── reviews/
│       └── 1-closest-work.md
├── literature/
│   ├── search/
│   │   ├── fresh-01.json
│   │   ├── closest-01.json
│   │   └── negative-01.json
│   ├── literature.json
│   └── papers/
│       └── <论文-slug>/
│           ├── <来源文件>
│           └── <论文-slug>-note.md
├── evidence-design/
│   ├── design.md
│   └── reviews/
│       └── assumptions.md
└── specs/
    ├── <方向slug>-idea-spec-draft.md
    ├── <方向slug>-idea-plan-draft.md
    └── <方向slug>-claim-tree-draft.json
```

| 步骤 | 保存内容 | 负责方 |
| --- | --- | --- |
| Step 1 核查起点 | `idea-seed.json` 记起点、初查问题、现象、约束和待核材料。实际检索引用批次记录，读过的原文位置记在论文笔记 | 主会话 |
| Step 2 提出并筛选 | `candidates/candidate-<编号>-<slug>.md` 保存各候选的研究问题、假设、推理和筛选依据。候选的关键决定和下一步写入 `spec.json` | 主会话综合，可使用独立分析结果 |
| Step 3 判断价值 | `literature/search/` 留本轮新增查询，`literature/literature.json` 按[研究问题证据模板](templates/question-evidence.md)引用上游结果并记录它们与当前命题的关系，`literature/papers/` 保存本轮取得的原文及笔记。按需记录的[候选核查原件](templates/candidate-verification.md)放 `candidates/reviews/`。更新候选的价值判断，在 `spec.json` 记录研究决定 | 各批独立写，主会话合并并记录用户决定 |
| Step 4 设计取证 | `evidence-design/design.md` 保存设计、对照、结果解释、成本及修订理由。需要独立检查时把原件放在 `evidence-design/reviews/` | 主会话维护方案。经确认委派的任务各写独立文件 |
| Step 5 交接 | 三份交接草案放 `specs/`，在 `spec.json` 记录各份草案版本、用户批准范围和待决事项 | 主会话 |

候选记录正文叫「候选研究问题与假设」。写明来源、关键观察及出处、假设与可区分的预测、最强替代解释、推荐／待补证／放弃及理由。每个优先候选回答「即使做成功，结果会回答什么科学问题，论文能据此提出什么新结论？」暂缓项写清哪条证据能改变判断，放弃项保留反证或最接近工作的定位。选取范围与理由见[运行手册 Step 2](research-workflow.md#step-2-主会话提出假设并筛选)。

新证据影响候选时，更新该候选的依据，并在 `spec.json` 记录实质变化。只有需要并列比较多个取证方案时，才在 `evidence-design/` 分别保存，并用相应的问题与假设编号关联。

累计记录由主会话合并。委派任务只写约定的独立文件，返回证据位置和文件路径。更新 `literature/literature.json` 或 `spec.json` 时，保留原始记录，将完整 JSON 写入同目录临时文件，检查可解析且键无重复后再替换。检索失败、无命中、部分结果和未执行分别记载。复用论文或笔记前，核身份、版本、已读范围和当前问题是否匹配。正文使用中文，技术名称与稳定标识保留原文。论文标识和跨机器交接见 [dl-assistant](../../dl-assistant/SKILL.md#所有技能共用的规则)。

## 决策日志与续做

`spec.json` 是本次研究的决策日志。它保存当前命题、已作决定和下次从哪里接着做。研究说明正文另存为 Markdown。

| 字段 | 怎么填 |
| --- | --- |
| `schema_version`、`topic`、`created` | 新记录使用版本 2，保存主题和创建日期 |
| `origin` | 起点、兴趣、资源、未知与起点记录路径 |
| `current_problem`、`current_hypotheses` | 当前问题与假设，分别用本轮局部 Q、H 编号。尚未形成时用 `null` 或空数组 |
| `status` | `exploring` 探索中、`discussing_value` 判断价值、`planning_evidence` 设计或限定范围取证中、`ready_for_handoff` 当前方案及投入已获确认、`handed_off` 已实际交接、`paused` 暂停、`stopped` 停止。交接后另记接收方和版本 |
| `decisions` | 逐条区分 agent 的候选筛选、用户认可研究取向、用户对本轮投入及版本的确认。记时间、对象、建议、依据、用户实际答复、批准范围和仍待决定的事项。尚无相应答复时可用 `null` |
| `revisions` | 命题实质变化时，保留旧命题、新命题、关联编号、改变判断的证据、失去或保留的研究价值。新命题使用新编号。只修正措辞可简记 |
| `next_step` | 写明下一项行动、对应路径或证据位置、前置条件和怎样算完成。已结束且无下一步时填 `null` |

续做时先读原目录中的日志和最新证据，需要时回查相关原始批次。暂停时写清为什么停、什么条件满足后可以继续。已经交接的版本若因新证据、设计变化或成本变化需要调整，记录变更并重新确认受影响的范围。文件存在只说明曾保存这份材料，核查深度和用户批准范围分别以对应记录为依据。

## 交接草案

**研究说明（spec）** 回答「研究什么、为什么值得、成功后能主张什么」。

**本轮取证方案（plan）** 回答「这轮要弄清什么、怎样取得证据、不同结果怎么解释」。

按 [草案交接格式](research-handoff.md) 写入现有文件路径。

| 文件 | 内容与用途 |
| --- | --- |
| `specs/<方向slug>-idea-spec-draft.md` | 研究说明草案。交代问题、假设、与最接近工作的差异和取证成功后的可能主张。需要选型时，提供任务、数据、模型、仓库线索和载体用途 |
| `specs/<方向slug>-idea-plan-draft.md` | 首轮取证方案草案。写清关键未知、前提、设置、对照、成本、结果解释和需要核实的实施条件 |
| `specs/<方向slug>-claim-tree-draft.json` | 初始两层 claim 树。注明当前问题、假设及对应实验预测在草案中的关联。`evidence_assessment` 初始为 `pending`，来源字段和本项目证据留空，贡献待核 |

提交两份 Markdown 草案供用户审阅。对获准版本记录路径和可识别的修订号、提交标识或内容摘要，并记录批准范围。需仓库选型时先交 `baseline-survey`，完成前置准备后，由 `code-idea-execution` 取得本轮证据。批准做基准或核查测量可行性时，按该范围记录。正式实验仍待确认时，日志保留明确的待决事项。

## 完整决策日志示例

以下沿用[运行手册的边缘视觉加速案例](research-workflow.md#完整示例--边缘设备上的视觉模型加速)。论文和用户答复均为虚构。这里已放下「首次组合」的预期主张，用户认可研究机制，批准范围只到基准核查。正式实验仍在 `planning_evidence`。

```json
{
  "schema_version": 2,
  "topic": "边缘设备上的视觉模型加速",
  "created": "2025-07-01",
  "origin": {
    "record_path": "idea-seed.json",
    "interest": "单张图像请求的端到端延迟",
    "initial_idea": "组合模型裁剪与算子融合",
    "resources": "可在一台目标设备上做测量",
    "unknowns": ["轨迹稳定性", "正式测量耗时"]
  },
  "current_problem": {
    "id": "Q2",
    "statement": "在单张请求下，什么条件能够解释并预测压缩与融合的组合收益？"
  },
  "current_hypotheses": [
    {"id": "H2", "statement": "算子实现固定时，组合收益随中间张量写回量的下降而变化。"},
    {"id": "H3", "statement": "写回量相近时，延迟差异主要随运行时选择的算子实现变化。"}
  ],
  "status": "planning_evidence",
  "decisions": [
    {
      "id": "D1",
      "date": "2025-07-01",
      "type": "candidate_screening",
      "subject": "Q2",
      "recommendation": "放弃首次组合的主张，优先查组合收益的条件和机制。",
      "basis": [
        {"path": "literature/literature.json", "location": "C v1 §4.3 表 3，已有组合部署对照"},
        {"path": "candidates/candidate-1-edge-vision.md", "location": "筛选结论与竞争解释"}
      ],
      "user_response": null,
      "approved_scope": [],
      "pending": ["研究取向", "C 的分项消融材料"]
    },
    {
      "id": "D2",
      "date": "2025-07-01",
      "type": "research_direction",
      "subject": "Q2",
      "recommendation": "继续研究组合收益的条件，比较访存与算子实现两种解释。",
      "basis": [{"path": "candidates/candidate-1-edge-vision.md", "location": "研究价值与剩余证据缺口"}],
      "user_response": "这个机制问题值得继续看。",
      "approved_scope": ["继续研究 Q2 并准备首轮取证方案"],
      "pending": ["基准核查和正式实验投入"]
    },
    {
      "id": "D3",
      "date": "2025-07-01",
      "type": "evidence_scope",
      "subject": "Q2 的测量可行性",
      "recommendation": "先确认延迟测量、轨迹及耗时，再决定正式对照的规模。",
      "basis": [{"path": "specs/edge-vision-idea-plan-draft.md", "location": "基准核查与停止条件"}],
      "user_response": "同意先做基准核查，正式实验等估完耗时再确认。",
      "approved_scope": ["在一台目标设备上做 plan v1 中的基准核查"],
      "draft_versions": [
        {"path": "specs/edge-vision-idea-spec-draft.md", "revision": "v1"},
        {"path": "specs/edge-vision-idea-plan-draft.md", "revision": "v1"}
      ],
      "pending": ["正式四组对照的设计和预算确认"]
    }
  ],
  "revisions": [
    {
      "date": "2025-07-01",
      "previous_problem": {"id": "Q1", "statement": "裁剪与融合的组合能否降低单张请求延迟？"},
      "previous_hypotheses": [{"id": "H1", "statement": "两项改动一起开启会降低端到端延迟。"}],
      "current_problem_id": "Q2",
      "current_hypothesis_ids": ["H2", "H3"],
      "reason": "C 已报告组合部署收益，原预期新增不足。将问题改为解释收益发生的条件。",
      "evidence": [{"path": "literature/literature.json", "location": "C v1 §4.3 表 3及附录 B"}],
      "value_change": "不再主张首次组合，可能的新增是能预测组合收益的条件及其解释边界。",
      "review_decision_id": "D2"
    }
  ],
  "next_step": {
    "action": "核对设备和运行时条件后，按获准范围重复测量基准延迟并检查是否可取得稳定执行轨迹。",
    "path": "specs/edge-vision-idea-plan-draft.md",
    "location": "基准核查与停止条件",
    "authorized_by": "D3",
    "done_when": "记下可测指标、波动、耗时及正式四组对照的成本依据，再与用户确认是否继续。"
  }
}
```
