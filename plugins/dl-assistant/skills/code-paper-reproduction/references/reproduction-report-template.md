# Reproduction 交付模板（code-paper-reproduction）

> reproduction 的交付是一个**目录** `docs/code-paper-reproduction/<repo>-<日期>/`（固定路径，不问用户），含：
> - `spec.md` — 复现规格（Step 2 产出，用户审过；模板见 `reproduction-spec-template.md`）
> - `reproduction.json` — **供下游技能读取的记录**（下游 execution / CIP 直接消费，报告与 JSON 同步）
> - `report.md` — 供用户阅读的报告，Spec 确认后建立，每项验证完及时更新
> - `runs/<run-slug>/` — 各 run 的 log / EXIT_CODE / metrics / 训练曲线（run-slug：eval / dev-full / scaled-b / trend-a / sweep-<档位> / reduced）
> - `alignment.md` — 论文 vs repo vs setup 对齐核对 + trust-traps 排查底稿
>
> 机读区单独拆 `reproduction.json`（和 `setup.json` / `baseline-survey.json` 一致），`report.md` 是人读叙事。
> 技术术语保留，整体中文。run 产物路径用**目录内相对路径**。

---

## reproduction.json（供下游技能读取的记录）

> 下游 `code-idea-prepare` / `code-reading` / `code-idea-execution` 直接读这一份。字段名稳定、值要真（验证过才填，查不到标 unknown，不编数字）。json 写不下注释，字段含义统一在模板下方的「字段说明」讲。

```json
{
  "inherits": {
    "setup_report": "docs/code-project-setup/<repo>-<日期>/setup.json",
    "conda_env": "<env-name>",
    "repo": { "commit": "<sha>", "branch": "<branch>" }
  },

  "idea_kind": "needs_retraining",
  "repo_role": "baseline | substrate（对打 baseline / 实验基座——baseline-survey clone 卡标，经 setup.json 透传）",
  "repro_strategy": "dev_full",

  "eval_判定": "reproduced",
  "training_判定": "full_reproduced",
  "trustworthy_for_delta": true,
  "evidence_strength": "high",
  "full_scale_alignment": "done",

  "target": {
    "paper": "<paper title / arxiv id>",
    "table_row": "Table 3, row 'baseline R50'",
    "dataset": "<dataset> / <split: val|test>",
    "metric": "mAP@[.5:.95] (pycocotools 官方 eval)",
    "paper_number": 41.2,
    "tolerance_band": "±0.5",
    "eval_reproduced": 41.0,
    "eval_in_band": true,
    "training_reproduced": 40.8,
    "training_in_band": true,
    "scaled_small_setting": "R18 @ 1x on COCO-mini (论文 Table 7)",
    "scaled_trend_ok": true,
    "frozen": true
  },

  "frozen_components": ["eval 协议", "metric 实现", "数据 split", "official checkpoint 血缘"],
  "mutable_components": ["loss", "架构", "数据增强", "优化器"],

  "noise_floor": {
    "metric": "mAP@[.5:.95]",
    "seeds": [42, 43, 44],
    "values": [40.8, 41.0, 40.7],
    "std": 0.15,
    "verdict_rule": "execution 的 delta < 2×std 时不可判 keep/discard"
  },

  "ready_commands": {
    "eval": "python tools/test.py configs/xxx.py ckpts/xxx.pth --eval bbox",
    "train": "python tools/train.py configs/xxx.py",
    "train_scaled": "python tools/train.py configs/xxx_r18_coco-mini.py"
  },

  "artifacts": {
    "eval": { "log": "runs/eval/run.log", "metrics": "runs/eval/metrics.json", "exit": "runs/eval/EXIT_CODE" },
    "dev_full": { "log": "runs/dev-full/run.log", "metrics": "runs/dev-full/metrics.json", "exit": "runs/dev-full/EXIT_CODE", "work_dir": "/server/path/to/work_dir" },
    "alignment": "alignment.md"
  },

  "baseline_curves": {
    "loss": "runs/dev-full/loss_curve.png",
    "metric": "runs/dev-full/metric_curve.png",
    "prediction_dynamics": "runs/dev-full/pred_dynamics/"
  },

  "checkpoint": {
    "<name>": { "path": "/ckpts/<file>.pth", "kind": "raw (非 EMA)", "select": "best", "strict_load": "strict=True 全 key", "source": "<url>" }
  },

  "reproduced_baseline_checkpoint": {
    "path": "/ckpts/reproduced_baseline.pth",
    "seed": 42,
    "config": "configs/xxx.py",
    "note": "execution 微调从这切，不从 official ckpt 切"
  },

  "training_chain": {
    "bn": "SyncBN (论文多卡同步；开发卡用 b 小 setting 补统计差)",
    "loss_reduction": "mean",
    "effective_batch": "论文 16 (8卡×2)；复现 16 (1卡×2×accum8)",
    "lr_scaling": "linear, base 0.02 @ bs16；warmup 500 iter"
  },

  "determinism": {
    "seeds": [42, 43, 44],
    "cudnn": { "deterministic": true, "benchmark": false },
    "worker_seed_fixed": true
  },

  "dev_card_footprint": {
    "card": "1×A100 40GB",
    "eval": { "mem_peak": "12GB/40GB", "time": "8min full val" },
    "train": { "mem_peak": "34GB/40GB", "time": "~14h full / ~40min 小setting" }
  },

  "known_pitfalls": [
    "本 repo 的 mAP 自实现与 pycocotools 差 0.4 个点——已统一用官方库 eval",
    "official ckpt 是 EMA 权重，execution 对比实验注意血缘"
  ],

  "blocked": [
    "full 规模多 seed/多数据集铺开: 未做（投稿级实验，归运行服务器；本 skill 只验训练链可信）"
  ],

  "reduced_setting": {
    "enabled": true,
    "scale_method": {
      "data": "各数据集等比采样（seed=42 固定抽样；档位按 wall-clock 标定，见 scale_sweep）",
      "schedule": "保持原文 100 epoch 计划（iteration 锚定项已换算，EMA 窗口按 iter 数等比调）"
    },
    "baseline_result": { "metric": "AP", "value": 72.3, "std": 0.2 },
    "scale_sweep": {
      "axis": "data（唯一缩减轴，模型容量不动）",
      "points": [
        { "data": "3%", "wall_clock": "12min", "value": 61.2 },
        { "data": "10%", "wall_clock": "40min", "value": 67.8 },
        { "data": "30%", "wall_clock": "2.5h", "value": 72.3 }
      ],
      "fit": "log-log 幂律（前 3 点拟合）",
      "holdout": { "data": "60%", "wall_clock": "4h", "predicted": 74.8, "actual": 74.5, "tolerance": "±0.5（跑前写死）", "hit": true },
      "verdict": "scaling_law_confirmed"
    },
    "noise_floor": { "metric": "AP", "std": 0.2, "calibration": "论文消融 -backbone 在 reduced 上 -1.8 AP（同向）；±0.4 以内视为噪声" },
    "config": "configs/xxx_reduced.py",
    "command": "bash scripts/train_reduced.sh",
    "footprint": { "time": "2.5h", "gpu_memory": "10GB" },
    "validity_check": { "method": "ablation_contrast", "evidence": "论文消融 -backbone 在 reduced 上 -1.8 AP，方向一致", "confidence": "medium" }
  }
}
```

