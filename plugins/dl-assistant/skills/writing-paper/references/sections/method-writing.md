# Method Writing

`writing-paper` 写方法的详细规则。Method 是三位一体的**「实现」面**——把总论点的具体实现讲清楚（Introduction 讲动机 / **Method 讲实现** / Experiment 讲证明）。不是代码说明书——把模块/数据流/loss/训练抽象成读者能理解、能复现、能相信的技术机制。

## 章节组织源头：代码核心改动的几个 part

内容组织最根本的源头是**代码里核心改动的几个 part**（读中期 repo 识别），不是从动机硬推结构。每个核心改动 part 对应一小节，组织上可呼应动机（part 顺序按叙事逻辑排），**part 之间要有逻辑递进**（backbone→neck→head，或 feature→fusion→loss）。方法简单就别硬拆，宁可 2-3 个清楚小节，不要 6 个空泛模块。

## 区分机制 / 实现 / 工程（三层）

| 层级 | 放哪里 | 示例 |
|---|---|---|
| 核心机制 | Method 主体 | 新的 matching / refinement / routing / training objective |
| 必要实现 | Method 末尾或 Impl Details | backbone、optimizer、采样方式、prompt 格式 |
| 工程细节 | Appendix 或不写 | 文件结构、wrapper、debug 参数 |

只把**支撑 claim**（ref `blueprint.md` 的 Contribution）的内容放进正文主线。

**不收什么**：训练细节（超参 / optimizer / lr schedule / 训练时长 / 实现细节数值）**不收进 Method**——那是 reviewer 复现 checklist 的内容，归实验节 setup（`experiment-writing-setup.md`）。Method 只讲方法本身：机制、数据流、目标函数。边界判断：删掉它方法还讲得清 → 归实验节；删掉它机制不完整（如训练目标本身是贡献）→ 留 Method。

## 读代码写方法

写实现细节要读真实代码时，**代码在 GPU 服务器（中期 repo）——找用户弄到本地或远程读**。读 forward/loss/train 脚本，提炼成论文表述（写抽象，不逐行解释调用链）。

| 代码事实 | 论文写法 |
|---|---|
| `forward()` 中 concat 两个 feature | fuse complementary evidence from … |
| loss 里加权多个项 | optimize a joint objective balancing … |
| 多阶段训练脚本 | decouple representation learning from task adaptation |

> 注意：上表是**示意，不是查找表**。同一个 `concat` 在不同论文可能是"融合互补证据"也可能只是无关紧要的实现细节——**真实写法取决于这个操作在你论文里实际承担的方法角色**（结合 `blueprint.md` 的 Contribution 判断），别看到代码模式就套对应短语。套模板会写出"听起来高级但失真"的方法描述。

## 符号体系构建（写 Method 先建符号表）

公式是 Method 的主体，符号是公式的地基。**动手写正文前先把符号表建出来**，落 `_draft/content/notation.md`——边写边造符号必然前后打架，事后统一成本极高。

**总原则：够用、精简、好理解。**

- **够用**：符号只服务论证需要——每个符号都要在至少一个公式/定义里承担角色，没进公式的概念不符号化。
- **精简**：没必要的符号一律不加。能用自然语言说清的概念（"the input image"、"the teacher model"）就别给符号；符号越少，读者要维护的心智映射表越短。一个概念犹豫要不要符号化时，默认不符号化。
- **好理解**：优先用**社区通行符号**（该领域读者已经习惯的记号，如注意力里的 Q/K/V、概率里的 p/q、损失里的 L）——造一套"自己体系内更优雅"的新记号，是把学习成本转嫁给读者。

**一致性约定**（建表时就定死）：

- **大小写/字体分层**：标量小写斜体（x, α）、向量小写粗体（**x**）、矩阵大写粗体（**W**）、集合大写花体/直立体（𝒟, X）——全篇一套约定，不混用。
- **下标语义稳定**：同一类下标全篇同一含义（i 永远是样本索引、l 永远是层号），不在不同节里复用同一个字母指不同东西。
- **每个符号定义一次**：首次出现处定义（公式后 `where` 逐符号释义），之后直接用；不重复定义、不中途改义、不让两个符号指同一个东西（同义符号合并）。
- **和方法图对齐**：总览图/模块图上标注的符号 = 正文符号，图与文共享同一套记号。

符号表定稿后**注入后续各节写作 prompt**（Method 各小节、Experiment 的分析式子、Appendix 的证明都消费同一份 `notation.md`），不是各写各的再对表。写后续节时新引入符号 → 先回 `notation.md` 补登记，再用。

## 默认结构 = 5 个写作决策点（goal）

**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。**

| goal | 作者在想什么 |
|---|---|
| 1. 组织骨架 | 方法节怎么组织（part / 路线图 / 符号） |
| 2. 讲机制 | 每个模块怎么讲清楚（动机先于公式） |
| 3. 辩护设计选择 | 为什么这么设计（防过度辩护） |
| 4. 符号命名 | 术语怎么处理（named-abstraction / 造词） |
| 5. 预判质疑 | 堵审稿人（披露代价 / 偏离标准给理由） |

