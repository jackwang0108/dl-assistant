# 选型报告与执行交接模板

本文件说明怎样把候选的选型依据、用户确认的使用范围，以及下游需要做的首批实测写进报告和交接记录。

默认保存到 `docs/baseline-survey/<日期>-<slug>/`，用户指定位置时用该位置。按[运行手册](workflow.md)填写 `baseline-survey.json` 和 `report.md`，需要保留详细出处时用[候选核查事实记录模板](fact-record-template.md)写到 `facts/`。用户确认后在报告中附 clone 卡。记录实际日期、版本和调查范围。

## baseline-survey.json

下面是可复制的起始结构。用本次材料替换示意条目，允许零个、一个或多个候选。未知值用 `null` 或明确的未知状态，空数组表示当前没有记录。有意义的未知应说明原因和影响。

```json
{
  "schema_version": 2,
  "direction": null,
  "created_at": null,
  "updated_at": null,
  "intent": null,
  "source_spec": null,
  "source_plan": null,
  "resource_constraint": null,
  "requirements": [
    { "id": "R1", "need": null, "mandatory": true, "rationale": null, "source_refs": [] }
  ],
  "search_scope": {
    "checked_at": null, "queries": [], "sources": [],
    "inclusion_reasons": [], "exclusions": [], "limitations": []
  },
  "sources": [],
  "paper_metrics": [],
  "validation_targets": [],
  "candidates": [
    {
      "id": "B1",
      "repo": null,
      "url": null,
      "revision": null,
      "revision_status": "unresolved",
      "roles": [],
      "repo_role": null,
      "official": null,
      "official_source_refs": [],
      "research_fit": [
        {
          "requirement_id": "R1", "assessment": "unknown", "finding": null,
          "basis_type": null, "source_refs": [], "unverified": [], "effect_on_choice": null
        }
      ],
      "exec_chain": {
        "train": null, "eval": null, "data": null, "measurement": null,
        "source_refs": [], "runtime_validated": false
      },
      "method_insertion_point": null,
      "env_deps": { "key_deps": null, "compile_landmines": null, "uncommon": null, "source_refs": [] },
      "weights": {
        "identity": null, "url": null, "revision": null, "config": null,
        "availability": "unknown", "aligns_code_version": null, "source_refs": [],
        "download_validation": "not_performed", "load_validation": "not_performed"
      },
      "dataset": {
        "identity": null, "url": null, "version": null, "split": null, "protocol": null,
        "aligns_paper": null, "source_refs": [], "runtime_validated": false
      },
      "licenses": {
        "code": { "terms": null, "source_refs": [] },
        "weights": { "terms": null, "source_refs": [] },
        "data": { "terms": null, "source_refs": [] },
        "use_constraints": [], "unresolved": []
      },
      "community_reports": [],
      "build_cost": { "assessment": "unknown", "basis": null, "unknowns": [] },
      "adapt_cost": { "changes": [], "changes_core_method": null, "basis": null, "unknowns": [] },
      "eligibility": "unassessed",
      "key_risks": []
    }
  ],
  "recommendation": {
    "status": "needs_more_information", "by_use": [], "combination_checks": [],
    "repo": null, "reason": null, "limitations": []
  },
  "decision": {
    "status": "pending", "primary_candidate_id": null, "repo": null, "repo_role": null,
    "components": [], "reason": null, "user_response": null, "date": null,
    "approved_scope": [], "pending_scope": [], "conditions": []
  },
  "self_checks": { "requirements": [], "recommendation": [] },
  "verification_tasks": [],
  "revisions": []
}
```

### 需求、来源与候选

