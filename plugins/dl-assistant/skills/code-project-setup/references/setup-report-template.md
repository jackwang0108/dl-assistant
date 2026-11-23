# Setup Report 模板（code-project-setup）

> 产物即真相。工程执行期间每完成一项任务，立即在对应章节记录实测值和任务是否成功。
> 「就绪结论」节在 T7 报告收尾时定稿。
>
> 下游技能统一从 **`setup.json`** 读取配置。本报告用中文面向用户说明仓库的准备情况和任务结果，保留必要的技术术语。
>
> 保存 `setup-report.md`，和 `setup-spec.md` / `setup-plan.md` / `setup.json` / `<repo>-datasets-intro.md` / `smoke.py` / `env/` / `images/`
> 同目录，**固定落 `docs/code-project-setup/<repo>-<日期>/`**。

---

````markdown
# Project Setup Report: <repo-name>

> 由 code-project-setup 在 GPU 服务器（开发卡）产出。机读交接在 `setup.json`。
> 任务执行记录（§2）随执行动态回填；第 0 节「就绪结论」在收尾时定稿。

## 0. 就绪结论（T7 收尾时定稿——读报告先看这一节）

- **三层验证**：Layer 1 import <✓> / Layer 2 synthetic smoke <✓> / Layer 3 smoke run <✓ 或部分>。
- **能直接干什么**：<ready 入口一句话——eval / smoke train / inference 各自命令在 setup.json>。
- **不能干什么（blocked）**：<blocked 清单一句话，如 train_full 需 8 卡、dataset2 待用户手动下>。
- **最大的语义风险**：<一句话，如 checkpoint 有 3 个 unexpected key 已确认是 module. 前缀、不影响>。
- **建议下一步**：<code-paper-reproduction（主线）/ code-reading>。

## 1. repo 介绍 + 继承来源

- **是什么 / 来自哪**：<任务 + 框架；baseline-survey 推荐（commit）/ 用户指定>。
- **继承自 `baseline-survey.json`**：主要调用关系 / 可能遇到的依赖问题 / 关键风险（直接使用已有信息）。
- **实测推翻 / 修正 survey 的地方**：<survey 预判 X，实测为 Y——如"预判 mmcv 难编译，实测官方 wheel 直接可装"；没有就写"无">。

## 2. 任务执行记录（随执行动态回填——每完成一个任务当场更新）

> 每个任务五件套：目的 / 做了什么 / 预期结果 / 实际结果 / 是否成功。
> 目的和预期结果从 setup-plan.md 对应任务抄；实际结果写**实测值**（不是"通过了"），失败写现象 + 处置。

### T1 网络镜像就绪

- **目的**：<从 plan 抄>
- **做了什么**：<实际执行的策略——直连通 / 配了 HF_ENDPOINT=... / PIP 走清华镜像>
- **预期结果**：<从 plan 抄>
- **实际结果**：<三条通道实测各一句话>
- **是否成功**：✓ / ✗（原因）

### T2 环境配置（含编译型依赖）+ Layer 1

- **目的**：<从 plan 抄>
- **做了什么**：<环境路线（conda / docker）、关键安装命令与版本决策、编译型依赖的最终版本搭配和遇到的安装问题（诊断详见 `compile-deps.md`）>
- **预期结果**：<从 plan 抄>
- **实际结果**：<Layer 1 实测：import 通过情况、torch/cuda 真值、算子 import 结果>
- **是否成功**：✓ / ✗（原因）
- **环境导出**：`env/` 五件套；CUDA/cuDNN 版本在 setup.json；OS 系统依赖（apt 装的）记这。

### T3 数据 & 权重就绪 + 数据集速览

- **目的**：<从 plan 抄>
- **做了什么**：<每个数据集：下载源 / 转换 / 改了哪些硬编码路径 / 测试子集构建方法；checkpoint 加载验证>
- **预期结果**：<从 plan 抄>
- **实际结果**：<每个 dataset 版本 / 路径 / loader 验证结果（真实样本非空）；checkpoint strict 加载 key 情况>
- **是否成功**：✓ / ✗（原因；blocked-by-* 的记这里并进 setup.json 的 blocked）

