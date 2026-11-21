# Fix Strategy（问题 → 修改策略）

`writing-paper-response` Step 2 逐条讨论用。六类分类告诉你"是什么问题"，本文件管**怎么改**——回应优先序阶梯（每层带操作细则）+ 六类各自的确诊 / 打法 / 常见错 + 修改方案的质量标尺 + page-line 定位 + problem-list 字段消费 + 反模式。

## 回应优先序阶梯（先查已有，再谈补新）

每条意见按这个顺序过筛，**能用下层就不用上层**：

### ① 论文已有，reviewer 没看到 → 引用澄清（成本 0）

- **先分清「没看到」还是「真没写」**——查成稿不查记忆（Step 1 已读成稿 + 证据存货）。reviewer 说"没讨论 X"，先在成稿里搜 X：有 → 没看到；没有 → 别硬说没看到，按真缺处理（往 ②③④ 走）。
- **rebuttal 指出原文位置**（page-line + 原句摘录），措辞对事不对人（"X is discussed in §3.2 (p5, L172)"，不写 "the reviewer missed..."）。
- **正文顺手改显眼**——reviewer 会漏看就是论文的锅，改法按漏因选：定义/讨论藏在后文 → 首次出现处加指针句（"详见 §4.2"）；埋在长段里 → 关键句独立成段或前移；说了但没和图表挂钩 → 加交叉引用（"as shown in Fig. 3"）。

### ② 已有数据/实验，没写进论文 → 补写（成本低）

- **「已有」必须核实，别编造**（红线）——查 Step 1 盘点的证据存货（CPE 数据包 / ingest-results 产物），存货里没有就问用户；都没有就不是「已有」，往 ③ 走。
- **补进正文还是 appendix**：这条证据直接回应核心质疑（影响录用的 substance 类）→ 正文；支撑性/补充性 → appendix，正文加一句指针。
- 补写时连带检查：新补的数字和正文已有叙述口径一致（协议、数据集版本、seed 数），别补出内部矛盾。

### ③ 补新实验 → 补实验项进清单（成本高，只给核心目的）

- **核心目的写成一句话**：回应什么质疑 / 确立什么主张（如「补 baseline Y 对比回应公平性质疑」）——这是 revision-brief.json 里 `补实验目的` 字段的内容，**设计交 writing-paper**。
- **写进清单前可行性确认三问**（和用户逐条过）：时限内做得完吗（Step 1 确认的 rebuttal 时限）？资源够吗（卡时 / 数据现成吗）？结果万一不利怎么办（备用降级方案先想好）？
- **承诺即兑现**——"We will add..." 写进 letter 就是欠债，AC 会盯着；做不到的承诺是 rebuttal 最常见的自杀。所有补实验项在 Step 3 汇总时统一做工作量盘点。

### ④ 降 claim / 承认局限 → 兜底（前三层都走不通时）

诚实降级比硬撑可信。三种降法（可组合）：

- **缩小适用范围**：claim 从「普遍成立」降到「在 X 条件下成立」，正文加适用条件限定。
- **弱化强度词**：significantly outperforms → performs comparably / achieves competitive results；删绝对化表述。
- **挪 future work**：做不到的验证声明移入 limitations / future work，诚实说明当前未覆盖。

**降完必须回查总论点**：被降的 claim 如果是总论点的承重墙，总论点就要改写——这动 blueprint 脊柱，**摆给用户并提示走 writing-paper 的 design-story 重塑**，不是 response 能单独拍板的。

## 六类 × 修改策略

总表（下面逐类展开）：

| 分类 | 一句话策略 |
|---|---|
| **misunderstanding** | 双管齐下：rebuttal 澄清 + 正文必须改 |
| **missing evidence** | 走阶梯：先查已有 → 真缺才补 → 补不了降 claim |
| **writing clarity** | 局部重写：reviewer 引的句子就是靶子 |
| **novelty concern** | 不嘴硬：补 differentiation（机制/设定/结果维度写具体） |
| **experiment concern** | 走阶梯 + 强化 fairness 声明 |
| **impossible request** | 替代证据 + 诚实说明限制；或降 claim |

