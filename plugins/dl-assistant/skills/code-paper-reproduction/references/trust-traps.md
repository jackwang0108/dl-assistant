# 可信度陷阱（trust traps）：跑出数 ≠ 数可信

> reproduction 的真盲区。复现失败里**最不像 bug 的那一类**——命令跑通了、有 metric 出来了，
> 但数字要么伪对齐（看着齐其实错）、要么伪差距（看着差其实是噪声/协议）。这些错不 crash、
> 不报 error，靠盯 traceback 永远抓不到。本手册把它们做成可操作的排查顺序 + 默认容差 band。
>
> 用法：reduced/eval/训练 跑出数和论文对不上（或"好得可疑"）时，**按下面顺序排**——前面的坑命中率远高于后面。
> ①-⑥ 是 eval 侧通吃的；**要重训/微调的 idea 还必须过 ⑦（训练链特有的伪对齐）**——它是 eval 对齐完全覆盖不到的盲区。
> full / b+a 都跑不动时用「组件级验证手册」验训练链语义（证据阶梯第 3 级）。

## 信任阶梯（双轨：eval 可信 + training 可信）

```
能跑              ← setup 的事（环境/依赖/数据/ckpt 就绪），前置已过
  ↓
跑出数            ← reduced/eval/训练 产出了 metric / log / artifact，命令不报错
  ↓
eval 可信         ← checkpoint eval 在容差 band 内对齐论文 + 排除 ①-⑥（推理链对）
  ↓
training 可信     ← 重训能复现论文数（或合理外推）+ 排除 ⑦（训练链对）
                    training-free idea 到 eval 可信即可；要重训 idea 必须到 training 可信
```

> **eval 可信是 training 可信的前置地基，不是 training-free 的专属。** 阶梯是递进的：要重训的 idea 也**先**把 eval 链校准（用 official checkpoint eval，官方权重训练已知正确），**再**叠训练复现。这样重训出的 gap 能干净归因——eval 已对 → gap 必在训练链（查 ⑦）；eval 没对 → 是 eval 链坏了（查 ①-④），训练数字没有可信标尺。所以 official checkpoint eval 对**所有** idea 都做，只是 training-free 到此为止、要重训的在它之上继续。

> **eval 可信 ≠ baseline 可信**。official checkpoint eval 只验推理链，碰不到训练链。绝大多数 idea 要重训，**只有 training 可信这层过了，你重训出来的 delta 才有意义**。这是本手册区别于"eval 对齐就完事"的根本。本 skill 的判断停在对应轨的"可信"档（见 SKILL 的双轨判定）。

---

## 排查顺序（按命中率降序，前三个是重灾区）

### ① metric 定义：同名不同算法（头号伪差距）

同一个 metric 名，背后可能是完全不同的算法/实现：

- **检测 mAP**：`mAP@.5` vs `mAP@[.5:.95]`（COCO 主指标）差一大截；同是 COCO mAP，**官方 `pycocotools` eval vs repo 自实现**可能差零点几到几个点。
- **分割 mIoU**：含不含 background 类、忽略不忽略 255/void 区、per-image 平均 vs 全局混淆矩阵——口径不同数字不同。
- **分类 acc**：top-1 vs top-5、有没有做 10-crop、用不用 EMA 权重。
- **生成 FID/IS**：用哪个 Inception 权重、多少张样本、resize 插值方式——FID 对这些极敏感。
- **检索 R@K**：i2t 还是 t2i、有没有去重、gallery 范围。

> **排查动作**：去**源码里读 metric 实现**（不是看 config 名），确认调的是官方库还是自实现、参数（IoU 阈值/类别集/平均方式）是什么；再和论文 metric 定义逐字对。**这一坑必须读源码，README 和 config 名都不可信。**

### ② dataset split：val/test 混淆 + 划分不一致

- **val 当 test 报**：论文报 test，你 eval 跑的是 val（或反过来）。很多 repo 默认 eval val，论文表是 test-dev（要提交服务器）。
- **划分版本**：同一数据集有多个 split 约定（如 Pascal VOC 07/12、不同 trainval 组合、COCO minival 5k vs val 全量）。
- **子集 eval 当全量**：reduced 时为了快只 eval 了一个 subset，忘了它不能和论文全量数字比。

> **排查动作**：确认 eval 命令实际加载的 split 文件 / annotation 路径；和论文"在哪个集上报"对齐；reduced subset 的数字**只用来验 pipeline，不和论文比绝对值**。

### ③ checkpoint 血缘：官方权重不等于"产出论文数字那一版"

