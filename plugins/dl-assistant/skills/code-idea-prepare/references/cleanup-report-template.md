# 代码整理报告与机读交接模板

本文件说明怎样记录代码整理的实际变更、改前改后的验证证据和未覆盖范围，并把可用版本、复跑入口和后续检查交给下游。

从开工起记录现场，调查后补建议，逐批回填 `cleanup-report.md` 与 `cleanup.json`。两份记录用同一组用途、变更、检查和 run ID。在[运行手册 Step 6](workflow.md#step-6-定稿并交接)逐项核对后交付。用[验证策略](verification-strategy.md)判断实际证据覆盖到哪里。

## 可复制的 cleanup-report.md

````markdown
# {仓库名} · 代码整理报告

- 本次结论 | {采用的版本与实际用途，哪些仍需补证}
- 工作位置与依据 | {日期、仓库、分支、机器和环境，setup/reproduction、方案与授权记录}
- 机读交接 | [cleanup.json](cleanup.json)

## 1. 可用版本与用途

| 用途或变更 ID | 当前结论 | 证据 | 未覆盖及下一步 |
| --- | --- | --- | --- |
| {USE-01} | {已实跑验证／保留但未实跑，对应版本及条件} | {检查 ID、run 或静态核对位置} | {需要补查的操作及接手阶段} |
| {CH-01} | {经确认移除、有意修复、未采用或撤销} | {确认记录、实际 diff 及执行结果} | {明确受影响的用途和限制} |

## 2. 改前现场与调查

{改前 commit 及相关未提交 diff、用户已有改动、环境、配置和资产。说明候选、查过的调用方及配置、保留或移除依据。按需链接 coverage/operation-paths.md，说明实际命令、输入、工具范围及未观察到的路径。}

## 3. 逐批变更和检查

| 批次与变更 ID | 类型与实际 diff | 检查 ID、预期和证据 | 实际观察与处理 |
| --- | --- | --- | --- |
| {B01、CH-01} | {预期保持或改变什么，实际涉及路径、版本或 diff} | {输入、改前与改后运行或审阅记录} | {采用、待验证、修正或撤销及理由} |

{差异调查写最早观察到差异的位置、已核条件、局部修正或撤销范围、复跑结论。保留失败和未采用的尝试。}

## 4. 复跑入口与交接

- 可用版本 | {实际 commit、相关 diff、分支和合并状态}
- 复跑 | {工作目录、实际命令或 command.sh，配置、环境、数据、权重、比较证据及范围}
- 交 code-reading | {入口、代码与配置、变化及执行路径记录}
- 后续检查 | {未实跑用途、训练阶段、数据或保存兼容、旧证据需要重核的条件与接手阶段}
```

## 可复制的 cleanup.json 起点

使用 `schema_version: 2`。以下为尚未执行的结构，按现场填充。产物相对路径从本次交付目录解析，仓库源码路径从实际仓库根目录解析。外部 run 和资产记录它们的实际位置及取得方式。

```json
{
  "schema_version": 2,
  "status": "not_started",
  "goal": null,
  "authorized_scope": [],
  "inherits": {},
  "before_state": {},
  "after_state": {},
  "retained_uses": [],
  "candidate_investigations": [],
  "changes": [],
  "verification_records": [],
  "runs": [],
  "revisions": [],
  "handoff": {
    "selected_state_refs": [],
    "supported_uses": [],
    "operation_paths_ref": null,
    "remaining_tasks": [],
    "next_skill": null
  }
}
```

| 字段 | 记录内容 |
| --- | --- |
| `status`、`authorized_scope` | 本轮进度和实际确认范围。按实际写 `not_started`、`in_progress`、`completed`、`partial`、`blocked`、`failed` 或 `cancelled`。无需改动时可完成调查并交原版本及可引用的证据 |
| `before_state`、`after_state` | 记录实际仓库、分支、commit、相关未提交 diff、环境和资产。核实用户已有改动的状态，注明实际合并情况。分支名用于定位版本 |
| `retained_uses`、`candidate_investigations` | 每个用途给 ID、适用条件、依据、相关检查和未知。候选记录实际调查范围及处理建议。只确认配置或源码存在的用途，把这段证据和实际运行范围说明清楚 |
| `changes` | 按变更 ID、批次、代码位置和授权记录。`kind` 用 `preserve_behavior`、`remove_out_of_scope` 或 `behavior_fix`。记录提议、实际采用、撤销或未采用，关联 diff、受影响用途和检查，有已确认移除功能时写实际支持范围变化及迁移 |
| `verification_records` | 每条记录关联实际变更和用途，写检查方式、判据依据、前后 run 或静态审阅证据、实际观察及限制。区分 `comparison_result` 和 `behavior_assessment`，使用[验证策略的值](verification-strategy.md#4-用实际配置复核并记录结论)。静态审阅记录材料和发现 |
| `runs` | 用唯一 ID 记录实际版本、运行状态、工作目录、命令、环境、配置、输入和产物。可复用上游 run，保存来源与证据范围。退出码只描述进程。每次尝试独立保存 |
| `revisions` | 按需记录差异、原因、局部修正或撤销、前后版本及重验引用，让接手人能回查早期观察和后来的判断 |
| `handoff` | 选定版本和配置，每项已验证用途关联检查、run、实际复跑入口和边界。路径记录使用 `coverage/operation-paths.md`。列出静态保留、待核事项和接手阶段。影响原复现证据时写明需要重新核的条件 |

## 完整填写示例 · edge-vision

沿用[运行手册的虚构案例](workflow.md#贯穿示例--edge-vision-的评测入口整理)。本例采用评测入口整理，独立的调试工具退役及缺标签行为修复留在各自的提议阶段。示例版本和路径只用于示范填写。

### cleanup-report.md

````markdown
# edge-vision · 代码整理报告

- 本次结论 | 采用 8bd7ac2 的评测入口整理。用 after-eval-02 验证了固定 Vision-S r1 EMA 权重和完整 Vision-Val v1/val 的评测。
- 工作位置与依据 | 2026-11-24，/srv/research/edge-vision，edge-dev-01，/srv/envs/edge-vision/bin/python。依据 setup E02/C03、复现 EVAL-01 v1 和 quality-spec.md 中批准的 B01。
- 机读交接 | [cleanup.json](cleanup.json)

## 1. 可用版本与用途

| 用途或变更 ID | 当前结论 | 证据 | 未覆盖及下一步 |
| --- | --- | --- | --- |
| USE-01 · 正式 EMA 评测 | 使用 8bd7ac2。500 个预期 ID 各计一次，Top-1 为 392/500（78.4%） | CHECK-Q01-FINAL，改前 eval-attempt-02，改后 after-eval-02 | 仅覆盖指定发布权重、划分与指标。后续重训需单独核查 |
| USE-02 · 旧模型配置 | 保留 configs/eval-legacy.yaml 及 legacy_small 注册项 | CHECK-LEGACY-REVIEW 核了源码和配置引用 | 本轮未实跑旧模型，使用历史 checkpoint 前补完整评测 |
| CH-01 · 评测入口整理 | 采用 B01 的最终版本。保留原参数、默认值和覆盖顺序，恢复了聚合前的样本 ID 传递 | CHECK-Q01-OVERRIDE、CHECK-Q01-FIRST、CHECK-Q01-FINAL | 本次获批范围是结构整理，调试入口退役和缺标签处理尚待各自确认 |

## 2. 改前现场与调查

改前版本 c91b7e4，记录时工作区干净。eval-attempt-02 使用 Vision-S r1 EMA、完整 500 样本及原 Top-1 聚合。代码调查发现旧模型没有经该命令执行，但正式配置仍可由注册表构造它，因此保留。入口、配置读取、权重加载、loader 和聚合的实际观察见 [执行路径记录](coverage/operation-paths.md)，覆盖当前评测及配置解析短跑。

## 3. 逐批变更和检查

| 批次与变更 ID | 类型与实际 diff | 检查 ID、预期和证据 | 实际观察与处理 |
| --- | --- | --- | --- |
| B01／CH-01 | tools/eval.py 的配置合并及评测调用整理。首版 41fa903，最终 8bd7ac2 | CHECK-Q01-OVERRIDE，对比 before-override-01 与 after-override-01 的配置解析记录 | 两侧 CLI 覆盖后的生效配置一致，短跑覆盖该输入路径 |
| B01／CH-01 | 首版 41fa903 | CHECK-Q01-FIRST，对比 eval-attempt-02 与 after-eval-01 的实际 ID 和指标 | 退出码 0，仍为 392/500。发现一个 ID 重复、一个 ID 遗漏，比较未满足覆盖预期 |
| B01／CH-01 | 8bd7ac2 修正聚合前的 ID 字段传递 | CHECK-Q01-FINAL，对比 eval-attempt-02 与 after-eval-02 | 退出码 0，500 个 ID 各计一次，加载 EMA，正确计数 392。该范围内未观察到差异 |
| B01／CH-01 | 8bd7ac2 保留旧模型路径 | CHECK-LEGACY-REVIEW，审阅 configs/eval-legacy.yaml 与对应注册项 | 配置仍可按注册名查到 legacy_small。结论限于静态审阅 |

首次完整改后运行的样本覆盖异常来自入口整理漏传聚合器需要的 ID 字段。loader 输出的 ID 与改前一致，差异首次出现在传入聚合器时。恢复字段映射后另建运行并复核。保留 [首次指标](runs/after-eval-01/metrics.json)、[样本差异](runs/after-eval-01/outputs/id-diff.txt) 和 [复跑指标](runs/after-eval-02/metrics.json)。

## 4. 复跑入口与交接

- 可用版本 | 8bd7ac2，code/baseline-cleanup，工作区干净，尚未合并。
- 复跑 | 在 /srv/research/edge-vision 运行 [after-eval-02 的命令](runs/after-eval-02/command.sh)，按其中指定的 Python 与 EVAL-01 v1 有效配置，保留 EMA、样本清单和聚合口径。用实际 ID、[加载日志](runs/after-eval-02/cip-edge-vision-after-eval-02.log) 与 392/500 的读数比较。
- 交 code-reading | 从 tools/eval.py 读配置、权重加载、loader 和聚合路径，参考 coverage/operation-paths.md 和 CH-01 的版本差异。
- 后续检查 | 后续执行若涉及旧模型，需补历史权重读回和实际评测。改训练循环前另建参数更新、调度及保存恢复的对照。缺标签修复另审其行为及原结果的适用性。
```

### cleanup.json

```json
{
  "schema_version": 2,
  "status": "completed",
  "goal": "整理评测入口的配置读取和调用",
  "authorized_scope": [
    { "change_id": "CH-01", "batch_id": "B01", "approval_ref": "quality-spec.md", "scope": "保持现有行为的结构整理及约定复核" }
  ],
  "inherits": {
    "setup": "/srv/research/edge-vision/docs/code-project-setup/edge-vision-2026-11-24/setup.json",
    "reproduction": "/srv/research/edge-vision/docs/code-paper-reproduction/edge-vision-2026-11-24/reproduction.json",
    "reproduction_target": "EVAL-01",
    "protocol_version": "v1"
  },
  "before_state": {
    "id": "before",
    "repo": "/srv/research/edge-vision",
    "commit": "c91b7e4",
    "tracked_diff": null,
    "worktree_clean": true,
    "environment": "/srv/envs/edge-vision/bin/python",
    "machine": "edge-dev-01"
  },
  "after_state": {
    "id": "after",
    "repo": "/srv/research/edge-vision",
    "commit": "8bd7ac2",
    "branch": "code/baseline-cleanup",
    "tracked_diff": null,
    "worktree_clean": true,
    "environment": "/srv/envs/edge-vision/bin/python",
    "merge_status": "not_merged"
  },
  "retained_uses": [
    {
      "id": "USE-01",
      "purpose": "正式固定权重 EMA 评测",
      "conditions": "Vision-S r1 EMA，Vision-Val v1/val 的 500 个样本及 EVAL-01 v1 指标口径",
      "verification_ids": ["CHECK-Q01-OVERRIDE", "CHECK-Q01-FINAL"],
      "unknowns": ["完整训练与训练间波动"]
    },
    {
      "id": "USE-02",
      "purpose": "保留旧模型注册与配置",
      "basis_refs": ["configs/eval-legacy.yaml", "coverage/operation-paths.md"],
      "verification_ids": ["CHECK-LEGACY-REVIEW"],
      "unknowns": ["旧模型与历史 checkpoint 未实跑"]
    }
  ],
  "candidate_investigations": [
    {
      "id": "C-01",
      "location": "configs/eval-legacy.yaml 与 legacy_small 注册项",
      "finding": "正式配置仍引用对应注册名",
      "recommendation": "retain",
      "limitations": ["本轮固定权重评测未经过该路径"]
    }
  ],
  "changes": [
    {
      "id": "CH-01",
      "batch_id": "B01",
      "kind": "preserve_behavior",
      "status": "kept",
      "locations": ["tools/eval.py"],
      "diff_range": "c91b7e4..8bd7ac2",
      "preserved_behavior": "配置及覆盖顺序、权重分支、样本身份与聚合",
      "retained_use_ids": ["USE-01", "USE-02"],
      "authorization_ref": "quality-spec.md",
      "verification_ids": ["CHECK-Q01-OVERRIDE", "CHECK-Q01-FIRST", "CHECK-Q01-FINAL", "CHECK-LEGACY-REVIEW"]
    }
  ],
  "verification_records": [
    {
      "id": "CHECK-Q01-OVERRIDE",
      "change_ids": ["CH-01"],
      "retained_use_ids": ["USE-01"],
      "method_kind": "run",
      "before_run_id": "before-override-01",
      "after_run_id": "after-override-01",
      "expected_behavior": "同一 CLI 覆盖参数产生相同的生效配置",
      "comparison_result": "no_difference_observed",
      "behavior_assessment": "not_applicable",
      "finding": "两次短跑的生效配置一致"
    },
    {
      "id": "CHECK-Q01-FIRST",
      "change_ids": ["CH-01"],
      "retained_use_ids": ["USE-01"],
      "method_kind": "run",
      "before_run_id": "eval-attempt-02",
      "after_run_id": "after-eval-01",
      "expected_behavior": "EMA、样本 ID 及出现次数和 Top-1 聚合保持一致",
      "comparison_result": "difference_observed",
      "behavior_assessment": "not_applicable",
      "finding": "指标均为 392/500，首次改后出现一个样本 ID 重复和一个遗漏",
      "evidence_refs": ["runs/after-eval-01/outputs/id-diff.txt"]
    },
    {
      "id": "CHECK-Q01-FINAL",
      "change_ids": ["CH-01"],
      "retained_use_ids": ["USE-01"],
      "method_kind": "run",
      "before_run_id": "eval-attempt-02",
      "after_run_id": "after-eval-02",
      "expected_behavior": "EMA、样本 ID 及出现次数和 Top-1 聚合保持一致",
      "comparison_result": "no_difference_observed",
      "behavior_assessment": "not_applicable",
      "finding": "实际加载 EMA，500 个预期 ID 各计一次，正确计数 392，Top-1 78.4%",
      "limitations": ["仅覆盖本次评测用途"]
    },
    {
      "id": "CHECK-LEGACY-REVIEW",
      "change_ids": ["CH-01"],
      "retained_use_ids": ["USE-02"],
      "method_kind": "review",
      "evidence_refs": ["configs/eval-legacy.yaml", "coverage/operation-paths.md"],
      "expected_behavior": "保留旧模型注册与配置引用",
      "comparison_result": "no_difference_observed",
      "behavior_assessment": "not_applicable",
      "finding": "前后配置及注册路径仍对应 legacy_small",
      "limitations": ["静态审阅，未实跑旧模型"]
    }
  ],
  "runs": [
    {
      "id": "eval-attempt-02",
      "execution_status": "completed",
      "commit": "c91b7e4",
      "exit_code": 0,
      "source_result_ref": "/srv/research/edge-vision/docs/code-paper-reproduction/edge-vision-2026-11-24/runs/eval-attempt-02/meta.json",
      "observations": { "correct": 392, "total": 500, "top1_percent": 78.4, "checkpoint_variant": "EMA" }
    },
    {
      "id": "before-override-01",
      "execution_status": "completed",
      "commit": "c91b7e4",
      "exit_code": 0,
      "meta_path": "runs/before-override-01/meta.json",
      "command_file": "runs/before-override-01/command.sh",
      "result_paths": ["runs/before-override-01/config/effective.yaml"]
    },
    {
      "id": "after-override-01",
      "execution_status": "completed",
      "commit": "41fa903",
      "exit_code": 0,
      "meta_path": "runs/after-override-01/meta.json",
      "command_file": "runs/after-override-01/command.sh",
      "result_paths": ["runs/after-override-01/config/effective.yaml"]
    },
    {
      "id": "after-eval-01",
      "execution_status": "completed",
      "commit": "41fa903",
      "exit_code": 0,
      "meta_path": "runs/after-eval-01/meta.json",
      "command_file": "runs/after-eval-01/command.sh",
      "result_paths": ["runs/after-eval-01/metrics.json", "runs/after-eval-01/outputs/evaluated-ids.txt", "runs/after-eval-01/outputs/id-diff.txt"],
      "observations": { "correct": 392, "total": 500, "top1_percent": 78.4, "duplicate_ids": 1, "missing_ids": 1 }
    },
    {
      "id": "after-eval-02",
      "execution_status": "completed",
      "commit": "8bd7ac2",
      "exit_code": 0,
      "meta_path": "runs/after-eval-02/meta.json",
      "working_directory": "/srv/research/edge-vision",
      "environment": "/srv/envs/edge-vision/bin/python",
      "command_file": "runs/after-eval-02/command.sh",
      "config_ref": "runs/after-eval-02/config/effective.yaml",
      "log_path": "runs/after-eval-02/cip-edge-vision-after-eval-02.log",
      "result_paths": ["runs/after-eval-02/metrics.json", "runs/after-eval-02/outputs/evaluated-ids.txt"],
      "observations": { "correct": 392, "total": 500, "top1_percent": 78.4, "checkpoint_variant": "EMA", "duplicate_ids": 0, "missing_ids": 0 }
    }
  ],
  "revisions": [
    {
      "change_id": "CH-01",
      "before_commit": "41fa903",
      "after_commit": "8bd7ac2",
      "action": "恢复聚合器输入中的样本 ID 字段映射",
      "basis_verification_id": "CHECK-Q01-FIRST",
      "recheck_verification_id": "CHECK-Q01-FINAL"
    }
  ],
  "handoff": {
    "selected_state_refs": ["after"],
    "supported_uses": [
      {
        "retained_use_id": "USE-01",
        "verification_ids": ["CHECK-Q01-FINAL"],
        "run_id": "after-eval-02",
        "command_file": "runs/after-eval-02/command.sh",
        "scope": "EVAL-01 v1 的 Vision-S r1 EMA 和完整验证集评测"
      }
    ],
    "operation_paths_ref": "coverage/operation-paths.md",
    "remaining_tasks": [
      { "retained_use_id": "USE-02", "task": "实际使用旧模型之前，核历史 checkpoint 读回及完整评测" },
      { "task": "进入训练代码改动之前，补改前参数更新、调度及保存恢复检查" }
    ],
    "next_skill": "code-reading"
  }
}
```

交付前解析 JSON，按用途、变更、检查和 run 回查引用。核两份文件的实际版本、观察、状态和未覆盖范围一致。
