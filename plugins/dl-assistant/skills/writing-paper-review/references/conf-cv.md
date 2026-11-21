# 会议评审参考 · 描述派（CV 三大顶会）

`writing-paper-review` Step 2/3 用。CVPR / ICCV / ECCV 共性：**弱化数值打分、重描述性论证、AC 三人会议（triplet）拍板、不看分数曲线**。审稿人 subagent 要写出有据有理的长评，而不是堆一个分数。

> ⚠️ **CVPR 明确禁止用 LLM 写 review/meta-review**（本地或 API 均不可）。我们这里是**模拟**审稿训练作者自查，不是真去投稿系统提交——但 reviewer 人设要写得像人类专家的判断，避免一眼 AI 腔（空泛、面面俱到、不痛不痒）。

## 评分

CV 会议近年走 OpenReview，但**录用不被数值曲线绑定**。reviewer 给一个总体推荐（强接受 / 接受 / borderline / 拒 / 强拒）+ Confidence，核心分量在**文字论证**而非分数。

## 评判准则（写进 reviewer 人设）

- **技术 sound + 对领域有贡献**即可接受；找论文里**好的、有启发的、推进了什么知识**。
- **鼓励新颖、大胆的概念**，哪怕没在很多数据集上验证。
- **不超 SOTA 本身不构成拒稿理由**——要权衡 novelty + 潜在影响 + 报告的性能。
- **易修的小瑕疵不该成为拒稿理由**。
- 评审要**具体、详细**——讨论比分数更能帮作者和 AC。

## 录用决策（AC 视角，Step 3 用）

- **AC triplet meeting**：三个 AC 一组,对 borderline（主要看评分分歧/spread 识别）开会讨论拍板，给 meta-review。
- **不公布分数曲线**——AC 基于评审 + 论文本身的贡献与价值定 accept/reject，不被"该有多少接受率"约束。
- 不公开评审、不向公众征求意见（双盲、封闭）。
- desk reject 触发项：超页数、未匿名、未用模板、dual submission、与并投稿 >20% 重叠。

## ECCV 差异

同 CV 体系（双盲、描述派、AC 拍板）。CCF 列为 B 类但属 CV 三大顶会，按本节同样标准模拟。