- **EMA vs raw**：很多 SOTA 训练维护 EMA 权重，论文数字来自 EMA，repo 默认 load raw（或反之）——差好几个点。
- **best vs last**：官方放的是 best epoch 还是 last epoch 的 ckpt？论文报的是哪个？
- **是不是那一版**：官方 release 的权重未必是产出论文表格那次训练的产物（可能是重训的、清理过的、换了 backbone init 的）。
- **strict 加载丢 key**：`load_state_dict(strict=False)` 静默丢了一半 key，模型一半是随机初始化，eval 还能跑出"不算太差"的数字——伪差距的隐形炸弹。

> **排查动作**：load 时**强制 `strict=True` 看报不报 missing/unexpected keys**（setup 的 numeric-sanity 已埋此检查，复现要再确认一次）；确认 load 的是 EMA 还是 raw、best 还是 last；权重来源对照论文/repo issue 确认血缘。strict 报 key 不匹配 = 命中语义判断即停（停下问用户）。

### ④ 评测协议：测试时增强没对齐

论文数字常含**测试时增强**，repo 默认可能没开（或反之）：

- **TTA / multi-scale test**：检测/分割常用多尺度测试 + flip 融合，能涨 0.5~2 个点。
- **flip / 10-crop / sliding window**：分类、分割的测试时技巧。
- **测试分辨率**：论文 train@224 test@384 这类"train-test resolution discrepancy"，repo 默认可能 test@224。

> **排查动作**：读论文 Implementation Details / Appendix 有没有"test-time augmentation / multi-scale"；对照 eval config 的 test pipeline；**协议不一致是伪差距高发区**，且开/关协议是实验语义判断 → 命中语义判断即停，别擅自开关。

### ⑤ 跟错论文表格行 / setting

- 论文一张表多行（不同 backbone / 不同输入尺寸 / 不同 schedule / w/ vs w/o 某 trick），**跟错行**就拿错了对比目标。
- main table vs ablation table 数字不同；论文正文数字 vs 附录数字不同。
- 对比的是"我们方法"那行还是"baseline"那行——复现 baseline 时要跟 baseline 行，不是 SOTA 行。

> **排查动作**：写 spec 时就**把"Table X 第 N 行 + 该行的 setting"钉死**（spec 模板已要求）；复现 spec 里写清对的是哪一行哪个 setting。

### ⑥ 噪声 vs 真差：小 gap 先怀疑噪声

- **单 seed 的 ±零点几**：很多任务单次训练的 run-to-run std 就有零点几到一个点。单 seed 复现出的小 gap，**先怀疑是噪声，不是 baseline 不可信**。
- **determinism 没固定**：cudnn.benchmark=True、dataloader 没固定 worker seed、没设 `cudnn.deterministic`——同样代码两次跑结果就不同。
- **batch size / 卡数变了**：你在 1 卡复现，论文 8 卡，有效 batch size 不同 → BN 统计、lr scaling 都受影响，数字本就该有差。

> **排查动作**：**对照 `setup.json` 的 `reproducibility` 块**（seed/cudnn 设在哪、固没固定）。determinism 没固定死时，band 内的 gap 大概率是噪声。存疑就**多跑 1-2 个 seed 看 std**——若论文数字落在你的 [mean − std, mean + std] 里，算对齐。卡数/batch 不同导致的系统性差，记为"setting 差异"而非"不可信"。

---

## ⑦ 训练链特有的伪对齐（只在「要重训」分流出现）

> ①-⑥ 主要管 eval 侧（推理链 + 权重 + 评测）。但绝大多数 idea 要重训/微调，这时 **eval 对齐 ≠ 训练链可信**——dataloader 增强、loss 实现、optimizer、分布式行为这些**只在训练时才跑到**，official checkpoint eval 完全碰不到它们。下面这些坑**只在你重新训练 baseline 时才暴露**，是"训练 loss/metric 曲线和论文对不上"的高频原因。**走 SKILL 决策树的「规模不大 full」「规模大 b+a」分流时，逐条核对。**

### BN 统计：同步 BN vs 普通 BN、卡数敏感

- **SyncBN vs 普通 BN**：多卡训练里论文常开同步 BN（跨卡统计 batch mean/var），repo 默认可能是普通 BN（每卡独立统计）。你在 1 卡复现时，普通 BN 的有效统计 batch = 单卡 batch，和论文 8 卡 SyncBN 的等效统计 batch 差 8 倍 → BN 统计量不同 → 收敛行为和最终数都不同。
- **BN 的 momentum / eval 时 running stats**：训练 momentum 配错、或 eval 时该用 running stats 却用了 batch stats，都让训练出的模型在 eval 时数字偏。
- **frozen BN**：检测任务常 freeze backbone BN，repo 配置里 freeze 没 freeze 影响很大。

> **核对**：读 config/源码确认 BN 类型（`SyncBatchNorm`?）、freeze 设置；对照论文 Implementation Details。1 卡复现大规模多卡训练时，BN 差异是头号"趋势对但数偏"的来源——这正是决策树「规模大」要靠 (b) 小 setting 补硬证据的原因。

