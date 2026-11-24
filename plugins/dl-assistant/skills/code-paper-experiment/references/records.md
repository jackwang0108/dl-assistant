# 论文实验记录字段说明

计划、执行规格和结果包均使用 `schema_version: 1`。批次 ID 由已批准的 plan 提供。科研设计变化保存新 plan 和新 batch ID。执行绑定变化保留 run-spec 修订，同一批的部分交付使用递增回包修订。

## 计划和执行规格

- plan 的 `approval.ref` 指向实际决定，`experiment_ids` 只列获批项。`comparison` 写组别和条件，`measurements` 定义测量 ID、单位和分析。`replicates.items` 写独立重复 ID 及适用的 seed。确定性测量、分析可登记一个独立工作单元，seed 留空。`interpretation` 写判据及依据，展示位置写 `paper_locations`。
- run-spec 为每个获批任务绑定实际入口、配置、代码和资源。前置额外工程调整或资源批准写 `approval_ref`，原计划用文件名和 SHA-256 引用。确有变化时保留原规格。对需要独立设备或不同条件的任务分别绑定，配置、模型和数据用实际版本或固定副本指针。

## 回包

- `paper-results.json` 的 `plan`、`run_spec` 以包内相对路径及 SHA-256 引用副本。原包保留；从第二次回包开始用 `previous_sha256` 指向上一版的 `paper-results.json` 摘要，可用 `--previous` 对账。
- 每项 `execution` 写状态、原因、尝试和 `resource_usage`，后者逐项记数量、单位和来源。`measurement` 写有效性及适用条件。`evidence` 写已回答和仍缺的问题。`deviations` 记计划、实际变化和影响。状态可为 `not_started`、`in_progress`、`completed`、`partial`、`failed`、`blocked`、`cancelled`。测量有效性用 `unassessed`、`valid`、`limited`、`invalid`。统计和证据按实际范围填写。预期作图、报告或源数据在 `artifacts` 逐项说明。
- `execution.attempts` 每项写 `attempt_id`、`replicate_id`、`seed`、`run_spec_revision`、`status`、`data_validity`、`meta_ref`、`metrics_ref`。未取到读数时 `metrics_ref` 可为空。重试或恢复分别以 `retry_of` 或 `resume_from` 记原尝试，并在元记录写实际 checkpoint 及恢复情况。将各次 [元记录](templates/paper-attempt-template.json)随包提供，引用该次尝试采用的规格副本。大文件可在元记录或产物引用中指向外部位置。
- 使用 W&B 时在 `execution.tracking` 记录实验的实例、项目和批次，在各尝试元记录保存实际 run、代码、配置摘要和同步证据。字段和路径见 [论文实验的 W&B 映射](../../wandb/references/experiment-records.md#论文实验回包的映射)。回包接续时保留已登记的 run 身份，按实际查回更新同步状态。
- 本地产物引用用 `{"path":"包内文件","sha256":"可选的摘要"}`。外部产物用 `{"external":{"location":"机器和实际路径","version":"固定版本或摘要","availability":"如何访问或当前缺项"}}`。校验器核外部引用字段，接收方还要核实际可访问性。
- `statistics` 中每条用稳定的 `id`，绑定 `measurement_id`、`unit`、`value`、`method` 和实际使用的 `attempt_ids`。每个统计最多用每个独立重复的一次有效尝试。简单均值写 `method: mean` 和 `group`，配对差的均值写 `method: mean_paired_difference`、`minuend` 和 `subtrahend`。适用时报告样本或配对数和不确定性。其他统计写 `method: analysis` 和 `analysis_ref`，引用可复查的计算输入、脚本及结果。机器只复算内置方法。
- `metrics.json` 的最小复算结构如下。组名、单位和测量 ID 按实际定义。明细读数、抽样或聚合依据另附出处。

```json
{
  "attempt_id": "attempt-01",
  "measurements": {"latency": {"unit": "ms", "values": {"baseline": 12.5, "combined": 10.7}}}
}
```

回包新增比较时用稳定的统计 ID。已交付的统计变更或撤回时，`changes` 每条记录 `exp_id`、`statistic_id`、`previous_value`、`reason` 和 `impact`。例如原数值只用了一个配对，补齐后更新同一统计并说明写作中需核对的正文和图表。仅新增此前无法计算的差值时，保留原尝试和未决说明。
