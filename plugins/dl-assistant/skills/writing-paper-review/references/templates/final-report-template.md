# 审稿总报告（<venue> · <subjectArea> · round-<N>）

> 本报告是**人读入口**：结论汇总 + 导航。内容全部渲染自本轮已落盘的结构化产物（reviews 评分 / meta-review / problem-list.json / 合规报告），**不产生新判断**——细节一律跟文件索引走。

- **论文**：<PDF 文件名 / 标题>
- **日期**：<YYYY-MM-DD>
- **评审配置**：<N> 个 reviewer（逐个列出 偏向×哲学）+ 魔鬼代言人（开 / 关）+ 合规审稿人（有 / 无）+ AC/AE

## 录用倾向

**<venue 真实刻度>**——<一句话结论（引自 meta-review）>

## 评分一览

| Reviewer | 偏向 × 哲学 | overall | confidence | 一句话立场 |
|---|---|---|---|---|

## 共识与分歧

- **共识**：<reviewer 一致认可的点 / 一致批评的点>
- **分歧**：<分歧点 → AC 裁了信谁（裁决过程见 meta-review.md）>

## 致命问题（severity=致命，共 <N> 条）

> 最该先看的一节。每条只给一句话 + location + source；依据与建议修法见 problem-清单.md。

1. **<问题一句话>**（location：…；source：reviewer-N / 魔鬼代言人 / 合规审稿人）

## 改进建议概览（severity=改进，共 <N> 条）

> 按类别归并（如「实验补强 3 条、写作 2 条、引用规范 1 条」），一句话概括每类；完整清单见 problem-清单.md。

## 已排除指控（rebuttal 防线预演）

> 魔鬼代言人提出、AC 裁决**不成立**的攻击点——真投时被喷这些，可以直接正面刚。

1. <指控一句话 → 为何不成立>

## 合规问题

> 本轮未启用合规审稿人则写「未启用」；启用了则：致命 / 改进各几条 + 各一句话，详见 compliance-review.md。

## 文件索引

| 文件 | 内容 |
|---|---|
| `meta-review.md` | AC 裁决全文（误读纠正 / 分歧处理 / 指控裁决 / rationale / major/minor points） |
| `problem-list.json` / `problem-清单.md` | 行动清单——机读契约（response 吃它）+ 人读版 |
| `reviews/reviewer-N.md` | 各审稿人完整意见（评分依据 / 检索结论） |
| `devil-advocate.md` | 魔鬼代言人指控清单原文 |
| `compliance-review.md` | 合规对照表（如启用） |

## 交接

- 消化意见（改稿 / rebuttal / 补实验）→ `writing-paper-response`（自己的论文，吃最新一轮 problem-list.json）；外部 PDF 场景无论文根——把本报告 + problem-清单 交用户转达即可
- 补实验 → response 定目的 → writing-paper backlog → design-experiment → code-paper-experiment