- `intent` 写真实的目标和用途，例如原样复现、选择本轮实现、测量分析或准备数据。`source_spec` 和 `source_plan` 记录实际读取的路径和版本。直接发起调研时引用用户提供的目标与条件。每项 `requirements` 说明为何需要、来自哪里，以及它是必要条件还是偏好。
- `search_scope` 写实际执行的查询、来源、纳入排除理由和未覆盖处。每项 `sources` 写 `id`、`kind`、`location`、`revision`、`accessed_at`（带时区）和 `read_scope`。关键判断在 `finding` 或事实记录指到章节、表格行、`文件:函数` 或配置键。不同版本和运行条件各留出处。
- `revision_status` 用 `resolved` 或 `unresolved`。优先记录实际读过的 commit 或可核对的发布版本。官方关系用 `official` 的 `true`、`false` 或 `null` 记录，并给出处。
- `roles` 可同时包含 `comparison`、`implementation`、`measurement` 和 `data_preparation`。`research_fit` 逐项对应必要条件，使用 `supported_by_sources`、`mismatch`、`unknown` 或 `not_applicable`。依据用 `basis_type` 标注为 `documentation`、`source_inspection`、`community_report` 或 `provided_run_result`，并写清证据范围。来源彼此冲突时保留版本和条件差异。
- `eligibility` 按实际用途判断。依据足够时用 `eligible`，可通过具体准备任务解除关键未知时用 `conditional`，已核到必要条件不匹配时用 `excluded`，调查尚不足时用 `unassessed`。推荐其他用途时重新说明适用条件。
- `exec_chain` 写实际核到的入口、关键调用和配置。按用途填写训练、评测、数据或测量链，无关或未知项可留空并在报告说明。需要改造时写 `method_insertion_point`、要改的模块及是否影响核心方法。依赖、编译问题、接入及改造成本都写依据，机器耗时和显存未知时保留未知。

### 权重、数据与验证目标

- `weights.availability` 用 `unknown`、`listed`、`restricted`、`not_provided` 或 `reported_unavailable`。发布信息只支持 `listed`。本轮的下载、加载均标 `not_performed`，其他人或此前的运行结果记独立来源和条件。
- 写清权重身份、来源、配置、数据版本和划分。预处理、筛样规则、指标定义和聚合方式写入 `protocol` 或候选详情。版本或协议是否匹配用 `true`、`false` 或 `null`，同时给出依据。分别记录代码、权重和数据的条款。一个候选内若有不同资产配置，逐项写清身份，实际选择某套配置时把身份写入 `decision.components`。
- 社区报告应注明来源、日期、仓库版本、权重、数据、配置、指标和结果，说明适用范围与是否为重复转述。未查到相关记录时写搜索范围。
- `paper_metrics` 只存已核到的、与拟复现对象可比的论文结果。保留 `metric`、`value`、`dataset` 和 `source_page`，补充数值单位、划分、模型、权重、配置、预处理、聚合方式和表格行。没有合适论文参考值时保留空数组。
- `validation_targets` 每项写 `id`、`candidate_id`、`requirement_ids`、行为或指标、核验协议、参考依据与未知。参考可以是核过的论文结果、相同条件的发布结果或可检查的预期行为。若参考仍待确定，在记录中说明。角色字段只概括仓库用途，具体目标取决于实际协议和参考证据。

### 推荐、用户决定与下游读取范围

- `recommendation.status` 用 `recommended`、`needs_more_information` 或 `no_suitable_candidate`。`by_use` 逐用途写候选、关联需求、出处、推荐及替代方案取舍。条件推荐要说清哪项结果会改变建议。组合时在 `combination_checks` 记录组件及接口、版本、数据、指标协议或许可的匹配依据与未决项。
- `decision.status` 用 `pending`、`selected`、`declined` 或 `deferred`。用户实际确认后填写 `user_response`、理由、时间、获准和待确认的范围。`components` 逐项记录候选 ID、用途、版本、实际选定的权重、配置、数据和关联的验证目标。只批准准备验证时，把准备任务和条件列入 `approved_scope`，把后续正式实验列入 `pending_scope`。
- 当前 `code-project-setup` 用 `decision.repo` 定位主要仓库并读取同名候选，包括 `exec_chain`、`env_deps` 和 `key_risks`。它将 `decision.repo_role` 和 `paper_metrics` 传给 `code-paper-reproduction`。用户明确选定主仓库时填写 `primary_candidate_id` 和 `decision.repo`。实际用途可归纳为用于比较的基线或用于分析实验的仓库时，`repo_role` 分别用 `baseline` 或 `substrate`。尚未确认、没有主仓库或主用途无法归纳时，相应字段留空。
- 多组件、详细验证目标、批准范围和实测待办目前由接手方在报告和 clone 卡中逐项核对。交接时让接手方核对全部组件和条件。复现目标仍需核所选版本、配置、数据和实际参考结果。若报告、事实记录或批准文件跨机器尚未取得，标明缺项，取得后再引用。

