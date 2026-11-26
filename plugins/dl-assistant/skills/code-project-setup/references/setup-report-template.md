# 准备报告、运行证据与机读交接

本文件说明怎样在执行过程中记录项目准备和入口验证的实际结果，并把可复跑的命令、证据和剩余问题交给用户与下游技能。

产物即真相。每完成一项任务，就按实际 plan 的任务编号和入口编号更新 `setup-report.md` 与 `setup.json`。保留原计划、已获准的改动和各次尝试。按 [SKILL 的产出约定](../SKILL.md#产出与保存)使用本次目录。恢复时先核已有报告、进程、日志、退出记录、版本和产物。

## setup-report.md

```markdown
# {仓库名} · 准备报告

> {实际日期、目标机器、代码版本、来源与本次检查范围。机读交接见 [setup.json](setup.json)。}

## 1. 现在可以做什么

| 四项交付 | 实际结果 | 仍待核查或受阻 |
| --- | --- | --- |
| 环境已配置 | {按实际环境说明可运行的入口、设备与关键版本} | {未覆盖的环境、依赖或设备} |
| 数据已准备 | {已取得和读取的版本、划分及样本范围} | {缺失、未读取或尚待核对的部分} |
| 权重已准备（如适用） | {发布身份、实际加载及覆盖范围} | {未验证的配置或未取得的资产} |
| 代码入口可直接运行 | {实跑入口及其覆盖范围，按下表列} | {未实跑、只通过部分检查或受阻的入口} |

| 入口 | 状态及已验证范围 | 证据与可复跑命令 | 尚未验证或如何解除阻塞 |
| --- | --- | --- | --- |
| {E01 等，沿用入口调查编号} | {实际完成的操作、输入及配置范围} | {执行任务、检查编号、命令和产物位置} | {剩余事项、下一步及责任人} |

## 2. 使用的版本与批准范围

{记录用户目标、入口报告和已批准的 spec 与 plan。已有选型时写实际确认的全部组件、版本、用途及实测待办。}
{列运行机器、分支、真实 commit 和必要 diff、环境、配置、数据与权重身份。对比选型的静态判断和本次实测，用版本及条件解释差异。}

## 3. 实际任务与检查

### {Plan 任务编号 · 入口编号 · 任务名称}

- 预期与依据 | {对应 spec 验收、上游需求或实测待办，输入和预期行为。}
- 实际命令与条件 | {命令、工作目录、解释器或容器、代码及 diff、设备、配置、资产、样本与精度。}
- 尝试与产物 | {时间、长任务会话或作业 ID、日志、实际退出码、输出路径。重试另记。}
- 检查结论 | {实测行为与预期的对照、失败现象及原因。}
- 可交付范围与后续 | {检查确认到哪里、缺什么、怎样续做。}

{按实际 plan 重复任务节。失败和后续复跑可同节并列，分别保留日志与版本。}

## 4. 环境、资产、改动与资源

- 环境与算子 | {实际环境、依赖版本与来源、导出文件、编译实现和入口实际是否使用。}
- 数据与权重 | {来源、版本、实际路径、完整性、划分或转换、loader 实读或权重覆盖范围。按需链接数据集速览。}
- 修复与授权 | {触发输入、最小改动、影响、实际批准、前后版本和复跑结果。}
- 资源与随机性 | {测量的操作、设备、输入、batch、精度、计时边界、重复读数与限制。区分实测、估算和未知。记录已查随机性设置及实际改动。}

## 5. 未决项、自查与交接

{逐项回应上游交给 setup 的实测待办。附实际结果、证据和未覆盖部分。其他阶段负责的任务按原条件移交。}
{检查入口清单是否逐项回应，支持范围是否有实跑证据，主要仓库和其他组件是否都交代，报告与 setup.json 能否对应。}
{交给用户的可复跑命令、准备目录和仍待解决的事项。涉及复现时给参考目标、实际协议及待核处。交给代码阅读时给源码版本、环境和入口。}
- Git 交接 | {本轮提交的文件或路径范围、外置证据的位置与获取方式、setup 分支、已确认的合并目标或只交付 setup 分支的决定。实测代码版本按各项检查保留，交付 commit 和实际合并结果在提交后向用户报告。已知阻塞在此记录。}
- 恢复条件 | {未结束任务、会话与日志位置、恢复条件和下一步。}
```

## setup.json

下面是可复制的起始结构，按实际任务填写。用入口调查的编号记录 `operations`，用计划任务编号和独立检查编号记录 `checks`。同一任务的不同运行尝试有独立检查编号和日志，原失败记录保留。

```json
{
  "schema_version": 2,
  "status": "not_started",
  "goal": null,
  "created_at": null,
  "updated_at": null,
  "source_survey": null,
  "source_entrypoint_report": null,
  "source_spec": null,
  "source_plan": null,
  "requirements": [],
  "repo": { "name": null, "url": null, "branch": null, "commit": null, "dirty": null, "diff_path": null },
  "repo_role": null,
  "components": [],
  "environments": [],
  "conda_env": null,
  "python": null,
  "torch": null,
  "cuda_toolkit": null,
  "operations": [],
  "checks": [],
  "supported_operations": [],
  "survey_task_responses": [],
  "ready_commands": {},
  "data": {},
  "checkpoint": {},
  "blocked": [],
  "paper_metrics": [],
  "validation_targets": [],
  "dev_card_footprint": null,
  "resource_observations": [],
  "reproducibility": { "seed_locations": [], "cudnn": {}, "dataloader": {}, "unverified": [], "changes": [] },
  "changes": [],
  "remaining_tasks": [],
  "dataset_report": null,
  "env_export": null,
  "smoke": null,
  "tracking_ref": null
}
```

### 入口、检查和实际结果

- 顶层 `status` 记录本轮批准的准备工作状态。`completed` 表示这轮任务已完成，完整入口是否已验证看各 `operations` 的范围。
- `operations` 每项写入口 `id`、用途、`requirement_ids`（有上游需求时，关联 `requirements`）、`check_ids`、状态、已验证范围和剩余事项。用 `checked` 表示所列操作范围已通过，`partial` 表示只支持其中一部分，例如验证集评测仅通过小样本运行。另可用 `not_checked`、`in_progress`、`blocked`、`failed` 或 `not_applicable`，不适用时写理由。
- `checks` 写 `id`、`operation_id`、`task_id`、检查层、预期行为与依据。记录真实运行环境、仓库 commit 及有影响的 diff、配置、数据、权重、样本范围和设备。 `execution` 留命令、工作目录、会话或作业 ID、日志、产物、进程状态及实际退出码。
- 检查的 `result` 用 `matches_expected`、`investigate`、`conflicts_with_expectation`、`not_checked` 或 `not_applicable`。退出码为零可以同时与预期冲突。缺少退出码时查进程和日志，再记录当前状态。
- `supported_operations` 列通过的实际范围、对应 `check_ids` 和限制。一个部分通过的入口可在这里列出已得到证据的部分。帮助命令、组件检查、真实小样本与全量运行分别记录。未解决的必要检查不得列入对应范围。
- `survey_task_responses` 逐项记录任务 ID、负责人、对应入口与检查、实际观察、未决事项及接手人。移交给其他阶段的待办按实际状态保存。

### 当前下游读取的字段

| 字段 | 怎样填写 |
| --- | --- |
| `repo`、`repo_role` | 保留主要仓库、实际分支与 commit。上游有明确选定角色时原样传递。直接准备项目且未指定角色时留空。其他组件写入 `components`，报告注明其版本与用途 |
| `conda_env`、`python`、`torch`、`cuda_toolkit` | 记录实际值。非 conda 环境将 `conda_env` 留空。容器、其他环境及其启动方式写入 `environments` 和实际执行记录 |
| `ready_commands` | 保留命令字符串映射。只填已验证且符合该字段用途的实际命令，入口的详细条件见对应检查。已通过的训练试跑可放 `train_smoke`。评测只跑过小样本时，将命令写进该入口检查，省略 `eval` 键，待完整入口验证后再填 |
| `data`、`checkpoint` | 按实际资产列路径、版本、状态、来源及检查范围，明确已取得、已读取或加载及仍受阻的部分 |
| `blocked` | 保留字符串数组，供当前下游识别。写入口或资产、原因和解锁动作。未安排的全量验证列在 `remaining_tasks` |
| `paper_metrics`、`validation_targets` | 保留参考结果及出处、实际口径和对应入口。无适用数值时用空数组。核查范围由该条证据支持，复现阶段仍需核参考结果 |
| `dev_card_footprint`、`reproducibility` | 按适用时记录实测设备和单步数据、实际 seed、采样或 worker 位置。未知留空或注明未核，其他资源量记测量条件 |
| `dataset_report`、`env_export`、`smoke` | 已有产物填实际路径。与报告同目录的产物用相对路径。需要多个检查脚本时在对应检查中指向实际文件 |

组合选型和多环境依赖按实际记录在 `components`、`environments` 和检查结果中，并随人读报告交接。当前下游仍从上表字段定位主要仓库、环境和命令，交接时显式指出额外组件及受限的验证范围。使用 W&B 时，`tracking_ref` 指向非敏感配置，按[共同记录约定](../../wandb/references/experiment-records.md)核运行和同步证据。

## 完整填写示例 · edge-vision

沿用[准备方案示例](setup-spec-and-plan.md#示例--从-edge-vision-入口报告写到执行任务)。仓库、命令、资产、批准和结果均为虚构。这里展示执行完成后互相对应的报告和 JSON。

### 示例 setup-report.md

```markdown
# edge-vision · 准备报告

> 2026-11-24，目标机 edge-dev-01。起点 a17c9d2，setup 分支当前为 c91b7e4。机读交接见 [setup.json](setup.json)。

## 1. 现在可以做什么

| 四项交付 | 实际结果 | 仍待核查或受阻 |
| --- | --- | --- |
| 环境已配置 | edge-vision conda 环境，四个入口共用目标 GPU 和运行时 | 其他设备和环境未核 |
| 数据已准备 | Vision-Val v1/val 和 Vision-Train v1/train 已取得。分别核了 17 样本评测和一个训练批次 | 全量读取及运行仍待核 |
| 权重已准备 | Vision-S r1 已校验，E01、E02、E04 实际加载 | E03 从头训练，无需发布权重 |
| 代码入口可直接运行 | 四个入口均得到指定范围内的证据，见下表 | 完整验证集评测及参考结果待复现 |

| 入口 | 状态及已验证范围 | 证据 | 尚未验证 |
| --- | --- | --- | --- |
| E01 单张推理 | 用真实图像输出分类结果 | P03，C01 及最终版本复核 C06 | 其他输入规模未核 |
| E02 评测 | 小样本通过，17 个指定 ID 都进入指标统计 | P05，首次 C02 和修复后 C03 | 完整验证集评测未执行 |
| E03 训练 | 一个真实批次完成一次参数更新 | P07，C04 | 完整训练未执行 |
| E04 轨迹测量 | 单张输入取得写回量及实际算子字段 | P08，C05 | 批量对照入口未定位 |

## 2. 使用的版本与批准范围

用户直接 clone 论文代码，暂无选型交接。入口清单以及四项准备任务范围见 entrypoint-report.md、setup-spec.md 和 setup-plan.md 的审阅记录。初次入口运行使用 b28d0e3，包含试跑配置。后续获准修正最后一批的统计覆盖，修复版为 c91b7e4。

各入口均从 /srv/research/edge-vision 运行。解释器为 /srv/envs/edge-vision/bin/python，设备为 edge-dev-01 上的一张 GPU。数据与权重版本见下。

## 3. 实际任务与检查

| 任务 | 操作和证据 | 结果 |
| --- | --- | --- |
| P01 环境 | 从仓库执行 `conda env create -n edge-vision -f environment.yml`。核实际解释器、项目导入、配置和设备。见 logs/p01-env.log、env/environment.yml | 四个入口共用环境可用 |
| P02 权重 | 从发布记录取得 Vision-S r1，在 /srv/assets/vision-s/r1 按清单执行 `sha256sum -c SHA256SUMS`。见 logs/p02-weights.log 及各入口加载日志 | 文件校验通过，E01、E02、E04 实际加载 |
| P03 推理 | 执行下方 E01 命令。见 logs/e01-inference.log 及修复后 logs/e01-inference-recheck.log | 退出码 0。真实输入输出分类结果 |
| P04 验证数据 | 在 /srv/assets/vision-val/v1 按发布清单核文件，读 E02 实际清单和 loader 输出。见 logs/p04-val.log | 数据版本及划分匹配，17 个试跑 ID 可读 |
| P05 评测 | 两次均执行下方 E02 命令，分别用会话 setup-dl-e02-eval-01 和 setup-dl-e02-eval-02 | 两次退出码均为 0。首次与预期冲突，修复后通过 |
| P06 训练数据 | 在 /srv/assets/vision-train/v1 按发布清单核文件。见 logs/p06-train.log，首批实际读取见 C04 | 训练划分与试跑配置匹配 |
| P07 训练 | 执行下方 E03 命令。见 logs/e03-train.log | 退出码 0，真实批次完成一次优化器更新 |
| P08 测量 | 执行下方 E04 命令。见 logs/e04-trace.log 和 outputs/e04-trace.json | 退出码 0，输出写回量单位和实际算子事件 |

### P05 的两次运行

- C02，b28d0e3，退出码 0。预期 17 个 ID 各统计一次，实际只统计 16 个。载入了协议要求的权重。核对清单、最后一批及配置，定位到评测路径丢弃不满批样本。原记录为 logs/setup-dl-e02-eval-01.log、outputs/e02-attempt-01/metric-ids.txt。
- C03，c91b7e4，退出码 0。用户确认保留末批的最小修复。按原权重、17 个样本、批大小 8 和同一指标实现复跑。比对 ID 后缺失和额外项均为空。证据为 logs/setup-dl-e02-eval-02.log、outputs/e02-attempt-02/metric-ids.txt 及 metrics.json。两次尝试的产物分别归档。

### 已复跑的命令

从 /srv/research/edge-vision 执行，沿用 c91b7e4、已准备的配置和资产。

- E01 ｜ `/srv/envs/edge-vision/bin/python tools/infer_one.py --config configs/single_request.yaml --image samples/val-001.jpg`
- E02 小样本 ｜ `/srv/envs/edge-vision/bin/python -u tools/eval.py --config configs/setup/eval-smoke.yaml`
- E03 训练试跑 ｜ `/srv/envs/edge-vision/bin/python tools/train.py --config configs/setup/train-smoke.yaml`
- E04 ｜ `/srv/envs/edge-vision/bin/python tools/measure.py --mode trace --config configs/trace.yaml --image samples/val-001.jpg`

## 4. 环境、资产、改动与资源

- 环境 ｜ edge-vision，Python 3.11。实际依赖导出见 env/environment.yml。目标 GPU 上编译算子已在 E01 和 E03 的入口日志中确认启用。
- 数据与权重 ｜ Vision-Val v1/val、Vision-Train v1/train、Vision-S r1 的版本、路径与检查范围见 setup.json。数据样本见 [数据集速览](edge-vision-datasets-intro.md)。
- 改动与授权 ｜ 根据 C02 的缺样本证据，经用户确认，修正验证入口的最后一批统计范围。修复为 c91b7e4，证据含 fixes/e02-last-batch.patch 和 C03。
- 资源和随机性 ｜ 本轮未实测单步耗时与显存。保留原随机性设置，已查训练 seed 位置，worker 细节待核。

## 5. 未决项、自查与交接

四个入口均已回应。当前下游可从 setup.json 的推理及训练试跑命令定位环境和配置。E02 的小样本命令见 C03。尚无全量评测证据，ready_commands 未填 eval。复现阶段从正式配置和 Vision-Val v1/val 着手核论文参考行及完整指标协议。代码阅读可用 c91b7e4 和实际入口。

- Git 交接 ｜ 修复、调查报告、spec、plan、准备报告与 setup.json、试跑配置、环境导出和轻量验证证据由 code/project-setup 提交。权重和数据的实际位置与来源见 setup.json。计划已批准本地合回 main，交付提交和合并结果在完成后提供。
- 恢复条件 ｜ 无运行中的 setup 任务。续做时核分支、资产、试跑配置、日志与退出记录。批量对照入口仍待补查，见入口调查报告。
```

### 示例 setup.json

```json
{
  "schema_version": 2,
  "status": "completed",
  "goal": "直接 clone 论文仓库后准备并验证四个正式入口",
  "created_at": "2026-11-24T09:00:00+08:00",
  "updated_at": "2026-11-24T17:00:00+08:00",
  "source_survey": null,
  "source_entrypoint_report": "entrypoint-report.md",
  "source_spec": "setup-spec.md",
  "source_plan": "setup-plan.md",
  "requirements": [],
  "repo": {
    "name": "edge-vision",
    "url": "https://example.invalid/research/edge-vision",
    "branch": "code/project-setup",
    "commit": "c91b7e4",
    "dirty": false,
    "diff_path": null
  },
  "repo_role": null,
  "components": [
    {
      "id": "main",
      "path": "/srv/research/edge-vision",
      "base_commit": "a17c9d2",
      "commit": "c91b7e4",
      "roles": ["inference", "evaluation", "training", "measurement"]
    }
  ],
  "environments": [
    {
      "id": "edge-env",
      "kind": "conda",
      "name": "edge-vision",
      "python_executable": "/srv/envs/edge-vision/bin/python",
      "python": "3.11",
      "device": "edge-dev-01 的目标 GPU",
      "export_path": "env/environment.yml",
      "log_path": "logs/p01-env.log"
    }
  ],
  "conda_env": "edge-vision",
  "python": "3.11",
  "torch": null,
  "cuda_toolkit": null,
  "operations": [
    {
      "id": "E01",
      "purpose": "单张推理",
      "requirement_ids": [],
      "check_ids": ["C01", "C06"],
      "status": "checked",
      "supported_scope": "用真实图像 val-001 完成单张推理，启用作者编译算子",
      "limitations": ["其他输入规模未核"]
    },
    {
      "id": "E02",
      "purpose": "验证集评测",
      "requirement_ids": [],
      "check_ids": ["C02", "C03"],
      "status": "partial",
      "supported_scope": "固定 val 清单的 17 个样本全部参与评测，批大小 8",
      "limitations": ["全量验证集评测和论文结果尚未核验"]
    },
    {
      "id": "E03",
      "purpose": "训练试跑",
      "requirement_ids": [],
      "check_ids": ["C04"],
      "status": "checked",
      "supported_scope": "从头训练一批真实样本并完成一次优化器更新，启用作者编译算子",
      "limitations": ["完整训练未执行"]
    },
    {
      "id": "E04",
      "purpose": "单张轨迹测量",
      "requirement_ids": [],
      "check_ids": ["C05"],
      "status": "checked",
      "supported_scope": "单张输入的写回量按字节记录并有实际算子事件",
      "limitations": ["批量对照入口未定位"]
    }
  ],
  "checks": [
    {
      "id": "C01",
      "operation_id": "E01",
      "task_id": "P03",
      "layer": "entrypoint",
      "expected_behavior": "加载 Vision-S r1 后为指定图像输出分类结果",
      "basis_refs": ["setup-spec.md", "configs/single_request.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "b28d0e3",
        "config": "configs/single_request.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["image-val-001"],
        "checkpoint_ids": ["vision-s-r1"],
        "input_scope": "一张真实图像 val-001"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python tools/infer_one.py --config configs/single_request.yaml --image samples/val-001.jpg",
        "working_directory": "/srv/research/edge-vision",
        "session": null,
        "exit_code": 0,
        "log_path": "logs/e01-inference.log",
        "output_paths": ["outputs/e01-attempt-01/prediction.json"]
      },
      "result": "matches_expected",
      "observations": ["成功加载 Vision-S r1，获得有效分类输出"]
    },
    {
      "id": "C02",
      "operation_id": "E02",
      "task_id": "P05",
      "layer": "entrypoint",
      "expected_behavior": "清单中 17 个样本各进入一次指标统计",
      "basis_refs": ["setup-spec.md", "configs/setup/eval-smoke.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "b28d0e3",
        "config": "configs/setup/eval-smoke.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["vision-val-v1"],
        "checkpoint_ids": ["vision-s-r1"],
        "input_scope": "Vision-Val v1/val，17 样本固定清单，批大小 8"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python -u tools/eval.py --config configs/setup/eval-smoke.yaml",
        "working_directory": "/srv/research/edge-vision",
        "session": "setup-dl-e02-eval-01",
        "exit_code": 0,
        "exit_code_path": "logs/setup-dl-e02-eval-01.EXIT_CODE",
        "log_path": "logs/setup-dl-e02-eval-01.log",
        "output_paths": ["outputs/e02-attempt-01/metric-ids.txt"]
      },
      "result": "conflicts_with_expectation",
      "observations": ["实际仅统计 16 个样本，缺最后一个不满批的样本 val-017"]
    },
    {
      "id": "C03",
      "operation_id": "E02",
      "task_id": "P05",
      "layer": "entrypoint",
      "expected_behavior": "清单中 17 个样本各进入一次指标统计",
      "basis_refs": ["setup-spec.md", "configs/setup/eval-smoke.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "c91b7e4",
        "config": "configs/setup/eval-smoke.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["vision-val-v1"],
        "checkpoint_ids": ["vision-s-r1"],
        "input_scope": "Vision-Val v1/val，同一 17 样本清单，批大小 8"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python -u tools/eval.py --config configs/setup/eval-smoke.yaml",
        "working_directory": "/srv/research/edge-vision",
        "session": "setup-dl-e02-eval-02",
        "exit_code": 0,
        "exit_code_path": "logs/setup-dl-e02-eval-02.EXIT_CODE",
        "log_path": "logs/setup-dl-e02-eval-02.log",
        "output_paths": ["outputs/e02-attempt-02/metric-ids.txt", "outputs/e02-attempt-02/metrics.json"]
      },
      "result": "matches_expected",
      "observations": ["统计 17 个 ID，缺失和额外项均为空"]
    },
    {
      "id": "C04",
      "operation_id": "E03",
      "task_id": "P07",
      "layer": "entrypoint",
      "expected_behavior": "一个真实批次完成前向、损失和一次预期参数更新",
      "basis_refs": ["setup-spec.md", "configs/setup/train-smoke.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "c91b7e4",
        "config": "configs/setup/train-smoke.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["vision-train-v1"],
        "checkpoint_ids": [],
        "input_scope": "Vision-Train v1/train 一个真实批次"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python tools/train.py --config configs/setup/train-smoke.yaml",
        "working_directory": "/srv/research/edge-vision",
        "session": null,
        "exit_code": 0,
        "log_path": "logs/e03-train.log",
        "output_paths": ["outputs/e03-parameter-update.json"]
      },
      "result": "matches_expected",
      "observations": ["完成一次预期参数更新，编译算子已启用"]
    },
    {
      "id": "C05",
      "operation_id": "E04",
      "task_id": "P08",
      "layer": "entrypoint",
      "expected_behavior": "单张输入取得写回量、单位与实际算子事件",
      "basis_refs": ["setup-spec.md", "configs/trace.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "c91b7e4",
        "config": "configs/trace.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["image-val-001"],
        "checkpoint_ids": ["vision-s-r1"],
        "input_scope": "一张真实图像 val-001"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python tools/measure.py --mode trace --config configs/trace.yaml --image samples/val-001.jpg",
        "working_directory": "/srv/research/edge-vision",
        "session": null,
        "exit_code": 0,
        "log_path": "logs/e04-trace.log",
        "output_paths": ["outputs/e04-trace.json"]
      },
      "result": "matches_expected",
      "observations": ["保存写回量的字节数及实际算子事件"]
    },
    {
      "id": "C06",
      "operation_id": "E01",
      "task_id": "P03",
      "layer": "entrypoint",
      "expected_behavior": "加载 Vision-S r1 后为指定图像输出分类结果",
      "basis_refs": ["setup-spec.md", "configs/single_request.yaml"],
      "context": {
        "component_ids": ["main"],
        "environment_id": "edge-env",
        "commit": "c91b7e4",
        "config": "configs/single_request.yaml",
        "device": "edge-dev-01 的目标 GPU",
        "data_ids": ["image-val-001"],
        "checkpoint_ids": ["vision-s-r1"],
        "input_scope": "一张真实图像 val-001"
      },
      "execution": {
        "status": "completed",
        "command": "/srv/envs/edge-vision/bin/python tools/infer_one.py --config configs/single_request.yaml --image samples/val-001.jpg",
        "working_directory": "/srv/research/edge-vision",
        "session": null,
        "exit_code": 0,
        "log_path": "logs/e01-inference-recheck.log",
        "output_paths": ["outputs/e01-attempt-02/prediction.json"]
      },
      "result": "matches_expected",
      "observations": ["修复后复核发布权重、编译算子和分类输出"]
    }
  ],
  "supported_operations": [
    {
      "operation_id": "E01",
      "check_ids": ["C06"],
      "scope": "用真实图像 val-001 完成单张推理，启用作者编译算子",
      "limitations": ["其他输入规模未核"]
    },
    {
      "operation_id": "E02",
      "check_ids": ["C03"],
      "scope": "固定 val 清单的 17 个样本全部参与评测，批大小 8",
      "limitations": ["全量验证集评测和论文结果尚未核验"]
    },
    {
      "operation_id": "E03",
      "check_ids": ["C04"],
      "scope": "从头训练一批真实样本并完成一次优化器更新，启用作者编译算子",
      "limitations": ["完整训练未执行"]
    },
    {
      "operation_id": "E04",
      "check_ids": ["C05"],
      "scope": "单张输入的写回量按字节记录并有实际算子事件",
      "limitations": ["批量对照入口未定位"]
    }
  ],
  "survey_task_responses": [],
  "ready_commands": {
    "inference": "/srv/envs/edge-vision/bin/python tools/infer_one.py --config configs/single_request.yaml --image samples/val-001.jpg",
    "train_smoke": "/srv/envs/edge-vision/bin/python tools/train.py --config configs/setup/train-smoke.yaml"
  },
  "data": {
    "image-val-001": {
      "path": "/srv/research/edge-vision/samples/val-001.jpg",
      "version": "v1",
      "split": "val",
      "status": "checked",
      "source": "Vision-Val v1/val，样本 val-001",
      "check_ids": ["C06", "C05"]
    },
    "vision-val-v1": {
      "path": "/srv/assets/vision-val/v1",
      "version": "v1",
      "split": "val",
      "status": "checked",
      "source": "Vision-Val v1 发布清单",
      "coverage": "完整资产已取得，实跑核对指定 17 个样本",
      "check_ids": ["C03"],
      "log_path": "logs/p04-val.log"
    },
    "vision-train-v1": {
      "path": "/srv/assets/vision-train/v1",
      "version": "v1",
      "split": "train",
      "status": "checked",
      "source": "Vision-Train v1 发布清单",
      "coverage": "完整资产已取得，实跑核对首个训练批次",
      "check_ids": ["C04"],
      "log_path": "logs/p06-train.log"
    }
  },
  "checkpoint": {
    "vision-s-r1": {
      "path": "/srv/assets/vision-s/r1/vision-s.pth",
      "version": "r1",
      "status": "checked",
      "source": "Vision-S r1 发布记录",
      "coverage": "文件校验通过，E01、E02、E04 实际加载",
      "check_ids": ["C06", "C03", "C05"],
      "log_path": "logs/p02-weights.log"
    }
  },
  "blocked": [],
  "paper_metrics": [],
  "validation_targets": [
    {
      "operation_id": "E02",
      "scope": "完整 Vision-Val v1/val 评测",
      "config": "configs/eval.yaml",
      "status": "not_checked",
      "reference": "论文参考行、指标口径及可比条件待复现核对"
    }
  ],
  "dev_card_footprint": null,
  "resource_observations": [],
  "reproducibility": {
    "seed_locations": ["tools/train.py 的训练入口"],
    "cudnn": {},
    "dataloader": {},
    "unverified": ["worker seed", "cuDNN 设置"],
    "changes": []
  },
  "changes": [
    {
      "id": "fix-01",
      "operation_id": "E02",
      "before_commit": "b28d0e3",
      "after_commit": "c91b7e4",
      "reason": "首次检查有 1 个末批样本未进入统计",
      "authorization": "用户确认保留最后一批，沿用原有指标实现",
      "diff_path": "fixes/e02-last-batch.patch",
      "check_ids": ["C02", "C03"]
    }
  ],
  "remaining_tasks": [
    {
      "operation_id": "E02",
      "task": "用正式配置跑完整验证集并核论文参考行",
      "owner": "code-paper-reproduction"
    },
    {
      "operation_id": "E04",
      "task": "若需要复跑批量对照，补查启动命令和配置",
      "owner": "code-project-setup"
    }
  ],
  "dataset_report": "edge-vision-datasets-intro.md",
  "env_export": "env/environment.yml",
  "smoke": null,
  "tracking_ref": null
}
```
