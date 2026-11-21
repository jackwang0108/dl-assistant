# Word Craft（字词层工艺）

`writing-paper` 的**字词层**工艺——**选词原则**。每个 section 写完由 write-section ③ 自审跑，audit 的润色 lens 全文润色再跑。

> 和 `sentence-craft.md`（句段层）、`anti-ai-patterns.md`（AI 禁止模式）正交。论证策略级反模式在各 section reference。下面每条原则后的"例"只是 anchor（非穷举词表）——**按原则判任何词**。

---

# 原则

## 1. 可核验
每个关于 magnitude / importance / cost 的断言要有**可核验支撑**（数字 / 形式化性质 / 具名对比）；assert 不出来就别写。
- 例：*significantly / substantially* → 给相对 % 或绝对数；*prohibitively expensive* → 报人年/美元；*essentially free / zero-cost* → 报 FLOPs / 参数量。

## 2. 精确匹配含义
状语 / 定语 / 谓语贴**真实机制**，不图响亮，不用画面感词替代机制词（画面感见 `anti-ai-patterns` 文艺腔）。
- 例：*novel / unified / comprehensive / powerful*（generic 空泛）→ 给方法一个 named-abstraction（见 `blueprint`）。

## 3. 不 over-claim（scope）
claim 精确**等于**已证的。全称 / 排他 / 首创堆砌都是 over-claim；存疑就 hedge，首创说一次 + 命名固化。
- 例：*the only … simultaneously / outperforms all / strictly dominates* → 具体分数 + 具名对手分；*for the first time* → 说一次，存疑用 *to our knowledge*。

## 4. 不 under-claim（不自我削弱）
claim 精确等于已证的——**也不许小于**已证的。优势满强度主张；局限一个不少，但写成**边界声明**（适用范围 / 条件 / 权衡），不写成**道歉**（预防性示弱）。判据：这句话是在陈述证据的边界，还是在替审稿人攻击自己？
- 禁预防性示弱表达：*unfortunately / regrettably / only achieves / merely / limited improvement / modest gains / still lags behind / remains inferior* → 删掉或改写成边界声明。
- 同一个局限两种写法：道歉式 *Unfortunately, our method only achieves limited improvement on small datasets* → 边界式 *On data-constrained settings, our method matches the strongest baseline at 1/5 the training cost*——信息量不变，姿态不同。
- 局部现象不上升为整体否定：某个 setting 不占优 ≠ 方法不行；该收缩的是主张的 scope，不是语气。
- 决策程序（先换框架，最后才软化措辞）见 `experiment-writing-results.md` 的「弱结果 / 负结果」。

## 5. 证据不标签
别给自己的构造设计贴**原理性标签**；该用定理 / 形式化证明，或为真实现象命名。
- 例：*principled / fundamental observation / central principle / deliberate* → 证明或命名，不贴标签。

## 6. 术语一致 / 功能词变化
**技术实体**（方法名 / 模块名 / 术语）全篇一致；**功能词**（不承载术语身份的动 / 形 / 副）可轮换避免单调。判据：这词**承载术语身份**吗？是 → 一致；否 → 可变。
- 例：方法名全程同一个（别 *our method / framework / approach* 乱换）；*propose / introduce / present* 可轮换。
- 边界对接 `anti-ai-patterns` 的"禁概念轮换"。

## 7. 强调靠稀缺
戏剧副词只在**真转折 / 反直觉发现**低频用——强调的价值来自稀缺，高频稀释。
- 例：*Crucially / Strikingly / Remarkably / in sharp contrast / Notably* → 低频；递进用 *Furthermore / Additionally*。

## 8. 简洁 + active
用**最紧凑的结构**承含义；主语做动作为主（passive 只在方法描述必要处）。
- 例：*in order to* → *to*；*it is worth noting that* → 删；*The feature is extracted by the encoder* → *The encoder extracts the feature*。

---

# 自查 checklist

```markdown
## 字词层自查
- [ ] magnitude/importance/cost 断言都有可核验支撑（数字/形式化/具名对比）
- [ ] 用词精确匹配真实机制（不空泛、不用画面感词）
- [ ] claim 精确等于已证（无全称/排他/首创堆砌；存疑已 hedge）
- [ ] 无自我削弱（无 unfortunately/only achieves/limited improvement 类预防性示弱；局限写成边界声明而非道歉；局部现象未上升为整体否定）
- [ ] 无自贴原理性标签（principled/fundamental/central）
- [ ] 技术实体全篇一致；功能词有变化（判据：承载术语身份？）
- [ ] 戏剧副词低频（只在真转折/反直觉）
- [ ] 简洁（无冗余短语）+ active voice 为主
```

> 不是 railroad——给原则，按原则判，只拦"不可核验 / 不精确 / over-claim / 自我削弱 / 自夸 / 术语乱 / 滥强调 / 冗余被动"。
