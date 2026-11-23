# Conclusion Writing

`writing-paper` 写结论的详细规则。Conclusion 不是 Abstract 的复读——在读者已读完全文的前提下，收束 claim、诚实说局限、指方向。**最后写**。

## 默认结构 = 5 个写作决策点（goal）

**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。**

| goal | 作者在想什么 | 对应段 |
|---|---|---|
| 1. 回扣核心 | 怎么收束已证明的（不复读 Abstract） | P1 |
| 2. 升华 take-away | 读者带走什么超出数字的洞察 | P2 |
| 3. 诚实局限 | 怎么说局限不伤核心贡献 | P3 |
| 4. 未来工作 | 由局限引出什么具体方向 | P4 |
| 5. 收尾（可选） | 用什么留最后印象 | — |

## 逐 goal 写作技法

### goal 1：回扣核心 —— 怎么收束已证明的（不复读 Abstract）

**选择逻辑**：怎么收束？
- 首尾呼应 → 镜像摘要/引言的命题句、贡献清单与编号
- 回扣洞察 → 回扣开篇的核心 insight/张力形成问答闭环

- ✓ **do：首句镜像复述方法定位**（`In this paper, we proposed NAME, a [定位] for Z`），措辞与摘要/引言同构呼应（不逐字照抄），语气从许诺转为已交付。
  - 解剖："In this paper, we propose KTV, a novel training-free, two-stage framework that addresses the critical challenges of temporal and spatial redundancy..."〔方法名+定位+所解挑战〕
- ✓ **do：回扣开篇的核心洞察/张力形成问答闭环**（`Our approach is based on the key insight that...`），把贡献重新嵌回开篇问题。
- ✓ **do：复用引言/摘要的标志性措辞**（首创声明、命名术语、核心张力句）强化方法品牌与首尾呼应，但**不引入新 claim**。
- ✗ **dont：用 `by X-ing / by Y-ing / by Z-ing` 并列动名词长句把方法全链路压成一句繁复排比复述**
  - 为什么坏：等于在结尾又写了一遍 method，冗余且削弱收束感；顶会只用轻量动作动词链且本就罕见（singleton）。
  - 反例："By computing temperature-scaled interactions..., adding a soft positional bias..., and applying an outer length normalization..., step-attention provides structured credit assignment"
- ✗ **dont：把多个失败模式与多个组件做成 `resolves X through A / resolves Y through B` 一一映射矩阵收束**
  - 为什么坏：把多元贡献拆散成对号入座的 checklist，丧失叙事统一性与中心主张穿透力；顶会回扣单一核心洞察形成首尾闭环。
- ✗ **dont：结论首句用 `first-of-its-kind / 范式命名` 等最大化标签总括全文，结尾措辞比摘要引言更强更夸张**
  - 为什么坏：结尾突然拔高措辞，易读成过度宣称，破坏首尾的等价镜像。该用中性方法名+一句话定位，措辞与摘要同构。

### goal 2：升华 take-away —— 读者带走什么超出数字的洞察

**选择逻辑**：你想让读者记住什么？
- 一个可迁移原则 → 升华到设计原则/范式
- 一个领域级洞察 → 核心论点标签句
- 多个收益 → not only...but also 打包

- ✓ **do：升华到领域级意义/设计原则/核心洞察**（`Together, our results establish X as a critical design principle for...`），给读者可被引用、可记忆的 take-home。
- ✓ **do：把数字升华成可迁移洞察或方法论建议**（`A hybrid pipeline is recommended: use X for..., followed by Y for...`），独立于表格的 take-away。
- ✓ **do：贡献拔高到范式/agenda**（`removes the barrier to...` / `a new paradigm`），但必须为此负责（有证据支撑）。
- ✗ **dont：号召式 `encourages the community to treat X as a first-class task` 替领域立法**
  - 为什么坏：单篇工作替整个领域定义议程与任务分级，越界自我赋权，易招反弹。顶会 hope/inspire 是谦逊定位为开放起点（`serves as a good entry point`），不替社区立法。
- ✗ **dont：作者自评排出"最耐久/最重要贡献"**（`We see VOLTBench and the attention-trace methodology as the more durable contributions`）
  - 为什么坏：越权替读者做价值排序、试图操纵记忆与引用；顶会平等复述贡献清单，让证据和方法本身说话。
- ✗ **dont：给方法自封 `primitive / vocabulary / recipe / toolkit` 等"概念基础设施"大名字**（目的是"提高被继承引用的概率"）
  - 为什么坏：为引用而包装的空壳命名，读者无法从"它是个 primitive"判断实际适用面；顶会靠具体罗列多个下游场景证可复用性。
- ✗ **dont：把核心发现压成分号串成一句的"金句列表"**（`finding A; finding B; and finding C`）
  - 为什么坏：牺牲可扫读性换格言感，读起来像刻意打磨的口号；顶会用编号 (i)(ii)(iii) 清单逐条铺陈。

### goal 3：诚实局限 —— 怎么说局限不伤核心贡献

**选择逻辑**：局限怎么呈现？
- 有具体失败场景 → 显式声明+点出可定位失败
- 有缓解/出口 → 局限即配 future work
- 有代价 → 让步软化量化

