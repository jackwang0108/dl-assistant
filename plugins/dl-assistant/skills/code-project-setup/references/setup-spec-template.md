# Setup Spec 模板（code-project-setup）

> 动手前的**准备规格说明**——让用户看清 agent 打算干啥 / 缺啥 / 风险在哪 / 资源够不够，确认后才转 Plan。
> spec 定 what / why（做什么、为什么、风险、标准），Plan 定 how（分任务执行）。
>
> 保存 `setup-spec.md`。继承自 `baseline-survey` 的结论融进各节、标 "(自 survey)"，不单成一节。
> 技术术语保留，整体中文。

---

````markdown
# Setup Spec: <repo-name>

> 动手前对齐。审阅通过后转为 setup-plan.md 执行。有问题就改，改到确认再转 Plan。

## 1. repo 介绍

- **是什么**：<用一句话说明任务、框架和实现来源，如 基于 MMDetection 3.x 的目标检测 repo，基于 Detectron2 修改的实现>。
  （写到"用户不看 README 也知道接手的是什么"为止；不要抄 README 简介。）
- **来自哪**：baseline-survey 推荐（commit <sha>）/ 用户指定（<url>）。
- **要 setup 成什么样**：可读（代码能 import）/ 可调（能改参数跑）/ 可信（三层验证 + 数值正确性检查通过），为下游 code-paper-reproduction / code-reading / code-idea-execution 备好 baseline。

## 2. 环境决策（每个决策都要带理由——没有理由的决策用户没法审）

- **环境路线**：conda 新建 / repo 官方 docker——<选择 + 理由>。
  （判据：repo 有官方维护的 Dockerfile / 镜像 且 编译型依赖重 → 优先 docker，省掉本地编译对齐；否则 conda。）
- **conda env 名** / **Python 版本**：<env-name> / 3.x
- **torch × CUDA 组合**：<torch 2.x + cuda 11.8>——<理由：机器 nvcc 是 X、repo 要求 Y，所以选这个组合>
- **编译型依赖处置方案**（选型报告列出的依赖风险，逐条写明处理办法）：
  - <mmcv-full：用预编译 wheel（cu118/torch2.1 index），不本地编译——理由：官方 wheel 覆盖此组合>
  - <flash-attn：无覆盖组合，源码编译预计 20 分钟；失败 fallback xformers>
  - 无编译型依赖则写"无"。
- **资源判断**：开发卡 <1×A100 40GB>，预计 smoke run 单 step 显存 <XGB>（依据：模型参数量 / 官方 config 的 bs），够支撑 execution 迭代开发（不对标 repo 声称的 8 卡规模）。

## 3. 数据 & 权重清单

**数据集**：

| 数据集 | 在 repo 里的角色 | 版本 | 来源 | 大小 | 需账号? | 处理（转换 / 预处理） | 自动 / 手动 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <COCO> | 训练 + val benchmark | v2 | <url / 官方> | ~25GB | 否 | COCO 格式直用 | 自动 |
| <CustomX> | 消融用 | - | <网盘> | 5GB | 是(提取码) | 需转 COCO 格式 | **手动(账号)** |

**checkpoint / 权重**：

| 权重 | 来源 | 大小 | 加载方式 | 自动 / 手动 |
| --- | --- | --- | --- | --- |
| <backbone.pth> | <url> | 200MB | strict=True 全 key | 自动 |

> 「在 repo 里的角色」一列必须填——它决定这个数据集值不值得花时间（benchmark 必须版本对齐论文，消融用可以宽松）。

## 4. 验证标准（"setup 完成"的定义——每条都要是可判定的通过条件，不是"能跑通"）

- **Layer 1 import / config**：framework + 项目 package + config 系统加载无报错；`torch.cuda.is_available()` 为真；编译型算子 import 无 undefined symbol。
- **Layer 2 synthetic smoke**：smoke script 调真实 model/loss/collate，forward 输出有限且非全零、loss 量级合理（参考：<N 类分类交叉熵初始 ≈ ln(N)>）、backward 梯度非全零。
- **Layer 3 官方命令 smoke run**：smoke train <5 iter> loss 从 <初始量级> 下降且无 NaN；tiny subset eval metric > 0 且已排除异常满分；实测开发卡单步显存峰值和耗时。
- （主要调用关系自 survey：训练链 `train.py:main → build_model → forward → loss`；eval 链 `eval.py:evaluate → load_ckpt → forward → metric`；数据链 `dataset.py:__getitem__ → transforms → collate`。）

## 5. 已知问题、待验证风险和需确认的实验变更

**确定要处置的**（已知、已列入计划）：
- <config 多处硬编码 data_root，逐处改全>
- <mmcv 编译（处置方案见 §2）>

**风险待验证的**（可能踩、setup 中实测核验）：
- <survey 预判：数据集 v1 vs v2 标注有改动，metric 可能对不上——数据就绪时对齐版本（自 survey)>
- <社区有人报 checkpoint key mismatch——Layer 3 加载时核 missing/unexpected keys（自 survey)>
- license 同意：<某权重需点击同意条款，是停下交用户的点>

**语义改动预警**（遇到时立即暂停，汇报为什么 + 怎么改，等用户确认）：
- checkpoint 加载可能 strict=False（key mismatch）→ 即停
- <数据集 annotation 可能要 label map 修正> → 即停
- <metric 调用参数 / config 中与实验相关的默认值> → 即停
````

---

## 填好的示例片段（深度对照）

**环境决策 · 浅（不合格）**：

> torch 2.1 + cuda 11.8，conda 新建。

**环境决策 · 深（合格）**：

> 环境路线：conda 新建——repo 无官方 Dockerfile，且依赖里有 mmcv-full 要现场对齐，docker 没有现成镜像可用。
> torch 2.1 + cuda 11.8——机器 nvcc 11.8、驱动支持到 12.x；repo requirements 钉 torch==2.1.*；
> survey 预判 mmcv 编译难，但官方 wheel index 恰好覆盖 cu118/torch2.1，直接预编译，不现场编译（自 survey，已核 wheel index 有货）。

差别：浅的只给结论，深的给了"为什么是这个结论"——用户审 spec 审的是后者。

---

## 模板使用说明

- **用 Spec 确认准备目标、方案和风险**。重点说明环境与资源决策的理由、哪些工作需要用户手动完成，以及已知问题、待验证风险和需确认的实验变更。
- **分别列出已确认问题与待验证风险**：「确定要处置」= 已核实、已列计划的工程活；「风险待验证」= 尚未确认、需要在 setup 中实测核对的情况。
- **继承自 survey 不单列**：survey 的主要调用关系进第 4 节、依赖安装和兼容性问题进第 2 / 5 节、关键风险进第 5 节，各标 "(自 survey)"。
- **没有 survey 也能填**：独立 setup 时，"来自哪"写用户指定，各节从 repo 实际探索填，不强依赖 survey。
- **spec 确认后才转 Plan**：spec 没确认不往下走（SKILL 核心纪律 · 两个确认点）。