### 字段说明

- **`inherits`**：使用的 setup 文件路径+ conda env + repo commit/branch——可回溯到具体环境状态。
- **`idea_kind`**：`training_free` | `needs_retraining`。**`repro_strategy`**：`eval_only` | `dev_full` | `scaled_b_plus_a`。所有分支都先用官方 checkpoint 跑评测。`eval_only` 在评测验证完成后结束，`dev_full` 继续在开发卡上进行全量训练，`scaled_b_plus_a` 继续做小规模完整复现和大规模短训趋势验证。
- **推理评测和训练复现的判定**：`eval_判定` ∈ `reproduced` | `partially_reproduced` | `not_reproduced_diagnosable` | `not_trustworthy`；`training_判定` ∈ `NA`(training-free) | `full_reproduced` | `b_plus_a_confirmed` | `partial` | `blocked_需运行卡` | `not_trustworthy`。`trustworthy_for_delta` 是总判断：training-free 看 eval_判定，要重训看 training_判定。
- **`evidence_strength`**：`high`（full 对齐）| `medium`（b+a）| `low`（组件级 + 旁证）——各项验证能支持的结论落到哪级写哪级。**`full_scale_alignment`**：`done` | `deferred_to_running_server`；deferred 时数值对齐归 `code-paper-experiment`，execution 的 delta 带着这个风险认知。
- **`target`**：指标契约的冻结块——metric 写精确定义（`mAP@[.5:.95] (pycocotools 官方 eval)`，不只写名字，trust-traps ①）；`table_row` 明确并固定哪行哪 setting（trust-traps ⑤）；`tolerance_band` 说明是论文自报还是默认；`scaled_*` 仅 `scaled_b_plus_a` 填；**`frozen: true` 表示已冻结，下游改口径 = 语义改动即停**。
- **`frozen_components` / `mutable_components`**：execution 的迭代边界——frozen 动了就破坏与论文基线的可比性（harness 只读），mutable 是 method 迭代空间。
- **`noise_floor`**：同配置跨 seed std，execution keep/discard 的判据来源；分流 B/C 训练侧默认 ≥2-3 seed（full 太贵时至少 2 个并在报告写明）。
- **`ready_commands`**：验证过的可运行入口；`train_scaled` 仅 scaled_b 填。
- **`artifacts`**：各 run 产物（目录内相对路径；恢复入口 + 审计依据）；scaled_b / trend_a / reduced 按实际分流填，不存在的省略。
- **`baseline_curves`**：baseline 训练参照曲线（loss / metric / 固定批预测演变）——execution 每版改动对照曲线形状，判"训崩了还是方法不行"。
- **`checkpoint`**：official checkpoint 的训练来源与版本（trust-traps ③，execution 要知道站在哪版权重上）。**`reproduced_baseline_checkpoint`**：本 skill 自己重训出的 baseline ckpt——execution 微调从这切。
- **`training_chain`**：重训对齐清单（trust-traps ⑦ 落地）——execution 重训时要对齐 BN / loss 归约 / 等效 batch / lr 缩放。
- **`determinism`**：seed 列表 / cudnn 实际设置 / worker seed 固定否（静态设置继承 setup.json `reproducibility` 块，复现时确认）。
- **`known_pitfalls`**：复现排查中发现的已知问题，execution 必须读取。
- **`blocked`**：没做的 / 做不了的，下游要知道边界。
- **`reduced_setting`**：要重训且 full 超迭代预算（默认 2-3h、上限 4h）时默认建；training-free 或 full 本就在预算内则整块省略——字段见 `reduced-setting.md`「交付格式」。**只减少训练数据量**（模型容量不动，动容量 = 改 baseline 语义），根据实测耗时选择数据规模；`scale_sweep` 存 scaling 验证链（各点数字 / 拟合 / 留出的较大规模的预测值与实测值 / verdict），`verdict: degraded` 时 execution 只排方向。

