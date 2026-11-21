# 模板：pitches/pitch-N-<slug>.md（Step 2 主会话产糙 pitch · 一页以内）

> 流程见 `direction.md` Step 2；公共语言规范见 `output-contract.md`。

一 pitch 一文件，**一页以内、五行正文**。pitch 是**待验证假设**——撞不撞车由 Step 3 调研回答，这里只凭种子 + 筹码 + 判断力。**被杀的 pitch 不删文件**，文件尾记杀的理由（复盘素材 + pitch 被撞死时回 Step 2 提备胎的池子）。

```markdown
# pitch-{N}：{一句话标题}（slug）

- **来源**：{用户 / 补丁候选——用户来源直接进幸存区、只能用户自己杀；补丁候选 = agent 补位生成的对照材料 / 兜底}
- **痛点**：{谁受什么罪——具体到哪类研究者 / 哪个方法的哪个缺陷，一句话}
- **武器**：{凭什么轮到我们——挂 idea-seed.json wedge 里的哪个筹码；挂不上筹码的 pitch 不许产}
- **战场**：{打谁、在哪打——有名字的 baseline + 有名字的 benchmark/指标}
- **主表预览**：{这篇论文的 Table 1 长什么样——哪几行哪几列、赢的条件是什么数字}
- **为何不是拼接**：{为什么这不是 A+B 的简单组合——组合之后产生了什么单拎任何一边都没有的东西（新能力 / 新视角 / 互相解除对方瓶颈）；答不出 = 缝合怪，不许产}

## 形态

{技术改进型 / 新任务红利型 / 迁移型 / 组合型（默认只产这四类）；现象驱动型 / 机理化型（仅用户点名要做理解型工作时才产，照样要过主表预览）}

## 来源素材

{从哪条种子 / 哪个筹码长出来的（指回 idea-seed.json 的种子清单和 wedge）}

## 品味杀结果（Step 2 用户评审后填）

{幸存 / 被杀（理由：…）/ 被改（改成了什么）/ 被糅（和谁糅成了哪个新 pitch）}
```

**填好的样子**（示例）：

> # pitch-2：用 motion 当分组信号破 video OCL 的 discovery 塌缩（motion-jepa-ocrl）
>
> - **痛点**：做 object-centric 视频表示的人被二选一卡死——外包 SAM（不优雅、误差传播）或 slot attention（discovery 不稳定、训练会塌）。
> - **武器**：用户吃透 SIGReg 原理化反塌缩（别人要用得现学）——正好压 mask-free discovery 塌缩这个头号病灶；外加 32×4090 够从头训 video JEPA。
> - **战场**：打 SAVi / VideoSAUR（slot 系）和 Object-centric LeJEPA（SAM 系），在 FG-ARI / ADE20k / DAVIS 上比。
> - **主表预览**：主表 = 分割/发现指标对比——行：SAVi、VideoSAUR、LeJEPA-OC、我们；列：FG-ARI / mIoU；赢的条件 = FG-ARI 超 slot 系最强者且 mIoU 追平 SAM 系。
>
> ## 形态
>
> 技术改进型（修 slot/SAM 两系的病灶）。
>
> ## 来源素材
>
> 种子：paper-card 的 connections（Object-LeJEPA 的 cyclic instability limitation）；筹码：wedge.tools（SIGReg）。

**字段纪律**：

- **五行正文缺一不可**——"痛点"答不出具体人群 = 没人 care 的方向；"武器"挂不上筹码 = 替别人找的方向；"战场"没有名字 = 假大空；"主表预览"写不出 = payoff 不具体；"为何不是拼接"答不出 = 缝合怪——都不许进品味杀。注意"为何不是拼接"不是禁组合型形态（组合 insight 是合法形态），是逼组合型说清**组合产生了什么单拎一边没有的东西**——答得出这个的组合才是真 insight，答不出的就是 A+B 堆叠。
- pitch 里**不写方法设计**（怎么训、什么架构）——那是挖方法阶段的事；pitch 只锁定"为谁解决什么、凭什么、赢在哪"。
- 数量：池子总量 5-8 个（用户 pitch 优先，补丁候选补位），互斥不撞车（主会话全局生成）；用户来源的 pitch 直接进幸存区、只能用户自己杀，编号接着排。