### 自查、首批实测与修订

- `self_checks` 写清每项判断的状态（`clear`、`limited`、`needs_revision`）、依据、未知和对选型的影响。可引用报告已有内容。必要条件无法确定时，按影响补查或给出有限的准备建议。
- `verification_tasks` 每项写 `id`、`candidate_ids`、`requirement_ids`、`source_refs`、已知（`known`）、待测（`unknown`）、为何必须运行（`why_runtime`）、负责 skill（`owner`）、实际条件和观察方法（`check`）、继续标准（`continue_if`）、当前可做范围（`allowed_scope`）、前置任务（`depends_on`）、资源（`resources`）、状态（`status`）和失败返回点（`return_to`）。可静态补齐的来源留在调查缺口。未获准或前置缺失的任务标 `blocked` 并说明原因。调查阶段准备验证任务记录为待办或阻塞。
- `revisions` 记录实际发生的变化、时间、原判断、触发变化的证据及受影响组件。后续实测附来源和实际设置，供复查调查判断的变化。

## report.md

```markdown
# {目标} · 选型报告

> {调查日期、读取范围、版本与执行边界。本轮只核查资料，目标环境仍待实测。}
> 结构化记录见 [baseline-survey.json](baseline-survey.json)。

## 1. 本轮需要什么

{研究问题或复现目标，输入材料、当前批准范围、资源约束。}

| 需求 | 必要性与来源 | 为什么需要 | 不满足会影响哪项判断 |
| --- | --- | --- | --- |
| {R1 和具体条件} | {必要或偏好，出处和版本} | {当前用途} | {会改变的选择或测量意义} |

## 2. 搜索与候选范围

{实际查过的来源、查询和版本，纳入排除理由，仍可补查的材料或访问缺口。}

## 3. 按必要条件比较

| 候选及版本 | 用途 | 对必要条件的支持、不匹配或未知 | 证据位置 | 对选择的影响 |
| --- | --- | --- | --- | --- |
| {候选 ID、仓库及 commit} | {实际用途} | {按 R 编号逐项写} | {来源 ID 或事实记录} | {推荐、条件推荐、补查或排除} |

## 4. 候选详情、成本与风险

### {候选 ID 与固定版本}

- 调用关系 | {实际文件:函数 → 模型加载或处理 → 输出或评测。按需写训练、数据或测量链和配置。}
- 接入及改造 | {环境依赖、已知编译问题、扩展位置、需改哪些模块、是否影响核心方法、成本依据与未知。}
- 权重与数据 | {权重身份、来源、加载配置，数据版本、划分、来源和协议。注明已查到的访问方式及加载状态。}
- 许可与社区报告 | {分别列代码、权重、数据条款。社区结果附实际版本、条件和来源。}
- 对选型有影响的风险 | {触发条件、影响、证据，以及现在补查还是稍后实测。}
- 参考结果 | {数值、单位与口径、模型与资产、出处和可比范围。无适用参考时说明。}

## 5. 推荐、替代方案与用户决定

{按用途推荐、待补证或无合适候选。写清决定性证据、未选替代的理由、组合的条件与冲突。}
{核对必要条件是否均有出处或保留未知，以及关键未知会怎样改变建议。}
{用户实际答复和日期，获准的组件、版本、配置和任务，待确认事项。未确认时留待决定。}

## 6. 首批实测待办

| 任务与需求 | 已知、待测与为何需要运行 | 谁负责、前置条件与资源 | 对象、条件和如何观察 | 什么结果可以继续 | 不满足回哪里 |
| --- | --- | --- | --- | --- | --- |
| {任务 ID，R 编号及出处} | {静态证据和只能运行验证的未知} | {skill、依赖、许可和批准范围} | {设置、观察对象、要留的记录} | {具体判据和允许进入的下一步} | {返回位置和触发条件} |

## 7. Clone 卡（用户确认后填写）

| 组件及用途 | 仓库 URL 与确认版本 | 运行入口与配置 | 权重与数据身份、来源和访问条件 | 协议、参考结果和待验证风险 |
| --- | --- | --- | --- | --- |
| {每个已选组件单独一行} | {URL 与 commit 或 tag} | {候选入口，注明未验证部分} | {权重版本、数据版本及 split、许可或申请方式} | {只列适用参考，引用实测任务} |

- 当前交接 | {主要仓库、完整组件、交付文件及其路径，跨机器仍缺的材料。}
- 获准范围 | {现在可开始的任务及其条件。}
- 待确认事项 | {本次结果回来后才能决定的实验，汇报需带哪些证据。}

## 8. 修订与下一步

{新证据、原判断、变化依据和受影响组件。注明谁接手、需汇报什么、何时回到选型或取证设计。}
```