---

## report.md（供用户阅读并随验证进度更新）

> **spec 确认后即建立，随验证逐节回填**——每个验证节当场写「目的 / 做了什么 / 预期结果 / 实际结果（实测值）/ 是否成功」，不留到最后补写。机读在 `reproduction.json`，本份**不重复 json 里的数字**，只叙事 + 指向 json / runs / alignment。

````markdown
# Reproduction Report: <repo-name>

> 由 code-paper-reproduction 在开发服务器产出。已对齐论文/repo/checkpoint/metric，按分流验证，落推理和评测验证与训练复现验证的结论。
> 机读在 reproduction.json；本份是人读叙事。

## 0. 推理和评测验证、训练复现验证结论（Step 6 定稿，建立时先占位）
- eval_判定 / training_判定 / trustworthy_for_delta / 证据强度 / full_scale_alignment / 能否开始 method 修改（能 / 先解决 X / 不建议基于此 repo 重训）。

## 1. 复现目标与分流（Step 2 定稿）
- 论文 / 目标行 / 数据集 split（确认 val 还是 test）/ metric 精确定义 / 论文数 + 容差范围。
- idea 类型 / 训练规模估算 / 选定分流及理由 / scaled 的小 setting（若有）。

## 2. 继承来源（Step 1 填）
- 吃的哪份 setup / 继承了什么（env/commit/ready 命令/数据 ckpt 路径/footprint/reproducibility 块）/ setup 标的语义风险实测结果。

## 3. 论文 vs Repo vs Setup 对齐表（Step 3-4 持续更新）
| 项目 | 论文 | Repo/config | Setup | 状态 |
|------|------|-------------|-------|------|
| backbone / 输入尺寸 / batch / optimizer / lr / scheduler / epochs | | | | 对齐/不一致/unknown |
| 数据增强 / metric 实现 / 评测协议(TTA/multi-scale) | | | | |
| checkpoint 的训练来源与版本(EMA?best/last?) | | | | |
| 训练链(BN类型/loss归约/等效batch/lr缩放/warmup) | | | | 仅要重训时填，对照 trust-traps ⑦ |

> 不一致项：哪些是"setting 差异（可解释）"，哪些是"对不上（要查）"。

