# 研究、代码与 W&B 运行的共同记录

本文件说明怎样把每次实验尝试与实际 W&B run 对齐，核实同步到了哪些记录，并保存可供复查和跨机器交接的证据。

本约定适用于启用 W&B 的代码实验。研究问题、批准设计、运行结果和证据判断仍保存在各自的本地记录里。历史记录按实际来源查证。人工推导直接保留推导记录。

## 1. 启动前登记身份和实际来源

1. **核本轮实际项目。** 从 setup 的 `tracking_ref` 或项目的 [自托管配置](deployment.md) 取实例地址、entity 和 project，确认实际执行进程使用同一实例。上传范围按项目已有约定。保存配置、快照和日志时核其中的凭证及敏感信息。
2. **为本次启动分配身份。** 从[实验元记录](../../code-idea-execution/references/experiment-meta-template.json)取实验、批准版本和重复编号。执行前登记唯一的 `attempt_id`、预分配 W&B run ID 和本次输出目录。重复编号按设计确定。一次重试或恢复沿用原重复编号。
3. **固定实际来源。** 保存本次设计副本、生效配置、实际 Git commit 和相关 diff。记录真实的数据、模型、设备和测量协议。计算设计、配置及适用 diff 的 SHA-256。各次尝试引用当时实际使用的文件。使用公共字段时保留其原值，后续变化写进对应的尝试和偏差记录，附实际批准依据。
4. **核 SDK 初始化参数。** SDK 的 `config.dl_assistant` 保存本次 `wandb.identity`，并加入 `scope_id`、`research_round`、`hypothesis_ids`，与本地完全一致。`config_sha256` 指向实际生效配置副本，将 run ID 单独记录。分布式任务按实际框架由主进程记录。确需记录各 rank 时，标明其所属尝试和 rank。

| 对象 | 用什么来定位 |
| --- | --- |
| 项目和 W&B run | 用 `base_url`、`entity`、`project`、`run_id` 共同定位 |
| 研究轮次、复现或论文批次 | 用 `research_round` 或 `scope_id` 关联上游记录，同时保留实际代码版本和批准设计 |
| 实验、重复与尝试 | 用 `experiment_id`、`replicate_id`、`attempt_id` 关联本地记录。各次实际启动默认有独立 run ID |
| 实际来源 | 用 Git 版本及 diff、设计和生效配置的引用、真实的模型和数据、执行及测量协议定位。展示用的 name、group 和 tags 用于浏览 |

### 元记录中的 W&B 字段

下面是虚构训练示例中第二次尝试的节选。实际填写时替换所有身份和摘要，其他实验字段按元记录模板保留。

```json
{
  "tracking": {
    "provider": "wandb",
    "base_url": "http://wandb.internal:8080",
    "entity": "research",
    "project": "edge-training",
    "scope_id": "v1-edge-training",
    "research_round": "v1-edge-training",
    "hypothesis_ids": ["H1"]
  },
  "design_record": {"path": "design.json"},
  "attempts": [{
    "attempt_id": "attempt-02",
    "replicate_id": "replicate-01",
    "retry_of": null,
    "resume_from": "attempt-01",
    "git_commit": "c91b7e4",
    "code_dirty": false,
    "configuration_ref": {
      "path": "runs/attempt-02/config.json",
      "sha256": "<该尝试配置副本的SHA-256>"
    },
    "wandb": {
      "run_id": "edge-a2",
      "sync_status": "pending",
      "local_dir": "runs/attempt-02/wandb",
      "reason": "等待按指定范围独立查回",
      "identity": {
        "experiment_id": "exp-007-train",
        "replicate_id": "replicate-01",
        "attempt_id": "attempt-02",
        "design_sha256": "<design.json的SHA-256>",
        "git_commit": "c91b7e4",
        "code_diff_sha256": null,
        "config_sha256": "<该尝试配置副本的SHA-256>",
        "data_refs": ["数据 train-v1 的固定清单，见运行记录"],
        "model_refs": ["attempt-01 的 step-1200 checkpoint，见运行记录"],
        "protocol_ref": "批准设计 v1 的训练及评测协议",
        "resume_from_attempt": "attempt-01"
      },
      "snapshot_ref": null
    }
  }]
}
```