## 完整填写示例 · 单张视觉请求的 T0 基准核查

沿用[运行手册的 T0 交接示例](workflow.md#交接示例--单张视觉请求的基准核查)和[候选 A 的事实记录示例](fact-record-template.md#完整填写示例--单张计时和轨迹)。下列仓库、权重、数据、路径、日期和用户答复均为示例。仓库使用保留域名 `example.invalid`。

### 示例 baseline-survey.json

```json
{
  "schema_version": 2,
  "direction": "端侧视觉推理的计时与轨迹核查",
  "created_at": "2025-07-01T10:00:00+08:00",
  "updated_at": "2025-07-01T15:00:00+08:00",
  "intent": "选择用于 T0 的单张推理测量实现",
  "source_spec": "inputs/approved-spec.json",
  "source_plan": "inputs/approved-plan.json",
  "resource_constraint": "一台目标设备，批大小 1。实测耗时和存储用量待核。",
  "requirements": [
    { "id": "R1", "need": "测输入处理开始至分类结果返回的延迟", "mandatory": true, "rationale": "建立此任务单张请求的计时基准", "source_refs": ["S1"] },
    { "id": "R2", "need": "取得写回量和实际算子实现的轨迹", "mandatory": true, "rationale": "判断后续能否用轨迹开展机制取证", "source_refs": ["S1"] },
    { "id": "R3", "need": "使用约定的模型权重与验证集", "mandatory": true, "rationale": "固定模型和数据条件", "source_refs": ["S1"] }
  ],
  "search_scope": {
    "checked_at": "2025-07-01T10:00:00+08:00",
    "queries": ["在两份给定实现内查找单张入口、计时边界和轨迹配置"],
    "sources": ["S1", "S2", "S3", "S4", "S5"],
    "inclusion_reasons": ["A、B 均为上游列出的端侧运行时"],
    "exclusions": [],
    "limitations": ["只核两条给定线索，未扩展社区复现检索"]
  },
  "sources": [
    { "id": "S1", "kind": "provided_plan", "location": "inputs/approved-plan.json", "revision": "v1", "accessed_at": "2025-07-01T10:00:00+08:00", "read_scope": "T0 的目标、资产及 T1 确认范围" },
    { "id": "S2", "kind": "code", "location": "https://example.invalid/vision-a/tree/a17c9d2", "revision": "a17c9d2", "accessed_at": "2025-07-01T10:30:00+08:00", "read_scope": "tools/infer_one.py、configs/single_request.yaml、requirements.txt 和 README 的轨迹说明" },
    { "id": "S3", "kind": "release", "location": "https://example.invalid/vision-a/releases/r1", "revision": "r1", "accessed_at": "2025-07-01T11:00:00+08:00", "read_scope": "Vision-S 权重、Vision-Val v1/val 的配置及访问条件" },
    { "id": "S4", "kind": "code", "location": "https://example.invalid/vision-b/tree/b28d0e3", "revision": "b28d0e3", "accessed_at": "2025-07-01T11:30:00+08:00", "read_scope": "README、bench.py:profile_subgraph 和 configs/batch.yaml" },
    { "id": "S5", "kind": "license", "location": "https://example.invalid/vision-a/releases/r1/terms", "revision": "r1", "accessed_at": "2025-07-01T12:00:00+08:00", "read_scope": "代码、Vision-S 权重和 Vision-Val 数据分别的使用条款" }
  ],
  "paper_metrics": [],
  "validation_targets": [
    { "id": "V1", "candidate_id": "B1", "requirement_ids": ["R1", "R3"], "behavior_or_metric": "同条件单张推理与端到端延迟", "protocol": "目标设备、批大小 1，使用 Vision-S r1 和 Vision-Val v1/val，从处理输入到取得分类结果", "reference": "S1 的流程边界与资产要求，无适用论文数值", "source_refs": ["S1", "S2", "S3"], "unknowns": ["目标设备能否加载，计时边界和重复运行波动"] },
    { "id": "V2", "candidate_id": "B1", "requirement_ids": ["R2"], "behavior_or_metric": "轨迹包含写回量和实际算子，且可说明采集对计时的影响", "protocol": "V1 同一设置，分别开启和关闭采集", "reference": "S1 所需字段，S2 提供候选采集入口", "source_refs": ["S1", "S2"], "unknowns": ["目标设备上的字段、对应事件和计时偏差"] }
  ],
  "candidates": [
    {
      "id": "B1", "repo": "vision-a", "url": "https://example.invalid/vision-a",
      "revision": "a17c9d2", "revision_status": "resolved", "roles": ["measurement"],
      "repo_role": "substrate", "official": null, "official_source_refs": [],
      "research_fit": [
        { "requirement_id": "R1", "assessment": "supported_by_sources", "finding": "tools/infer_one.py:main 包含输入处理至分类结果返回的计时，configs/single_request.yaml 指定批大小 1", "basis_type": "source_inspection", "source_refs": ["S2"], "unverified": ["目标设备上的计时完整性和波动"], "effect_on_choice": "优先核验 A 的端到端入口" },
        { "requirement_id": "R2", "assessment": "unknown", "finding": "README 有轨迹接口说明。目标设备的输出字段待定位", "basis_type": "documentation", "source_refs": ["S2"], "unverified": ["写回量、实际算子及采集干扰"], "effect_on_choice": "影响 T1 是否能沿用此运行时" },
        { "requirement_id": "R3", "assessment": "supported_by_sources", "finding": "发布记录与单张配置指向 Vision-S r1 和 Vision-Val v1/val", "basis_type": "documentation", "source_refs": ["S1", "S2", "S3"], "unverified": ["下载、加载及实际读取划分"], "effect_on_choice": "资产及协议可定位，需在 T0 核验" }
      ],
      "exec_chain": { "train": null, "eval": "tools/infer_one.py:main → 读取单张配置 → 加载 Vision-S → 返回分类结果", "data": "configs/single_request.yaml → Vision-Val v1/val", "measurement": "tools/infer_one.py:main 的输入处理前和分类结果返回后的计时边界", "source_refs": ["S2"], "runtime_validated": false },
      "method_insertion_point": null,
      "env_deps": { "key_deps": "requirements.txt 列 Python 3.11 与 vision-runtime 1.4", "compile_landmines": null, "uncommon": "目标设备驱动与运行时的兼容性待核", "source_refs": ["S2"] },
      "weights": { "identity": "Vision-S", "url": "https://example.invalid/vision-a/releases/r1", "revision": "r1", "config": "configs/single_request.yaml", "availability": "listed", "aligns_code_version": true, "source_refs": ["S2", "S3"], "download_validation": "not_performed", "load_validation": "not_performed" },
      "dataset": { "identity": "Vision-Val", "url": "https://example.invalid/vision-a/releases/r1", "version": "v1", "split": "val", "protocol": "按单张配置执行输入处理，批大小 1", "aligns_paper": null, "source_refs": ["S1", "S2", "S3"], "runtime_validated": false },
      "licenses": {
        "code": { "terms": "MIT", "source_refs": ["S5"] },
        "weights": { "terms": "发布条款允许内部研究", "source_refs": ["S5"] },
        "data": { "terms": "研究组现有授权覆盖内部验证", "source_refs": ["S1", "S5"] },
        "use_constraints": ["仅在当前内部验证范围使用资产"], "unresolved": []
      },
      "community_reports": [],
      "build_cost": { "assessment": "unknown", "basis": "配置入口明确，目标设备兼容性尚待实测", "unknowns": ["驱动兼容性", "安装时间与存储用量"] },
      "adapt_cost": { "changes": [], "changes_core_method": false, "basis": "T0 先按现有配置检验", "unknowns": ["是否需另选轨迹采集方式"] },
      "eligibility": "conditional",
      "key_risks": ["轨迹可能缺所需字段，采集可能影响计时"]
    },
    {
      "id": "B2", "repo": "vision-b", "url": "https://example.invalid/vision-b",
      "revision": "b28d0e3", "revision_status": "resolved", "roles": ["measurement"],
      "repo_role": "substrate", "official": null, "official_source_refs": [],
      "research_fit": [
        { "requirement_id": "R1", "assessment": "mismatch", "finding": "README 声明支持推理计时，所核 bench.py:profile_subgraph 只记录批量子图耗时", "basis_type": "source_inspection", "source_refs": ["S4"], "unverified": ["其他入口是否支持单张端到端计时"], "effect_on_choice": "当前入口不适合 T0" },
        { "requirement_id": "R2", "assessment": "unknown", "finding": "所核入口只查到子图吞吐和耗时", "basis_type": "source_inspection", "source_refs": ["S4"], "unverified": ["写回量和实际算子实现的采集支持"], "effect_on_choice": "若重评 B 则补查可用的轨迹入口" },
        { "requirement_id": "R3", "assessment": "unknown", "finding": "configs/batch.yaml 有权重与数据配置，未查明其与要求资产是否同版", "basis_type": "source_inspection", "source_refs": ["S4"], "unverified": ["与目标权重和数据划分的匹配"], "effect_on_choice": "若找到合格计时入口再补查资产" }
      ],
      "exec_chain": { "train": null, "eval": "bench.py:profile_subgraph → 批量子图运行 → 输出吞吐和耗时", "data": "configs/batch.yaml", "measurement": "子图计时，不含完整输入至分类结果的边界", "source_refs": ["S4"], "runtime_validated": false },
      "method_insertion_point": null,
      "env_deps": { "key_deps": null, "compile_landmines": null, "uncommon": null, "source_refs": [] },
      "weights": { "identity": null, "url": null, "revision": null, "config": "configs/batch.yaml", "availability": "unknown", "aligns_code_version": null, "source_refs": ["S4"], "download_validation": "not_performed", "load_validation": "not_performed" },
      "dataset": { "identity": null, "url": null, "version": null, "split": null, "protocol": "所查入口为批量子图测试", "aligns_paper": null, "source_refs": ["S4"], "runtime_validated": false },
      "licenses": { "code": { "terms": null, "source_refs": [] }, "weights": { "terms": null, "source_refs": [] }, "data": { "terms": null, "source_refs": [] }, "use_constraints": [], "unresolved": ["因当前入口与 R1 不匹配，未继续核条款"] },
      "community_reports": [],
      "build_cost": { "assessment": "unknown", "basis": "未进入工程尽调", "unknowns": ["依赖与设备兼容性"] },
      "adapt_cost": { "changes": [], "changes_core_method": null, "basis": "尚未核到可用单张端到端入口", "unknowns": ["需要替换入口还是补写测量链"] },
      "eligibility": "excluded",
      "key_risks": ["当前核到的子图读数无法代表端到端延迟"]
    }
  ],
  "recommendation": {
    "status": "recommended",
    "by_use": [
      { "use": "T0 有限准备验证", "candidate_id": "B1", "requirement_ids": ["R1", "R2", "R3"], "reason": "A 可定位端到端入口与资产，轨迹留待实测", "source_refs": ["S1", "S2", "S3", "S4"], "alternative": "B2 已查入口只计批量子图" }
    ],
    "combination_checks": [],
    "repo": "vision-a",
    "reason": "A 更适合直接核验单张端到端计时",
    "limitations": ["T0 以确认入口和轨迹能力为目标。正式四组 T1 待讨论"]
  },
  "decision": {
    "status": "selected",
    "primary_candidate_id": "B1",
    "repo": "vision-a",
    "repo_role": "substrate",
    "components": [
      { "candidate_id": "B1", "roles": ["measurement"], "revision": "a17c9d2", "config": "configs/single_request.yaml", "weights": "Vision-S r1", "dataset": "Vision-Val v1/val", "validation_target_ids": ["V1", "V2"] }
    ],
    "reason": "核实当前设备是否具备后续取证所需的测量能力",
    "user_response": "先用 A 做 T0。四组实验等结果回来再决定。",
    "date": "2025-07-01",
    "approved_scope": ["T0：目标设备上按约定资产和批大小核入口、计时和轨迹"],
    "pending_scope": ["T1：正式四组实验及投入"],
    "conditions": ["只使用选定版本和资产，改变测量含义前回取证设计"]
  },
  "self_checks": {
    "requirements": [
      { "check": "用途和必要条件均可追溯", "status": "clear", "finding": "R1–R3 来自 T0 方案", "source_refs": ["S1"], "unknowns": [], "effect": "按 T0 的条件比较" }
    ],
    "recommendation": [
      { "check": "推荐边界与关键未知", "status": "limited", "finding": "A 的 R2 待实测，B 所查入口与 R1 不匹配", "source_refs": ["S2", "S4"], "unknowns": ["目标设备轨迹字段及干扰"], "effect": "仅建议准备性验证" }
    ]
  },
  "verification_tasks": [
    {
      "id": "VT1", "candidate_ids": ["B1"], "requirement_ids": ["R1", "R3"], "source_refs": ["S1", "S2", "S3"],
      "known": "候选入口、配置与两项资产有固定来源",
      "unknown": "实际能否加载约定资产、计时是否覆盖完整请求及读数波动",
      "why_runtime": "目标设备上的加载、计时输出和波动需执行确认",
      "owner": "code-project-setup",
      "check": "在目标设备上按固定版本、权重、划分和批大小 1 运行，核资产、起止边界，记录实际配置及重复读数",
      "continue_if": "资产匹配，单张请求稳定完成且计时覆盖完整请求，可以继续 VT2",
      "allowed_scope": "T0，保持选定版本和资产",
      "depends_on": [],
      "resources": "一台目标设备，耗时和存储待核",
      "status": "pending",
      "return_to": "先查版本、资产和配置。口径对不上则回 baseline-survey 核入口"
    },
    {
      "id": "VT2", "candidate_ids": ["B1"], "requirement_ids": ["R2"], "source_refs": ["S1", "S2"],
      "known": "仓库说明存在轨迹接口",
      "unknown": "写回量、实际算子可观测性及采集对计时的偏差",
      "why_runtime": "字段和采集干扰取决于目标设备与实际运行",
      "owner": "code-project-setup",
      "check": "同设置分别开启和关闭轨迹，记录字段、对应事件、原始输出、重复读数、波动和差异",
      "continue_if": "两项轨迹均可定位，且计时基准在约定协议下仍可用，可带证据回来讨论 T1",
      "allowed_scope": "T0，只核轨迹与基准计时",
      "depends_on": ["VT1"],
      "resources": "与 VT1 同一台目标设备",
      "status": "blocked",
      "return_to": "字段缺失或采集影响计时时记录限制并核替代入口。测量含义要变则回取证设计"
    }
  ],
  "revisions": []
}
```

### 示例 report.md（含 clone 卡）

```markdown
# 端侧视觉推理 · T0 选型报告

> 2025-07-01 核查用户提供的两条线索和已读版本。本轮调查只读取资料。
> 结构化记录见 [baseline-survey.json](baseline-survey.json)。

## 1. 本轮需要什么

从 inputs/approved-plan.json v1 核到本轮只做 T0。目标是确认一台目标设备能否测量单张请求的延迟，并提供后续取证所需的轨迹。正式四组 T1 实验待确认。

| 需求 | 为什么必要 | 不满足的影响 |
| --- | --- | --- |
| R1 批大小 1，计时从输入处理至分类结果 | 建立与研究问题对应的基准 | 子图或批量结果无法回答单张请求延迟 |
| R2 可观察写回量和实际算子实现 | 核实后续是否具备机制取证手段 | 轨迹缺项时需评估替代方式 |
| R3 使用 Vision-S r1 和 Vision-Val v1/val | 固定模型及数据条件 | 口径变化须先重新确认 |

## 2. 搜索与候选范围

在上游给定的 A、B 固定版本内搜索单张入口、计时和轨迹。已核 A 的推理配置、依赖及发布资产，B 读到 README、子图基准和批量配置。未搜索社区复现记录，B 的其他入口和资产条款未查，若 A 的 T0 无法成立再定向补查。

## 3. 按必要条件比较

| 候选 | R1 计时 | R2 轨迹 | R3 资产 |
| --- | --- | --- | --- |
| A · a17c9d2 | 源码可见单张端到端边界，目标设备待测（S2） | 文档有接口，字段和计时干扰待测（S2） | 资产和配置可定位，加载待测（S1–S3） |
| B · b28d0e3 | 所查入口测批量子图，与本轮条件不匹配（S4） | 所查入口输出吞吐和耗时，轨迹能力未知（S4） | 配置可见，具体权重和数据划分未核（S4） |

## 4. 候选详情、成本与风险

A 的 tools/infer_one.py:main 读取 configs/single_request.yaml，加载 Vision-S，完成输入处理并返回分类。计时边界在输入处理前和分类结果返回后。requirements.txt 列 Python 3.11 和 vision-runtime 1.4，设备驱动兼容性及存储、耗时待核。T0 使用现有配置，主要未知是能否采到指定字段，以及采集会怎样影响计时。详见 [单张推理与轨迹记录](facts/a-inference-and-trace.md)。

S3 定位 Vision-S r1 和 Vision-Val v1/val。代码为 MIT，权重允许内部研究，数据使用研究组已有授权（S1、S5）。资产尚待下载和加载。T0 核对实际行为和协议，本轮无适用的论文参考数值。

B 的 bench.py:profile_subgraph 使用批量配置，所查实现只计子图。要重新考虑 B，先定位覆盖完整请求的入口，再核对应资产和条款。

## 5. 推荐、替代方案与用户决定

建议先用 A 做 T0。与 B 相比，A 的完整请求计时有源码依据。若 A 无法取得可解释的轨迹或采集干扰使基准无法使用，需评估独立采集或重新比较运行时。

用户于 2025-07-01 确认先用 A 做 T0。范围限于目标设备上固定版本、权重和数据划分下的计时与轨迹核查。正式四组 T1 实验和投入待 T0 结果回来后决定。

## 6. 首批实测待办

| 任务 | 负责人及条件 | 观察和应保存的证据 | 继续或回退 |
| --- | --- | --- | --- |
| VT1 · R1/R3 | code-project-setup 用目标设备、A a17c9d2、Vision-S r1、Vision-Val v1/val，批大小 1 | 核实际加载及输入至分类结果边界，保存资产身份、配置、位置、重复读数和波动 | 资产匹配且取得稳定的全请求读数后做 VT2。口径不匹配先核版本与配置，仍有偏差则回选型 |
| VT2 · R2 | code-project-setup 完成 VT1 后在同设置开启和关闭轨迹 | 保存写回量、实际算子字段、事件位置、原始输出、重复读数及偏差 | 两项均可定位且计时基准在约定协议下仍可用时，带证据讨论 T1。字段缺失或干扰计时，核替代入口。若改变测量含义，回取证设计 |

## 7. Clone 卡

| 组件及用途 | 仓库与版本 | 候选入口和配置 | 权重、数据和访问 | 待验证风险 |
| --- | --- | --- | --- | --- |
| A，T0 测量实现 | https://example.invalid/vision-a · a17c9d2 | tools/infer_one.py:main，configs/single_request.yaml，批大小 1 | S3 发布页，Vision-S r1 与 Vision-Val v1/val，按 S5 内部研究条款 | VT1 核加载和完整请求延迟，VT2 核轨迹字段与采集影响 |

- 当前交接 | 主要仓库 vision-a。随报告提供 baseline-survey.json、事实记录和批准计划。
- 获准范围 | 仅执行 VT1 及符合前置条件的 VT2。
- 待确认事项 | T1 的四组对照、条件及预算。回传实际设置、运行入口、端到端读数、波动、耗时、轨迹字段与采集偏差。

## 8. 修订与下一步

当前无修订。由 code-project-setup 回传 T0 的证据，再讨论是否推进 T1。后续如需核对独立的参考结果，提供所选版本和可比协议给 code-paper-reproduction。
```
