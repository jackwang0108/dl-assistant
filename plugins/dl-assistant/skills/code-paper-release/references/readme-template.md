# `README.md` template（发行版使用说明）

release repo 的 README——**供外部读者快速了解论文和代码**。假设读者只有论文 PDF，拿到 repo 后 5 分钟内要知道：这是什么工作、效果如何、怎么跑起来。

> 写作纪律：
> - **按外部读者可获得的资料编写**——零内部信息（无中期 repo 节点名/分支名、无被否 idea、无内部研究过程记录、无内部路径）。
> - **命令必须真跑过**——README 里每条命令都是 Step 5 回归实际验证过的，一条都不许凭记忆写。
> - **先给结果再给步骤**——外部读者 先看到主表和 teaser，建立信任后才愿意装环境。
> - 方括号 `<...>` 是占位符，生成时替换；没有的节（如 demo 视频）整节删掉，不留空标题。

## 生成时照这个结构写

````markdown
# <论文标题>

[<会议/期刊 徽章，如 NeurIPS 2026>] [[论文 PDF 链接]](<arXiv 或会议链接>) [[项目页]](<GitHub Pages URL，如有>) [[预训练权重]](<权重下载链接>)

> <一句话说清这篇论文做了什么、效果多好——从 abstract 提炼，不超过两句。>

![teaser](<teaser 图路径或链接>)

## 简介

<2-4 句：问题是什么、方法核心是什么、主表关键数字。从论文 abstract/introduction 提炼，不抄原文整段。>

## 主要结果

<论文主表，markdown 表格照抄 PDF 主表数字，标粗本方法。表下注明：完整结果见论文。>

| Method | <指标1> | <指标2> |
|---|---|---|
| <最强 baseline> | ... | ... |
| **Ours** | **...** | **...** |

## 环境安装

```bash
conda env create -f environment.yml
conda activate <env 名>
```

Docker 用户见 [Docker 使用](#docker-使用)（可选节）。

## 数据准备

<小数据集：给自动下载命令/脚本。>
<大数据集：一句话 + 指向 `docs/data_preparation.md`。>

## 推理（用预训练权重）

```bash
# 下载预训练权重（<HF Hub / 云盘链接>），放到 checkpoints/
bash scripts/eval.sh --checkpoint checkpoints/<权重文件> --data <数据路径>
```

预期输出：<主表指标数值>（基准见 `docs/perf-baseline.json`）。

## 训练

```bash
bash scripts/train.sh --config configs/<主表 config> --data <数据路径>
```

<训练资源参考：X 卡 Y 小时（来自 CPE GPU 小时用量记录）。>

## 复现主表（性能回归测试）

```bash
bash scripts/perf-regression.sh
```

一键复现主表并比对基准（`docs/perf-baseline.json`），逐项输出 pass/fail。

## Docker 使用（可选节）

```bash
# 推理镜像
docker build -f docker/Dockerfile.infer -t <repo>-infer .
docker run --gpus all -v <数据目录>:/data -v <权重目录>:/checkpoints <repo>-infer ...

# 训练镜像
docker build -f docker/Dockerfile.train -t <repo>-train .
```

## 仓库结构

<5-10 行目录导览，只列 外部读者 需要知道的：src/ 模块与论文 method 组件的对应、configs/、scripts/、docs/。>

## 引用

```bibtex
<论文 bibtex>
```

## License

<LICENSE 名，见 LICENSE 文件>
````

## 各节深度标尺

- **一句话简介**：能独立看懂，不依赖读全文。浅（差）：「This is the official implementation of our paper.」深（好）：「我们提出 X，用 <一句话机制> 解决 <什么问题>，在 <数据集> 上把 <指标> 从 A 提到 B。」
- **主要结果**：照抄论文主表数字，和 PDF 一致（Step 5 对外验收已核过）。不要把消融表也堆进来。
- **Quickstart 运行命令**：装环境 → 备数据 → 推理 → 训练 → 回归，顺序就是 外部读者 的实际操作顺序。每条命令都带具体参数，不写 `<见文档>` 式占位。
- **训练资源参考**：外部读者判断跑不跑得起的依据，从 CPE `pkg-meta.json` 的 GPU 小时用量记录获取实际用量。
