# 本轮实验结论与证据交接模板

本文件说明怎样汇总本轮实际执行、有效观察和逐项命题的证据判断，并把可复查的结果、未决解释和下一步建议交给 iterate。

在[运行手册 Step 6](workflow.md#step-6-记录判断与边界并交接)填写本轮的 `conclusion.md` 和 `conclusion.json`。发生中止、受阻或部分完成时，同样保存实际结果和限制。每批交回时更新两份文件，两份均使用相同的观察、命题、实验和运行 ID。保留此前的观察及核查来源，新增批次补上本次依据。详细执行记录从实验台账和各项元记录回查，独立判断引用实际完成的核查。

## 怎样组织整轮结论

- **先讲本轮学到了什么。** 用实际读数或有出处的定性观察回答本轮问题，紧接着写适用条件和最重要的未知。
- **分别说明执行、测量与证据。** 列出获批任务做到哪里、哪部分数据有效、每个已核命题的证据怎样变化。厘清计划内完成、失败、未执行与后续待审建议。
- **把可能解释写到证据支持的范围。** 写原先要区分哪些解释、观察实际支持什么，以及还有哪条解释与观察相容。原因已有核查证据时给路径。意外或事后观察写出来源和待验证条件。
- **让下一轮知道缺哪条证据。** 写明缺少的对照、测量或条件。若有跨规模问题，按实际报告已测规模、成对观察的方向及升档条件。未测范围标为待核。取证建议及其用途交 iterate 与用户判断。

## 可复制的 conclusion.md

```markdown
# {研究版本} · 本轮实验结论

> **先看结果**　{实际主要观察、关键数值及条件}。{这个观察支持什么，当前还不能区分什么}。

- 本轮范围 | {研究问题、假设及已批准的范围}
- 本次更新 | {这次交回的批次、实验与运行；各批核查及对应单实验报告的位置}
- 来源 | [研究说明](research-spec.md)、[取证方案](research-plan.md)、[关键代码与测量](claim-code-map.md)、[实验台账](experiments/index.json)、{独立核查记录}

## 1. 原先要区分什么

{本轮未知、先验及其来源。分别说本项目数据和外部证据。}

## 2. 实际执行与有效观察

| 观察 ID／任务 | 实际执行和测量范围 | 读数、比较条件及证据 |
| --- | --- | --- |
| {OBS-01／任务 ID} | {完成、失败、受阻或待审；测量有效性及其范围} | {组别、运行、读数和单位或定性依据，原始路径} |

{列重大偏差、失败、未执行事项和影响。意外观察按实际证据单列。}

## 3. 逐命题的证据判断

| 命题 | 本轮判断及来源 | 实际依据和仍未区分的解释 |
| --- | --- | --- |
| {子论点 ID} | {从 claims.json 引用 evidence_assessment，注明独立核查或主会话的实际范围} | {观察 ID、可比条件、限制及所缺证据} |

## 4. 交接给 iterate

- 可复查材料 | {版本、实际代码和配置、模型、数据、命令、日志、原始结果及独立核查位置}
- 待补证据 | {缺什么、补后能回答什么、当前停点和需要确认的条件}
- 取证建议 | {建议优先核哪项及其理由，交 iterate 和用户决定}
```

## conclusion.json 起点与字段说明

路径相对本轮目录。外部材料注明实际位置或起点。按实际核查填写，尚无结果时保留空值或待评估状态。

```json
{
  "schema_version": 2,
  "version": null,
  "status": "not_started",
  "status_reason": null,
  "sources": {
    "spec": "research-spec.md",
    "plan": "research-plan.md",
    "claim_code_map": "claim-code-map.md",
    "index": "experiments/index.json",
    "claims_json": "claims.json"
  },
  "review": {"status": "not_reviewed", "path": null, "scope": [], "batches": []},
  "experiment_counts": {"registered": 0, "completed": 0, "failed": 0, "blocked": 0, "cancelled": 0, "not_started": 0, "in_progress": 0},
  "prior_beliefs": [],
  "observations": [],
  "measurement_quality": [],
  "evidence_updates": [],
  "deviations": [],
  "unexpected_observations": [],
  "scale_risks": [],
  "handoff": {
    "next": "iterate",
    "remaining_tasks": [],
    "recommendations": []
  }
}
```

| 字段 | 怎样填 |
| --- | --- |
| `status`、`status_reason` | 描述获批任务的实际执行情况，如 `not_started`、`in_progress`、`completed`、`partial`、`blocked`、`failed` 或 `cancelled`。写明范围和停点，证据方向另按各命题记录 |
| `experiment_counts` | 从本轮台账按实验统计，保留失败、未开始和进行中的条目。实际尝试与独立重复在元记录中回查。正在建议的新任务记入交接待办 |
| `sources`、`review` | 引用实际版本、台账、论点和关键代码位置。核查按实际写 `not_reviewed`、`partial` 或 `completed`，注明查了哪些任务和命题。`batches` 逐批写批次 ID、状态、独立核查路径（未开展时为空）和实际范围，保留此前各批记录。`path` 只在存在一份汇总核查时指向该文件 |
| `prior_beliefs`、`observations` | 标明原先观察或依据的来源。每条本轮观察给 ID，写问题、实验和 run ID、实际条件、读数与单位、范围和原始路径。需要额外说明时引用统计入口或推导 |
| `measurement_quality` | 按相关任务和范围写 `data_validity`、依据和局限。保留执行失败或失配造成的证据缺口，并注明哪些结果仍可用 |
| `evidence_updates` | 逐命题引用 [claims.json](../../dl-assistant/references/claims-template.json) 中的 `evidence_assessment` 及实际判断来源。关联观察、核查和仍待验证的解释。未独立核查时如实说明 |
| `deviations`、`unexpected_observations` | 保存实际偏差或事后观察、关联证据和影响。已验证的原因注明依据，尚待查证的解释继续保留 |
| `scale_risks` | 有关时记录实际配置与证据、已测条件和变化方向、未测范围及需要升档验证的触发点 |
| `handoff` | 给待补证据、行动条件、建议和预期能回答的问题。指向可复查的配置、命令或运行。后续设计与投入由 iterate 和用户决定 |

## 完整填写示例 · edge-vision

沿用[运行手册](workflow.md#示例--edge-vision-的计时与轨迹)和[独立证据核查](acceptance-contract.md)的虚构案例。以下是 configuration-comparison 的四组配置比较已获批并实际执行后的本轮交接。baseline-timing 已完成，备选解析器检查曾获准但失败，正式机制隔离对照待确定。

### conclusion.md

```markdown
# v1-edge-vision · 本轮实验结论

> **先看结果**　目标设备上按同一计时口径，原版 12.6 ms，组合配置 10.8 ms，差值为 −1.8 ms。该观察说明组合配置在所测条件下更快。实际算子和写回量同时变化，现有对照无法分开解释两者对收益的影响。

- 本轮范围 | Q2。按 approve-baseline-timing 完成 baseline-timing，后来获批并完成 configuration-comparison 的四组配置比较。另行批准的备选解析器检查未完成。机制隔离对照留到下一步讨论。
- 来源 | [研究说明](research-spec.md)、[取证方案](research-plan.md)、[关键代码与测量](claim-code-map.md)、[实验台账](experiments/index.json)、[独立核查](executions/configuration-comparison/execution-result-review.md)。

## 1. 原先要区分什么

现有文献报告组合部署收益。Q2 想解释并预测这一收益出现的条件。H2 关注中间张量写回量，H3 关注运行时选择的实际算子实现。baseline-timing 先核在目标设备能否取得同口径的延迟与轨迹，configuration-comparison 再取得配置比较的实际读数。

## 2. 实际执行与有效观察

| 观察 ID／任务 | 实际执行和测量范围 | 读数、比较条件及证据 |
| --- | --- | --- |
| OBS-01／baseline-timing | exp-baseline-timing 的 attempt-01 已完成，耗时 18 分钟。数据用于核可测性 | 同一原模型和目标设备。关闭轨迹时为 12.5、12.6、12.7 ms，开启时为 15.3、15.4、15.6 ms。见 [baseline-timing 逐次读数](experiments/exp-baseline-timing/runs/attempt-01/metrics.json) |
| OBS-02／configuration-comparison | exp-configuration-comparison 的四组配置计时完成。数据在该计时范围内有效 | baseline-01 为 12.6 ms，combined-01 为 10.8 ms，差值 −1.8 ms。正式计时均关闭轨迹，同设备、输入、批大小、预热和同步边界。见 [配置比较与轨迹](experiments/exp-configuration-comparison/analysis/latency-comparison.json) |
| 备选解析器检查 | exp-trace-reader-smoke 的 attempt-01 执行失败，完整分组统计未生成 | [诊断日志](experiments/exp-trace-reader-smoke/runs/attempt-01/run.log) 可用于排查格式兼容性。baseline-timing 使用原工具，计时和轨迹另有证据 |

本轮台账三项中，baseline-timing 和 configuration-comparison 的配置比较完成，备选解析器检查失败。正式计时根据 baseline-timing 的观察与轨迹分开采集。configuration-comparison 现有轨迹显示算子实现和写回量同时改变，配置读数仍可用，机制隔离条件尚未落实。

## 3. 逐命题的证据判断

| 命题 | 本轮判断及来源 | 实际依据和仍未区分的解释 |
| --- | --- | --- |
| C1 · 实际算子固定时的写回量解释 | insufficient_evidence，[独立核查](executions/configuration-comparison/execution-result-review.md)后写回 [claims.json](claims.json) | OBS-02 的读数支持配置收益。运行时实现切换也可能解释变化，仍缺同一实际算子、不同写回量的对照 |
| C2 · 写回量相近时的算子实现解释 | pending，C2 的独立核查仍未开展 | 尚需确认哪些组满足写回量相近且选中不同实际算子。现有观察继续供下一轮核对 |

## 4. 交接给 iterate

- 可复查材料 | 从 [台账](experiments/index.json) 找实际运行和命令，[baseline-timing 元记录](experiments/exp-baseline-timing/meta.json)与 [configuration-comparison 元记录](experiments/exp-configuration-comparison/meta.json)记录各自版本、有效配置、模型、数据和日志。
- 待补证据 | C1 需要固定实际算子、改变写回量的对照。C2 需要核满足写回量相近、实际算子不同的条件。正式机制试验的比较组、测量及投入待确认。
- 取证建议 | 优先查运行时能否在目标条件下固定实际算子。若能落实，再用同设备和计时协议核写回量变化。由 iterate 与用户决定是否采用。
```

### conclusion.json

```json
{
  "schema_version": 2,
  "version": "v1-edge-vision",
  "status": "partial",
  "status_reason": "baseline-timing 和 configuration-comparison 的获批配置比较已完成，另行批准的备选解析器检查失败。机制隔离对照待讨论。",
  "sources": {
    "spec": "research-spec.md",
    "plan": "research-plan.md",
    "claim_code_map": "claim-code-map.md",
    "index": "experiments/index.json",
    "claims_json": "claims.json"
  },
  "review": {
    "status": "partial",
    "path": null,
    "scope": ["configuration-comparison 的计时对照与 C1"],
    "batches": [
      {
        "id": "configuration-comparison",
        "status": "partial",
        "path": "executions/configuration-comparison/execution-result-review.md",
        "scope": ["配置比较计时和 C1，未独立核 C2"]
      }
    ]
  },
  "experiment_counts": {"registered": 3, "completed": 2, "failed": 1, "blocked": 0, "cancelled": 0, "not_started": 0, "in_progress": 0},
  "prior_beliefs": [
    {
      "question_id": "Q2",
      "scope": "已有工作报告组合部署收益，本轮拟区分写回变化与实际算子选择两种解释",
      "source": "research-spec.md"
    }
  ],
  "observations": [
    {
      "id": "OBS-01",
      "plan_task_id": "baseline-timing",
      "experiment_id": "exp-baseline-timing",
      "run_ids": ["attempt-01"],
      "metric": "端到端延迟",
      "readings": {"trace_off": [12.5, 12.6, 12.7], "trace_on": [15.3, 15.4, 15.6]},
      "unit": "ms",
      "elapsed_minutes": 18,
      "conditions": "目标设备、同一原模型、固定输入、单张请求、相同预热与同步计时边界",
      "evidence_paths": ["experiments/exp-baseline-timing/runs/attempt-01/metrics.json"]
    },
    {
      "id": "OBS-02",
      "plan_task_id": "configuration-comparison",
      "experiment_id": "exp-configuration-comparison",
      "run_ids": ["baseline-01", "combined-01"],
      "metric": "端到端延迟",
      "readings": {"baseline": 12.6, "combined": 10.8, "combined_minus_baseline": -1.8},
      "unit": "ms",
      "conditions": "同一目标设备、输入、批大小、预热及同步计时条件，正式计时关闭轨迹",
      "evidence_paths": ["experiments/exp-configuration-comparison/analysis/latency-comparison.json"]
    }
  ],
  "measurement_quality": [
    {
      "experiment_id": "exp-baseline-timing",
      "data_validity": "valid",
      "scope": "轨迹采集对测量的影响，以及准备任务的实测成本",
      "observation_ids": ["OBS-01"]
    },
    {
      "experiment_id": "exp-configuration-comparison",
      "data_validity": "valid",
      "scope": "四组配置在所测设置下的计时。实际算子和写回量同时变化，机制仍未隔离",
      "observation_ids": ["OBS-02"],
      "source": "executions/configuration-comparison/execution-result-review.md"
    },
    {
      "experiment_id": "exp-trace-reader-smoke",
      "data_validity": "unassessed",
      "scope": "备用解析器失败，仅有诊断日志",
      "evidence_paths": ["experiments/exp-trace-reader-smoke/runs/attempt-01/run.log"]
    }
  ],
  "evidence_updates": [
    {
      "claim_id": "C1",
      "evidence_assessment": "insufficient_evidence",
      "source": "acceptance-v1",
      "review_ref": "executions/configuration-comparison/execution-result-review.md",
      "observation_ids": ["OBS-02"],
      "inference_limits": ["观察支持所测条件的配置收益。C1 仍需固定实际算子实现、只改变写回量的对照。"]
    },
    {
      "claim_id": "C2",
      "evidence_assessment": "pending",
      "source": null,
      "observation_ids": [],
      "inference_limits": ["尚未开展 C2 的独立核查。待核是否有满足写回量相近且实际算子不同的对照。"]
    }
  ],
  "deviations": [
    {
      "experiment_id": "exp-trace-reader-smoke",
      "attempt_id": "attempt-01",
      "finding": "备选解析器提前退出，未生成完整分组统计",
      "impact": "原工具的 baseline-timing 数据已有独立来源；该解析器仅在后续需要时再核兼容性。",
      "evidence_path": "experiments/exp-trace-reader-smoke/runs/attempt-01/run.log"
    },
    {
      "experiment_id": "exp-configuration-comparison",
      "finding": "现有轨迹显示算子实现与写回量同时变化，机制隔离条件未落实",
      "impact": "现有数据用于配置比较；固定算子的机制问题待补。",
      "observation_ids": ["OBS-02"]
    }
  ],
  "unexpected_observations": [],
  "scale_risks": [],
  "handoff": {
    "next": "iterate",
    "remaining_tasks": [
      {"claim_id": "C1", "needed": "固定实际算子实现、改变写回量的可比对照", "approval": "待确认设计和预算"},
      {"claim_id": "C2", "needed": "核写回量相近且实际算子不同的条件与证据", "approval": "待确认是否另做取证"}
    ],
    "recommendations": [
      {
        "action": "优先核目标条件下能否固定实际算子",
        "basis": "OBS-02 仍同时包含实际算子与写回量变化",
        "purpose": "判断能否用原计时协议取得可区分 C1 的对照"
      }
    ]
  }
}
```

交接前解析 JSON，并逐条回查观察、证据判断和待补证据的引用。核两份结论中的实际版本、读数、适用条件和未完成事项一致。
