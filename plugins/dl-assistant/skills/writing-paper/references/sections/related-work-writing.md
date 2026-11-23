# Related Work Writing

`writing-paper` 写相关工作的详细规则。Related Work **不是文献综述——建立领域地图，把本文放到一个清楚、可信、有差异化的位置**（锚定位）。它先于 Introduction 写，定住本文位置，让 Introduction 的 gap 顺理成章。

> 论文事实用 `paper-search` MCP 查证，不编造作者/年份/结论。引用给 URL，不给内部 paper_id。

## 先定写作功能（选一个为主）

| 功能 | 适用 | 写法重点 |
|---|---|---|
| 定位方法路线 | 方法创新为主 | 分类技术路线，说明本文属哪条线、突破哪里 |
| 定义任务背景 | 新任务/新场景 | 先写任务和 benchmark，再写方法 |
| 对比竞争方法 | 强 baseline 很近 | 精准写差异，不泛泛综述 |
| 支撑问题重要性 | 引言需铺垫 | 强调已有工作共同遇到的限制 |

## 默认结构 = 5 个写作决策点（goal）

**每个 goal 都有多条打法，先看「选择逻辑」定打法，再看 do / dont。** 推荐标准：taxonomy 终点能自然导向本文 gap（= Introduction 的 gap = `blueprint.md` 的 RW 起点）；不把本文塞进拥挤但差异弱的类别。

| goal | 作者在想什么 |
|---|---|
| 1. 搭骨架 | 怎么把领域切成可导航的地图 |
| 2. 写每类工作 | 怎么综述一类方法（不写成流水账） |
| 3. 点出 gap | 怎么从综述收束到空白 |
| 4. 定位本文 | 怎么把本文放进地图（防综述病） |
| 5. 特殊情况 | 并发工作 / 最相似竞品 / 数据集综述 |

## 引用选择

| 类型 | 数量 | 用途 |
|---|---|---|
| 奠基工作 | 1-2 | 定义问题/技术源头 |
| 代表路线 | 每类 2-4 | 说明这类方法做了什么 |
| 近期强相关 | 3-6 | 直接对比本文差异 |
| baseline | 按实验需要 | 和 Experiments 对齐 |

## 逐 goal 写作技法

### goal 1：搭骨架（taxonomy）—— 怎么把领域切成可导航地图

**选择逻辑**：按什么轴分类？
- 方法路线分代/分类 → 按方法范式（二分/三分/代际）
- 按问题设置/结构 → 按技术维度
- 主题密集 → 加粗 run-in 小标题按主题族

- ✓ **do：节首立显式分类骨架再分块**（`two main approaches` / `categorized into N` / `fall into N paradigms`），让后续每个小节对号入座。
  - 解剖："There are two main approaches: one involves carefully designed prompt engineering...; the other..."〔分类总纲→分块展开〕
- ✓ **do：加粗 run-in 小标题按主题切分**（`Expressing queries with programs. Several prior works...`），省去正式子节又可扫读。
- ✓ **do：子节标题用排比/描述性短语编码分类维度**（`Scene synthesis with / via / using <角度>`），让标题即分类轴。
- ✓ **do：导览句预告综述范围/路线图**（`In this section, we first...followed by...`）。
- ✗ **dont：子节标题写成断言句/缺陷命题**（"The use of RoPE introduces channel inefficiency in K." / "Adversarial training missing on the auxiliary classifier"）
  - 为什么坏：标题预载作者结论，读者还没看证据就被强加判断，失去导航锚的检索功能。
  - 自查：标题是完整论断句而非中性名词短语。

### goal 2：写每类工作 —— 怎么综述一类方法

**选择逻辑**：这类方法的成熟度？
- 成熟/广度方向 → 统一动词模板密集罗列（展示覆盖面）
- 关键路径方法 → 逐篇先承认做法再 `However` 点局限
- 多篇共性 → 归纳一类方法的共性局限

- ✓ **do：统一动词模板密集罗列**（`方法[ref] + 动词(proposes/leverages) + 一句话机制`），节奏整齐可扫读，密集堆引用展示广度。
- ✓ **do：逐方法先承认做法再 `However` 点局限**——先客观陈述（可用 `pioneering/seminal` 给 credit），紧接 `However` 点具体局限（写明失效边界、可核查代价）。
- ✓ **do：归纳一类方法的共性局限/共享假设**（`A common property is...` / `all these works ignore...`），把整类方法收束到一个共性缺陷。
- ✓ **do：编年/演进叙事串文献**（`Early...Recently...` / `from X to Y`），每代点进步与遗留问题。
- ✗ **dont：把每个被引方法都压成"机制(+优点) + but + 局限"的机械立-破节奏**
  - 为什么坏：每条都即时附带缺陷，综述像为每个前人凑缺陷，失去中立梳理的呼吸感；也把本该留到实验的详细比较过早塞进综述。
  - 自查：几乎每句被引工作都以 `but / constrained to / does not model` 结尾。
- ✗ **dont：每个子节都强制收尾一句自我定位**——定位句只部署在最可比前驱/节末 gap 桥接等关键节点，保留中性密集罗列段（见 goal 4 反模式）。

### goal 3：点出 gap —— 怎么从综述收束到空白

**选择逻辑**：gap 怎么钉？
- 一类方法共性失效 → 让步-翻转诊断集体局限
- 无前人做过 → 首发/空白声明（带 hedge）
- 你有实验 → refuted 子论点落 gap（非 strawman）

- ✓ **do：让步-翻转句收束到 gap**（`Despite/While X...they neglect/remain limited...resulting in`）
  - 解剖："Despite these advances, existing prototype-based PFL methods mainly focus on aligning global and local prototypes, while overlooking the aggregation bias..."〔让步+翻转+点缺口〕