- ✓ **do：显式声明局限并点出具体失败场景**（`AlignDiff may fail on tasks with drastic domain gaps, such as medical image segmentation`），先于审稿人点出质疑，以坦率换可信度。
- ✓ **do：局限即配具体可执行 future work 出口**（`While our method performs well...it still causes a slight drop...To fix this gap, one potential direction is to...`），把"没做"包装成可接力路线图。
  - 解剖：让步承认局限→紧跟具体方向（点名 benchmark/技术手段）。
- ✓ **do：局限后配缓解/让步软化**（置换检验、消融自证、`while/despite` 让步、量化代价反证可承受），使弱点读起来是被管理的。
- ✓ **do：Limitations 开门见山点名核心局限**（`The main limitation of X lies in...`），用计数框架（`two primary limitations merit consideration`）。
- ✗ **dont：把自家局限辩解性地 reframe 为特性或规律**（`We prefer a different interpretation: Hebbian learning is a transient phase...`）
  - 为什么坏：把缺陷诠释为特性、把巧合上升为规律，辩解性 spin 削弱可信度；顶会只学术性地 reframe 领域共识（不 reframe 自家短板），局限直接承认并管理。
- ✗ **dont：给每条局限都强制配一句缓解/future work 出口**
  - 为什么坏：把真实弱点一律包装成"已意识可补救"，像防御性辩解、淡化问题；顶会把缓解设为可选（"如可能"），无解的局限直接老实承认。
- ✗ **dont：把局限防御性外推为"整个子领域共有/任务固有上限/继承自教师模型"**
  - 为什么坏：把锅甩给领域/任务而非公允对待短板；顶会对局限做建设性正向收尾（缓解/future work/non-goal 边界/让步反转守住贡献），或单设失败分析章节主动坦陈。
- ✗ **dont：用多层证据等级标签 + 把数字重框成缓冲表述做过度对冲**（`working hypothesis / correlational / plausibly / readers should treat the absolute numbers as a point-in-time measurement rather than a permanent verdict`）
  - 为什么坏：把贡献埋进层层限定里，读起来不自信、重点模糊；顶会只在真正不确定处用单层轻量 hedge（`We posit that...` / `This suggests...`）。
- ✗ **dont：把单点发现外推成 `general principle that may generalize to [更广领域] + leave to future work`**
  - 为什么坏：虚涨显著性又不背书——声明普适性却把验证推给未来，既无法被本文证据支撑、也无法被立即反驳。

### goal 4：未来工作 —— 由局限引出什么具体方向

**选择逻辑**：方向怎么写不空泛？
- 多方向 → 编号清单（每条可操作下一步）
- 谦逊定位 → 定位为起点/initial step

- ✓ **do：未来工作写成编号方向清单**（`Future work should (i)...(ii)...(iii)...`），每条给可操作的下一步（点名数据集/方法变体/带引用的解法），由本文实验发现的不足支撑。
- ✓ **do：谦逊定位为起点/initial step**（`We hope our study offers an initial step toward...` / `a solid starting point`），降预期同时邀请跟进。
- ✓ **do：未来方向诚实标注代价**（`Thinking models override position bias at substantial cost (~6x output tokens); distilling this...remains open`）。

### goal 5：收尾（可选）—— 用什么留最后印象

- ✓ **do：用具体数字/倍数而非套话收束**（`more than 20x speedup` / 与摘要对称的 headline 数字），留一句可被单独引用的浓缩结论。
- ✓ **do：落地展望/部署友好**（`a practical recipe for...` / 列举具体下游应用场景），但要有部署证据支撑。
- ✓ **do：抛出显式 open question 点名未来方向**（`A compelling open question is whether...`），把本文边界转化为可被后续追问的具体课题。

## 全节自查（反模式信号清单）

写完逐条勾：

- [ ] 是否用 `by X-ing/by Y-ing` **动词链排比重铺方法**？或 `resolves X through A/resolves Y through B` **一一映射矩阵**？
- [ ] 首句是否用 **`first-of-its-kind`/范式命名**在结尾突然拔高措辞？
- [ ] 是否**号召社区替领域立法**（`treat X as a first-class task`）？**自评耐久贡献**（`the more durable contributions`）？**自封 primitive 大名字**？
- [ ] 核心发现是否压成**分号金句列表**（非编号清单）？
- [ ] 局限是否**辩解性 reframe 为特性**？是否**每条强制配出口**？是否**外推为子领域共有天花板**？是否**多层证据等级过度对冲**？
- [ ] 是否把单点发现**外推成 general principle + leave to future work**？
- [ ] （现有保留）是否**引入了新 claim**（正文没证明的）？局限是否和 Experiments 暴露的弱结果一致（不能正文回避、结论才承认）？未来工作是否具体不空泛？

## 与全文协同（三位一体）

- P1 回扣的 contribution = 引言的 contribution 列表 = `blueprint.md` 的 Contribution（首次完整呈现后，此处收束）。
- P3 的局限和 Experiments 暴露的弱结果/边界一致。
- 某 limitation 可靠补实验消除 → 产实验计划包回 `code-paper-experiment` 补，不写进局限。

## 文风 lint

写完按句段、字词和常见生成式写作问题三类写作要求 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# Conclusion 写作计划
## 1. 五个 goal 逐段要点（回扣/升华/局限/未来/收尾）
## 2. 局限清单（真实边界，不伤核心 Contribution；与 Experiments 弱结果一致）
## 3. 未来工作方向（具体可操作，由局限引出）
## 4. Conclusion 草稿（英文）
## 5. 反模式信号清单逐条勾 + 无新 claim 自查
```
