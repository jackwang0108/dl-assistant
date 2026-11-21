# AI Anti-Patterns（AI 禁止模式）

`writing-paper` 的 **AI 禁止模式层**——LLM 写学术文时系统性踩的坑（机器指纹），reviewer 一眼识破"AI 写的"。纯负向（detect + 改）。write-section ③ 写后自审跑、audit 的润色 lens 全文润色再跑。

> 和 `word-craft.md`（字词层）、`sentence-craft.md`（句段层）正交。那两个管"字词/句段怎么写好"，本文件管"怎么避免读起来像机器写的"。下面每条原则后的"例"只是 anchor——**按原则判**。

---

# 原则

## 1. 用最精确、最常见的说法，不用空洞的"高级感"词

人用朴素精确的技术词；LLM 过度产出"文艺/商业腔"填充词。每遇一个先问：**这是这个意思最精确、最常见的说法，还是一个空洞的"高级感"词？** 是后者就换成具体技术词。

- 例（anchor，非穷举，DL 文章不会用这些词）：delve / tapestry / realm / embark / testament / navigate / multifaceted / synergy / holistic / foster / cutting-edge / groundbreaking。
- **判据是"这词增加技术信息吗"，不是"在不在表上"**：`robust / leverage / comprehensive / paradigm / cornerstone` 等是 DL/CS 正常技术词，增加信息，**不算 AI 味**（旧版从别的学科抄来的词表误伤过这些）。

## 2. 机制词优先于比喻/金句

学术文用精确机制词；LLM 用色彩感/格言感替代精确性（让读者记比喻而非机制）。

- 格言 / slogan / 二元对立短句（_quality over quantity_、_the edge or the center, but rarely both_——脱离技术语境追金句）→ 给失败模式/发现命名（紧绑技术对象，如 _Positional Disparity_）。
- 去技术化隐喻 / 拟人动词 / 口语习语（_bakes in a prior_ / _hits a wall_ / _demolish_）→ 用精确机制词；就地解释用 `i.e./e.g.`。

## 3. 标点克制

- 破折号 em dash `—` 全文 ≤3（建议 0-1）。
- 分号 ≤2/1000 词（该用句号就别用分号串独立子句）。
- 别连续 ≥2 段以"冒号 + 列表"开头。

## 4. 直入主题，删喉音开场/元评论

- 删喉音开场（_In the realm of…_ / _It's important to note…_ / _It goes without saying…_ / _When it comes to…_ / _At the end of the day…_）→ 直入主题。
- 删元评论（_This section will discuss…_ → 直接 discuss）。
- 句首怎么变化（非这类开场、也非通篇 We）见 `sentence-craft` 的 opener。

## 5. 结构由内容驱动，不为对称削足适履

别为对称把内容塞进预设模板：

- 三段式强迫症（什么都说成 3 点）→ 2 强点 > 3 注水。
- 段落等长（全篇 150-200 词）→ 段长该有变化。
- 镜像结构（每节内部都 topic→3 证据→synthesis）→ 结构随内容。
- 预设数字凑结构（N 挑战 ↔ N 贡献 ↔ N 模块全对齐同一数）→ 点数由实质决定。
- 缩写泛滥（每子模块都起缩写，正文堆 PAVE-Net/XX-Encoder/YY-Decoder）→ 只核心方法一个自解释缩写。

## 6. 术语一致（边界见 word-craft）

别用 3+ 词指**同一技术实体**（学术写作术语一致是优点）。边界：**功能词**（不承载术语身份）可轮换，判据见 `word-craft`；本条只禁指代同一技术实体的概念轮换（_our method/framework/approach_ 乱换）。

## 7. 句长有变化（工艺见 sentence-craft）

5+ 连续句子全落在窄字数区间 → flag（LLM 趋同质长度，人写有变化）。**工艺怎么做**（长短交错）见 `sentence-craft`；本条只管"同字数"这个指纹，两者不矛盾。

---

# 自查 checklist

```markdown
## AI 禁止模式自查

- [ ] 无空洞"高级感"填充词（用最精确常见的说法；判据=增加技术信息吗，robust/leverage 等正常技术词不算）
- [ ] 机制词优先，无比喻/金句/拟人替代精确描述
- [ ] 标点克制（em dash ≤3，分号 ≤2/1000 词，无连续冒号-列表段）
- [ ] 无喉音开场/元评论，直入主题
- [ ] 结构由内容驱动（无三段式/段落等长/镜像/预设数字/缩写泛滥）
- [ ] 术语一致（同一技术实体不轮换；功能词边界见 word-craft）
- [ ] 句长有变化（无 5+ 句同字数）
```

> 不是 railroad——给原则，按原则判，只拦"机器指纹"（文艺腔/比喻/标点滥/开场套/假对称/术语乱/句长同质）。
