# 会议评审参考 · 打分派（OpenReview 体系）

`writing-paper-review` Step 2/3 用。这类会议共性：**结构化子维度评分 + 数值 overall + confidence**，有 rebuttal 轮和 discussion 期，AC/SAC 综合数值与讨论定夺。审稿人 subagent 按目标会议加载对应那一节，照搬其评分维度和刻度。

> 模拟时严格用会议的真实刻度（不要自创 1-5 通用分）。overall 数值要和文字意见自洽——给低分必须在意见里有对应的硬伤。

## NeurIPS

**子维度（各 1-4：4 excellent / 3 good / 2 fair / 1 poor）**：
- **Soundness**：技术主张、实验与方法是否严谨，中心主张是否被证据支撑
- **Presentation**：写作清晰度、与已有工作的语境化
- **Contribution**：对所研究领域的贡献质量（问题是否重要、是否有原创性、结果是否值得分享）

**Overall（1-6）**：
- 6 = Strong Accept；5 = Accept（技术扎实、影响明确）
- 4 = Borderline accept（接受理由略胜，慎用）
- 3 = Borderline reject（拒绝理由略胜，慎用）
- 2 = Reject（技术缺陷/评估薄弱）；1 = Strong Reject
- 另填 **Confidence(1-5)**、Strengths、Weaknesses、Questions、Limitations、Ethics flag

**文化**：鼓励"对 novelty 的质疑要给出具体已有工作引用"；不允许只挑组织/语法。

## ICLR

**子维度**：Soundness / Presentation / Contribution（各 1-4）+ **Confidence(1-5)**。
**Rating（离散 {1,3,5,6,8,10}）**：10 = 卓越、8 = 好论文接受、6 = 勉强过线、5 = 勉强不过、3 = 拒、1 = 严重缺陷。
**文化**：**全程公开**（OpenReview，评审可被作者和公众看到），rebuttal 后鼓励改分。Summary / Strengths / Weaknesses / Questions 分栏。

## AAAI

**Overall（1-10）**：10 = 顶 5% 开创性、9 = 顶 15% strong accept、8 = 顶 50% clear accept、7 = 好论文接受、6 = 略高于线、5 = 略低于线、4 = 不够好拒、3 = 明确拒、2 = strong reject、1 = trivial/错误。
**Confidence(1-5)**：5 = 绝对确定（查了数学/相关工作）… 1 = educated guess。
**文化**：**两阶段**——Phase 1 可直接 desk reject（不进二轮）；Phase 2 完整审 + 作者 feedback window。

## CoRL（机器人 + 学习，OpenReview）

**子维度（描述性，无固定数值轴）**：
- **Quality**：技术是否 sound、主张是否被理论/实验支撑、方法是否恰当、是否完整工作、对优劣是否诚实
- **Clarity**：是否清晰、组织是否良好、是否足够让专家复现
**录用**：OpenReview 式 overall + AC meta-review + rebuttal；录用后评审公开。
**文化（重要，写进 reviewer 人设）**：CoRL 明确反对这些**不构成拒稿理由**的话术——"必须开源/必须有定理/必须上真机/没超 SOTA"。审稿人要看**新视角/洞见/知识增量**，不是刷榜。

## ACL / EMNLP（ARR 体系，特殊，单列）

ACL Rolling Review 把评分拆成**两个正交维度**，是这套体系最大特点：
- **Soundness（1-5，0.5 步进）**：方法与结论是否被证据支撑。**给低分必须在评审文字里指出具体硬伤**——低 Soundness 无依据＝评审不合格。
- **Excitement（1-5，0.5 步进共 9 档）**：主观兴奋度/影响力（5=Highly Exciting … 1=Not Exciting），允许纯主观、不必给硬理由。
- **Overall Assessment**：若投 ACL 会议，该接受到什么档（Main / Findings / 不接受）。
- **Confidence(1-5)**。
**分流文化**：sound 即可进 **Findings**；**Main 会议**额外要 Excitement/novelty/impact。所以 reviewer 要分开判"够不够扎实"和"够不够激动人心"——一篇可以"sound 但不 exciting"。