- ✓ **do：招牌 gap 收束句**（`remains a challenging open question` / `largely unexplored`），配 `To our knowledge` 做 hedge。
- ✓ **do：用具体可量化数字钉死缺陷**（类别数 27 vs 93、参数量、精度 %）——具体到数字的短板最难被辩护。
- ✓ **do：refuted/abandoned 子论点落 gap**（`we find that [路线] suffers from [问题], as evidenced by [我们的消融]`）——有实验背书，不是 strawman。
- ✗ **dont：三连贬义词否定整条路线**（"often results in human biases, extraneous noises, and labor-intensive efforts"）
  - 为什么坏：三个笼统贬义词概括整条路线，不可证伪、不指向具体技术缺口，稻草人化对手。
  - 自查：一句里堆 ≥3 个贬义/负面词给整条研究路线扣帽子。
- ✗ **dont：前向引用本文尚未展开的实验来担保 gap**（"as we show in our experiments, our method achieves the largest gains precisely in this setting"）
  - 为什么坏：期票式循环担保——gap 重要性靠本文自己未呈现的结果撑，读者读到实验前无法独立判服。

### goal 4：定位本文 —— 怎么把本文放进地图（防综述病）

**选择逻辑**：本文相对前人的位置？
- 最相似竞品 → 单独点名逐点差异化
- 一类方法 → 每节末尾收尾定位句（硬约束）
- 降低对抗 → 互补/正交定位

- ✓ **do：每个 taxonomy 类别介绍完后，末尾必有两三句收尾把本文放进去**（**硬约束：没收尾句的类别 = 综述，不是 related work**）
  ```
  [这类方法做了 X / 共同没解决 Y]。
  Unlike methods that [existing assumption], our approach [key difference],
  which enables [specific capability].
  ```
- ✓ **do：点名最相似工作逐点差异化**（`The methods most similar to ours are...` / `differs in N aspects: First...Second...`）。
- ✓ **do：承认传承/正交互补软化竞争**（`Building on` / `orthogonal to` / `complementary`），给同行 credit、降低对抗性。
- ✗ **dont：专设定位小节用 `Unlike [大类], we...` 排比扫荡多个范式大类**
  - 为什么坏：把每个大类压成稻草人属性再批量否证，对照建立在排比修辞而非可核验技术细节上，像营销话术；"堵审稿人混淆"的防御动机本身就显得不自信。
  - 反例："Unlike generative models, we operate as a discriminative token classifier... Unlike encoder-only models... And unlike multi-stage pipelines..."
- ✗ **dont：定位句加一次性隐喻包装**（`treating X as the common currency` / `the mirror image of X` / `an escape route from Y`）
  - 为什么坏：把可核验的技术差异换成一次性文学比喻，增加读者核对定位的成本。
- ✗ **dont：相关工作末尾插"我们 NOT 做 Y"防御性免责声明**（`rather than proposing a new architecture`）
  - 为什么坏：欲盖弥彰，把注意力引向你想回避的误读；scope 应由 intro/method 正向框定承担。

### goal 5：特殊情况 —— 并发 / 最相似 / 数据集

- ✓ **do：并发工作单独成段声明关系**（`A concurrent work, X, also explores...however, it relies on...`），逐一点名 complementary/orthogonal，体现公允与时效。
- ✓ **do：漏斗式收窄到 niche**（广角大领域→逐层收窄→`However, there remains relatively little work` 反转定位空白）。
- ✓ **do：数据集综述递进补全链**（按"谁、为补什么而建"逐个写一句），空白精确到维度（类别数/粒度/模态）而非泛泛。

## 全节自查（反模式信号清单）

写完逐条勾：

- [ ] 子节标题是否写成了**论断句/缺陷命题**（非中性名词标签）？
- [ ] 是否把每个被引方法都压成"机制 + but + 局限"的**机械立-破节奏**？
- [ ] gap 是否用**三连贬义词**给整条路线扣帽子？是否**前向引用本文未展开实验**担保 gap？
- [ ] 是否专设小节用 `Unlike [大类], we...` **排比扫荡**多个范式大类？
- [ ] 定位句是否加了**一次性隐喻包装**（common currency / mirror image）？
- [ ] 末尾是否插了"我们 **NOT** 做 Y"防御性免责声明？
- [ ] （现有保留）**每个 taxonomy 类别有没有收尾放本文**？（没有 = 综述病）遗漏最直接竞争工作？把已有工作说弱了（strawman）？gap 和 Introduction 一致？baseline 和 Experiments 对齐？

## 与全文协同

- taxonomy 终点 = Introduction 的 gap = Abstract 第 2 句 = `blueprint.md` 的 RW 起点。
- 定位句的差异点 = Method 的「与已有方法关键差异」= Experiments 要证明的点。

## 文风 lint

写完按句段、字词和常见生成式写作问题三类写作要求 跑一遍（`sentence-craft.md` + `word-craft.md` + `anti-ai-patterns.md`，句段/字词/AI 跨节通用；论证层查本节 checklist）。

## 输出

```markdown
# Related Work 计划
## 1. 写作功能 + 推荐 Taxonomy
## 2. 引用选择表 | 小节 | 论文(URL) | 为什么引用 | 与本文关系 |
## 3. 每节收尾句（把本文放进去） | 类别 | 收尾：本文相对这类工作的位置 |
## 4. refuted/abandoned 子论点落哪节
## 5. 段落大纲（按 5 个 goal 组织）
## 6. Related Work 草稿（英文）
## 7. 反模式信号清单逐条勾
```
