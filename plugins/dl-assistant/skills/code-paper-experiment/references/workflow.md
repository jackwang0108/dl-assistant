# 执行论文实验与分批交接

路径相对项目根。批次目录选在 `docs/paper-experiments/<batch-id>/`。同一批的命令、日志及运行数据用实际位置引用。

## 1. 接收计划或恢复现场

1. 按[记录字段说明](records.md)读获批的 `plan-vN.md` 和 `plan-vN.json`，确认批次 ID、研究主张、比较条件、计划重复、预算、停止条件和覆盖任务。把获批计划作为固定副本保存。若资料只允许准备检查，按该任务的实际范围工作。
2. 先用已有 run-spec、报告、尝试记录和回包确定已交回什么。复用已有结果时核实际 commit、输入和测量条件，记录来源及可复用范围。核心现象、机制或贡献仍待研究时，交 iterate 明确取证。
3. 有计划缺项时说明具体影响。改变正式比较、分析规则或资源时，将受影响项和建议交审。实质改变计划后由 writing-paper 保存新计划版本和批次。工程绑定的获批修订保留原 run-spec 和实际运行引用。

## 2. 绑定执行并核启动条件

读实际入口、数据处理、统计逻辑和准备记录。从实际仓库核 `git rev-parse HEAD`、相关 diff 和生效配置。逐项写入 [run-spec](templates/run-spec-template.json)，记工作目录、命令、配置副本、设备、资产版本、批准和停止条件。执行前给用户实际配置、关键科学对照、依赖和投入；已有授权覆盖时沿用。需要先选配置的任务按计划用已确定的验证数据，并核下游依赖的配置已确认。

做适合操作的最小检查。训练核数据、更新、保存和评估路径；测量核采样及计时边界；纯分析核输入、统计入口和输出。确认实际前置结果可用后再运行依赖项。已有等价检查可引用。

## 3. 登记、运行和恢复

按[单实验报告](templates/exp-report-template.md)先写获批设计。每次运行记录 `attempt_id`、`replicate_id`、适用时的 seed、绑定的 run-spec 修订、命令、实际配置、开始及结束、日志和退出证据。实际启动失败或没跑的项目也记状态和原因。高成本或不确定时长的任务在实际机器用 tmux 或集群调度器托管。

使用 tmux 时，将 run-spec 中核对过的工作目录、环境和命令保存为本次尝试目录里的 `command.sh`，将下面的 `run_long`、`attempt_dir` 和 `session` 换成本次实际路径和会话名。集群用调度器提交同一命令，登记作业 ID、日志和实际退出状态。详见[共享长任务说明](../../dl-assistant/references/long-run-ops.md)。

```bash
run_long=/srv/skills/dl-assistant/scripts/run-long.sh
attempt_dir="$PWD/docs/paper-experiments/edge-vision-latency/experiments/exp-target-latency/runs/latency-attempt-01"
session=paper-latency-attempt-01
printf -v run_command 'bash %q' "$attempt_dir/command.sh"
bash "$run_long" "$session" "$attempt_dir" "$run_command"
```

启动后和重连时，分别用 `tmux has-session -t "=$session"`、`tail -n 30 "$attempt_dir/$session.log"` 和 `cat "$attempt_dir/$session.EXIT_CODE"` 核对会话、日志和退出记录。会话结束且退出记录缺失时，查进程和实际产物，证据不足就保留待核状态。

续做先找原作业、日志和退出状态。重试或从 checkpoint 恢复时新建尝试目录，引用原尝试并保留原重复身份。同一独立重复统计时只选一次有效尝试，按计划规则注明取舍。改变输入、数值精度、模型、数据划分或评估条件时记录影响和实际批准。W&B 的同步状态与执行结果分开，汇总引用确切 run 和必要的查询快照。

## 4. 复核、保存并交回写作

先回填实际条件和原始读数，再依原比较、重复及分析规则复算。记录失配、缺组、异常和有效范围。保留所有尝试，逐项区分执行状态、测量有效性和证据所能说明的内容。对会改变论文判断的结果复核实际输入、纳入规则、统计代码和来源。

每次回包放入新的 `handoffs/rev-<N>/`。复制获批 plan 和本次使用的 run-spec 快照，保留 `paper-results.json` 中上一回包的摘要引用。相同实验、尝试和读数沿用原 ID。修订包含本批全部计划项。更正已交付值时记录原值、理由及影响；新增尝试或补齐数据以原始证据为准。

优先随包保存小型原始读数、报告和复算材料。大文件可给机器、固定路径和版本或摘要，并注明可访问性。机器检查覆盖 JSON 身份、任务对账、引用及声明为简单可复算的均值或配对差。按实际路径运行：

```bash
bash "$skill_dir/scripts/check-run-artifacts.sh" --plan "$plan_path" --spec "$spec_path"
bash "$skill_dir/scripts/check-run-artifacts.sh" --pkgdir "$handoff_dir"
bash "$skill_dir/scripts/check-run-artifacts.sh" --pkgdir "$handoff_dir" --previous "$previous_dir"
```

退出 0 表示声明的本地记录检查通过，退出 1 表示内容或引用不一致，退出 2 表示参数用法错误。若退出 3，按 `UNCHECKED` 核跨机不可取得的 W&B 恢复目录，保留本地实验结果，并对各项证据说明可用范围。外部证据和非内置分析方法要按实际来源另外核查。标明任务是否完成、证据支持范围、欠缺项和受影响的写作位置，再把回包路径交 writing-paper。关键科学判断变化时另附具体条件、反证或证据缺口交 iterate。
