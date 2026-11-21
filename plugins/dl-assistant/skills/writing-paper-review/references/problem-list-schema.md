# problem-list.json Schema（review → response 交接契约）

`writing-paper-review` Step 4 汇总产出、`writing-paper-response` 消费的核心交接物。**机读契约是 `problem-list.json`**（唯一真相源）；人读的 `problem-清单.md` 从 json 渲染，是派生物不是第二真相源。每条一组机读字段——response 靠字段机械分流，不解析自由文本。

## 文件结构

```json
{
  "_notes": {
    "是什么": "审稿问题清单——review → response 的机读交接契约。Step 4 从 {reviews, meta, accusations, compliance} 汇总去重编号产出；人读 problem-清单.md 从本文件渲染。",
    "severity 判定": "对照 fairness-firewall.md（七类=改进）+ calibration.md（致命类）；合规问题按 desk-reject 级别判（页数超/匿名泄露=致命，版式小瑕疵=改进）。"
  },
  "venue": "<目标 venue>",
  "subjectArea": "<投稿领域/track>",
  "meta": {
    "recommendation": "<AC 录用倾向/决定>",
    "一句话结论": "<meta-review 的一句话结论>"
  },
  "problems": [ "<problem 对象，见下>" ]
}
```

## problem 字段

| 字段 | 取值 | 说明 |
|---|---|---|
| `id` | `P1` / `P2` / … | 去重后连续编号（跨 reviewer 同一问题合并为一条） |
| `severity` | `致命` / `改进` | 对照 `fairness-firewall.md`（七类=改进）+ `calibration.md`（致命类）；response 据此排优先级 |
| `type` | `内容` / `合规` / `指控成立` | 来源类别：reviewer/AC 的内容问题、合规审稿人的 desk-reject 项、魔鬼代言人经 AC 裁决成立的指控 |
| `location` | section + page-line | 问题锚点（如 `Experiments §4.2, p6 L188`） |
| `verbatim_quote` | 逐字原文引用 | **必填**——问题指的原文逐字引用（含页码）。引不出原文 = reviewer 没读，该条在 Step 4 汇总时直接丢弃并计数汇报，不进清单 |
| `问题描述` | 自由文本 | reviewer 的 weakness/question 摘要（忠实，不润色掉锋芒） |
| `依据` | 评审标准条目 | 命中的评审表单 / firewall / calibration / authorkit 哪条判据（如 `calibration·过度声称`） |
| `close_criterion` | 可验收条件 | **必填**——「改成什么样这条就算关闭」（如「Table 2 增加与 X 在 Y 设定下的对比」）。reviewer/AC 建档时给初版；response 逐条讨论时用户可修订。给不出可验收条件的空泛批评（「实验不够充分」式）在打回 reviewer 补写和直接丢弃之间由 AC 裁 |
| `建议修法` | 自由文本 | AC/meta 层给的修法提示（response 可推翻——最终方案由 response 与用户定） |
| `source` | `reviewer-N` / `AC` / `魔鬼代言人` / `合规审稿人` | 哪份报告提的；多条同类合并时列全（如 `reviewer-1, reviewer-3`） |

## 示例（problems 里的一条）

```json
{
  "id": "P2",
  "severity": "致命",
  "type": "内容",
  "location": "Experiments §4.2, p6 L188",
  "verbatim_quote": "「We compare against XXX and YYY on the ZZZ benchmark.」（p6 L188）",
  "问题描述": "主表 baseline 缺 2024 年后的 SOTA（缺 XXX / YYY），无法判断当前真实位置",
  "依据": "calibration·baseline 公平性（致命类）",
  "close_criterion": "主表或补充实验中加入至少 2 个 2024 年后的该任务 SOTA 对比；或在 limitations/实验节显式说明选取理由并获用户认可",
  "建议修法": "补最新 SOTA baseline 对比，或诚实说明选取理由",
  "source": "reviewer-2, reviewer-4"
}
```

> response 消费约定：`severity=致命` 对应 response 侧的 substance 类（必正面改 + 正面刚），`改进` 对应可权衡类——标签是先验，逐条讨论时用户可推翻（见 `writing-paper-response/references/fix-strategy.md`）。`close_criterion` 是初版判据，response 逐条讨论时可与用户修订（外部来源的意见没有判据，由 response 讨论起草）；定稿后的判据随 `revision-brief.json` 的 `关闭判据` 字段交 writing-paper，改稿按判据锁范围、按判据验收勾单。
