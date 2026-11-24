# 复现报告与机读交接模板

本文件说明怎样把每个复现目标的实际结果、可比性和证据范围写成报告，并交付下游可以复跑的基准、适用条件和待验证事项。

默认保存到 `docs/code-paper-reproduction/<repo>-<日期>/`，也可使用用户指定路径。从第一次运行开始更新 `report.md` 和 `reproduction.json`，按[运行手册 Step 6](workflow.md#step-6-交付可比较的基准)核对后交付。两份记录使用同一目标 ID、协议版本和 run ID。参考、判据和授权引用[复现规格](reproduction-spec-template.md)，具体排查引用[条件核对记录](alignment-template.md)。对日志、退出码和指标填写实际存在的路径。大文件记录原位置、版本或校验值及取得方式。

## 怎样写结论

每个目标依次回答**执行到哪里 → 证据覆盖什么 → 条件是否可比 → 与参考差多少 → 可以供谁做什么**。条件变化保留原版本和相关运行。计划复跑或等待补证时，说明下一步需要的条件和接手阶段。

| 实际情况 | 报告写法 |
| --- | --- |
| 目标未运行，或中途受阻 | 写计划覆盖的目标和已经完成的检查，给出具体阻塞及解除条件。只有参考值时把实测结果留空 |
| 命令完成，实际条件与参考不同 | 保留原始读数和条件。例如「500 个样本统计完整，raw 权重得 77.6%。参考使用 EMA，本次仅用于排查加载条件」 |
| 条件可比，参考与实测仍有差距 | 记录单位、差值、比较依据及尚未解决的解释。另判断实测是否可用于同协议下的改前对照，写清验证范围及依据 |
| 条件可比，观察达到已确认的判据 | 写参考和实测、协议、主要证据及可用的 run。单次观察按单次交付，另列未验证的情况 |

## 可复制的 report.md

````markdown
# {项目} · 复现与基准交付报告

- 日期、仓库与环境 | {实际路径、分支、commit 或 diff、机器和运行环境}
- 依据 | [复现规格](spec.md)、[条件核对](alignment.md)、[机读记录](reproduction.json)、{setup、survey 或研究材料及版本}

## 1. 逐目标结论

| 目标与协议 | 执行及证据范围 | 参考与实测 | 可比性、判断及用途 | 未决及下一步 |
| --- | --- | --- | --- | --- |
| {目标 ID、协议版本} | {未开始、受阻、部分完成或完成，实际样本或训练阶段} | {参考位置和单位，逐次实测或主结果及对应 run} | {关键条件、与参考的判断、可交付的基准及证据} | {尚缺什么、接手阶段或适用边界} |

## 2. 运行记录与差距

| Run | 实际入口、配置和条件 | 结果或偏差 | 原始证据 |
| --- | --- | --- | --- |
| {run ID} | {命令、配置、权重、数据，以及与目标协议相关的变化} | {运行状态、退出情况、观察和单位，或未完成原因} | {command.sh、meta.json、日志、退出码、指标、产物的实际路径} |

{说明参考统计口径、观察到的主要差距及其影响。保留失败、条件不一致的运行和不同 seed。随机性说明重复单位、次数及已测读数。有待查原因时，引用 alignment.md 的证据与下一项检查。}

## 3. 低成本配置（适用时）

{写用途、实际配置和资源消耗、与正式条件的差异、已跑的基线与对照、证据支持的用途、升档条件。仅讨论或提出候选时写到该进度。}

## 4. 交接与未决事项

- 改前对照 | {给 prepare 的目标、run、复跑命令和环境、需要保持的配置、样本与权重、要比较的读数或行为、未覆盖的回归项}
- 代码阅读与后续实验 | {实际入口和关键文件、已验证范围、可用权重与基准，以及做后续比较前要验证的条件}
- 变更和资源 | {影响运行与判定的代码或协议变更、批准范围及资源，当前提交和合并状态}
- 下一步 | {需要谁做什么，取得什么证据后再判断。相关 survey 待办或 setup 缺项按其实际编号引用}
```

## reproduction.json 的记录结构

以 `schema_version: 2` 记录逐目标结果。以下是未执行的可复制起点，按实际情况增减目标和运行。`null` 表示该项尚无记录，必要时在对应目标说明原因。产物相对路径以交付目录为起点，仓库内配置路径以实际工作目录为起点，外部资产记录可取得的实际位置。

```json
{
  "schema_version": 2,
  "status": "not_started",
  "inherits": {},
  "sources": [],
  "targets": [
    {
      "id": "EVAL-01",
      "target_type": "evaluation",
      "purpose": null,
      "requested_scope": "original_conditions",
      "reference": null,
      "protocol": { "id": "EVAL-01", "version": "v1", "status": "draft" },
      "execution_status": "not_started",
      "run_ids": [],
      "data_validity": "unassessed",
      "comparability": { "status": "unresolved", "evidence_refs": [] },
      "assessment": "not_assessed",
      "finding": null,
      "uncertainty": null,
      "use_scope": { "supported_uses": [], "remaining_checks": [] }
    }
  ],
  "runs": [],
  "ready_commands": {},
  "checkpoint": {},
  "remaining_tasks": []
}
```

| 字段 | 填写规则 |
| --- | --- |
| `status`、`execution_status` | 记录本轮及目标的进度，按实际用 `not_started`、`in_progress`、`completed`、`partial`、`blocked`、`failed`、`cancelled`。一次运行退出为零只说明该次运行完成，目标的分析和交付范围另核 |
| `targets[].target_type`、`requested_scope` | 按实际用 `evaluation`、`training` 或 `behavior`。用 `original_conditions` 或 `modified_conditions` 表明要核原条件还是在明确的新条件下建立基准 |
| `reference`、`protocol` | 保存出处、版本和精确结果或行为、单位、统计或选择方式。写协议 ID、版本、确认及实际判据的引用。修正加载以符合原协议时沿用版本，改变划分、指标等比较条件时保留原版本，记录新协议和受影响的运行 |
| `data_validity`、`comparability` | 数据有效范围按证据写 `unassessed`、`valid`、`limited`、`invalid`，说明实测覆盖和缺项。可比性用 `matched`、`different`、`unresolved`、`not_applicable`，附条件、证据和影响。诊断 run 的可比性单独记录 |
| `assessment`、`finding` | 用 `consistent_with_reference`、`discrepant`、`insufficient_evidence`、`not_comparable` 或 `not_assessed`。解释所用判据、观察值、范围和证据。关键条件不同或不明时用 `not_comparable`，在可比较但证据量不足时用 `insufficient_evidence` |
| `runs` | 每次尝试独立登记目标和协议版本、实际执行状态、工作目录、代码版本、环境、命令、配置、数据与 checkpoint 身份。引用 `meta.json`、日志、退出码、指标和产物，可复用完整运行记录。保存读数和单位、实际统计范围、比较状态、偏差和恢复来源 |
| `uncertainty`、`use_scope` | 分别说明数值误差、评测随机性、训练 seed 或抽样是否实际查过，记录已有逐次读数及限制。用实际 run 标记每项可交付用途，同时写未覆盖的条件及下一项检查 |
| `inherits`、`sources`、`remaining_tasks` | 引用实际读取的 setup、survey、规格、原文或发布记录。按需写来源版本、位置及取证范围，保留原待办编号、阻塞、所需补证和接手阶段 |

### 运行入口、资产和现有下游查找字段

- **`ready_commands`** 保留 `eval`、`train` 或 `train_scaled` 等实际验证过的入口。每条命令能回查到相应 run 的工作目录、环境、有效配置和范围。拟运行的命令写进规格或待办。把成功运行但偏离目标条件的命令留在该次 run。
- **`checkpoint`、`reproduced_baseline_checkpoint`** 按实际保存发布权重和自训权重的身份、位置、来源、实际变体及适用条件。自训权重另外关联生成和选取它的运行。交接时写明基线从哪份权重启动及其用途。
- **`target`** 为旧读取路径保留有对应证据的参考行、数据、指标定义和实测读数。单目标或已选定一个明确的下游基准时，标明它指向哪个目标和 run。其余目标在 `targets` 各自交付。已有具体比较判据时引用协议及依据。
- **`determinism`、`noise_floor`、`baseline_curves`、`artifacts`** 按实际写已核随机性配置、同条件重复的读数与统计量、曲线和产物索引。未做重复时在 `uncertainty` 说明。附统计量的单位、重复对象和原始结果位置，后续比较按本轮目标和设计选择判断方法。
- **`reduced_setting`** 需要时记录候选或已验证状态、配置及命令、与目标条件的差异、实际资源、基线 run 和 `baseline_result`、已有的同规模成对对照、适用范围和升档条件。候选入口留在提议记录，实测后再交可复跑的配置与结果。观察到规模敏感性时交付成对结果及限制。
- **下游交接** 给出目标、协议、run 和用途，再给入口及必须保持的条件。部分本地下游仍读取旧的整体可信度、容差或分流标签。交接时提示依据逐目标证据核定使用范围，不从旧标签推断本轮结果。W&B 项目按[共同实验记录](../../wandb/references/experiment-records.md)关联运行，分别记录本地执行、同步与证据有效范围。

## 完整填写示例 · edge-vision

沿用[复现规格](reproduction-spec-template.md#完整填写示例--edge-vision-运行前规格)和[条件核对](alignment-template.md)中的虚构项目。这里展示同一组证据怎样分别写进两份交付文件。示例中的路径和资源记录用于说明填写方式。

### report.md

````markdown
# edge-vision · 复现与基准交付报告

- 日期、仓库与环境 | 2026-11-24，/srv/research/edge-vision，code/paper-reproduction，c91b7e4，edge-dev-01，/srv/envs/edge-vision/bin/python。
- 依据 | [复现规格](spec.md)、[条件核对](alignment.md)、[机读记录](reproduction.json)、setup.json 的 E02 与 C03、论文 v2 表 2 和 §4.2。

## 1. 逐目标结论

| 目标与协议 | 执行及证据范围 | 参考与实测 | 可比性、判断及用途 | 未决及下一步 |
| --- | --- | --- | --- | --- |
| EVAL-01 v1 · 发布权重全量评测 | 完成评测及核对。Vision-Val v1/val 的 500 个 ID 各计一次 | 论文表 2 的 Vision-S 行为 Top-1 78.4%。eval-attempt-02 用 EMA 得 392/500，Top-1 78.4% | 权重变体、数据、输入处理和指标均已核。在论文报告精度内一致。将 eval-attempt-02 交给 prepare 作为改前对照 | 完整训练和训练间波动未验证。如后续涉及重训，需单独建立训练基准 |

## 2. 运行记录与差距

| Run | 实际入口、配置和条件 | 结果或偏差 | 原始证据 |
| --- | --- | --- | --- |
| eval-attempt-01 | tools/eval.py，configs/eval.yaml，Vision-S r1 raw | 退出码 0，388/500，Top-1 77.6%。权重变体偏离 v1，仅用于排查 | [命令](runs/eval-attempt-01/command.sh)、[记录](runs/eval-attempt-01/meta.json)、[日志](runs/eval-attempt-01/repro-edge-vision-eval-01.log)、[退出码](runs/eval-attempt-01/repro-edge-vision-eval-01.EXIT_CODE)、[指标](runs/eval-attempt-01/metrics.json)、[样本 ID](runs/eval-attempt-01/outputs/evaluated-ids.txt) |
| eval-attempt-02 | 同一入口，使用该 run 的 [EMA 配置](runs/eval-attempt-02/config/eval-ema.yaml)。同一代码、环境、样本、预处理和指标 | 退出码 0，392/500，Top-1 78.4%。日志证实选择同一 r1 发布的 EMA | [命令](runs/eval-attempt-02/command.sh)、[记录](runs/eval-attempt-02/meta.json)、[日志](runs/eval-attempt-02/repro-edge-vision-eval-02.log)、[退出码](runs/eval-attempt-02/repro-edge-vision-eval-02.EXIT_CODE)、[指标](runs/eval-attempt-02/metrics.json)、[样本 ID](runs/eval-attempt-02/outputs/evaluated-ids.txt) |

首轮读数比参考低 0.8 个百分点。两次均覆盖同一完整清单。论文 §4.2 与首次加载日志显示权重变体不同，获准后只切到 EMA。第二次观察支持权重变体解释此次差距，详见 alignment.md。参考与实测都是固定权重的评测读数，未进行同条件重复或多 seed 重训。

## 3. 低成本配置

本轮只标定固定权重的全量评测，未建立 reduced 训练配置。

## 4. 交接与未决事项

- 改前对照 | prepare 从 eval-attempt-02/command.sh 复跑，使用实际工作目录和解释器，保持 Vision-S r1 的 EMA、Vision-Val v1/val 的 500 个 ID、预处理、类别映射和 Top-1 聚合。核样本覆盖、正确数及 78.4% 的读数。
- 代码阅读与后续实验 | 核 tools/eval.py 的权重选择、loader 和指标调用。若后续涉及训练，在比较方法之前单独核训练配置和生成基线权重的过程。
- 变更和资源 | 两次使用 c91b7e4。第二次只新增运行专用 EMA 配置，复跑经用户确认。未合并分支。首轮预算与复跑确认见 spec.md，实际执行记录见各 run。
- 下一步 | 已有评测基准可供 prepare 验证清理前后行为。完整训练和训练间波动留待有对应目标时单独验证。
```

### reproduction.json

```json
{
  "schema_version": 2,
  "status": "completed",
  "inherits": {
    "setup_report": "docs/code-project-setup/edge-vision-2026-11-24/setup.json",
    "setup_checks": ["E02", "C03"],
    "conda_env": null,
    "repo": { "commit": "c91b7e4", "branch": "code/paper-reproduction" },
    "spec": "spec.md"
  },
  "sources": [
    { "id": "paper-v2", "kind": "paper", "version": "v2", "location": "表 2 Vision-S 行与 §4.2，见 spec.md" },
    { "id": "vision-s-r1", "kind": "release", "version": "r1", "location": "权重发布记录，见 alignment.md" }
  ],
  "targets": [
    {
      "id": "EVAL-01",
      "target_type": "evaluation",
      "purpose": "为 prepare 建立固定权重的改前评测对照",
      "requested_scope": "original_conditions",
      "reference": { "source_id": "paper-v2", "metric": "Top-1", "value": 78.4, "unit": "%", "statistic": "固定发布权重的评测读数" },
      "protocol": {
        "id": "EVAL-01",
        "version": "v1",
        "status": "approved",
        "approval_ref": "spec.md",
        "conditions": "Vision-S r1 EMA；Vision-Val v1/val 的 500 个样本各计一次；同预处理、类别映射和 Top-1 聚合",
        "comparison_rule": "可比条件核实后按参考显示精度比较，同时保存原始分子和分母"
      },
      "execution_status": "completed",
      "run_ids": ["eval-attempt-01", "eval-attempt-02"],
      "data_validity": "valid",
      "comparability": {
        "status": "matched",
        "run_id": "eval-attempt-02",
        "evidence_refs": ["alignment.md", "runs/eval-attempt-02/outputs/evaluated-ids.txt", "runs/eval-attempt-02/repro-edge-vision-eval-02.log"]
      },
      "assessment": "consistent_with_reference",
      "finding": "EMA 评测 392/500，Top-1 78.4%，与对应参考行在报告精度内一致",
      "uncertainty": {
        "design": "一次符合 v1 条件的固定权重评测",
        "raw_result_refs": ["runs/eval-attempt-02/metrics.json"],
        "limitations": ["未测固定权重的重复评测波动", "未测训练间波动"]
      },
      "use_scope": {
        "supported_uses": [
          { "use": "prepare 的改前评测对照", "run_id": "eval-attempt-02", "conditions_ref": "alignment.md" }
        ],
        "remaining_checks": ["完整训练", "训练间波动"]
      }
    }
  ],
  "runs": [
    {
      "id": "eval-attempt-01",
      "target_id": "EVAL-01",
      "protocol_version": "v1",
      "status": "completed",
      "code_commit": "c91b7e4",
      "working_directory": "/srv/research/edge-vision",
      "environment": "/srv/envs/edge-vision/bin/python",
      "meta_path": "runs/eval-attempt-01/meta.json",
      "command_file": "runs/eval-attempt-01/command.sh",
      "config_ref": "configs/eval.yaml",
      "data": "Vision-Val v1/val",
      "checkpoint": { "release": "Vision-S r1", "loaded_parameters": "raw" },
      "exit_code": 0,
      "exit_code_path": "runs/eval-attempt-01/repro-edge-vision-eval-01.EXIT_CODE",
      "log_path": "runs/eval-attempt-01/repro-edge-vision-eval-01.log",
      "metrics_path": "runs/eval-attempt-01/metrics.json",
      "sample_ids_path": "runs/eval-attempt-01/outputs/evaluated-ids.txt",
      "observations": [{ "metric": "Top-1", "value": 77.6, "unit": "%", "numerator": 388, "denominator": 500 }],
      "comparison_status": "not_comparable",
      "deviations": ["实际加载 raw；v1 要求 EMA"]
    },
    {
      "id": "eval-attempt-02",
      "target_id": "EVAL-01",
      "protocol_version": "v1",
      "status": "completed",
      "code_commit": "c91b7e4",
      "working_directory": "/srv/research/edge-vision",
      "environment": "/srv/envs/edge-vision/bin/python",
      "meta_path": "runs/eval-attempt-02/meta.json",
      "command_file": "runs/eval-attempt-02/command.sh",
      "config_ref": "runs/eval-attempt-02/config/eval-ema.yaml",
      "data": "Vision-Val v1/val",
      "checkpoint": { "release": "Vision-S r1", "loaded_parameters": "EMA" },
      "exit_code": 0,
      "exit_code_path": "runs/eval-attempt-02/repro-edge-vision-eval-02.EXIT_CODE",
      "log_path": "runs/eval-attempt-02/repro-edge-vision-eval-02.log",
      "metrics_path": "runs/eval-attempt-02/metrics.json",
      "sample_ids_path": "runs/eval-attempt-02/outputs/evaluated-ids.txt",
      "observations": [{ "metric": "Top-1", "value": 78.4, "unit": "%", "numerator": 392, "denominator": 500 }],
      "comparison_status": "matched",
      "deviations": []
    }
  ],
  "target": {
    "target_id": "EVAL-01",
    "run_id": "eval-attempt-02",
    "paper": "edge-vision v2",
    "table_row": "表 2 Vision-S 行",
    "dataset": "Vision-Val v1/val",
    "metric": "Top-1（正确数除以参与统计的样本总数，以百分比报告）",
    "paper_number": 78.4,
    "eval_reproduced": 78.4
  },
  "ready_commands": {
    "eval": "/srv/envs/edge-vision/bin/python -u tools/eval.py --config /srv/research/edge-vision/docs/code-paper-reproduction/edge-vision-2026-11-24/runs/eval-attempt-02/config/eval-ema.yaml"
  },
  "checkpoint": {
    "vision-s-r1": {
      "source_id": "vision-s-r1",
      "path": "/srv/assets/edge-vision/vision-s-r1.pth",
      "kind": "EMA",
      "verified_run_id": "eval-attempt-02"
    }
  },
  "artifacts": { "alignment": "alignment.md", "report": "report.md" },
  "remaining_tasks": [
    { "item": "完整训练及训练间波动", "condition": "后续目标需要重训比较时单独验证" }
  ],
  "next_step": "用 eval-attempt-02 交 code-idea-prepare 核清理前后的评测行为"
}
```

交付前用 JSON 解析器检查机读记录。从每条交付用途回查目标、协议、run、命令与证据路径，并与人读报告里的数字、单位、状态和未决项逐条核对。
