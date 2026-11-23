# Review Protocols（写后自审 + 全文润色 子 agent 协议）

正文起草与检查由不同的 agent 负责——写正文的 agent 对自己的文字（尤其 AI 味）有确认偏误，自审容易手软、自我合理化。所以自审/润色**派未参与写作的子 agent**（由未参与起草者检查），只对着 checklist + lint 裁，不掺写作时的妥协。

> 本文件是两块**子 agent 调度协议**（给什么、它做什么、报什么）：一、逐节写后自审（write-section ③ / ingest-results ④）；二、全文润色（audit 的润色 lens）。**audit 的 fan-out 编排（三 lens、owner 划分）在 `ops/op-7-audit.md`**。子 agent 本身的派发流程见 SKILL.md / 各目标操作的 reference。

## 一、写后自审子 agent（write-section ③ 逐节 / ingest-results ④ 结果批）

每节正文写完、本地验证前（或验证后），派一个子 agent 自审；ingest-results 每批结果回填后同样派一个。

### 给子 agent 什么（输入）

- **该节正文**：`content/<节>.md`（刚写的纯文字）。
- **该节写作指南**：`references/sections/<节>-writing.md` 的「**全节自查 checklist**」（refs_v2 每个章节指南末尾自带反模式信号清单）。
- **句段、字词和常见生成式写作问题三类写作要求 lint**（跨节通用）：`references/craft/sentence-craft.md`（句段层：句式/主从/主语/句长 变化）+ `word-craft.md`（字词层：选词原则）+ `anti-ai-patterns.md`（AI 禁止模式：机器指纹）。
- **蓝图约束**：该节挂的 contribution / C-ID（claim 回扣，防悬空主张）。
- **蓝图全文** `_draft/blueprint.md` + **已写节** `content/`（本节之前写的）：跨节一致性对照基准（术语/gap/named-abstraction/contribution 跟它们一致不）。
- **已写节 digest** `_draft/paper-state.json`（每节的论点句/术语/符号/关键数字/图表清单）：跨节一致性对照基准（比对已有 digest，不用重读全文）。
- **符号表** `_draft/content/notation.md`：符号一致性对照（无同名异义/异名同义）。

### 子 agent 做什么

只审、不改（改回主流程）：逐条过「全节自查 checklist」（论证层）+ 跑句段、字词和常见生成式写作问题三类写作要求 lint（句段/字词/AI）+ **跨节一致性**（术语/gap/named-abstraction/contribution 跟 blueprint + 已写节 digest；符号跟 notation.md）+ **引用覆盖**（key baseline/相关工作引了没、orphan claim 有主张没 ref），**输出命中项 + 改法**，不下场重写。

### 子 agent 报什么（输出）

```markdown
# <节> 自审报告
## checklist 逐条（该节指南的「全节自查」）
- [ ]/✗ [条目] — 命中位置（行/段）— 问题 — 改法
## 句段层（sentence-craft）
- [句式单调 / 失序 / 过度嵌套 / 句首通篇 We 等] — 位置 — 改法
## 字词层（word-craft）
- [不可核验 / 不精确 / over-claim / 自夸 / 术语乱 等] — 位置 — 改法
## AI 禁止模式（anti-ai-patterns）
- [文艺腔 / 比喻 / 标点滥 / 开场套 / 假对称 / 句长同质 等] — 位置 — 改法
## 跨节一致性
- [术语/gap/named-abstraction 跟 blueprint 或已写节 digest 不一致 / 符号跟 notation.md 不一致] — 位置 — 改法
## 引用覆盖
- [key baseline/相关工作漏引] / [orphan claim（有主张没 ref）] — 位置 — 改法
## 结论：通过 / 需回改（列待改项 + 优先级）
```

### 主流程怎么用

- **需回改** → 回 write-section ② 重写该节（按报告改），再本地验证 + 再自审，循环到通过。
- **通过** → ④ 初稿本地验证 → ⑤ 用户审 PDF。
- **注意**：命中项**不是死规矩**——子 agent 标出来，主流程（或用户）判断是否真改（有些"命中"是合理修辞）。子 agent 宁可多标，别漏。

## 二、全文润色子 agent（audit 的润色 lens）

一致性 lens 通过后，派子 agent 对**全文**做语言润色（只改语言不补内容）。

### 给子 agent 什么

- 全文各节 `content/*.md`。
- `sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`（全文跑）。
- 润色纪律：**只改语言（句长变化/术语一致/精确数字/去 AI 味），不补内容**。要补内容回 write-section。

### 子 agent 做什么

- 全文跑句段、字词和常见生成式写作问题三类写作要求 lint（句段/字词/AI），逐命中给 before/after/原因。
- 英文打磨（句长变化、术语一致、精确数字）。
- **meaning-risk flag**：可能**改变含义**的改动（不只是语言）逐条标 before / after / 原因 / 风险等级——**不擅自改**，列为**确认点**给用户确认（防润色偷改 claim）。

### 子 agent 报什么

```markdown
# 全文润色报告
## 安全改动（语言层，不改变含义）— 可直接落
- [位置] before → after — 原因
## meaning-risk 改动（可能改变含义）— 用户确认才落
- [位置] before → after — 原因 — 风险（高/中/低）
## AI 味/文风命中汇总（全文）
## 结论
```

### 主流程怎么用

- **安全改动** → 直接落（改 content + 转译 + 本地验证）。
- **meaning-risk 改动** → 列为确认点给用户确认，确认的落、否决的不落。
- 润色想补内容 → 回 write-section（润色不补内容是 hard rule）。

## 为什么要子 agent（不是自审）

- **由未参与起草者检查**：没参与写作，不带"我这么写是有道理的"偏误。
- **指令跟随**：子 agent 只对着 checklist + lint 裁，不被写作时的妥协污染——这正是用户痛点"指令跟随差"的对症。
- **可校准**：首跑时人工抽查几节自审报告，看 checklist 触发率（太松没意义、太严全 flag），据此调子 agent 的严格度。

## 派发注意（主流程）

- 子 agent 必须 **general-purpose**（禁 Explore），直接向子 agent 提供对应的检查清单和 lint 片段。
- 一节一个子 agent（隔离上下文）；全文润色一个子 agent（要看全文）。
- 子 agent 报告落 `_draft/`（如 `_draft/audit/<节>.md`），不进 Overleaf。
