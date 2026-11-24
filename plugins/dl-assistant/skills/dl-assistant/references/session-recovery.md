# 恢复研究与执行上下文

本文件说明怎样在新会话或换机器后，用已有产物找回当前研究轮次、获批任务、实际运行和下一步。先用只读操作核对现场，再按已确认的范围继续。

## 1. 定位研究轮次和获批任务

1. **确认项目根和实际代码。** 从用户指定的仓库、轮次或产物开始。换机器时分别记下当前副本和原运行所在的机器与工作目录。核当前 Git commit 及已有改动。研究代码可沿同一个 `main` 推进多个轮次，轮次身份按项目记录核对。

   ```bash
   hostname
   git rev-parse --show-toplevel
   git status --short --branch
   git log -1 --oneline
   git diff --stat
   git diff --cached --stat
   ```

2. **定位本次讨论的轮次。** 用户点名了轮次、执行批次或决定时，从该记录所在轮次开始。其余情况先读 `docs/research/research-rounds.json`，按[轮次登记说明](research-rounds.md)识别候选轮次，再用已有交接、相关决定和实际任务核实。若索引暂缺，可按下面的只读命令找已有产物。登记顺序和文件修改时间可用于定位。若两个候选有不同的待做工作且现有证据不足以确认，报告具体差别后请用户明确本次要继续哪项。

   ```bash
   rg --files docs/research docs/idea-find \
       -g 'research-rounds.json' -g 'research-plan.md' -g 'next-step-decision.md' \
       -g 'execution-conclusion.json' -g 'spec.json'
   ```

3. **核本次允许做什么。** 打开本轮 `research-spec.md`、`research-plan.md` 和实际批准记录。逐项核方案修订、任务 slug、比较条件、资源和停止点。首轮批准来自 `docs/idea-find/` 中对应草案及 `spec.json` 的决定。已建的后续轮从索引的 `approval_ref` 查来源决定，再核当前 plan。遇到同轮补证，以该任务实际绑定的 plan 修订和决定为准。只获准复查已有材料时，继续读、核或复算已有证据。需重新运行或采新读数时，核是否有对应任务及批准。
4. **对照执行、证据和决定。** 用下表找本次续做所需的最少材料，核当前代码与获批设计的对应关系。

| 要确认什么 | 先读哪些记录 |
| --- | --- |
| 本轮问题、预测和当前证据 | `research-spec.md`、`claims.json`、`execution-conclusion.md` 和 `execution-conclusion.json` |
| 哪些批次已交回，哪些运行仍在继续 | `experiments/index.json` 的批次和实验条目，实验及 run 的 `meta.json`。从 `report.md` 回查实际条件和原始读数 |
| 哪一份结果做过独立核查 | 台账或结论引用的 `executions/<批次-slug>/execution-result-review.md`，核其实际覆盖的实验、run 和命题 |
| 最近相关的决定允许继续到哪里 | 本轮 `decisions/<决定-slug>/next-step-decision.md` 或索引引用的上一轮决定，再核实际 plan 修订、任务、预算及停止点 |
| 真实实现、环境和基线 | 从 `claim-code-map.md`、实际命令和发生过的运行核当前入口、配置、代码、数据和权重。再按需从 `docs/research/PROJECT_CONTEXT.md` 找 setup、复现、清理和调研资料 |

| 发现什么 | 怎样判断下一步 |
| --- | --- |
| 正在续做 v2，最新日志属于 v1 | 用台账和 run 核日志绑定的轮次、设计及实际 commit。v1 观察留在 v1，v2 只执行自身已批准的任务 |
| 同一轮 plan 有多个修订，或用户只批准了准备 | 对照实际决定、任务及获批修订。按已明确批准的部分继续。正式实验及预算仍待决定时，汇报所缺的确认 |
| 换机后当前副本与原运行不同 | 分别记机器、目录、commit、配置和环境。复用结果前核差异是否影响比较。没有原材料时，说明可核范围及受影响的判断 |
| 报告、核查、论点记录与原始读数不一致 | 核各自引用的实验、run、指标和范围。能复算时保留原条件、单位和方法，只更新已获证据支持的判断 |

## 2. 在实际运行机器核长任务

