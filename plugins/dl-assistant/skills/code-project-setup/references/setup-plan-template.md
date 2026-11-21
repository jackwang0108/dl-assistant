# Setup Plan 模板（code-project-setup）

> 由 `setup-spec.md` 转。spec 定 what / why，本份定 **how——分任务执行计划**。
> 审阅通过后进工程执行区，按任务开 tasklist 逐项跟踪。
>
> 保存 `setup-plan.md`。技术术语保留，整体中文。
>
> **每个任务对应 setup-report.md 的一节**——执行时逐节回填实际结果（见 `setup-report-template.md`），
> 所以任务边界要和 report 的任务节一一对得上。

---

````markdown
# Setup Plan: <repo-name>

> 由 setup-spec.md（已审阅确认）转来。本份把 spec 的方案分解成有序任务，执行时进 tasklist 跟踪，
> 每完成一个任务当场回填 setup-report.md 对应任务节。有问题就改，改到确认再执行。

## T1 网络镜像就绪

- **目的**：明确本次下载策略，避免后续装包 / 下数据反复失败。
- **做什么**：探网络（直连 / 代理 / 镜像），配 `HF_ENDPOINT` / `PIP_INDEX_URL` 等（通用策略见 `dl-assistant/references/network-mirror.md`）。
- **预期结果**：装包、下权重、下数据三条通道各验证一次能通；采用的策略值确定，记进 report。
- **依赖**：无

## T2 环境配置（含编译型依赖）+ Layer 1

- **目的**：把代码能 import 的环境建出来。
- **做什么**：按 spec §2 建 conda env（或起官方 docker）、装依赖、处置编译型依赖；装完做 Layer 1 import 验证。
- **预期结果**：framework + 项目 package + config 系统加载无报错；CUDA 链对齐（`torch.cuda.is_available()` 为真、算子无 undefined symbol）；`env/` 五件套导出。
- **依赖**：T1

## T3 数据 & 权重就绪 + 数据集速览

- **目的**：数据真能被 loader 读到、checkpoint 真能加载。
- **做什么**：下载 / 转换 / 改硬编码路径 / 造 subset / 验证 loader 读真实样本；checkpoint 下载并 strict 加载验证；挑样本产 `<repo>-datasets-intro.md` + `images/`。
- **预期结果**：每个数据集 loader 读到真实样本（非空）、版本与论文协议对齐；checkpoint strict 加载 key 全中；数据集速览落盘。
- **依赖**：T1

## T4 Layer 2 synthetic smoke

- **目的**：在真实数据之外先验一次数值链路，拦截静默错误。
- **做什么**：写 smoke script 调真实 model / loss / transform / collate / trainer 组件，显式断言数值；script 落盘 `smoke.py`。
- **预期结果**：forward 输出有限非全零、形状对；loss 有限正数、量级合理；backward 梯度非全零。smoke script 进产出目录。
- **依赖**：T2, T3

## T5 Layer 3 官方命令 smoke run

- **目的**：验证官方入口命令每条链能从头跑到尾、出的数机械上合理；实测开发卡足迹。
- **做什么**：枚举官方 train / eval / inference / demo / preprocess 命令逐个判 ready / blocked；能轻量跑的做 smoke 验证（tiny subset eval → 1-5 iter train）；记单 step 显存 / 耗时。
- **预期结果**：smoke train loss 趋势下降无 NaN；eval metric > 0 且非假满分；`dev_card_footprint` 实测值到手；blocked 清单明确。**不对照论文数字**（那是 code-paper-reproduction 的事）。
- **依赖**：T4

## T6 可复现性基线

- **目的**：摸清 repo 随机性从哪来，给 execution 的可比性审计打底（只摸不改）。
- **做什么**：查 seed 设置位置、`cudnn.deterministic` / `benchmark`、dataloader shuffle / worker seed。
- **预期结果**：`setup.json` 的 `reproducibility` 块填齐 + report 记一节叙事。
- **依赖**：T5

## T7 报告收尾

- **目的**：把执行中动态回填的 report 定稿，机读区填齐。
- **做什么**：写「就绪结论」节；`setup.json` 全字段定稿（值要真：验证过才填 ✓，没验证标状态，查不到标 unknown）；核对目录产物齐。
- **预期结果**：setup.json + setup-report.md 描述同一事实不打架；产出目录完整。
- **依赖**：T1-T6

## T8 git 汇报 → merge

- **目的**：让 setup fix 干净可回溯地进主分支。
- **做什么**：在 `code/project-setup` 分支向用户汇报全部修复；用户同意才 merge；有疑问停在分支继续修。
- **预期结果**：用户同意，merge 回主分支，交棒下游。
- **依赖**：T7

## 执行纪律

- **tasklist 跟踪**：进工程执行区时，把任务建进 tasklist，逐项 in_progress → completed。
- **report 动态更新**：每完成一个任务，当场回填 setup-report.md 对应任务节（实际结果 + 是否成功），不留到最后补写。
- **语义改动即停**：任意任务执行中命中语义改动（strict=False / label map / metric / config 实验值），立即停下、汇报为什么 + 怎么改、等用户拍板（SKILL 核心纪律，贯穿全程）。
- **长任务托管**：大下载 / 偏长 smoke run 走 tmux detach（详见 `dl-assistant/references/long-run-ops.md`），不用 run_in_background。
- **死结上报**：编译型依赖反复修不动、大资源超 spec 估算、需人工点击同意条款——停下报告用户，不盲耗。
- **只补未完成**：中断恢复时扫产物定位断点，不重跑已验证的任务。
````

---

## 填好的示例任务（深度对照）

**浅（不合格）**：

> ## T3 数据就绪
> - 下载数据集，验证 loader。

**深（合格）**：

> ## T3 数据 & 权重就绪
> - **目的**：COCO val2017 真能被 repo 的 loader 读到，且和论文协议（v2 标注、官方 split）对齐。
> - **做什么**：官方源下 val2017 + annotations（镜像站加速）；改 `configs/base.py` 和 `tools/train.py` 两处硬编码 data_root；固定 seed 抽 200 张造 smoke subset；用 repo 的 `CocoDataset` 读 3 个真实样本；下 R50 backbone 权重 strict 加载。
> - **预期结果**：loader 返回非空样本、bbox 格式 xyxy 与 annotation 一致；权重 167 个 key 全中无 missing；数据集速览落盘（3 样本：典型 / 密集小目标 / 遮挡）。
> - **依赖**：T1

差别：浅的没有可判定的完成线，agent 做到哪算哪；深的「预期结果」就是完成判据，也是 report 回填时的对照基准。

---

## 模板使用说明

- **T1-T8 是典型骨架，不是菜单**：按 spec 增删——没有编译型依赖就合并 T2 内容、没有数据要下就砍 T3 大半、走 docker 就把 T2 换成镜像路线。但**任务边界要和 report 的任务节一一对应**（report 按任务节动态回填）。
- **每个任务三件套**：目的（为什么有这一步）/ 做什么（具体动作）/ 预期结果（可判定的完成判据）——预期结果就是执行后 report 里「实际结果」的对照基准。
- **任务粒度**：按"一个可验证的产出"切（环境建好、数据就绪、某层验证通过），不是按命令粒度。
- **每个任务可追溯到 spec 某一节**，不凭空加任务。
- **T8 git 汇报 merge 是最后一步**：所有修复在 project-setup 分支，完成后汇报、用户同意才 merge（详见 SKILL 核心纪律 · git 工作流）。
- **Plan 确认后才执行**：Plan 没确认不进工程执行区（SKILL 核心纪律 · 两个确认点）。