### 分布式 loss 归约：mean vs sum

- **loss 在多卡间 mean 还是 sum**：分布式训练 loss 归约方式不同，等效于 lr 差了卡数倍。repo 实现和论文不一致 → 实际 lr 偏了 → 曲线不对。
- **grad 是否 all-reduce 平均**：DDP 默认平均梯度，但有的实现手动 sum，配合 loss 归约方式一起决定有效 lr。

> **核对**：读 trainer 的 loss/backward 部分，确认归约方式；1 卡复现时尤其注意——单卡没有归约，等效 lr 可能和多卡的论文设置不同。

### 梯度累积 / 等效 batch size

- **有效 batch = 单卡 batch × 卡数 × 累积步数**。你在 1 卡用 grad accumulation 凑论文的有效 batch，但 BN 统计仍是单卡 batch（见上）——有效 batch 对了 BN 还是不对。
- **lr 没随 batch 缩放**：论文用 linear scaling rule（lr ∝ batch），你改了 batch 没改 lr → 收敛不对。

> **核对**：算清论文有效 batch = 多少，你的复现有效 batch = 多少，lr 有没有按比例调。等效 batch 对齐是训练复现的基本功。

### 训练时增强 vs eval 时增强不一致

- **训练增强 pipeline**：RandAug/Mixup/CutMix/大尺度 jitter 这些只在训练用，配置漏了或开错 → 训出来的模型 eval 时数字偏（且 eval 对齐时根本看不出来，因为 eval pipeline 是另一套）。
- **训练分辨率 vs eval 分辨率**：train@224 eval@224 vs train@224 eval@256，训练侧配错会让整条曲线偏。

> **核对**：读 train pipeline 的 transform 列表，逐个对论文 Implementation Details；这是 eval 对齐完全覆盖不到的盲区。

### lr schedule / warmup / EMA（训练侧）

- **warmup**：论文常用 linear warmup 若干 iter，repo 配置漏了 → 早期 loss 炸或震荡，趋势就不对（决策树 (a) 大规模趋势外推时，warmup 没配对会让早期点全偏）。
- **scheduler 类型**：cosine vs step vs poly，end lr、衰减点配错 → 中后期曲线分叉。
- **lr decay 按 epoch 数锚定**：schedule 里"epoch 30 衰减"这类配置是按原数据集规模定的，换数据集 / 缩规模后 epoch 数变了，lr 可能过早衰减到 0，模型静默地训不到位——**不要信任 lr decay 默认值**。缩规模复现 / reduced 配置时必须等比压缩 schedule（见 `reduced-setting.md`）。
- **EMA 训练侧**：论文训练时维护 EMA 权重，你没开 EMA → 最终数偏低（这和 ③ 的"eval 时 load EMA vs raw"是一体两面，训练侧要真的开 EMA 训）。

> **核对**：对论文的 lr schedule 三件套（warmup / 类型 / 终值）+ EMA 设置。**(a) 趋势外推特别吃 warmup 和早期 schedule**——早期点对不对，warmup 配对没是头号因素。

> **小结**：⑦ 的核对结果落到复现 spec 的「训练链」对齐行和 report 的训练复现结果。命中其中"该不该开同步 BN / 改 loss 归约 / 调 lr 缩放"这类 → 是**实验语义判断**，命中语义判断即停，别擅自改。

---

## 组件级验证手册（不跑完整训练，验训练链语义）

> 证据阶梯第 3 级的操作手册：full / b+a 都跑不动时，不跑完整训练也能验训练链语义；也适用于 training 曲线异常时的排障——先回到组件级，把"训练链断了"和"规模/超参问题"分开。
> 改动代码后的排障同样用这套手册（`code-idea-execution` 经全路径引用本文件）。
>
> **排查前置：simplify**——先关数据增强、固定 seed，把变量减到最少再定位；增强是又一个引入静默 bug 的机会，确认链路正确后再加回来。

### 1. overfit one batch：训练链没断的最强证据

- **目的**：验证 forward / backward / optimizer 整条链能学习。
- **操作**：取一小批数据（少到 2 个样本），加大模型容量，训到 loss 压到接近 0；可视化同一张图里 label 和 prediction，收敛后必须完全对齐。
- **判定**：压不下去 / 对不齐 = 训练链有 bug，不许往下一阶段走。

### 2. verify loss @ init：秒级抓配置错

- **目的**：初始 loss 是可推导的理论值，不对就是配置错。
- **操作**：第一个 step 的 loss 对照理论预期——分类 cross-entropy 应约 ln(n_classes)（最后一层初始化正确时）；L2 回归 / Huber 同理可推导默认值。
- **判定**：明显偏离理论值 = 初始化 / label 处理 / loss 实现有错。
- 附：最后一层 bias 可按数据先验初始化（回归均值、不平衡类别的正例率先验），消除"hockey stick"初期曲线。

