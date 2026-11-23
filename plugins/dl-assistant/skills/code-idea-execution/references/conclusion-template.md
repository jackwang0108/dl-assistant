# Conclusion 模板（code-idea-execution · 04-conclusion.md + conclusion.json）

> 由 **code-idea-execution** 产出。本 plan 的**结果 + 诊断 + 事实裁决 + 版本结论**。
> `04-conclusion.md` 是人读叙事；`conclusion.json` 是机读交接（iterate / release / writing-paper 读）。
> 记事实 + 验收裁决（子论点级）；**研究方向（下版做什么）不写这，交 iterate 的 from-previous**。
> claim 裁决从 `claims.json` 渲染，不手抄。

---

````markdown
# Conclusion · v<N>-<slug>

## 执行摘要

- **版本**：v<N>-<slug> ｜ **攻的子论点**：C_x ｜ **实验完成度**：X / Y
- **主要发现**：[一句话]
- **版本结论**：成功（C_x supported）/ 失败（refuted）/ 部分成功（mixed）
- **tag**：成功节点打 `claim-C<id>`（锁 method）/ 失败·分析节点无 tag

## §1 实验结果（按实验 / 问题维度，每个：目的 → 数字 → 诊断 → 判决）

> 本节按 plan 的实验、或跑出来的问题维度展开，每个写完整的「**回扣目的 → 数字表 → 诊断（为什么/根因）→ 判决（支撑/部分/证伪 + trade-off 诚实）**」。
> 诊断深度是本节核心：量级诊断（L2 norm 占比）/ 三角验证（统计 + per-image + viz）/ fail-win 对称分析。描述性为主（「数据显示 X」），判断归 iterate。
> 每个实验的 keep/discard 对照 meta.json 预登记的 `decision_rule` 写——按预登记规则判的，还是事后补的解释（后者要标出来）。

### [维度 1：如「Run1 fusion vs R2 主性能」/「select_layer ablation」/「P2' 跨块治愈」]

- **目的**：回答什么（回扣子论点 C_x / 哪个判据）
- **结果**（数字表）：

    | 配置 | metric | 值  | vs 锚点 | 超 noise_floor? |
    | ---- | ------ | --- | ------- | ---------------- |

- **诊断**（为什么是这个结果 / 根因）：[机制结论。例：「不是 RGB 高频不够强，是 F_high residual（norm 25.87）淹没了它」]
- **判决**：支撑 / 部分 / 证伪 C_x —— **trade-off 诚实**（例：「改善了 A，同时出现 B 问题，净 +X 但 miss +Y」）

### [维度 2：如「abs_hf 高频分析」/「case study 6 图」/「fail-win 对称」]

[同上结构——目的 / 数字表 / 诊断 / 判决]

### 未跑 / 未完成的实验

| 计划实验 | 为什么未完成 | 影响 |
| -------- | ------------ | ---- |

### scale-risk 清单（有则写）

机制上可能和容量/数据规模交互的变体（reduced 上成立、full 上可能消失或反转），逐个列：变体 + 一句话理由。CPE 跑 full-scale 时优先验这些。

## §2 claim 裁决（从 claims.json 渲染，不手抄）

> claim 裁决（supported / plausible / insufficient_evidence / contradicted，枚举以 `claims-template.json` 为准）由验收子 agent 写进 claims.json。本表从那渲染；完整裁决 + 证据指针读 claims.json。**contradicted 表示证据与预测相反**。子论点是否设为 refuted，由 iterate 分析原因后与用户决定。

| Claim（子论点） | verdict                     | evidence          | is_innovation |
| --------------- | --------------------------- | ----------------- | ------------- |
| C_x             | supported / contradicted / … | exp-001: [metric] | true / false  |

## §3 版本结论（成功 / 失败 / 部分 + trade-off 诚实）

- **本 plan overall**：成功 / 失败 / 部分成功
- **trade-off 诚实**：[数据级证实，不单向改善。例：「救 R2 失败 16/20 但丢 R2 胜利 10/20——fusion 是重分配非单向改善，净 cIoU 升但 miss 升」]
- **对总论点的影响**（陈述事实，演化判断归 iterate）：[这版结果让总论点更稳 / 更悬 / 待定]

## §4 可复现信息

- **git**：commit `<sha>` ｜ branch `idea/v<N>-<slug>` ｜ tag `claim-C<id>`（成功节点）/ 无（失败·分析）
- **命令**：见 plan 机读交接区
- **产物**：`experiments/<exp>/runs/` + `analysis/` + 台账 `experiments/index.json`
- **机器**：[跑在哪——文件不在找用户要，不绑传输]
````

---

## conclusion.json（机读交接区，供 iterate / release / writing-paper 读）

```json
{
  "version": "v<N>-<slug>",
  "status": "completed | abandoned",
  "outcome": "supported | partially_refuted | refuted | inconclusive",
  "node_type": "success | failure",

  "claims_json": "claims.json",
  "method_tag": "claim-C<id>[-v<k>] | null",

  "golden_metrics": [
    {
      "claim_id": "C_x",
      "metric": "...",
      "value": 0,
      "experiment_id": "exp-XXX",
      "git_tag": "claim-C<id>"
    }
  ],

  "key_insights": [
    { "summary": "...", "impact": "..." }
  ],

  "scale_risks": [
    { "variant": "exp-XXX 的什么改动", "reason": "为什么可能容量/规模敏感" }
  ],

  "evidence_quality_issues": [
    {
      "issue": "...",
      "severity": "critical | moderate | minor",
      "affected_claims": ["C_x"]
    }
  ],

  "handoff": { "next": "iterate" }
}
```

---

## 模板使用说明

- **`status` 枚举对齐 idea_tree 节点**：`completed`（跑完）/ `abandoned`（中途放弃）——部分完成不写 status，用 `outcome: partially_refuted` + 执行摘要的实验完成度表达。
- **`outcome: refuted` 是版本级事实描述**（核心子论点未获支持 / 实验结果不利），不写进 claims.json、不改任何 claim 的 `status`——子论点状态由 iterate 分析原因后与用户决定。
- **`claims_json`** 记录保存完整验收结论的文件路径。
- **`method_tag`**：成功节点打的 git tag（指向验证通过的方法实现）；失败/分析为 null。`node_type: success` 才有 tag。
- **`golden_metrics`**：release 用——每个 supported 子论点的关键数字 + 出处实验 + 锁它的 tag。
- **`key_insights`**：iterate 用（供 iterate 进一步分析）。
- **`scale_risks`**：reduced 迭代的需要在全量规模复核的风险——CPE full-scale 优先验清单；没有则空数组。
- **`evidence_quality_issues`**：跨 claim 共性问题（execution 汇总验收结果后写），单 claim 的问题在 claims.json 各自的 `evidence_quality.issues` 里。