从当前批次的台账和 run 元记录取实验与尝试身份、原机器、工作目录、tmux 会话或调度器作业 ID、实际日志和退出状态位置。先查原任务，核实后再决定续做、重试或复跑。

下面以 `edge-vision` 的计时核查为例。在原执行机器上操作，变量换成实际 run 记录中的值。

```bash
session=idea-edge-timing-01
log_dir=/srv/research/edge-vision/docs/research/v1-edge-vision/experiments/exp-baseline-timing/runs/attempt-01
log_path="$log_dir/$session.log"
exit_code_path="$log_dir/$session.EXIT_CODE"

if tmux has-session -t "=$session" 2>/dev/null; then
    printf '%s\n' "找到原会话"
else
    printf '%s\n' "当前未查到原会话，继续核日志和退出记录"
fi
test ! -f "$log_path" || tail -n 30 "$log_path"
test ! -f "$exit_code_path" || cat "$exit_code_path"
```

集群任务用原作业 ID 查调度器的当前状态、历史、退出信息和实际输出。详见[长任务托管与恢复](long-run-ops.md)。

| 当前发现 | 怎样处理 |
| --- | --- |
| 原会话或作业仍在 | 核确实是同一次尝试，读最新日志、输出及实际阶段，继续监测原任务 |
| 会话已消失，退出码也缺失 | 查原机器进程、调度历史、最后日志和已有产物。仍无法确定时记「状态待核」，等核实身份和进展后再决定是否启动新尝试 |
| 退出码为 0 或调度显示成功 | 核实际产物、预期数量及完整性，再回填为完成。数据和测量的有效性按实际比较另核 |
| 确认失败或中止 | 记录退出原因和已有结果。获批范围允许重试或恢复时，新建尝试，引用旧尝试和实际 checkpoint，并记录验证过的恢复范围 |
| 无法访问原机器或产物 | 说明缺少的机器、作业或文件及其影响。先做可以独立完成的核查，并标明哪些判断等原记录回来才能做 |

把核实后的状态和出处写回原实验、台账或报告。仍在运行、结束但测量待核、只有部分结果这几种情况分别注明。

## 3. 向用户汇报四项

| 汇报内容 | 怎样写 |
| --- | --- |
| **当前问题** | 写本轮要区分什么，以及来自文献或实际观察的依据 |
| **实际进展与证据** | 写这次核到哪些任务完成、继续运行或受阻，数据能用到哪里，命题的证据判断及仍未区分的解释 |
| **实际代码、配置和基准** | 给实际 commit、关联的 diff、关键代码位置、配置及原基准 run。跨机器或与原记录有差异时，说明影响 |
| **已批准的下一步与停止点** | 写这次继续哪个任务、批准修订及范围、预计做到哪里汇报、还有哪些待确认 |

例如，续做虚构项目 `v1-edge-vision` 时，发现 `baseline-timing` 已到停止点，而正式比较仍待确认。用户汇报可写成：

> **当前问题**　先核目标设备能否取得稳定计时，以及采集轨迹时读数会怎样变化。
>
> **实际进展与证据**　准备任务已完成。关闭轨迹时三次读数为 12.5、12.6、12.7 ms，开启时是 15.3、15.4、15.6 ms。在所测设置下，采集轨迹会影响计时。C1 和 C2 的正式机制对照仍待取证。
>
> **实际代码、配置和基准**　读数来自 `exp-baseline-timing/runs/attempt-01/`。按它的元记录核使用的 commit、设备、命令和生效配置。
>
> **已批准的下一步与停止点**　`approve-baseline-timing` 只批准了准备核查，已到停止点。建议正式计时关闭轨迹并另采机制轨迹。四组 `configuration-comparison` 及预算待确认。

## 4. 查阅和更新项目背景

需要长期问题、基线和上游资料时，读 `docs/research/PROJECT_CONTEXT.md`。首次准备仓库时由 `code-idea-prepare` 按[项目背景模板](project-context-template.md)初始化。跳过 prepare 时由 execution 开立首轮时按已核事实补建。后续在长期研究问题、已确认目标、采用的基线或关键资料位置变化时更新。

本轮进度、批准、证据和未决工作分别从方案、决定、台账与结论恢复。