> 数据集本身长啥样（是什么 / 规模 / 真实样本）见 `<repo>-datasets-intro.md`，台账只记就绪状态。

### T4 Layer 2 synthetic smoke

- **目的**：<从 plan 抄>
- **做了什么**：<smoke script 调了哪些真实组件；script 已落盘 `smoke.py`>
- **预期结果**：<从 plan 抄>
- **实际结果**：<实测值：smoke loss = X.XX（参考量级 ln(N)≈Y）、输出有限非全零、梯度范数 > 0>
- **是否成功**：✓ / ✗（原因）

### T5 Layer 3 官方命令 smoke run

- **目的**：<从 plan 抄>
- **做了什么**：<枚举了哪些官方命令、各判 ready / blocked；smoke 跑了哪些>
- **预期结果**：<从 plan 抄>
- **实际结果**：<smoke train：loss X.XX → Y.YY 下降；tiny eval metric = Z（非零，且已排除异常满分）；checkpoint missing/unexpected keys 清单；单 step 显存 XGB / 耗时 Ys>
- **是否成功**：✓ / ✗（原因）

> smoke run 用于验证评测命令可以完成并通过基本数值检查。与论文数字比较由 code-paper-reproduction 完成。

### T6 可复现性基线

- **目的**：<从 plan 抄>
- **做了什么**：<查了哪些文件的随机性来源>
- **预期结果**：<从 plan 抄>
- **实际结果**：<seed 位置 / cudnn deterministic·benchmark / dataloader shuffle·worker seed——机读版在 setup.json `reproducibility` 块，这里记叙事与发现（如"repo 根本没设 seed"）>
- **是否成功**：✓（只摸清未强改——留给 execution 的可比性审计做依据）

### T7 报告收尾

- **做了什么**：就绪结论定稿、setup.json 全字段填齐、产物核对。
- **是否成功**：✓

### T8 git 汇报 → merge

- **实际结果**：<用户同意，merge 回主分支（merge commit）/ 停在分支待确认>
- **是否成功**：✓ / 待确认

## 3. 允许的 setup fixes 与语义风险

- 本次在 `code/project-setup` 分支做了哪些 setup fix（dependency / path / config 运行参数），用户已同意 merge。
- **仍需注意的语义风险**（触及或未触及但需提防：strict=False 影响、label map、metric 参数、与实验相关的 config 默认值）。

## 4. 下游交接

- ready 入口 → 推荐给 `code-paper-reproduction`（验性能，主线下一步）/ `code-reading`（读源码）/ `code-idea-execution`（实现 idea）的具体 command / config / 数据 / checkpoint。
- 仍 blocked 的资源清单。
- Layer 3 smoke run 已记录损失趋势和指标量级。之后由 `code-paper-reproduction` 与对应的参考结果比较。
- 建议下一步 skill。
````

---

## setup.json（供下游技能读取的配置，单独文件）

> 下游 agent（`code-paper-reproduction` / `code-reading` / `code-idea-execution`）直接读这一份继承配置。
> 字段名稳定、值要真（验证过才填 ✓，没验证标状态，查不到标 unknown，不编）。

