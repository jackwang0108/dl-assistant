# 会议评审参考 · 精审派（图形学 + 机器人会议）

`writing-paper-review` Step 2/3 用。SIGGRAPH / RSS / ICRA / IROS 共性：**多审稿人（常 3-4 审）、强调 impact、rebuttal 范围严格（只纠错不加新结果）、AE/委员会精审**。

## SIGGRAPH（+ SIGGRAPH Asia）

**审稿规模**：每篇 **4 份全文审**（委员会成员 + 外审），双盲。
**评分（6 档单一刻度，Journal/Conference/dual-track 同一把尺）**：
Strong Reject / Reject / Borderline Reject / Borderline Accept / Accept / Strong Accept。整篇作为整体评（含所有方面）。
**rebuttal（严格）**：限 **1000 词纯文本**，**只能纠正事实错误、回答具体问题**——不许放新结果、新实验、修订文本、URL，越界材料会被忽略。
**录用**：rebuttal 后资深 reviewer 通读全部评审 + rebuttal，委员会会议给"conditionally accepted"或"rejected"。
**双轨**：dual-track 投稿可被推荐为 Journal（TOG）或 Conference track，由委员会定。Conference track 对形式完整性/验证要求**更宽容**（容纳更早期/更冒险的工作）。

## RSS（Robotics: Science and Systems）

**审稿规模**：AC 分配 **3 个高专业度 reviewer** 全文审 + AC 自己评。
**评分**：
- **Quality Score（5 档）**：Excellent（年度最有意思之一）/ Very Good（扎实、重要贡献）/ Good（有瑕疵但好贡献）/ Fair（在路上但还没到）/ Poor（需大改）
- **Impact（checkbox）**：是否与典型投稿足够不同、可能对机器人某子领域有重大影响
- **首轮推荐（6 档）**：Strong Accept / Accept / Weak Accept / Weak Reject / Reject / Strong Reject
**review form 特色**（写进人设）：要求 reviewer 先**复述论文立场到作者会说"我都希望自己这么表述"**；列出认同点、说明从论文学到什么——建设性、尊重。
**硬性 desk reject**：缺 Limitations 章节、正文有外链（github/项目页）、未匿名、模板不对、不完整、非英文。

## ICRA / IROS（IEEE 机器人会议，含 RA-L 关联）

**录用机制**：AE 组织评审 → AE 给推荐 → SE/EIC 终定（三级）。双盲（double-anonymous）。
**review form 特色（RA-L/ICRA 体系，写进人设）**：
- **录用推荐不写进给作者的评论里**——推荐单独填，给作者的正文只谈论文优劣与改进。
- 评审要 accurate、insightful、constructive，即使负面也不贬低作者努力；太短/太浅的评审 AE 会直接退回。
- **ICRA 禁止把稿件内容喂给任何 AI 系统**（保密义务）——同 CV，模拟时人设要像人类专家判断。
- 很多 ICRA 论文实为 RA-L 等期刊论文获准在会议展示，机制偏期刊味（见 journals.md）。

> 机器人这一类整体比 CV 更看**真机/系统可行性与影响**，但 CoRL（见 conf-openreview.md）明确"不必上真机"——同领域不同会议口味不同，按目标会议加载。
