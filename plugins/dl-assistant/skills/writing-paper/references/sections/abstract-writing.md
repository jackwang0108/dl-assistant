# Abstract Writing

`writing-paper` 写摘要的详细规则。Abstract 是全文的最小投影——把 `blueprint.md` 的一句话核心主张压缩成一段读者 30 秒能抓住的话。**最后写**（全文定型后才好收口）。

## 默认结构 = 5 个写作决策点（goal）

挂靠 `blueprint.md` 的章节叙事"摘要"，按下面 5 个决策点展开成 4-6 句。每个 goal = 作者那一刻在想什么。**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。**

| goal        | 作者在想什么                   | 对应句             |
| ----------- | ------------------------------ | ------------------ |
| 1. 立正当性 | 怎么开头让审稿人觉得这事值得做 | 第1句 背景/价值    |
| 2. 切空白   | 我的 gap 怎么说才不像 strawman | 第2句 缺陷         |
| 3. 介绍方法 | 方法怎么一句话讲清楚           | 第3句 方法         |
| 4. 报结果   | 结果不算最强，怎么报可信       | 第4句 结果         |
| 5. 收尾升华 | 最后一句留什么印象             | 第5句 意义（可选） |

## 逐 goal 写作技法

每个 goal 下：先「选择逻辑」（什么情况用什么打法），再 `✓ do`（推荐做法）和 `✗ dont`（反模式）平级列出。do 带「为什么好 / 怎么写 / 解剖」，dont 带「为什么坏 / 自查信号」。例句给顶会好句 vs AI 坏句对照。

### goal 1：立正当性 —— 怎么开头让审稿人觉得这事值得做

**选择逻辑**：正当性靠什么立？

- 任务本身有高层价值 / 广泛应用 → 任务价值 + 应用清单
- 任务是某学科基石 / 长期目标 → 学科级愿景或共识
- 你的发现反直觉 / 挑战共识 → 反直觉钩子
- 你有初步实验发现 → 经验观察引爆

- ✓ **do：用任务的高层次价值或应用清单立正当性，语气中立**
    - 为什么好：靠价值本身和应用数量倒推重要性，不空喊 important。
    - 怎么写：一句话点任务价值 + 一串具体应用（数字电视/AR/会议等），用数量与多样性说话。
    - 解剖："Reconstructing humans and their environments in a globally consistent 4D space is essential for comprehensive perception."〔一句话立价值，不铺垫〕
- ✓ **do：定义式或现象式陈述开篇锚定领域**（直说任务是什么/范式是什么）。
- ✓ （备选）反直觉钩子 `challenges the conventional wisdom` / 经验观察引爆 `we empirically show`。
- ✗ **dont：用危机/经济/伦理等道德色彩框架放大严重性**
    - 为什么坏：带推销色彩，显得在为问题造势而非客观陈述，反而降低可信。
    - 自查：开头出现伦理/公平/经济成本/现实利害框架。
- ✗ **dont：堆 `arbitrarily close / wasteful / prohibitively` 等价值判断形容词**（→ 该用可核验数字，见 goal 2）。

### goal 2：切空白 —— gap 怎么说才不像 strawman

**选择逻辑**：你的 gap 是哪种？

- 前人方法在某边界失效、有数据 → 让步转折锚具体失效
- 前人依赖一个不成立的隐含假设 → 揭假设
- 领域被两类互斥范式瓜分、各有代价 → 二分/两难，腾出第三位置
- 是普遍现象但没人命名定位过 → 命名根因，占概念资产

- ✓ **do：单一让步转折（While/Although...However）一句同时完成背景+痛点**
    - 为什么好：让步先公允承认前人真实成就（不 strawman），转折把失效钉在可陈述的事实上；一句话压缩，不单独占问题段。
    - 怎么写：让步=前人的具体能力/进展（带术语），转折=失效边界（尽量带数字或具名场景）。
    - 解剖："3D Gaussian splatting enables high-quality NVS at real-time frame rates〔让步：锚真实成就〕. However, its quality drops sharply as we depart from training views〔转折：失效边界〕."
- ✗ **dont：多层转折螺旋堆叠（方案→缺陷→新方案→新缺陷）**
    - 为什么坏：每层缺陷都被下一个方案稀释，没有一个痛点真正立住；暴露"为造 gap 而造 gap"的刻意；拉长摘要。
    - 自查：≥2 层 `However / Yet / Furthermore` 链，或"方案紧接其缺陷再引新方案"。
    - 反例："To address this, recent RL methods adopt...but frequently overlook...Furthermore,..."
- ✓ **do：把缺陷归因到可命名根因**（`We attribute...to...` / `stems from`）或**暴露隐含假设**（`implicitly assuming`）。
    - 为什么好：把表面症状翻译成可下手的机制问题，既让"前人为何不行"可追，又为方法的"对症设计"埋好因果锚点。
- ✓ **do：用可核验数字/工程代价给严重性定级**
    - 怎么写：相对下降% / 绝对开销（人年·美元·GPU）/ 具体阈值（dB·延迟），配具名对手或基线做锚点。
    - ✗ 反面：堆 `substantially / significantly` 极限量词（不可核验、带推销色）。
- ✓ **do：gap→方法用桥接句** `To address this gap, we propose NAME` 干净闭合。
    - ✗ 反面：插 `Consequently, X is imperative...` 必然性演绎句——必要性已由 gap 本身承担，再强调像在替方法做广告。