```json
{
  "repo": { "name": "<repo>", "url": "<git-url>", "branch": "<branch>", "commit": "<sha>" },
  "conda_env": "<env-name>",
  "python": "3.x",
  "torch": "2.x (cuda 11.8)",
  "cuda_toolkit": "11.8",
  "ready_commands": {
    "eval": "python tools/test.py configs/xxx.py ckpts/xxx.pth --eval bbox",
    "train_smoke": "python tools/train.py configs/xxx.py --cfg-options runner.max_iters=5",
    "inference": "python demo.py --img demo.jpg --config configs/xxx.py --ckpt ckpts/xxx.pth"
  },
  "data": {
    "<dataset>": { "path": "/data/<dataset>", "split": "train/val", "status": "✓ loader 读到真实样本" }
  },
  "checkpoint": {
    "<name>": { "path": "/ckpts/<file>.pth", "status": "✓ strict=True 全 key 加载", "source": "<url>" }
  },
  "blocked": [
    "train_full: blocked-by-resource（需 8 卡，开发卡仅够 smoke）",
    "<dataset2>: blocked-by-data（需 Kaggle 账号，待用户手动下）"
  ],
  "dev_card_footprint": {
    "card": "1×A100 40GB",
    "single_step": { "mem_peak": "18GB/40GB", "time": "0.8s/iter @ bs=2" },
    "verdict": "够支撑 smoke 迭代开发；full 规模需 release 后上多卡运行服务器"
  },
  "reproducibility": {
    "seed_locations": ["<train.py:42 全局 seed>", "<dataloader.py worker_init_fn>"],
    "cudnn": { "deterministic": "true | false | 未设置", "benchmark": "true | false | 未设置" },
    "dataloader": { "shuffle": "<train: true / val: false>", "worker_seed": "<固定 | 未固定>" }
  },
  "paper_metrics": [
    { "metric": "<如 mAP>", "value": "<论文值>", "dataset": "<数据集/split>", "source_page": "<出处页码>" }
  ],
  "dataset_report": "<repo>-datasets-intro.md",
  "env_export": "env/",
  "smoke": "smoke.py"
}
```

字段说明（json 无注释，写在这里）：

- `conda_env`：激活方式 `conda activate <env-name>`；走 docker 路线时改为镜像名 + 进入方式。
- `torch` / `cuda_toolkit`：torch 及其绑定的 CUDA / 环境内 nvcc 版本。
- `ready_commands`：**只放 Layer 3 已验证过的入口**，下游可直接用。`train_smoke` 是用官方命令做分钟级试运行，不是 reproduction 的 reduced setting（用于迭代的小时级较小实验），名字不混用。
- `data` / `checkpoint` 的 `status`：✓ = 已验证可读，✗ = blocked。
- `blocked`：下游要知道还差什么。
- `dev_card_footprint`：开发卡单步显存峰值和耗时实测值——判断够不够支撑 execution 迭代，非对标原文多卡规模。
- `reproducibility`：可复现性基线（只摸清未强改），给 execution 的可比性审计打底；叙事版在任务执行记录 T6。
- `paper_metrics`：自 `baseline-survey.json` **原样继承、不核对**——指标契约的传递带，code-paper-reproduction 的验收基准初稿（CPR 会回论文核对并冻结）。
- `dataset_report` / `env_export` / `smoke`：指向同目录的补充材料。

---

## 模板使用说明

- **每完成一项任务就更新报告**：任务执行记录（§2）是执行过程中逐节回填的——每完成一个任务当场写「实际结果 + 是否成功」，不留到最后。实际结果写**实测值**（loss 数值、显存 GB、key 数量），不写"通过了"三个字。
- **就绪结论前置**：§0 是收尾时定稿的 TL;DR——用户读报告先看这节就知道"就绪到什么程度、能干什么、不能干什么、需要优先处理的风险"，后面各节是证据。
- **任务节与 plan 一一对应**：plan 加了 / 删了任务，台账同步加 / 删节；「目的」和「预期结果」直接从 plan 抄，「实际结果」回填时对照预期写。
- **下游统一从 setup.json 读取配置**：conda_env / ready_commands / data / checkpoint / blocked / dev_card_footprint / reproducibility / paper_metrics 这几个 key 下游 agent 直接读。人读 `setup-report.md` 描述同一事实的另一面，**保持两份文件中的信息一致**——改了路径 setup.json 和 setup-report.md 都改。
- **恢复入口**：`setup.json`（尤其 conda_env / data / checkpoint / ready_commands）+ 任务执行记录的成败状态，就是 setup 中断后的恢复总纲，配合扫 env / 数据 / ckpt 真实文件定位断点（见 `dl-assistant/references/long-run-ops.md`）。