## 逐 goal 写作技法

### goal 1：组织骨架 —— 方法节怎么组织

**选择逻辑**：方法复杂度？
- 多模块 pipeline → 代码 part 对应小节 + 路线图句 + 总览图
- 形式化重 → Preliminaries/Problem Formulation 钉符号
- 理论密集 → 命题链（Definition→Proposition→Corollary）

- ✓ **do：节首路线图句配总览图**（`We first describe... (Sec. 3.1). We then... (Sec. 3.2)` / `Figure X illustrates N components`），先给地图再下钻细节。
- ✓ **do：前置 Preliminaries/Notation 一次性约定符号**（集合、输入输出、优化目标），为后续公式提供共享记号基底。
- ✓ **do：加粗 run-in 小标题切分模块**（`Three-stage SFT. / Spatial Encoder.`），省子节编号又可扫读。
- ✓ **do：首段枚举命名组件+总图骨架**（`consists of N components: (1)...(2)...`）。
- ✗ **dont：用"元公式/统一抽象框架"把多个模块强行统一**（`Equation (7) is the meta-equation...by substituting different choices of Parameter, we obtain adaptive versions of X, Y, Z`）
  - 为什么坏：强制读者先记一个抽象母式再做心智代入，增加认知负担；这种"统一"常是表层包装，反而掩盖模块间真实差异。
- ✗ **dont：把方法核心强行组织成从严到宽的概念阶梯**（`a hierarchy of X — A, B, C, D — each admitting progressively more flexible transformations`）
  - 为什么坏：虚构并不必然存在的偏序关系，读者要额外记层级方向，难判相邻层级有无实质差别。

### goal 2：讲机制 —— 每个模块怎么讲清楚

**选择逻辑**：读者理解路径？
- 先懂 why → motivation-first（动机/直觉先于公式）
- 公式重 → 公式后白话解读（Intuitively / where 释义）
- 抽象 → 抽象后具体例子（For example）

- ✓ **do：动机/原理/直觉先于公式（motivation-first）**——每个子节或公式前，先用一两句白话讲清"要解决什么、为什么这么做"，让读者带语义抓手读数学。
  - 解剖："Our goal is to enforce that semantic parts with the same semantics exhibit consistent spatial distributions in canonical space..."〔先讲 goal 再给公式〕
- ✓ **do：公式/定理后紧跟白话或直觉解读**（物理含义 / `where` 逐符号释义 / `This shows that...`），让公式不孤立。
- ✓ **do：抽象定义后紧跟具体例子**（`For instance, given [真实取值]...`），用最小样例验证理解。
- ✓ **do：先命名痛点/挑战 → `To address` 引出对应模块**（问题→方案显式钩接，设计动机自明）。
- ✗ **dont：用格言式裸断言开节或标记重要性**（"This is the central result." / "The implication is stark."）
  - 为什么坏：替读者下结论，靠语气而非内容标记重要性；方法本身不够强时这种宣告反而暴露底气不足。
  - 自查：节首/公式后出现 3-6 词、不带论证 payload 的独立断言句。

### goal 3：辩护设计选择 —— 为什么这么设计（防过度辩护）

**选择逻辑**：怎么让选择显得非任意？
- 排除次优解 → 朴素做法→However缺陷→己方（单一 strawman，点到为止）
- 理论背书 → 借经典理论 / 把前人写成特例
- 反例驱动 → 失败案例论证步骤必要性
- 经验驱动 → 小实验观察 → thus we design

- ✓ **do：朴素/前人做法 → `However` 点破缺陷（带数字）→ 己方设计**，让创新显得被既有做法的不足逼出来。
  - 解剖："A naive approach...would be to jointly optimize...via SGD. However, this approach..."〔朴素→缺陷→己方〕
- ✓ **do：借既有框架/经典算法/权威结论为选择背书**（`Following / grounded in / as according to Tobler's law`），把正当性外包给引用。
- ✓ **do：用定理/形式化性质背书 + 把前人方法写成特例**（`reduces to / as special cases / naturally recovered`），用包含关系立统一性。
- ✓ **do：用反例/失败案例/反事实论证步骤必要性**（`If...were employed instead` / 配图失败案例），让步骤成为对真实问题的修复。
- ✓ **do：经验观察驱动设计**（`we observe...thus we design`，配 preliminary experiment/可视化）。
- ✗ **dont：把构造性设计选择包装成"fundamental observation / central principle"贴标签 + 预堵嘴**
  - 为什么坏：该用定理证明或为真实现象命名；给自己的构造性设计贴 `fundamental observation` 标签是修辞拔高，紧跟一句堵"这只是 trick"的嘴，反而显得在为选择辩解。
  - 反例："The fundamental observation behind LGGFN is that the TB loss...is itself a function over trajectories..."
