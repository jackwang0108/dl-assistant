# 研究、代码与 W&B 运行的共同记录

本约定对新增、启用 W&B 的代码实验适用；不迁移历史数据，不为人工推导伪造 run。研究问题/假设和批准记录仍由原 skill 生成，W&B 不另维护可覆盖它们的研究状态文件。

## 身份与职责

| 对象 | 身份与来源 | W&B 中的关联 |
| --- | --- | --- |
| 项目 | 项目文件和自托管实例配置 | base_url + entity + project，不仅 project 名 |
| 研究轮次 | `ideas/v<N>-<slug>/` 与批准设计 | research_round，不能用它替代代码版本 |
| 复现/论文批次 | reproduction 记录或 batch_id | scope_id，复现可为该次报告的唯一 ID，无 idea 轮次可 null |
| 问题/假设 | 原 ID 与版本化设计 | 在 config 保存关联，不自动生成 supported 标签 |
| 实验 | 原 experiment_id / exp_id | 同一实验的多 seed/重复/尝试都可检索 |
| 重复 | replicate_id，seed 可为 null | 重试不是新重复；同 seed 也不自动是同一个重复 |
| 尝试 | attempt_id，运行前登记 | 默认独立 run ID，重启/恢复另记来源 |
| 实际来源 | commit+diff、解析配置、模型/数据/协议身份 | config 保存摘要和内容校验；必要小文件作产物 |

group/name/tags/job_type 可用于展示，不作唯一身份和科学判断。恢复自 checkpoint 时记录 checkpoint 校验/路径和训练状态恢复范围，W&B 日志续接不等于模型/优化器/随机性恢复。分布式训练按实际框架在主进程记录，若确需 rank 独立诊断，则记录 parent/rank，汇总不能当独立 seed。

## meta 的附加字段

原 meta schema_version=2 保持，增加可选 tracking；新启用项目的每个代码 attempt 必须有对应 wandb 字段。旧无 tracking 的 meta 沿用原检查，不代表 W&B 已验证。服务不可达的尝试也入账，不能删掉以通过检查。

```json
{
  "tracking": {
    "provider": "wandb",
    "base_url": "http://wandb.internal:8080",
    "entity": "team",
    "project": "audio-study",
    "scope_id": "research-v3",
    "research_round": "v3",
    "hypothesis_ids": ["H2"]
  },
  "attempts": [{
    "attempt_id": "attempt-02",
    "replicate_id": "seed-0",
    "resume_from": "attempt-01",
    "git_commit": "本次实际commit",
    "code_dirty": false,
    "configuration_ref": {"path": "runs/attempt-02/config.json", "sha256": "解析后配置文件的SHA256"},
    "wandb": {
      "run_id": "实际预分配ID",
      "sync_status": "pending",
      "local_dir": "runs/attempt-02/wandb",
      "reason": "等待服务恢复后补同步",
      "identity": {
        "experiment_id": "exp-007-compare",
        "replicate_id": "seed-0",
        "attempt_id": "attempt-02",
        "design_sha256": "设计副本的SHA256",
        "git_commit": "本次实际commit",
        "code_diff_sha256": null,
        "config_sha256": "解析后配置文件的SHA256",
        "data_refs": [],
        "model_refs": [],
        "protocol_ref": "实际协议版本引用",
        "resume_from_attempt": "attempt-01"
      },
      "snapshot_ref": null
    }
  }]
}
```

只展示新增字段，不是完整可运行 meta。design_sha256 对应 meta.design_record.path 的真实内容；snapshot_ref 用 `{path,sha256}`，相对实验目录且不可越界。synced 必须有独立读回保存的快照，不因 SDK finish 返回就填 synced。identity 在启动时固定，不把旧 attempt 的实际代码/config 改成最后一次；identity 保留原始值，各 attempt 可因记录过的调整具有不同来源。

每个attempt记录自己的实际来源；没有覆盖字段时，检查器继承meta的git_commit、code_dirty、code_diff_path和configuration_ref。configuration_ref为实验目录内解析配置副本的`{path,sha256}`，实际内容与identity.config_sha256必须相符；dirty代码还须保存实际diff并核其SHA256。相对本轮基准的来源调整保留deviation_ref及实际批准依据，不把旧attempt改指最新文件。检查器核本地文件一致性，不证明该文件确实用于远端运行，也不认证批准真实性。缺失历史配置不补造，保留待核查限制。

