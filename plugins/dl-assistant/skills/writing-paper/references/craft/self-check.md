# Self-Check（audit 一致性 lens 清单——纯内容一致性）

`writing-paper` 的 **audit 目标（op-7-audit）一致性 lens** 清单——由未参与起草的子 agent 在每次 audit 中使用。这是 writing-paper 自己的写作质量检查——不把质量关推给 `writing-paper-review`。

> **本清单只管内容一致性**（要判断力的）。其他检查各归各家，别在这里重复：
> - 确定性检查（label/\ref、蓝图↔成稿、venue 合规、页数）→ op-7 主 agent 查（grep/对照就能定）。
> - 渲染/美观检查 → `visual-aesthetic-review.md`。
> - 逐节写后自审（write-section ③ / ingest-results ④）→ `section-self-audit.md` 一；句段、字词和常见生成式写作问题三类写作要求 润色 → 同文件 二。

## 自检清单（六项）

### 1. claim 回扣完整性 + 事后核验（事前脊柱 + 写作期防 drift 闭环）

事前脊柱（`blueprint.md` / `claims.json`）已有。本步加**写作期事后核验**——草稿措辞可能 drift 出 claim 树：

- 随机采样正文每条 `\cite{}`，判引用是否支撑所在句的 claim（claim↔ref 对齐）。
- 出两类问题：**uncited_assertions**（悬空主张：正文有 claim 但没 ref 到 C-ID）+ **claim_drifts**（措辞 drift 出 claim 树：正文说的比 claim 树多 / 偏）。
- 每条 contribution → 有实验支撑？每个实验 → 支撑某维度（无主实验丢 appendix）？

### 2. 三位一体一致性（核心）

- Introduction 的 gap = Related Work taxonomy 终点 = Experiment 要证明的点？
- 方法名全程同一个名字（intro / method / experiment / 图）？
- contribution 列表（intro）= Method 兑现 = Experiment 证明 = Conclusion 回扣？
- Abstract 许诺的每点正文都兑现？

### 3. 引用完整性

- 正文每个 `\cite{key}` 在 refs.bib 有对应？（无 undefined）
- refs.bib 每条都被正文引用？（无 orphan）
- 标了 `needs_human_verify` 的 bib 条目逐条人工核（尤其 core 引用）？
- 关键 baseline / 竞争工作没漏引？

### 4. 图表内容完整性

- manifest 里每个图表资产都产出了？（status 无滞留 intent）
- 每个图表正文有引用句？（无悬空图表）
- caption 三段式（what / how / takeaway）？
- 多图风格统一（paper palette / 标注样式一致）？
- （渲染/美观层不在这里查——归 `visual-aesthetic-review.md`。）

### 5. 附录完整性

- 正文引用的附录内容附录都有？（无悬空引用）
- 附录设置和正文一致（locked_decisions 没破）？
- 复现必要信息（数据 / 配置）正文 + 附录齐全？

### 6. 符号一致性

- 全文符号与 `_draft/content/notation.md` 一致？
- 无同名异义（同一符号两个意思）/ 异名同义（同一概念两个符号）。

## 怎么跑

逐项过，不过的回对应目标改（内容问题回 write-section）。**每次 audit 都跑本清单**——一致性过了才轮到润色 lens（见 `section-self-audit.md` 二）。**一致性没过不润色**——润色只改语言，内容问题必须先修。

## 输出

```markdown
# 自检报告
## 1. claim 回扣 + 事后核验  | uncited_assertions / claim_drifts | 位置 | 修法 |
## 2. 三位一体一致性 | ... |
## 3. 引用完整性 | ... |
## 4. 图表内容完整性 | ... |
## 5. 附录完整性 | ... |
## 6. 符号一致性 | ... |
## 结论：通过 / 需回改（列待改项）
```
