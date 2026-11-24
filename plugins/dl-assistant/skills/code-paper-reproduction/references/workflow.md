# 复现参考结果与建立比较基准运行手册

每一步写清执行什么操作、从输出检查什么、异常时回到哪一步、把证据记在哪里。按 [SKILL 的六步流程图](../SKILL.md#运行流程图)推进。具体命令从实际仓库、配置和已验证入口中取得。示例中的项目和结果均为虚构。

## Step 1 核对 setup 与当前现场

从当前仓库开始，优先读取用户给的 setup 目录。将本轮目标与实际检查范围对应起来。旧记录或无 setup 文件的已有项目，用当前环境、配置和资产补核所需前置条件。

| Setup 记录 | 复现怎么用 |
| --- | --- |
| `components`、`environments`、`data`、`checkpoint` | 核本轮所需的实际仓库、环境、数据和权重身份。记录已确认可复用的版本和范围 |
| `operations`、`supported_operations` | 定位对应入口，确认实际完成的是组件检查、小样本试跑还是完整入口运行 |
| `checks` | 回查实际命令、工作目录、配置、输入、日志和结果。确认检查条件还能否用于当前目标 |
| `validation_targets`、`paper_metrics` | 定位待核的正式配置、参考结果和出处。Step 2 再核精确表格行及协议 |
| `ready_commands`、`blocked` | 查已验证命令和仍受阻的入口。按实际需要处理与本轮目标有关的缺项 |

`ready_commands.eval` 缺失时先查正式评测候选入口和已有检查。若 setup 只跑过小样本，但所需环境、权重和完整验证数据已准备，则进 Step 2 核论文目标及正式配置。若环境或资产缺失、正式路径需要 setup 修复，再把具体缺项交回。两种情况分别写到开工记录。

```bash
git rev-parse --show-toplevel
git status --short --branch
git rev-parse HEAD
git diff --stat
git diff --cached --stat
git branch --list 'code/paper-reproduction'
df -h .
command -v tmux
```

按实际硬件核设备和占用。NVIDIA 机器可用 `nvidia-smi -L` 与 `nvidia-smi`。用计划采用的解释器核版本，例如 `"$repro_python" -V`。查准备记录中的真实入口、资产路径以及已验证版本。资产或环境有变化时，只补核受影响入口。数据和权重缺少必要身份、校验或真实读取证据时，交 `code-project-setup` 做对应准备。

| 已有状态 | 先核什么 | 怎样续做 |
| --- | --- | --- |
| 只有 setup 小样本检查 | 检查范围、命令、试跑配置与正式配置差异 | 在 Step 2 核正式目标与入口，需要补准备的项目交 setup |
| 复现规格已批准 | 规格版本、用户答复、预算、当前代码和资产 | 条件一致则继续对应运行，实质变化回 Step 2 |
| 有已启动任务 | 原运行的 `meta.json`、会话名或作业 ID、日志和退出记录 | 按 [Step 3](#step-3-按目标执行评测训练或组件检查)核状态，活跃任务沿用原会话 |
| 有结果或 checkpoint | 产生它的命令、协议、运行状态和实际完整性 | 条件一致时复用已有结果。续训另记尝试和 checkpoint 来源 |

**核对完先向用户汇报。** 说明实际仓库、分支与 commit、执行机器、已准备并可复用的环境和资产、已验证入口的范围、缺项及准备从哪一步继续。按[复现条件与差距核对模板](alignment-template.md)创建 `alignment.md`，把依据记入开工核对。与当前目标无关的缺项可以留在未决记录。

例如：「当前是 edge-vision 的 c91b7e4，目标机 edge-dev-01。Setup 的 C03 已验证 17 个样本都进入 E02 的指标统计，环境、Vision-S r1 与 Vision-Val v1/val 可以复用。完整评测还没跑。我先核论文参考行与 `configs/eval.yaml`，再给你看复现条件和成本。」

## Step 2 定位准确的参考结果与协议，写复现规格

1. **确认要复现什么。** 按[复现规格分析指引](reproduction-spec-guide.md)从后续用途倒推目标，再找对应的参考结果或行为。按[论文检索](../../paper-search/SKILL.md)先用 `get_capabilities` 核可用来源。有 DOI 或 arXiv ID 时用 `get_papers` 核身份。仅有标题时用 `resolve_papers` 核候选。读 arXiv 源码时按[论文源码](../../tex-mcp/SKILL.md)用 `tex_open` 固定版本，以 `document_id` 调用 `tex_outline`、`tex_read` 读表格和方法。需核成品版式或手上只有 PDF 时，按[论文 PDF](../../pdf-mcp/SKILL.md)用 `pdf_open` 打开固定文件，再查相关页和图表。若目标是维护者报告的参考行为，则核实际发布版本、模型、数据和协议。
2. **把参考条件逐项落到实际代码。** 从表格行、图注和实验设置取模型变体、checkpoint 来源、数据及划分、指标单位、聚合与训练条件。沿实际启动命令、配置覆盖、权重加载、loader 和指标实现追到关键调用。可用下方搜索起步，再回读配置与源码确认。
3. **写清要验证的操作和判据。** 根据[复现验证策略](reproduction-strategy.md)选择适用的评测、训练或组件检查。说明每项要回答什么、目标条件与当前条件有何差异、何时停止、重复运行的依据和预计成本。先写可比条件，再写结果接近、有差距或证据不足时如何判断，以及哪些观察会触发追加检查。判断数值时注明单位和判据依据。
4. **给用户审阅。** 按[复现规格模板](reproduction-spec-template.md)保存 `spec.md`，引用 `alignment.md` 的核对表。请用户确认三个决定：**对照哪条结果、怎样判断可比、本轮投入多少资源**。说明仍未知的条件、打算怎样补证、何种变化需要重新确认。记录实际答复及批准版本。

```bash
rg -n 'checkpoint|resume|ema|split|dataset|metric|evaluator|batch|warmup|scheduler' configs tools scripts
```

只查项目实际存在的目录，按需要从命令继续查模块和函数。核对表至少包含「目标或条件｜参考值及原文位置｜实际配置与源码位置｜已核、差异或未知｜对比较的影响」。评测重点查实际 split、预处理、标签、聚合和原始或 EMA 权重。训练另外查有效 batch、BN、损失归约、数据增强、学习率时点和最终选取哪份权重。没有数值参考时，明确有出处的组件行为或检查范围。

### `alignment.md` 的核对片段

以本页的虚构 edge-vision 为例，第一次交审时可以这样写。目标编号与协议版本用于关联后续运行。

| 条件 | 参考条件与来源 | 当前配置或源码位置 | 当前判断及影响 |
| --- | --- | --- | --- |
| 目标 EVAL-01，协议 v1 | 论文 v2 表 2 的 Vision-S 行，Top-1 78.4% | `configs/eval.yaml`，`tools/eval.py` 的实际指标调用 | 待跑全量，按相同 Top-1 口径比较 |
| 数据及统计范围 | 表 2 图注及 §4.2，Vision-Val v1/val，500 个样本各计一次 | `configs/eval.yaml` 的 val 清单，`tools/eval.py` 的 loader 与指标入口 | 数据身份已核，完整统计覆盖待实测。Setup 的 C03 只覆盖 17 个 ID |
| 权重 | §4.2 指定 Vision-S r1 的 EMA 参数 | 发布文件可取得，`tools/eval.py` 的加载分支待从初次运行日志核实际选择 | 权重版本已核，参数变体待核。若实际用了原始参数，该结果仅用于诊断 |
| 指标及输出单位 | §4.2，正确分类数除以参与统计样本数，以百分比报告 | `tools/eval.py` 调用的分类指标，定位分子、分母和输出单位 | 指标定义已核，实跑保留分子、分母及样本 ID |

## Step 3 按目标执行评测、训练或组件检查

开始修改项目代码时，默认在本地 `code/paper-reproduction` 分支工作。核对起点和用户已有改动。首次从已确认的起点用 `git switch -c code/paper-reproduction` 建分支。续做先核已有分支对应的工作内容和记录，再切回。记录实际 commit 和有影响的 diff。

从已核入口提取完整命令。只通过小样本的命令沿用其验证范围，正式运行前重新核正式配置、权重和数据。把执行目录、解释器或容器、实际参数及输出路径写进 `runs/<run-slug>/command.sh`。在 `meta.json` 记录目标和协议版本、代码 commit 与 diff、有效配置、输入资产、设备、精度、seed 和状态。配置可由代码版本及覆盖项重建时记路径和参数。其他实际配置、覆盖文件或样本清单按需保存到 `config/`。独立重复记 seed 或重复编号，失败、中断和续训各用独立尝试编号。

| 操作 | 从哪里取实际命令 | 启动前核对 | 实际运行后留证 |
| --- | --- | --- | --- |
| 推理与评测 | 从 setup 已验证入口或作者正式配置追到实际脚本，核包装命令和设置覆盖项 | 模型与 checkpoint 实际加载路径、数据清单、预处理、指标及报告单位 | 确认加载的权重变体，保存样本 ID 与覆盖范围、指标输入输出、日志和退出码 |
| 训练 | 从对应参考结果的训练说明、启动器和实际配置提取。需恢复时核项目支持的恢复命令和附带状态 | 初始权重、恢复来源、有效 batch 与更新次数、BN、损失归约、调度、seed 和 checkpoint 选择规则 | 实际条件、逐次指标和曲线、训练产出的 checkpoint 身份，以及最终拿哪份权重评测和为什么 |
| 组件或局部检查 | 从仓库原测试或正式入口调用的组件提取检查脚本与测试参数 | 目标组件、可追溯输入、实际设备及预期行为依据 | 实际输入和观察、执行证据、覆盖范围及需要后续验证的部分 |

运行完成后把实际指标和范围存进 `metrics.json`，按形成的实际产物记录 `outputs/` 或大文件原位置。无数值输出的检查在报告中记录观察和日志。随运行更新 [复现报告和机读记录](reproduction-report-template.md)。项目使用 W&B 时，按[共同记录约定](../../wandb/references/experiment-records.md)关联本地尝试、运行和同步证据。

### 长任务启动与重连

预计超过 5 分钟、时长不确定或重跑代价高时，在实际执行机器使用 [run-long.sh](../../dl-assistant/scripts/run-long.sh) 托管。集群用调度器提交，记录作业 ID 和输出路径。诊断运行或 reduced 对照同样适用。

下面的例子在目标机从仓库根目录运行。先按计划写好 `command.sh` 和 `meta.json`，替换本机的脚本、目录及会话名称。示例的 `command.sh` 使用已核对的正式评测配置。

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /srv/research/edge-vision
exec /srv/envs/edge-vision/bin/python -u tools/eval.py --config configs/eval.yaml
```

将它保存到本次运行目录，再从仓库根目录启动。

```bash
run_long=/srv/skills/dl-assistant/scripts/run-long.sh
run_dir="$PWD/docs/code-paper-reproduction/edge-vision-2026-11-24/runs/eval-attempt-01"
session=repro-edge-vision-eval-01
printf -v run_command 'bash %q' "$run_dir/command.sh"
bash "$run_long" "$session" "$run_dir" "$run_command"
```

启动后立即核实际会话、日志和退出记录。重连从原运行的 `meta.json` 取得会话名和目录，复用这些变量核查。

```bash
tmux has-session -t "=$session"
test ! -f "$run_dir/$session.log" || tail -n 30 "$run_dir/$session.log"
test ! -f "$run_dir/$session.EXIT_CODE" || cat "$run_dir/$session.EXIT_CODE"
```

退出码缺失时核进程、日志和产物。会话已消失但找不到退出码时，状态保留待核。进程结束后查实际结果是否齐全，从有依据的 checkpoint 或下载断点续做。详见[共享长任务说明](../../dl-assistant/references/long-run-ops.md)。

### 一次运行实际留下什么

下面是上面启动示例的 `runs/eval-attempt-01/meta.json`，已按第一次运行的结果回填。`command_file`、日志、退出码、指标和产物路径均相对于该次运行目录。实际项目按已有证据填写。

```json
{
  "run_id": "eval-attempt-01",
  "attempt": 1,
  "target_id": "EVAL-01",
  "protocol_version": "v1",
  "repo_commit": "c91b7e4",
  "working_directory": "/srv/research/edge-vision",
  "environment": "/srv/envs/edge-vision/bin/python",
  "machine": "edge-dev-01",
  "config": "configs/eval.yaml",
  "data": "Vision-Val v1/val，完整 500 个样本",
  "checkpoint": { "release": "Vision-S r1", "loaded_parameters": "raw" },
  "comparison_seed": null,
  "session": "repro-edge-vision-eval-01",
  "command_file": "command.sh",
  "log_path": "repro-edge-vision-eval-01.log",
  "exit_code_path": "repro-edge-vision-eval-01.EXIT_CODE",
  "exit_code": 0,
  "execution_status": "completed",
  "metrics_path": "metrics.json",
  "outputs": ["outputs/evaluated-ids.txt"],
  "comparison_status": "not_comparable",
  "comparison_note": "参考结果用 EMA，首次运行日志显示加载 raw 参数"
}
```

此例 `comparison_seed` 留空，表示本次只进行固定权重评测，未开展按 seed 的训练比较。记录运行的实际随机性检查。`metrics.json` 记本次 Top-1 为 77.6%，分子 388、分母 500。该读数供诊断，比较结论另记在 `alignment.md`。

## Step 4 核对可比性与实际差距

每项目标分别回答四个问题。命令实际完成了吗？目标行为或数据范围核到了哪里？参考与本次条件能比较吗？在可比范围内，实际读数和参考差了多少？

- **先核条件。** 检查指标定义和单位、样本覆盖、数据及标签、实际权重、配置和评测方式。若实测数字接近，也核对应的是哪一行、哪份权重及哪种运行条件。
- **再定位差异。** 按[差距排查](trust-traps.md)找到一个能解释观察的候选原因。写下支持证据、反对证据、哪条证据会推翻当前解释。用一次有针对性的复跑核设计，例如锁定同一真实样本、配置和指标，比较评测入口原始权重和 EMA 路径。依据项目批准范围决定是否执行。
- **按证据解释波动。** 固定权重的评测重复、重训 seed、数据抽样和评测样本变化分别记录。保留每次实际读数。比较规则用已确认的协议、实际重复结果和误差依据。缺少可比条件或足够观测时，记录当前未知和影响。
- **决定何时结束。** 已能回答目标时进入交付；还有能改变判断的检查且在批准范围内时回 Step 3。需要改协议、关键条件或预算时回 Step 2。缺资源或重复检查没有新信息时，保留部分结果和下一项待核事项。

将参考值、实测值、条件对照、相关运行与各项解释写入 `alignment.md`。查看[完整填写示例](alignment-template.md#完整填写示例--edge-vision-的评测条件核对)核对如何保留原判断和新增证据，再把逐目标结论和适用范围同步到人读报告及机读记录。

### 差距排查示例 · 样本一致，权重变体不同

1. **写观察。** `eval-attempt-01` 正常结束，实测 77.6%，论文参考 78.4%。对照实际参与统计的 500 个 ID、标签和聚合路径，当前没有发现样本覆盖差异。
2. **写待检验的原因。** 日志指出加载了 raw 参数。论文 §4.2 指定 EMA。回查 r1 发布说明和 `tools/eval.py` 的加载分支，核这两个参数集的来源。明确下一次运行要验证的是：在其他条件固定时，选择该版本的 EMA 会不会消除观察到的差距。
3. **说明变更并复跑。** 向用户说明切换的是权重变体，给出实际出处和预计开销，回 Step 2 确认。获准后把 EMA 覆盖配置另存到 `runs/eval-attempt-02/config/`，依仓库支持的参数写新 `command.sh`。使用同一代码版本、环境、500 个样本、预处理与指标，单独保存新会话、日志和退出码。
4. **记录什么改变了判断。** `eval-attempt-02` 的日志确认加载 EMA，实际统计仍为 500 个样本，实测 392 个正确、Top-1 78.4%。该证据支持此权重和评测协议下的复现。若切换后差距仍在，就保留两次结果，按实际证据继续查实现差异，或在预算内据实交付未决项。两次运行都无法直接给出训练复现结论。

## Step 5 按需准备 reduced 迭代配置

1. **判断是否值得缩。** 后续要反复比较、目标配置又超出预算时，用稳定吞吐估计候选档耗时。核能否保留关键类别、场景、分组、模型、训练阶段和评测协议。只缩训练数据时查实际更新次数、warmup 和衰减时点，以及能否沿用同一验证集。目标配置已在预算内时直接沿用。
2. **交用户确认方案。** 给出拟保留和改变的条件、实测与估算成本、用哪一个已有或获准的对照，以及先跑哪档、什么结果会触发升档。关键条件保不住时说明还可以用小配置做哪些局部检查。
3. **按 Step 3 托管实跑。** 获准后保存子集身份、配置、命令、每档基线与同一对照的读数、配对差值和各档内的波动。每次尝试单独记录。两档有差异时同时回查实际数据覆盖和训练时点。

**中期决策真正需要的证据是：同一个改动相对同一个基线的收益，会不会随着规模变小、消失或反向？**

| 实际结果 | 怎样交付 |
| --- | --- |
| 各档内方向稳定，两档方向反向 | 标明同类候选对规模敏感。用已验证的低成本配置做局部诊断，取舍升到更合适的档，按需要复查此前仅凭低成本结果被淘汰的候选 |
| 只有一档，或较大档没有同一对照 | 交付可复跑的基线检查、实测成本和当前覆盖，跨规模收益记为未知 |
| 关键分组或训练阶段缺失 | 指出缺失条件与受影响的研究问题，说明补样本、延长必要阶段或升档的具体触发点 |

Reduced 具体配置与记录见 [Reduced 配置参考](reduced-setting.md)，适用范围和升档条件按本步执行。有希望或有争议的方法结果按批准的研究方案回目标条件验证。

## Step 6 交付可比较的基准

对照 `spec.md` 逐项目标交付，确认人读报告和机读记录引用同一版本、命令与证据。

- 给用户说明实际跑出了什么、参考是否可比、仍有哪些未决事项。核工作区与变更，并在报告中记分支、实际提交和合并状态。
- 需要清理代码时，给 `code-idea-prepare` 可复跑的改前对照、必须保持的条件、实际指标或行为证据、需要补回归的未覆盖范围。无需清理时记录理由，交 `code-reading` 实际环境、源码、关键配置和运行入口。
- 给后续方法实验提供实际基线起点、权重身份、训练与评测命令、数据划分和指标定义、实测读数与随机性记录。交付了 reduced 时，同时注明其适用范围和升档条件。保留所有运行尝试，按实际位置引用大文件。

用下面的核对表逐目标确认报告可用于后续比较。只有局部结果时，也交付已经确认的证据，注明接手阶段与下一步。

| 要能查到什么 | 从哪里核对 |
| --- | --- |
| 比较对象、参考结果与协议 | `spec.md` 与 `alignment.md` 的目标 ID、协议版本、参考行、资产配置、指标及单位 |
| 可复跑的当前基准 | `report.md` 与 `reproduction.json` 引用 run，回查 `command.sh`、`meta.json`、代码及 diff、实际配置、数据和 checkpoint 来源 |
| 实测范围与差距 | 按实际运行记录日志、退出码、读数和聚合范围。写明相对参考的结论与当前限制 |
| 供 prepare 做改前和改后对照的条件 | 指定要重跑的命令及版本、须保持的数据和权重、要比较的实际指标、逐样本覆盖或其他行为，以及未覆盖的回归项 |
| 未决项与升档条件 | 核每个获准目标都有结果或具体缺项。写到接手人知道所需资源、下一步证据和可复用部分 |

## 贯穿示例 · 从 17 样本试跑到复现标定

1. **从 setup 证据开工。** 根据 E02 的 C03 及待核目标汇报：17 个样本的路径已跑，环境、权重和完整验证数据可复用。准备查 `configs/eval.yaml` 和正式参考行。
2. **锁定要比较的结果。** `alignment.md` 的 EVAL-01 对应论文 v2 表 2 的 Vision-S 行。用户确认跑 500 个验证样本、按论文 Top-1 口径核指标、确认本轮投入和比较条件。所有运行引用该目标版本。
3. **从实际命令得到可追查的结果。** `eval-attempt-01` 用 Step 3 的 `command.sh` 通过 tmux 实跑。`meta.json`、退出码、`metrics.json` 与 500 个 ID 对照后，发现加载的权重变体不符。按 Step 4 回审后，`eval-attempt-02` 使用已核对的 EMA 参数复跑，保留实际命令、有效配置、日志和输出。完整评测结论引用第二次运行，首次结果保留供排查。
4. **对 reduced 保留局部范围。** 后续需要反复训练时，按实测成本提出配置。已有的同一消融在 30% 训练数据上相对基线下降 1.1 个百分点，在 60% 时上升 0.7 个百分点，两档内重复分别支持各自方向。报告记为规模敏感。30% 档用于基线复跑和局部诊断，同类改动的取舍升档，正式收益回目标条件验证。
5. **给 prepare 一个明确的改前对照。** 把 `eval-attempt-02` 的代码版本、命令、EMA 权重、数据清单和指标口径交给代码整理。清理后复跑同一命令，核 500 个 ID 的统计覆盖和 Top-1。完整训练若尚未核验，交接时单列训练证据的缺口。