### 3. input-independent baseline：模型真的从输入学到东西了吗

- **目的**：排除"模型无视输入也能训出像样的 loss"。
- **操作**：输入全零（或固定常数）训练，性能必须显著差于真实输入。
- **判定**：差不多好 = 标签泄漏 / 数据路径错，模型没在用输入。

### 4. 进网络前可视化：预处理/增强的唯一真相源

- **目的**：预处理 / 增强 bug 在 loss 曲线上常常隐形（网络会学着绕过去，静默变差）。
- **操作**：把正要送进 `model(x)` 的 tensor（和 label）解码成图像/文本可视化——这是唯一无歧义的检查点；左右翻转后 label 有没有同步翻转这类坑一眼可见。
- **判定**：看到的和预期不符 = 预处理/增强 bug，查实再继续。

### 5. 梯度依赖检查：抓 batch 维串味和自回归泄漏

- **目的**：view/permute 用错会把 batch 内信息混在一起，网络照常训练但静默变差；自回归模型 off-by-one 会偷看要预测的目标。
- **操作**：把 loss 设为第 i 个样本的输出之和，反传到输入，确认只有第 i 个输入有非零梯度；自回归模型同理确认 t 时刻只依赖 1..t-1。
- **判定**：别的输入 / 未来位置有梯度 = 依赖串味，定位到具体层。

### 使用方式

- **证据阶梯第 3 级**：全过 → 训练链语义正确（`evidence_strength: low`，数值对齐 deferred）；任何一项不过 → 训练链有 bug，逐项查实。
- **曲线异常排障**：training loss 不降 / 震荡 / 早期炸 → 先 simplify，再按 1→2→3→4→5 顺序过，多数问题在前三项现形。

---

## 容差 band（默认值）

**优先级：论文自报 > 默认 band。**

1. **论文自报 std / 多次实验范围**最权威——论文写了 "X.X ± Y.Y" 或给了多 seed，**直接拿 ±std 当 band**。
2. 论文没报方差时，用下面的**默认 band**（经验值，覆盖常见任务）：

| 任务 | 指标 | 默认容差 band | 备注 |
| ---- | ---- | ------------- | ---- |
| 图像分类 | top-1 acc | ±0.3% | 大模型/大数据集可放宽到 ±0.5% |
| 目标检测 | mAP / AP | ±0.5 | COCO mAP；单 seed run-to-run 常达此量级 |
| 语义分割 | mIoU | ±0.5 | |
| 生成 | FID | 看趋势 + 量级 | FID 对实现极敏感，绝对值难严格对齐，看同量级 + 趋势 |
| 检索 | R@K | ±0.5~1.0 | |
| NLP/LLM | acc/F1/BLEU | ±0.3~0.5 | 任务相关，small benchmark 方差更大 |

3. **落到机读区 `tolerance_band` 字段**，说明用的是论文自报还是默认。

> 这些是**判"齐没齐"的参考线，不是硬阈值**。band 内 = 倾向 Reproduced；band 外但能解释（如卡数不同）= Partially / diagnosable；band 外且无法解释 = 存疑。生成类、强化学习这类高方差任务，**趋势和量级比绝对值更重要**。

---

## 伪对齐：数字"太好"也要警惕

不只是"差了"要查，**"好得可疑"同样是陷阱**：

- **eval 跑了 train 集**：脚本默认或路径写错，eval 在训练集上跑 → 虚高。
- **数据泄漏**：test 样本混进了 train，或预训练权重已见过 test 分布。
- **恰好满分 / 恰好 0**：metric 实现 bug 导致退化（如全预测同一类恰好碰上类别不平衡），看着是数字其实无意义。
- **跟错了更高的行**：把论文 SOTA 行当 baseline 行复现，"轻松超过"其实是比错对象。

> 数字明显优于论文报告时，**先反查上面四条**，再宣布复现成功。复现的目标是"和论文对齐"，不是"超过论文"——超过往往意味着对比口径错了。

---

## 何时升级到语义判断即停 / 下源码追到底

- 命中 **③ checkpoint strict 报 key 不匹配** / **④ 协议要不要开** / **②val-test 该用哪个不确定** / **⑦ 该不该开同步 BN / 改 loss 归约 / 调 lr 缩放** → 这些是**实验语义判断**，命中语义判断即停（停下问用户）。
- gap 原因查到 metric 实现 / dataloader 行为 / 训练链某处、**对齐表里看不直接** → **不是切出去，是 reproduction 该下源码追到底**：读那段源码把可疑点查实（如 ⑦ 里 BN 同步/loss 归约/lr 缩放到底在哪、对没对齐），追到能落判定 为止。可信度结论是本 skill 的交付，不追完就没有结论。
- 反复修不动的工程死结（不是语义判断）→ 上报用户。
