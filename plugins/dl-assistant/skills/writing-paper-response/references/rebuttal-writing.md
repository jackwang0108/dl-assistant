# Rebuttal Writing（回复文本写作）

`writing-paper-response` Step 2 写每条回复 + Step 3 汇总 rebuttal letter 用。管回复的**语气、结构、字数**。

## 回复语气选项（三档，按意见来源 + 用户选）

| preset | 语气 | 何时用 |
|---|---|---|
| **balanced** | 平衡——承认合理质疑 + 辩护自己的 | 默认。审稿场景大多数意见 |
| **conciliatory** | 温和让步——感谢指出、坦诚接纳 | 导师 / 合作者；或 reviewer 确实说得对、自己改 |
| **firm** | 坚定辩护——指出 reviewer 误读、给证据反驳 | reviewer 误读 / 要求不合理（impossible request）/ 攻击不成立 |

选 tone 的依据：意见来源（审稿偏 balanced/firm，内部偏 conciliatory）+ 意见性质（三层分流：misread-risk 偏 firm 澄清、polish 偏 conciliatory 接纳、substance 视情况）。**用户在逐条讨论时定 tone**。

## response letter 标准结构（Comment / Response / Changes）

每条意见按这个三段式回复（rebuttal letter 的基本单元）：

```markdown
**[R2.3] Comment:** <复述 reviewer 原话或摘要，让 AC 不用翻原文也知道在说哪条>

**Response:** <直接回应：先一句话立场（同意/部分同意/不同意），再给理由 + 证据。不绕弯>

**Changes:** <改了哪——section + page-line，或新增 figure/table。没改的（纯澄清）说明为什么不用改>
```

- **Comment 复述要忠实**——别歪曲原意（AC 会对照原 review）。
- **Response 先给立场**——reviewer / AC 第一眼要看到你是接纳还是辩护，不是读完一段才知道。
- **Changes 用「章节及原句或图表编号」定位，page-line 留空待回填**——原句或图表编号让 reviewer 能快速定位修改，是回复信定位修改的依据；但 **response 产 letter 时改稿还没发生，页码和行号须等改稿完成后填写**（改稿后页码必变）。letter 里 page-line 栏留空，由 writing-paper 改稿完成后回填（修改需求清单里的改动落进 Changes，和 writing-paper 改稿的 changelog 对得上）。

## 目标会议或期刊的字数限制（以当年官方为准）

rebuttal 字数 / 时限各 venue 不同，**Step 1 确认 venue 后查当年官方 rebuttal 指南**（venue-contract 里没记 rebuttal 规则，需要另行核查）。核对**字数/页数限制、格式（纯文本？可否附图/附 PDF）、截止时间、匿名规则、是否允许新结果/appendices**；以官网当年 author guidelines / rebuttal instructions 为准，交叉验证多来源、标注来源 + 时间，二手信息（博客/论坛）只作线索并标注，查不到标「需用户确认」。常见参考（仅供参考，以当年官方要求为准）：

| venue | rebuttal 限制（参考）|
|---|---|
| NeurIPS | 限制字数 / pin（近年收紧，按当年）|
| ICLR | OpenReview，限制字数 + 格式 |
| CVPR / ICCV / ECCV | 限时 rebuttal，常限页 / 字数 |
| ACL / EMNLP（ARR） | author response 限字数 |
| SIGGRAPH | **1000 词纯文本**，只能纠事实、不加新结果 |
| 期刊 | 无 rebuttal，走 revision 循环（见 writing-paper-review journals）|

> 字数紧时：优先回应 **substance** 和误读类（影响录用的），polish 类一句带过或合并。清单里的改动类型（补实验项 vs 纯改稿）帮你快速分类哪些必须详答。

## 给 AC 的总体说明（审稿场景）

rebuttal letter 顶部（或单独）给 AC 一段 cover letter，做**跨 reviewer 综合权衡**（reviewer 只看自己的，AC 要看全局）：

- **主要改动总结**（3-5 句）：这轮 rebuttal 做了哪些关键修改 / 补了哪些实验。
- **一致性权衡**：多个 reviewer 意见冲突时（一个要加 X、一个说 X 多余），说明你怎么权衡的、信了谁、为什么。
- **核心关切回应**：点出哪几条是决定录用的关键质疑（borderline 论文），你怎么回应了。

> cover letter 不是逐条复述，是给 AC 一个「全局图」——帮 AC 在 discussion 时替你说话。

## 通用原则

- **先感谢后回应**（审稿场景）——礼貌但不过度（一句 "We thank R2 for..." 够了，别整段客套）。
- **给数字 / 证据，别给形容词**——"we added baseline Y, now +2.3%" 强过 "we significantly improved"。
- **如实说明局限**。对无法满足的请求，说明具体限制，并提供可用的替代证据。
- **新结果守 venue 规则**——SIGGRAPH 等禁新结果，别越界；允许的 venue 新结果对应的补实验项已在 `revision-brief.json` 里规划。