### goal 3：介绍方法 —— 方法怎么一句话讲清楚

**选择逻辑**：你的方法"新"在哪？

- 新在是首创 / 范式级 → `the first` 声明 + 范式命名
- 新在某个核心洞察 → `key insight` 标签句
- 新在组合 / 工程 → 组件配收益句式

- ✓ **do：`We propose NAME (FullName), a [定位] framework that [一句话机制]`**
    - 怎么写：NAME 做成自解释缩写或复合名词，首次给全称+缩写，后文统一用缩写，术语和 Method/Experiment 一致。
- ✓ **do：组件配收益句式**（`NAME introduces X to prevent Y` / `..., enabling Z`），机制与收益一一绑定。
- ✓ （按情况）首创声明带 hedge：`To the best of our knowledge, the first...`，抢占身位又留余地。
- ✓ （按情况）`Our key insight is that...` 标签句前置核心思想。
- ✗ **dont：多处反复堆 `for the first time / to our knowledge`**
    - 为什么坏：强首创说一次即可，多处堆砌显得硬卖、触发 over-claim 怀疑。
    - 自查："首次"类声明出现 ≥2 处。

### goal 4：报结果 —— 结果不算最强，怎么报可信

**选择逻辑**：你的结果"强"在哪？

- 单点大幅领先 → 头条数字 + 具名对手
- 全面但小幅 → 先重选主战场（摘要报的是最强维度上的数字；评价维度的重选回 design-story / ingest-results 定，不在摘要层临时找补），不得已才多维数字 + hedge
- 有代价 / 让步 → while 对偶 + 让步反转

- ✓ **do：落到具体可核验数字，配具名锚点**
    - 为什么好：数字可被审稿人核验、可被引用；具名对手给数字一个参照系。
    - 解剖："improves unlearning effectiveness by at least 50.1% and robustness by at least 37.2% on Llama-2-7B"〔数字 + 具名模型〕
- ✗ **dont：用 `significant / effective` 等空泛形容词；或 `the only method that simultaneously achieves...` 全胜宣言**
    - 为什么坏：全称/排他命题一个反例即崩，易判 over-claim。
    - 反例："the only method that simultaneously achieves high accuracy, controlled memory length, and consistent behavior..."
- ✓ **do：`while`/对偶打包收益与零代价**（`improve A while maintaining B without C`）。
- ✗ **dont：断然否认存在 trade-off**（`does not come at the cost of` / `simultaneously improves both`）
    - 为什么坏：绝大多数方法有代价，断然否认不可信；用 `Although 对手更优，己方在 X 占优` 的让步反转诚实承认更可信。
    - 自查：出现 `not at the cost of / simultaneously improves both`。
- ✓ **do：hedge 软化**（`up to / potential / on most metrics`），把精确数字留正文——**只在主战场已选定、数字本身需要限定时用**；不用 hedge 把弱结果包装成可接受（那是防御性写作，见 `word-craft` 原则 4）。

### goal 5：收尾升华 —— 最后一句留什么印象

**选择逻辑**：你想让读者记住什么？

- 一个可迁移原则 → 升华到设计原则
- 一个新资源 → 数据集/工具打包成贡献
- 可复现性 → 代码链接收尾

- ✓ **do：升华到可迁移的设计原则或对领域的诊断洞察**（口语化对称句），或加泛化声明 `Beyond X, we further...`。
- ✓ **do：把数据集/产物命名打包为独立贡献**（规模+划分+属性枚举）。
- ✓ （可选）开源/资源链接收尾，把可复现性前置到高曝光位置。
- ✗ **dont：号召式 `encourages the community to treat X as a first-class task`**
    - 为什么坏：单篇工作替整个领域立法、定义议程，越界自我赋权，易招反弹。

## 全节自查（反模式信号清单）

写完逐条勾：

- [ ] 开头是否用了危机/伦理/道德色彩框架，或堆价值判断形容词（`arbitrarily close / wasteful`）而非可核验数字？
- [ ] 切空白是否**多层螺旋堆叠**（≥2 层 However/Yet/Furthermore 链）？
- [ ] gap→方法间是否插了 `Consequently, X is imperative` 必然性演绎句？
- [ ] 结果是否用了 `significant/effective` 空泛词，或"全胜/唯一"全称宣言？
- [ ] 是否**断然否认 trade-off**（`does not come at the cost of`）？
- [ ] 收尾是否号召社区/替领域立法（`treat X as a first-class task`）？
- [ ] （现有保留）每个强 claim 正文是否有证据？强首创是否只说一次？不堆缩写、不引参考文献、不写公式？长度按目标会议惯例（见 `_draft/venue-contract.md`）？

## 与全文协同（三位一体）

- 第 2 句缺陷 = 引言的 gap = Related Work taxonomy 终点。
- 第 3 句方法 = `blueprint.md` 的一句话核心主张（named-abstraction 术语全篇一致）。
- 第 4 句结果 = Experiments 主结果表的关键数字。

> Abstract 写完做一次反向检查：它许诺的每一点，正文都兑现了吗？

## 文风 lint

写完按三层 craft 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# Abstract 写作计划

## 1. 五句式逐句草稿（中文要点 → 英文成稿）—— 每句先定 goal、再按「选择逻辑」选打法

## 2. 关键数字来源 | 数字 | 出处(实验表) |

## 3. Abstract 草稿（英文）

## 4. 一致性自查（每句 ↔ 正文证据）+ 反模式信号清单逐条勾
```
