# Experiment Writing — Results（实验章·结果/分析）

`writing-paper` 写实验章节结果/分析部分的规则。Experiment 是三位一体的**「证明」面**——针对总论点设计实验，证明方法满足它。每个实验都要能回扣到总论点或子论点（contribution）。

> 本文件管**主结果 / 消融 / 分析**——**数据批到了之后由 ingest-results 写**，按 CPE 实际说明对齐（**不按原 plan**）：加/改的实验补进来、没跑的删掉、结果分析按报告。结果可信度消费 `claims.json` 裁决 + conclusion 可比性审计，**不在写作阶段重新审计**。
> 实验章为什么按数据可用性分两块写、各自职责见 `SKILL.md`。

## 默认结构 = goal 3（报主结果）+ goal 4（消融）+ goal 5（分析）

实验章 5 个 goal 按**数据可用性**切两块：**本文件写 goal 3+4+5**（数据批到了之后由 ingest-results 写）；goal 1 组织 / goal 2 Setup 不依赖真实结果，见 `experiment-writing-setup.md`。

| goal | 作者在想什么 | 何时写 |
|---|---|---|
| 1. 组织实验 | 怎么把实验对齐到总论点（RQ/维度/路线图） | 数据可用前（write-section） |
| 2. Setup | 数据/baseline/metric/实现怎么写清楚又公平 | 数据可用前（write-section） |
| 3. 报主结果 | 数字怎么报可信（防过度宣称） | 数据批到后（ingest-results） |
| 4. 消融 | 怎么证明组件必要性（防戏剧化） | 数据批到后（ingest-results） |
| 5. 分析 | 怎么解释机制为什么/边界 | 数据批到后（ingest-results） |

**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。** 篇幅紧时优先：setup、主性能、核心消融、一个最有解释力的分析。

## 逐 goal 写作技法

### goal 3：报主结果 —— 数字怎么报可信（防过度宣称）

**选择逻辑**：你的结果"强"在哪？
- 单点大幅领先 → 绝对分+对手名+对手分三件套
- 有劣势维度 → 让步反转（Although 对手更优，己方在 X 占优）
- 全面但小幅 → 先重选主战场（换评价维度/场景/约束，见「弱结果 / 负结果」），不得已才多维数字 + hedge

- ✓ **do：用具体可核验数字量化——绝对分+对手名+对手分三件套**
  - 为什么好：数字可逐条核对、可回查；具名对手给数字参照系。
  - 解剖："attaining an average score of 67.6, surpassing both Qwen3-VL-32B at 60.6 and Seed1.5-VL at 62.9."〔绝对分+两个具名对手分〕
- ✓ **do：让步-反转承认劣势再夺回**（`Although dense matchers outperform ours in accuracy, SRPose offers a significant advantage in speed...`），把让步变成反衬而非软肋。
- ✓ **do：数字后补机理性因果归因**（`The suboptimal performance of INSANet (mAP 13.80%) is due to...fixed static weights rather than...adaptive`），把横向对比升级为机理诊断。
- ✓ **do：结论先行/topic sentence**——每段第一句先抛可独立成立的结论，再展开表格数字。
- ✗ **dont：`the only method that simultaneously achieves...` 全胜宣言**
  - 为什么坏：全称/排他命题一个反例即崩，易判 over-claim。
  - 反例："Fine-Mem is the only method that simultaneously achieves high accuracy, controlled memory length, and consistent behavior..."
- ✗ **dont：断然否认存在 trade-off**（`does not come at the cost of quality...simultaneously improves both rather than trading one for the other`）——绝大多数方法有代价，断然否认不可信，该用让步反转诚实承认。
- ✗ **dont：用画面感强动词把性能落差渲染成"事件"**（`RoBERTa's accuracy collapses from 0.945 to 0.565, a 40% relative drop` + 先铺陈对手惨状再亮己方）
  - 为什么坏：用情绪/情节替代机理，读起来像推销；惨状铺陈诱导读者按叙事节奏而非证据下判断。该用"具体降幅+机理性归因"。