源服务器检查未同步attempt时，local_dir必须存在。跨机器交接不强制搬运整个W&B恢复目录；小型配置、设计、diff及已声明synced的读回快照仍须随包取得。未复制的恢复目录保留local_dir，并在wandb.recovery_ref记录原始绝对path、availability（accessible/unavailable/not_checked）及reason。包检查在接收端找不到该目录时标UNCHECKED、退出3，不改执行状态或sync_status，也不声称恢复已验证。local_dir只是目录存在检查，不能证明日志完整；补同步必须回到实际可访问的来源核查。

SDK `wandb.init(config=...)` 的 `config.dl_assistant` 保存本例 identity，以及 tracking 的 scope_id、research_round、hypothesis_ids；它们应与本地完全一致。checkpoint、data_refs、model_refs 按真实版本/校验和实际可访问位置记录，未知或不适用说明原因，不用空列表掩盖缺失。config_sha256 指向不含凭证的实际解析配置，而不是包含 run ID 的递归自引用文件。

sync_status：
- pending：尚待同步/读回，含正在记录，保留本地目录。
- offline：主动离线记录，保留本地目录与原因，MCP 暂不可查。
- failed：同步失败，保留本地目录和原因；不改变训练退出状态。
- unknown：无法核实远端，保留本地目录和原因。
- not_created：SDK 初始化失败，仍记录预分配 run ID、本地日志目录与原因。
- synced：独立读取到所需记录并核对，保存快照。它只描述快照的字段/范围，不表示全部历史/产物均上传。

每个 attempt 都有预分配 run ID，同一 meta 内不能让两个 attempt 共用同一 run ID。实例 + entity + project + run_id 是跨项目完整身份，台账汇总时也查重；本地检查器只核当前 meta，不证明全项目无重复。特殊续接原 run 须另有明确记录策略和验证，不用默认格式掩盖多次启动。

## 查询快照和论文来源

synced 的最小快照：schema_version=1、base_url、entity、project、run_id、queried_at、query（实际字段、step 范围、采样/分页等参数）、coverage（实际覆盖和限制）、config.dl_assistant（读回身份）、summary 和所需历史/产物引用。将原始返回和转换脚本一并保存，不能手工拼出期望 config 当读回证据。结构检查器只能核本地快照的内容和哈希，无法证明其来自远端。

iterate 先从全部台账构造应查运行集合，查缺项/未同步/失败和配置差异，再按批准设计分析。多次查询记录时间，运行仍在写入时固定已观测的范围；分页/抽样可能遗漏尖峰或后续数据，不能称完整曲线。正式均值/方差等用明确原始读数、重复集合和分析脚本，不用 UI 自动平滑曲线或只有最优值的 summary 代替。

论文与交接包保留实例/run 全身份、checkpoint/Artifact 精确版本和 digest、查询快照及哈希、指标字段、step/选择规则、单位、重复/排除、计算脚本与输出。Mutable alias 和链接可作方便入口，但不能是唯一来源。需要远端服务才能取到的资产明确可访问性、备份及缺失风险；本地快照/关键数字随原数据包传递，不能只放一个网页 URL。

## setup 与 reproduction 的映射

setup 的 setup.json 增加 tracking_ref 指向项目 tracking.json，W&B 最小检查作为普通 operations/checks，保存真实测试 run 和日志；没有执行部署就保持 not_checked/blocked。初始化、指标 step/单位、分布式重复写入、凭证/资产上传范围及失败降级都纳入检查。正式参数与小样例检查分开。

reproduction.json 顶层引用相同 tracking_ref；runs 每项作为独立尝试，保存 attempt_id、replicate_id 和 wandb 字段，identity.experiment_id 对应 target_id，scope_id 对应该份复现记录的唯一标识。协议/代码/条件仍用原字段记录，不能用 W&B config 替代。复现不强制建立 ideas 节点；无相关假设则 hypothesis_ids 为空。现有 meta 检查器不直接检查 reproduction 格式，复现自查需对照此约定和实际读回。
