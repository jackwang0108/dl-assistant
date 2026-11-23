# Meta-Review（<venue> · <subjectArea>）

- **录用倾向 / 决定**：<venue 真实刻度：accept/borderline/reject 或 SA…SR 或 major/minor revision>
- **一句话结论**：<这篇的命运 + 最关键的理由>
- **语言**：简体中文（术语保留英文）

## 评分一览与立场地图

| Reviewer | 偏向 × 哲学 | overall | confidence | 一句话立场 |
|---|---|---|---|---|
| reviewer-1 | | | | |
| … | | | | |

## 核查与裁决

> 指引：AC 不是汇总员是裁判——每条都写你**对照 PDF 原文后**的结论，不转述 reviewer 的话。

### 误读纠正

<哪个 reviewer 在哪条上误读了原文、原文实际是什么（页码）、纠正后对评分的影响；无则写「无」>

### 分歧处理

<分歧点 → 信谁 → 原文依据；属口味分歧（两方都成立）时，看致命硬伤是否被任何一方坐实>

### 重大缺陷审稿人指控裁决

> 指引：逐条裁决，不许批量略过。成立 → 转 major points；不成立 → 进「已排除指控」。

**成立**：

1. <指控内容 → 成立依据（原文页码 / 检索结果） → 转入 major points>

**已排除指控**（这份清单是作者的 起草 rebuttal 时可查阅的核查记录，不许省略）：

1. <指控内容 → 为什么不成立（一句话）>

## 区分度检查

> 指引：reviewer 评分挤在同一分段（如全 borderline）时必填——为什么这篇不是明显的 accept、也不是明显的 reject？给出明确倾向，并说明依据。评分本身有区分度则写「评分有区分度，无需」。

## Rationale（综合理由）

> 指引：按 venue 真实机制写——CV 三会对论证不对分数曲线；OpenReview 派综合数值 + discussion；期刊按 AE 决定信格式。结构建议：主论点 → 关键证据 → 残余风险 → 倾向。

## Major Points（必须解决；Step 4 机械抽进 problem-list.json）

> 指引：每条带六件套（location / verbatim_quote / 依据 / close_criterion / 建议修法 / source），Step 4 才能不解析自由文本直接抽。verbatim_quote 保留 reviewer 的逐字原文引用（reviewer 没给的你补；引用对不上原文的整条不成立）；close_criterion 是「改成什么样这条算关闭」的可验收条件（reviewer 没给的你补写）。

1. **<问题>**（location：…；verbatim_quote：「<原文>」pN；依据：<calibration / 评审表单 / authorkit 条目>；close_criterion：<可验收条件>；建议修法：…；source：reviewer-N / 魔鬼代言人 / 合规审稿人）

## Minor Points（改进建议）

1. <同 Major Points 格式>