- ✗ **dont：把次要/单点发现外推成部署价值或宏大愿景**（`This property is attractive for deployment, since...` / `hints at the rational design of...`）——该用独立的下游/扩展实验证泛化，而非修辞外推。

### goal 4：消融 —— 怎么证明组件必要性（防戏剧化）

**选择逻辑**：消融怎么组织才可逐行核验？
- 多组件 → 勾选(✓)矩阵逐行累加（Base→+A→+A+B）
- 变体 → 统一短码命名（`w/o X` / 编号行号）
- 证必要性 → drop+confirm（去掉降多少→确认该组件 role）

- ✓ **do：消融用勾选矩阵逐行累加或 `+DR/+CA step by step` 增量**，每步只加/去一个组件，报绝对值与边际 Δ。
  - 为什么好：每个组件的边际贡献可量化、可单独归因、像可推演的因果链。
- ✓ **do：消融变体统一短码命名**（`Ours w/o X` / `(1)...(2)...` / 表格行号），定义处紧跟一句 `removing the...` 说明拆了哪块，读者从名字即反推。
- ✓ **do：`removing X causes the largest drop, confirming its role in...`** 把跌幅反证为组件必要性，把每行翻译成一句功能诊断。
- ✗ **dont：把消融写成"起承转合"戏剧叙事**（`Initially, employing solely DDC yields limited success...However, the subsequent integration...marks a significant enhancement...culminates in...`）
  - 为什么坏：把精确数字模糊成情节起伏，读者无法定位每个组件贡献多少、无法核验。该用勾选矩阵/增量 Δ 做可逐行推演的因果链。
- ✗ **dont：每个实验子块强制套 `Setup./Results./Insights./Takeaway.` 四段式 + 双重微总结**
  - 为什么坏：同一发现被反复重述（路标而非新证据），稀释信息密度。子节内只用 `Results→Discussion`（选择性，few），Takeaway 只在节末用一次（单层）。

### goal 5：分析 —— 怎么解释机制为什么/边界

**分析针对方法本身的核心机制**，系统完整探索——回答主性能/消融都不回答的问题。**和消融的区别**：消融证明"组件必要性"（去掉降多少）；分析解释"机制为什么/怎么/在哪失效"。

**系统探索四维度**（围绕机制）：

| 维度 | 回答 | 常见做法 |
|---|---|---|
| 机制验证 | 它真在做我们说的事吗 | probing / 中间量可视化 / 注意力图 |
| 敏感性 | 它对什么敏感 | 关键超参扰动 / 输入变化 |
| 边界 | 它在哪里不 work | 跨 setting / 域迁移 / 极端条件 |
| 错误分析 | 它怎么错的 | failure case 分类 / 错误来源 |

- ✓ **do：用研究问题/假设驱动分析**（`This motivates three key questions: (1)...(2)...` / `If X captures Y, Z should hold`），用 `To test this hypothesis` 引出对照实验让结果验证或证伪。
- ✓ **do：反直觉/异常发现标记成卖点并机理解释**（`Surprisingly, ...` + 立即给机理或命名固定术语）；符合直觉的对照用 `as expected` 建立基线预期。
- ✓ **do：排除替代解释/对照实验证伪坐实因果**（`This rules out the explanation that...is merely due to...`），主动设计对照排除最自然的替代解释（更大 backbone/更多参数/挑数据/泄露）。
- ✓ **do：定性可视化/前后对照佐证机制**（t-SNE / baseline 失败 vs 我方成功），与数字交叉印证。

## 弱结果 / 负结果

**原则：诚实度不变，进攻性拉满。** 弱结果一个不许藏（op-7 诚实性 lens 查），但呈现方式按下面的决策程序走——先换框架，最后才软化措辞。语言层的措辞禁令见 `word-craft` 原则 4（不 under-claim）。

**决策程序（按优先级，靠前优先）**：