- ✗ **dont：围剿式枚举多个替代方案逐一否决，制造"唯一幸存者"**
  - 为什么坏：刻意制造"我的方法是唯一可能"的过度必然性，显得刻意辩解；顶会只否定一个朴素做法、点到为止，偏离标准做法时只交代被舍弃的那一个选择。
- ✗ **dont：每给出构造就紧跟 `This design has N desirable properties. First...Second...` 编号清单做预辩护**
  - 为什么坏：夹在动机与实验间的多余辩护层，像为尚未验证的设计抢着逐条自证，稀释主线。顶会只在子模块结尾用 `In summary` 收束（singleton），或把设计原则前置作目标（few）。
- ✗ **dont：进入构造前必抛 P1/P2/P3 desiderata 清单**（除非它承载真实的 competing needs）
  - 为什么坏：把对既有设计的平凡重述包装成"目标"，表演性验收清单徒增叙述；顶会只在少数论文、原则承载真实张力时用（few）。
- ✗ **dont：连续否定排比强调零开销**（"no X loss, Y loss, or Z loss is used" / "adds no parameters and no computation"）
  - 为什么坏：防御性过强（此地无银三百两），把篇幅花在方法没用什么上，暗示对复杂度质疑心虚；该用正面量化（`adds only 10M FLOPs but increases tracking performance`）。

### goal 4：符号命名 —— 术语怎么处理

- ✓ **do：给现象/失败模式/洞察造词命名并即时定义**（`loss oscillation` / `semantic traps` / `termed X: <定义>`），铸可复用概念资产。
- ✓ **do：方法名做成自解释缩写/复合名词**（首次全称+缩写，后文统一），术语全篇一致（= intro 的 named-abstraction = experiment 消融组件名 = 方法图模块名）。
- ✓ **do：公式后 `where` 逐符号释义 + 给核心公式打助记标签**（`Eq. (5, EOT)`），让公式自洽可读。
- ✓ **do：`Intuitively,` 白话桥接公式与形式化**，形式与直觉成对出现。

### goal 5：预判质疑 —— 堵审稿人

- ✓ **do：预判审稿质疑主动披露局限/代价再化解**（超参→给敏感性分析位置；强声明→upper-bound；效率开销→量化数字）。
- ✓ **do：为偏离标准做法给明确舍弃理由**（`Instead of X, we use Y because...` / 前三步是 standard practice，后几步 distinguish our process），把新颖性落在明确位置。
- ✓ **do：代价/收益权衡句回应开销质疑**（`X adds only...but increases...` / `strikes a balance between A and B`）。
- ✓ **do：诚实标注推测/负结果/能力边界**（`We suspect...` / `We also experimented with X, but did not observe improvement`），增加可信度。

## 机制 ↔ Contribution 对齐（协同关键）

每个核心机制都要回答：

- 它支撑 `blueprint.md` 的哪个 Contribution（ref C-ID）？
- 和已有方法的关键差异是什么？（和 Related Work 的差异化句一致）
- Experiments 里有没有消融/分析证明它有用？没有实验证据 → 降低表述强度。

> 术语一致性（三位一体锁死）：Method 的机制名 = Introduction 的 named-abstraction = Experiments 消融表的组件名 = Method Figure 的模块名。全程同一个名字。

## 全节自查（反模式信号清单）

写完逐条勾：

- [ ] **公式检查（重点查——公式是 Method 最容易翻车的地方）**：每个公式的下标 / 维度 / 与符号表（`_draft/content/notation.md`）一致性**逐个核**。逐公式过：每个符号都在符号表里？下标用法和定义处一致？维度对得上（矩阵乘法形状、求和上下界、归一化维度）？
- [ ] 是否用**元公式**把多模块强行统一（"meta-equation...by substituting..."）？或把核心组织成**概念阶梯**（"hierarchy...progressively more flexible"）？
- [ ] 节首/公式后是否甩了**格言式裸断言**（"This is the central result."）？
- [ ] 是否给构造性设计贴 **`fundamental observation / central principle` 标签 + 预堵嘴**？
- [ ] 是否**围剿式枚举多个替代方案**逐一否决制造"唯一幸存者"？
- [ ] 每个构造后是否紧跟 **`desirable properties` 编号清单**预辩护？或进入构造前必抛 **P1/P2/P3**？
- [ ] 是否用**连续否定排比**强调零开销（"no X, no Y, no Z"）？
- [ ] （现有保留）每个机制是否 ref C-ID？术语是否全篇一致？只把支撑 claim 的内容放正文？符号是否服务理解（不炫技）？

## 文风 lint

写完按三层 craft 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# Method 写作计划
## 1. 核心改动 part 清单（读代码识别，每个 ↔ Contribution）
## 2. 符号表（落 `_draft/content/notation.md`）+ 章节结构（part 间逻辑递进）
## 3. 逐 goal 写作（组织/讲机制/辩护/命名/堵质疑）
## 4. 机制到 Contribution（C-ID）的映射 | 机制 | 支撑的 Contribution | 所需证据 |
## 5. 正文草稿（英文）
## 6. 应移至附录的内容 + 反模式信号清单逐条勾
```
