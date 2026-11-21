# Fairness Firewall（公正性防火墙）

`writing-paper-review` reviewer prompt 注入用（横切，所有 venue 通用）。**任何 weakness 先过这道墙**——区分「严谨审稿」和「键盘喷子」。

> 来源：从各 venue 公开评审准则（CVPR "不超 SOTA 不构成拒稿理由"、CoRL "不必开源/不必上真机/没超 SOTA 不拒"、ACL "低 Soundness 必须指硬伤"）提炼的通用横切清单。venue 特色条款留在各 venue 文件，本文件管通用下界。

## 精神

**指出问题可以，但不能拿不致命的问题当拒稿理由来压分。** 真实好 reviewer 会写"baseline 略老"作为改进建议，但不会因此打 strong reject。喷子才拿小瑕疵当 fatal flaw。

## 过墙清单（下列七条 = 缺陷但**不致命**，写进 weakness 要诚实标为「改进建议 / 小瑕疵」，不能当 fatal flaw 压低分数）

1. **没超 SOTA** —— 权衡 novelty + 潜在影响 + 报告的性能，本身不是拒稿理由。没超还能中的工作多得是（新视角 / 新机制 / 新分析）。
2. **存在 limitations** —— 所有工作都有局限。存在 limitation ≠ 拒稿；只有"关键 limitation 没在论文承认、且动摇主 claim"才算硬伤。
3. **"本可以再做一组实验 / 再多消融一项"** —— 是 minor improvement 建议，不是 fatal flaw。除非缺的那组直接动摇核心 claim。
4. **缺开源代码** —— 不构成拒稿理由（除非 venue 明确强制开源）。开源是加分项，不是门槛。
5. **写作小瑕疵 / 个别 typo / 局部表述不清** —— 易修，不该拒。只有全文组织混乱、claim 和正文对不上才升级。
6. **"方法不够新颖" 空口断言** —— novelty 质疑**必须检索举证**（"X 等 [ref] 已做过高度相似工作，见动作 B 检索"）。"我感觉不够新"不算证据，过了墙的是不合格的 weakness。
7. **没在某个数据集上验证** —— 除非是该领域公认的 canonical benchmark 且没做就说不过去，否则不致命。

## 怎么用（reviewer 写 weakness 时）

每写一条 weakness，先自问：**这条过了防火墙吗？**

- 属上面七条之一 → 要么**降级**（标为「改进建议/小瑕疵」，不影响录用判断），要么**删掉**。不能当成 fatal flaw 写进打分理由。
- 不属七条 → 才可能是真 weakness，再看是不是致命（致命判据见 `calibration.md`）。

## 反向：什么真算拒稿硬伤（防火墙上界，对照）

过了墙的 weakness 里，**致命**的才算拒稿理由——判据见 `calibration.md`（reviewer 校准节）。典型：novelty 被检索证伪、claim 过度声称且实验不支撑、方法根本性错误。

> 一句话：**防火墙管"什么不算拒"，calibration 管"什么真算拒"，一对上下界，reviewer 打分才平衡。**