## 4. 推理链验证（Step 3 当场回填）
- **目的**：用 official checkpoint eval 验证推理、权重加载和评测流程。
- **做了什么**：命令 / seed / 排了哪些 trust-traps（①-⑥）。
- **预期结果**：论文数 ± band。
- **实际结果**：实测值（不是"通过了"）/ 差距 / 在 band？
- **是否成功**：是 / 否（否则记录修法与重验）。
- log 路径见 `runs/eval/`，对齐核对底稿见 `alignment.md`。

## 5. 训练链验证（Step 4 当场回填，training-free 时空着注明）
- 每个 run 一小节（dev-full / scaled-b / trend-a 各自）：**目的 / 做了什么（命令、seed 列表）/ 预期结果 / 实际结果（多 seed 列逐值 + std）/ 是否成功**。
- 随机种子造成的数值波动：noise_floor 怎么测的、std 多少。
- scaled_a 的 loss 曲线形状是否对齐论文；命中各项验证能支持的结论哪一级、deferred 了什么。
- baseline 训练曲线产物（loss / metric / 固定批预测演变）路径。

## 6. reduced 配置（Step 5，可选；无则注明未建）
- 配置 / 有效性验证（方法 + 证据 + confidence）/ 噪声标定结论。

## 7. 差距分析（命中了哪些 trust-traps）
> 详细逐条核验落 `alignment.md`，本节是摘要 + 结论：metric 定义 / split / checkpoint 的训练来源与版本 / 评测协议 / 训练链数值接近但设置或实现不一致 / 差异是否超出随机波动 / 表格行 / 最可能的差距来源（一句话定性）。命中的坑已同步进 json `known_pitfalls`。

## 8. 下游 handoff（Step 6 定稿）
- 给 CIP / execution：可信 baseline / 走的分流 / ready 命令 / 推理评测与训练复现的数值 + 容差范围 + 随机种子造成的数值波动 / frozen|mutable 边界 / 曲线参照 / checkpoint 的训练来源与版本 / 训练链关键设置。
- 是否需要 code-idea-prepare 的判断+ 理由。
- 仍 blocked / 未做的；建议下一步。
````

---

## 模板使用说明

- **机读区是契约**：`idea_kind` / `repro_strategy` / `eval_判定` / `training_判定` / `trustworthy_for_delta` / `evidence_strength` / `full_scale_alignment` / `target` / `frozen_components` / `mutable_components` / `noise_floor` / `ready_commands` / `checkpoint` / `reproduced_baseline_checkpoint` / `training_chain` / `determinism` / `dev_card_footprint` / `known_pitfalls` / `blocked` 这几个 key 下游直接读，**字段名稳定、值要真**（验证过才填，查不到标 unknown，不编）。
- **两项验证结论用于 execution 的入场判断**：**eval 对齐 ≠ baseline 可信**。绝大多数 idea 要重训，execution 看 `training_判定`——它是 `not_trustworthy` 或停在 `blocked_需运行卡` 时，`trustworthy_for_delta=false`，execution 知道不能在这 repo 上重训做创新实验。只有 training-free 才退看 `eval_判定`。
- **`repro_strategy` 让 execution 知道结论依据及使用限制**：`dev_full` = 训练链端到端在开发卡验过（可直接核对完整训练结果）；`scaled_b_plus_a` = 小 setting 对齐 + 大规模趋势对（可开始迭代，full 规模数字上运行服务器补）。`evidence_strength` 进一步标证据强度，`low` 时 execution 只排方向、重大决策回 full。
- **`target.frozen` 是指标契约的冻结标记**：冻结后 metric 口径 / 评测协议 / 数据 split 只读，execution 改协议 = 语义改动即停。
- **metric 定义不能只写名字**：`mAP` 没用，要写 `mAP@[.5:.95] (pycocotools 官方 eval)`（trust-traps ① 落地）。
- **按验证进度更新 report.md**：spec 确认后建立、随验证逐节回填（目的/做了什么/预期/实际/是否成功），Step 6 只定稿「推理和评测验证、训练复现验证结论」和「handoff」两节——不最后一次性补写。
- **报告与 JSON 同步**：`reproduction.json` 和 `report.md` 描述同一事实的两面，改动任何结果时同步更新两份文件。run 产物由 json `artifacts` 引用，不复制进正文。
- **恢复入口**：`reproduction.json`（尤其 `artifacts`）就是 reproduction 中断后的恢复总纲，配合扫 `runs/*/run.log` / `EXIT_CODE` / metric 文件定位断点（见 `dl-assistant/references/long-run-ops.md`）。
