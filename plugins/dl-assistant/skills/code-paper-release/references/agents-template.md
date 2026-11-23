# `AGENTS.md` template（release repo 的 供编程助手使用的说明）

release repo 根目录的 `AGENTS.md`——**给 agent 读的安装/运行指引**，和 README（给人读）互补。外部读者 用 coding agent 跑这个 repo 时，agent 读它就能自主完成装环境、备数据、训练、推理、回归，不用人逐条转述。

> 写作纪律：
> - **命令精确到参数**——agent 照抄就能跑，不要「按需修改」「参考文档」式模糊。
> - **写清输出落点**——每个命令的产物落在哪（checkpoint 路径、log 路径、metrics 输出），agent 验证结果要用。
> - **写清判断标准**——怎么算成功（loss 降 / metrics 落在基准容差内），agent 自己裁决。
> - **已知问题与解决方法必写**——发行版验证中实际遇到的问题（数据版本、驱动要求、显存门槛），这是这份文件最值钱的部分。
> - 按外部读者可获得的资料编写，同 README：零内部信息。

## 生成时照这个结构写

````markdown
# AGENTS.md

本文件指导 coding agent 安装、运行本仓库。所有命令在 <OS + GPU 型号> 上实测通过。

## 环境

- 依赖：conda（必需）；Docker（可选，见文末）。
- 安装：
  ```bash
  conda env create -f environment.yml
  conda activate <env 名>
  ```
- 硬件门槛：<GPU 型号/显存下限，如 单卡 24GB>；训练参考资源：<X 卡 Y 小时>。
- 验证环境就绪：<一条 smoke 命令，如 python -c "import torch; ..." 或跑 1 个 step>。

## 数据

- 准备：
  ```bash
  <下载/预处理命令>
  ```
- 数据落点：`<预期目录结构>`；大数据集详细步骤见 `docs/data_preparation.md`。
- 验证数据就绪：<一条检查命令，如 ls 计数或 dataloader 单 batch 试跑>。

## 推理

```bash
bash scripts/eval.sh --checkpoint <权重路径> --data <数据路径>
```

- 预训练权重：<下载链接 + 放置路径>；也接受自训权重（同格式）。
- 产物保存位置：metrics 打到 stdout + `<metrics 输出文件路径>`。
- 成功判据：输出指标落 `docs/perf-baseline.json` 对应 tolerance 内。

## 训练

```bash
bash scripts/train.sh --config configs/<主表 config> --data <数据路径>
```

- 产物保存位置：checkpoint → `<路径>`；log → `<路径>`。
- 成功判据：loss 正常下降、出 checkpoint；复现性能用回归脚本判（下节）。

## 性能回归（复现主表）

```bash
bash scripts/perf-regression.sh
```

逐项输出 pass/fail（比对 `docs/perf-baseline.json`）。全部 pass = 环境/代码/数据/权重全链路正确。

## 目录与论文组件的对应关系

<目录树：src/ 各模块对应论文哪个组件（标论文公式/section 编号）、configs/、scripts/、docs/。agent 改代码前先读这节。>

## 已知问题与解决方法

<发行版验证中实际遇到的问题，逐条写：现象 → 原因 → 解法。例如：torch 版本必须 >= X（低版本 <算子> 行为不同）；数据集必须是 <版本>，新版字段改名；单卡 batch 需梯度累积等效。没有就写「暂无」。>

## Docker（可选）

```bash
docker build -f docker/Dockerfile.infer -t <repo>-infer .
docker run --gpus all -v <数据>:/data -v <权重>:/checkpoints <repo>-infer <命令>
```

容器内命令与裸机一致；数据/权重一律挂载，不进镜像。
````

## 与 README 的分工

| | README | AGENTS.md |
|---|---|---|
| 读者 | 人（外部读者） | agent |
| 重点 | 工作介绍 + 效果 + quickstart | 精确命令 + 产物保存位置 + 成功判据 + 已知问题与解决方法 |
| 写法 | 先结果后步骤，有图有表 | 纯操作序列，无叙事 |

两份文件的命令必须一致（同一真相源：Step 5 回归实际跑过的运行命令）——改一处同步另一处。
