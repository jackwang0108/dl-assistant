# Sentence Craft（句段层工艺）

`writing-paper` 的**句段层**工艺——英语句子**语法结构**（怎么组成）+ **写作原则**（怎么写出多变、清晰、有层级的学术句）。正面向。每个 section 由 write-section 写时注入 prompt、写后自审（③）跑。

> 和 `word-craft.md`（字词层）、`anti-ai-patterns.md`（AI 禁止模式）正交。句长**工艺目标**（长短交错）在本文件；句长**机器指纹**（burstiness）在 `anti-ai-patterns`。

---

# A. 语法结构（术语锚点）

LLM 原生掌握英语语法，不展开教学——此处只留 B 节原则要引用的术语锚点：

- **clause 与句型**：clause = 主语 S + 谓语；五种基本句型 SV / SVO / SVC / SVOC / SVOO。句子按从句结构分 simple / compound（并列）/ complex（主从）/ compound-complex。
- **成分填充（A.4）**：名词性角色 ← NP / 名词性从句 / 动名词 / 不定式；定语 ← 形容词 / 介词短语 / 定语从句 / 分词；状语 ← 副词 / 介词短语 / 状语从句 / 分词短语。
- **非谓语动词（A.5）**：不定式 to do / 动名词 doing / 分词 doing·done——一句塞多个动作但不变成 compound 的核心机制。
- **从属 vs 并列（A.6）**：从属把次要信息降级、主句承核心；并列（and/but/or）把对等信息并排。

---

# B. 写作原则

## B.1 变化（variety）
三维度都变，一段内别连续同 profile：句子类型（simple/compound/complex 混用）＋ 句型（5 种别通篇 SVO）＋ 成分填充方式（NP/从句/分词/介词穿插）＋ 句长（长短交错）。

## B.2 主次（hierarchy）
核心论点进**主句**；次要信息（让步/条件/背景/补充）**降级**成从句或分词。别全平铺并列。→ 用 A.6 从属。
- ✗ *We tried X. It failed. We then did Y.*
- ✓ *After X failed, we did Y.*

## B.3 主语与焦点（subject & end-focus）
- 主语 = 该句**话题**；别通篇 we——换过程（动名词/分词）/ 结果（名词）/ 现象 / 方法名当主语。
- 新信息靠**句末**（end-focus：英语重心在后，新的/重的放句尾，旧的放句首）。

## B.4 句首（opening）
别通篇主语开头。用状语 / 分词 / 介词 / 从句 opener 起句换节奏。→ 用 A.4–A.5。
- *Having fixed the backbone, we …* ／ *To enforce consistency, …* ／ *Despite the gap, …* ／ *When applied to long sequences, …*

## B.5 简洁（concision）
用**最紧凑的结构**承含义：
- 能用分词/介词短语就别开从句（*the feature from the encoder* 优于 *the feature that comes from the encoder*）。
- 别过度嵌套（一句 ≥3 层从句读不动）、别过度并列（一串 and/but 平铺）。
- 名词化适度——堆名词化会僵。

## B.6 衔接（cohesion）
- 段首 **topic sentence**（一句能独立成立的结论）。
- 句间 **given→new**（句首接旧信息，句末抛新信息，链到下句）。
- 衔接词（However / Therefore / Moreover）**克制**——滥用是 AI 味，见 `anti-ai-patterns`。

---

# C. 自查 checklist

```markdown
## 句段层自查
- [ ] 变化：句子类型/句型/成分填充/句长 四方面不单调（一段内非连续同 profile）
- [ ] 主次：核心在主句，次要信息降级成从句/分词（非全平铺并列）
- [ ] 主语：非通篇 we（有过程/结果/现象/方法名当主语）；新信息靠句末
- [ ] 句首：非通篇主语开头（有状语/分词/介词/从句 opener）
- [ ] 简洁：用最紧凑结构；无 ≥3 层嵌套、无 and/but 一串平铺、名词化不堆
- [ ] 段落：段首 topic sentence；句间 given→new；衔接词克制
```

> 不是 railroad——给语法骨架 + 原则，灵活组合，只拦"单调 / 失序 / 啰嗦"。