1. **是否必须讨论？** 与核心主张无关的弱结果不进入主线；与核心主张相关的必须报（藏短 = 诚信问题）。
2. **能否换框架解释？** 从目标差异、约束条件、适用场景重新定位：这不是"输了"，是"这场比赛本来就不是本文要赢的"。
3. **是否体现合理权衡？** 明说拿什么换了什么（精度换 1/5 训练成本），权衡是设计选择不是失败。
4. **能否收缩主张？** 把 claim 的 scope 收到证据牢固支撑的范围内，避免无意义的正面对撞；该收缩的是 scope，不是语气。
5. **是否该移出核心论证？** 这个结果不该再承担证明核心贡献的职责——挪作分析/边界材料，或触发回 design-story 换故事（见 op-5 否定信号触发）。
6. **以上都不可行且确实影响核心结论** → 才必要说明，用边界声明的姿势（适用范围/条件），不用道歉式措辞。

- ✓ **do：边界声明**——`On data-constrained settings, our method matches the strongest baseline at 1/5 the training cost.`（同一个"小数据集上提升有限"的事实，声明适用范围 + 亮出交换来的优势）。
- ✓ **do：让步反转夺回**（goal 3 的选择逻辑）——承认劣势维度后立即把读者带到占优维度。
- ✓ **do：用分析实验解释边界**——弱结果配一个 goal 5 的边界/错误分析，把"不行"变成"知道在哪不行、为什么"。
- ✗ **dont：预防性示弱措辞**——*unfortunately / only achieves / limited improvement / modest gains / still lags behind*（`check_ai_tells.py` 硬查）。这是替审稿人完成论证。
- ✗ **dont：局部上升为整体**——某个 setting 不占优写成对方法整体的否定；也不提炼成结论。
- ✗ **dont：藏短**——明显失败必须报，且和 Conclusion 的局限一致（不能正文回避、结论才承认）。
- ✗ **dont：辩解性 reframe**——把弱点包装成特性或普遍规律（结论局限段的同款禁令，见 `conclusion-writing` goal 3）。换框架 ≠ 强行洗白：解释必须本身站得住。

## 按 CPE 实际对齐（ingest-results 必做）

- CPE **加**的实验（plan 没有但跑了）→ 补进 section/appendix。
- CPE **改**的实验（配置变了）→ setup 按实际改、结果按实际。
- **删**掉没跑的（plan 有但 CPE 没跑）→ 别留空 claim。
- 结果分析按 CPE **报告**（不按原 plan 的预期数字）。

## 全节自查（反模式信号清单 · 结果/分析相关）

写完逐条勾：

- [ ] 主结果是否用了 `significant/effective` 空泛词，或 **`the only...simultaneously` 全胜宣言**？
- [ ] 是否**断然否认 trade-off**（`does not come at the cost of`）？
- [ ] 是否用**戏剧化动词渲染落差**（collapses / plummets + 对手惨状铺陈）而非降幅+机理归因？
- [ ] 是否把次要发现**外推成部署/愿景价值**（attractive for deployment）而不补实验？
- [ ] 消融是否写成**起承转合戏剧叙事**（Initially/However/culminates）而非增量矩阵？是否强制**四段式+双重微总结**？
- [ ] 弱结果是否走了决策程序（换框架/权衡/收缩 scope 优先），还是直接软化措辞了事？
- [ ] 是否有预防性示弱措辞（unfortunately/only achieves/limited improvement/still lags behind）或把局部弱结果上升为整体否定？
- [ ] 弱结果是否全部如实报了（无藏短），且与 Conclusion 局限一致？

> setup 部分的反模式（baseline 公平 / metric 标准 / 覆盖维度 / data leakage）见 `experiment-writing-setup.md`。

## 与全文协同（三位一体）

- 每个实验回扣总论点的一个维度（ref C-ID）；主结果数字 = Abstract 第 4 句。
- 弱结果/边界和 Conclusion 的局限一致（不能正文回避、结论才承认）。

## 文风 lint

写完按三层 craft 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# 实验章 results 写作计划（数据批回填）
## 1. 按 CPE 实际对齐：加/改/删实验
## 2. 主结果叙述（三件套数字 + 机理归因）
## 3. 消融叙述（增量矩阵 + drop+confirm）
## 4. 分析（四维度）
## 5. results 自查逐条勾 + Reviewer 风险清单
```