### misunderstanding（误解）

- **怎么确诊**：reviewer 复述的你的方法/结论和成稿写的不一样。注意区分「真误解」和「reviewer 其实看懂了但觉得你没论证」——后者是 missing evidence，别按误解处理。
- **打法**：reviewer 会误读就是论文的锅，**双管齐下**——rebuttal 里澄清 + **正文必须改**（只回复不改正文是最常见错误，下一个读者还会误读）。定位 reviewer 引的原句 → 分析为什么会误读：歧义（一词两义）→ 换词或首次出现处加定义；位置偏（关键限定藏在后文）→ 限定前移；缺铺垫（结论先于动机出现）→ 补一句过渡。
- **常见错**：澄清时流露出指责 reviewer 的语气；只改 rebuttal 不改正文。

示例（comment-N 片段）：

```markdown
- 分类：misunderstanding
- 根因分析：reviewer 把 τ 理解为固定阈值，原文 §3.2 "τ is adapted" 的 "adapted" 没有展开机制，歧义词
- 稿件修改：§3.2 第二段 "τ is adapted" → "τ is adapted per-sample by EMA of the running loss (Eq. 4)"，首次出现处加指针
- 回复文本（firm）：We clarify that τ is adapted per-sample rather than fixed (§3.2, p5 L172 in revision)...
```

### missing evidence（缺证据）

- **怎么确诊**：reviewer 质疑的命题，成稿里确实没有证据支撑（查成稿 + 证据存货确认）。
- **打法**：走阶梯——先查已有证据（①②）→ 真缺才 ③ 补实验（给核心目的，设计交 writing-paper）→ 补不了 ④ 降 claim。**先想清楚 reviewer 要的证据强度**：有的质疑一个已有数字就能平（走①②），有的质疑的是方法有效性本身（多半要③）。
- **常见错**：能用已有数据回应的却承诺了新实验（白白欠债）；该正面补的用嘴硬糊弄（reviewer 二轮会抓）。

### writing clarity（表达不清）

- **怎么确诊**：reviewer 明说看不懂 / 反复要求 clarify，且不是误解（理解方向没错，就是读着费劲）。
- **打法**：reviewer 引的句子就是靶子，局部重写——长句拆短、术语首次出现给定义、段落主旨句前置。段级/节级问题（整节结构乱）进清单交 writing-paper 的 write-section 目标。
- **常见错**：只改 reviewer 引的那一句，上下文衔接断了；润色时顺手改了技术内容（表达改动不碰语义）。

### novelty concern（创新质疑）

- **怎么确诊**：reviewer 说和某工作一样 / incremental。先看 reviewer 引的对照工作是不是真的最接近（Step 1 证据存货 / problem-list 的 location 有没有引原文）。
- **打法**：**不嘴硬**。补跟最相近工作的 differentiation——对比段或对比表，差异写具体：机制（做法上差在哪一步）/ 设定（问题设定、假设）/ 结果维度（他们在 X 上好，我们在 Y 上好）。related work 漏引的补引（进清单）。差异说不清时老实走 ④：把 contribution 从「新机制」降为「新组合 + 实证收益」，实证收益就是证据问题（转 missing evidence 打法）。
- **常见错**：用「我们很不一样」式形容词辩护，不给具体差异；回避 reviewer 点名的那篇，挑软的对比。

### experiment concern（实验质疑）

- **怎么确诊**：baseline 不公平 / 设置不对 / 缺关键对照 / 数字对不上。
- **打法**：走阶梯 + **强化 fairness 声明**——baseline 公平性质疑 → `For fair comparison` 式声明写清对齐了什么（backbone / 训练轮数 / 数据增强 / 调参预算）；缺 baseline → ③（补实验项）或诚实说明选取理由；数字对不上 → 先核对自己有没有写错（写错了就是 erratum，直接认错改正文）。
- **常见错**：公平性质疑只回一句 "we followed standard practice"（没说清对齐了什么等于没答）；承诺补的实验和质疑不对口（reviewer 要效率对比你补消融）。