`configuration_ref` 和 `snapshot_ref` 使用 `{path, sha256}`，路径从实验目录起算并留在该目录内。`design_sha256` 对应实际保存的设计文件。代码有未提交变更时，保存实际 diff 并填入其摘要。各模型、checkpoint 和数据引用写实际版本、可取得位置和校验依据，未知项写明影响。

## 2. 运行、重试和恢复分别记录

| 情况 | 本地怎样记 | W&B 怎样记 |
| --- | --- | --- |
| 首次启动或新的独立重复 | 按批准设计用对应的 `replicate_id`，另建 `attempt_id` 并保存实际命令及配置 | 分配本次独立 run ID，关联实际代码和配置 |
| 失败后从头重试 | 沿用原 `replicate_id`，另建尝试，用 `retry_of` 引用失败尝试，记录原因 | 登记新的 run ID。旧尝试的日志、状态和 run 身份保留 |
| 从 checkpoint 恢复 | 沿用原 `replicate_id`，用 `resume_from` 指向同一重复的较早尝试。写 checkpoint 路径、版本及实际恢复的模型、优化器、调度和随机状态 | 默认新建 run ID，`identity.resume_from_attempt` 与 `resume_from` 一致。若项目另有续接原 run 的约定，按其可核的方式记录 |

每次执行后，用实际进程状态、退出码和产物更新本地尝试。上传或查询有问题时，保留本地原始结果、已分配的 run ID 和日志目录。按 [部署与故障处理说明](deployment.md#sdk-地址和故障处理)处理离线和补同步。已经取得本地结果时，用它们恢复记录或补同步。

本地文件和身份可用以下命令核对。将两个变量分别设为实际 W&B skill 目录及本实验元记录路径。

```bash
python3 "$wandb_skill_dir/scripts/check_tracking.py" --meta "$experiment_meta"
```

[本地检查器](../scripts/check_tracking.py)核声明的身份、文件摘要和快照结构，同一元记录的重复 run ID，以及 `resume_from` 是否指向同一重复的较早尝试。它继承元记录中没有被尝试覆盖的 `git_commit`、`code_dirty`、`code_diff_path` 和 `configuration_ref`，并用该元记录的 `design_record.path` 核设计摘要。`retry_of`、多份元记录间的 run 身份和实际来源由实验记录另行核对。输出 `PASS` 表示本地声明通过。`SKIP` 表示未声明追踪。

## 3. 独立查回已同步的范围

**执行状态、同步状态和研究证据分别判断。** 运行结束后先核本地结果，再按实例、entity、project 和 run ID，用项目已验证的 API 或 MCP 独立查询。读取实际返回的 `config.dl_assistant`、所需指标和装载的产物记录，核身份、字段、步数、单位和覆盖范围。查回的结果缺页、重试或缺时间段时，记实际覆盖及影响。再对照获批测量条件，判断这些读数可以支持什么。

| `sync_status` | 怎样确认和记录 |
| --- | --- |
| `pending` | 上传或独立查回尚未完成。只查到部分结果、尚未达到本次需核范围时，保存已查快照、缺失区间和后续动作 |
| `offline` | 实际采用离线记录，保留本地目录和原因。补同步前核实例、项目、run 身份及已存在记录 |
| `failed` | 同步操作失败。保存本地目录、错误和可取得的原始结果，另记进程的实际退出情况 |
| `unknown` | 远端不可查或当前权限下无法确认。保存原因和待查范围 |
| `not_created` | SDK 初始化失败。留预分配 run ID、实际日志或恢复目录和初始化失败原因 |
| `synced` | 已独立查回并核实本次需用的字段和区间，保存快照与摘要。后续可使用的范围以快照中的实际覆盖为准 |

已查回快照至少包含 `schema_version: 1`、`base_url`、`entity`、`project`、`run_id`、`queried_at`、`query`、`coverage`、查询返回的 `config.dl_assistant`、`summary` 及所需历史或产物引用。查询记录写字段、step 范围、分页和采样条件。保留实际返回和按实际需要使用的转换脚本。运行仍写入时用查询时间和实际 step 冻结本次观察范围。

分析时从本地台账列出所有相关尝试，查这一范围内的缺失运行、失败、未同步或条件变化。正式统计使用有明确重复集合、纳入规则和计算方法的原始读数。查询快照可用来核对这些来源。科学判断仍按获批实验的比较与分析规则。

## 4. 交接时保留可取得的证据

- **给出能复跑和能读回的材料。** 保存实际代码版本及 diff、批准设计、生效配置、命令、本地日志和关键结果，以及各次尝试的完整 run 身份、查询快照和摘要。远程 checkpoint 或 Artifact 给出固定版本、digest 和可取得位置。论文结果同时保留指标字段、单位、step/选择规则、重复与排除、计算脚本及输出。
- **交代接收端缺哪些材料。** 未同步的尝试在源机器保留 `local_dir`。跨机交接未复制整个恢复目录时，在 `wandb.recovery_ref` 记录原始绝对路径、`availability`（`accessible`、`unavailable` 或 `not_checked`）及原因，小型设计、配置、diff 和所需快照应可取得。接收端包检查缺恢复目录时记 `UNCHECKED`、退出 3。补同步回到实际可读的来源核对。执行状态和同步状态继续按各自证据记录。

### 示例 · 一次训练重复从失败到查回

以下为启用 W&B 的虚构训练实验 `exp-007-train`，三个时点都属于同一独立重复 `replicate-01`。

| 时点 | 本地执行记录 | W&B 及证据状态 |
| --- | --- | --- |
| 第一次尝试失败 | `attempt-01` 非零退出，日志和 step 1200 的 checkpoint 已保存 | `edge-a1` 的远端状态无法核实，记 `unknown` 并保存本地记录，作为失败尝试留在台账 |
| 恢复后运行完成 | `attempt-02` 从 `attempt-01` 的 checkpoint 恢复，记录加载验证以及模型、优化器、调度和随机状态实际恢复的部分。完成后退出码 0，结果保存在当前尝试目录 | 新 run 为 `edge-a2`。独立查回尚未完成，仍为 `pending`。本地指标按实际结果保存 |
| 独立查询后交接 | 从已登记的命令、配置、日志及指标定位恢复段，核恢复位置和最终评测读数 | 按完整身份查回恢复后 step 1201–2000 的所需指标和最终评测摘要，核源配置，保存带 SHA-256 的查询快照。仅将 `edge-a2` 的已核范围记为 `synced`，`edge-a1` 和早期曲线的缺项单列 |

交接提供两个尝试的 run 身份、实际命令和配置、本地日志和结果、恢复证据、查询字段与步数范围，以及仍待补的记录。两次启动作为同一次重复解释。

## setup 与 reproduction 的映射

- **Setup。** `setup.json.tracking_ref` 指向非敏感项目配置。按 `operations` 和 `checks` 保存 SDK 写入、独立查询、指标和 step、分布式记录、实际上传范围及故障策略的测试证据。注明小样例的实际覆盖和仍待验证的正式参数。
- **Reproduction。** `reproduction.json` 用同一 `tracking_ref`。各 `runs` 绑定实际 `attempt_id`、`replicate_id` 和 W&B 记录。`identity.experiment_id` 对应复现的 `target_id`，`scope_id` 对应该份复现记录的身份。协议、代码和适用范围保留在复现记录。复现无研究论点时，`hypothesis_ids` 留空，`research_round` 可留空。对照实际发布权重和已验证入口时，从复现记录及实际读回核证据。