### impossible request（不可能要求）

- **怎么确诊**：要求的实验/分析在 rebuttal 时限内物理上做不完（重训全量模型、需要拿不到的私有数据），或与论文范围无关。
- **打法**：替代证据 + 诚实说明限制；或 ④ 降 claim。**给替代不给拒绝**——"做不了 X" 后面必须跟 "但我们做了/已有 Y，能部分回答您的关切"。替代证据走阶梯①②找。
- **常见错**：硬辩（越辩越像心虚）；一口答应然后兑现不了；态度上把 impossible 写在脸上（措辞对事："X requires retraining on the full corpus, which is beyond the rebuttal period; we instead provide Y..."）。

## 修改方案的质量标尺（「具体要求」字段）

`revision-brief.json` 的 `具体要求` 是 writing-paper 照着改的执行单——**写完自问：换一个没参与讨论的 agent，拿着这条能直接动手改吗？**

- **浅（没法执行，打回）**：「改 Method 部分使其更清楚」「加强实验部分的论述」。
- **深（可执行）**：「§3.2 第二段末加一句：τ 的逐样本自适应机制（Eq. 4），并把它和 reviewer 混淆的固定阈值用法区分开；§3.1 中 τ 首次出现处加指向 §3.2 的指针句」。

深度标尺：**落点（section + 锚点）+ 动作（加/改/删/挪什么）+ 内容要点（写什么，关键句可以直接给措辞）** 三样齐全才算可执行。补实验项除外——它不填具体要求，改填补实验目的。

## page-line 定位（每条必做）

rebuttal letter 的 Changes 要能和改稿对上——所以**逐条讨论时就定位**，别攒到汇总：

- **意见锚点**：reviewer 指的原文在哪页哪行（引原句）。
- **修改落点**：改动落在哪个 section + 锚点。锚点写法：摘原句 5~10 个词（够在全文唯一定位），或图表号 / 公式号（"Fig. 2 右半"、"Eq. 4 之后那段"）。**page-line 在 comment-N 里记录的是改前定位；letter 里的 page-line 栏留空，writing-paper 改稿完成后回填**（改稿后页码必变，写死必错）。

## 消费 problem-list.json 的字段

输入是 `writing-paper-review` **最新一轮**的 `problem-list.json`（round-N 取最大 N；人读 problem-清单.md 是派生物，别拿它当输入）时，每条已带机读字段（完整 schema 见 `writing-paper-review/references/problem-list-schema.md`）：

- **`severity=致命`** → 三层分流基本锁 **substance**：必须正面改 + 正面回应（rebuttal 里最能决定录用的条目，详答）。
- **`severity=改进`** → 多为 **polish / misread-risk**：可权衡，rebuttal 里一句带过或合并。
- **`type=合规`** → **不走六类策略讨论**：照 authorkit / venue 硬性要求改（页数 / 匿名 / 版式），没有策略空间，直接进清单（局部改）。
- **`type=指控成立`** → **按致命处理**——魔鬼代言人提出、AC 裁决成立的指控是最凶的攻击点，必须正面刚。
- 标签是输入先验不是铁律——逐条讨论时用户可推翻。

## 反模式

- **只回复不改正文**——misunderstanding / clarity 类，rebuttal 里解释得再好，下一个读者照样误读。
- **改正文忘了回 letter**——改稿和回复是一对：清单里的每项改动都要出现在 Changes 里（section + 锚点），别改完了 letter 还停在旧版。
- **承诺做不到的实验**——先过可行性三问再写进清单；letter 里的承诺 AC 会盯着兑现。
- **降 claim 降穿总论点**——承重墙 claim 被降，总论点必须改写，摆给用户走 design-story 重塑。
- **澄清时指责 reviewer**——措辞对事不对人；reviewer 误读是论文写得不够清楚，不是 reviewer 的问题。
- **用形容词代替证据**——"significantly better" 不如 "we added baseline Y, now +2.3%"。
