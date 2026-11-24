# 论点、代码与测量映射模板

本文件提供可复制的 `claim-code-map.md` 和完整示例，用于记录获准取证项对应的实现、对照、读数和用户审阅。调查时按[映射指引](claim-code-map-guide.md)找代码和实际证据，在[运行手册 Step 3](workflow.md#step-3-准备实现并审阅开跑条件)用映射及实际 diff 交审。

## 可复制模板

````markdown
# {研究版本} · 论点、代码与测量映射

- 研究和批准 | {研究说明、取证方案、论点记录、获批版本和决定位置}
- 代码与配置 | {真实仓库、分支、commit、实际 diff 和命令来源}
- 范围 | {本轮要做的任务、当前实现/试跑状态、已核的继承记录}

## 共用入口和测量

| 路径 ID | 怎么进入及生效条件 | 实际源码位置、输入和输出 | 原始记录及已核范围 |
| --- | --- | --- | --- |
| {PATH-01} | {命令、配置和覆盖方式} | {commit、文件行或符号、调用和结果} | {内容、run、路径、单位与聚合，拟接入或实际核查} |

## {问题／假设／子论点 ID，或准备任务 ID}

- **要回答什么** | {用自己的话解释命题或未知，对齐研究说明及论点记录}
- **代码和机制** | {引用共用路径，给当前改动与实际 diff 位置，说明输入、处理、输出和调用关系}
- **对照与验证逻辑** | {各组真正改变什么及保持什么，读数来源和预期，什么结果能区分哪些解释}
- **实际检查及开放前提** | {试跑、源码证据、有效范围，尚待核的条件与不符合时的解释限度}
- **关联取证与证据** | {plan 任务、已登记实验或 run，尚未运行时写待登记/待运行}

## 顺序、依赖和审阅

- 运行安排 | {前置、可并行、需要先补证或重新确认的任务}
- 用户审阅 | {实际展示的代码和配置、版本或 diff、用户答复、批准范围与待决项}
- 开跑前核查 | {实施、对照、版本、已核条件与未解决项的证据位置及行动影响}
```

## 完整填写示例 · edge-vision 的 baseline-timing 和 C1

沿用[执行手册的虚构案例](workflow.md#示例--edge-vision-的计时与轨迹)。baseline-timing 已按 approve-baseline-timing 完成。示例假定用户后来批准准备 configuration-comparison 的实现和局部试跑，正式四组测量与隔离对照尚待开跑审阅。代码位置和配置名用于展示记录方式。

```markdown
# v1-edge-vision · 论点、代码与测量映射

- 研究和批准 | research-spec.md 的 Q2/H2，research-plan.md 的 baseline-timing/configuration-comparison，claims.json 的 C1。approve-baseline-timing 批准 baseline-timing。随后仅批准 configuration-comparison 实现与局部检查，正式开跑待确认。
- 代码与配置 | /srv/research/edge-vision，main。baseline-timing 在 c91b7e4 取得，configuration-comparison 审阅拟用 8d34a2f，关键差异为 c91b7e4..8d34a2f。
- 范围 | 本轮记录计时准备和 C1 的机制对照。其他命题可复用共用路径，其各自对照需单独说明。

## 共用入口和测量

| 路径 ID | 怎么进入及生效条件 | 实际源码位置、输入和输出 | 原始记录及已核范围 |
| --- | --- | --- | --- |
| PATH-01 配置 | 从实验的 scripts/run.sh 进入 tools/bench_latency.py。各组的 configs/ 和 CLI 覆盖决定裁剪、融合与轨迹采集 | tools/bench_latency.py:parse_args 与 resolve_config，输出最终生效配置 | baseline-timing 与 configuration-comparison 局部检查保存生效配置。已核 8d34a2f 下四组配置能进入对应分支 |
| PATH-02 算子选择与写回 | 从 PATH-01 进入运行时构建，按实际输入与配置决定算子。机制诊断记录实现 ID 和中间张量写回量 | runtime/dispatch.py:select_kernel 返回实际实现 ID。runtime/trace.py:collect_writeback 保存跟踪记录 | 局部试跑保存选择日志和轨迹。其他正式输入是否也选同一实现仍待核 |
| PATH-03 计时与汇总 | 原模型和比较组使用同一设备、输入及预热。正式延迟使用关闭轨迹采集的独立运行 | tools/bench_latency.py:measure_request 核开始与结束的同步位置，analysis/summarize_latency.py:read_timings 按请求汇总毫秒读数 | baseline-timing 的原始逐次读数和计时状态在 exp-baseline-timing 的 attempt-01。正式 configuration-comparison 读数待运行 |

## Q2／baseline-timing · 测量可行性

- **要回答什么** | 目标设备能否稳定取得单张请求延迟，轨迹采集是否会影响计时。
- **代码和机制** | 沿 PATH-01 和 PATH-03，用同一原模型和计时协议分别开关轨迹。PATH-02 检查能否实际取得实现 ID 和写回记录。
- **对照与验证逻辑** | 在相同输入、设备、批大小、预热和计时边界下，比较有无轨迹采集时的逐次延迟及轨迹可用性。
- **实际检查及开放前提** | approve-baseline-timing 的准备任务已做完。关闭轨迹时为 12.5、12.6、12.7 ms，开启时为 15.3、15.4、15.6 ms。该设置下采集会影响计时。正式延迟和机制轨迹拟分别采集，并核实际实现和输入能否对应。
- **关联取证与证据** | baseline-timing，exp-baseline-timing／attempt-01。C1 的正式取证待运行。

## Q2／H2／C1 · 固定实际算子后的写回量对照

- **要回答什么** | 在实际算子实现相同的条件下，改变写回量时，端到端延迟是否出现方案预期的变化。
- **代码和机制** | 关键 diff 在 tools/bench_latency.py:resolve_config 和 runtime/dispatch.py:select_kernel。沿 PATH-01 核对照配置，沿 PATH-02 核两组的实际算子身份和写回量，再从 PATH-03 取同口径的原始延迟。
- **对照与验证逻辑** | 比较实际选中同一算子、写回量不同的两组，固定设备、运行时、输入、批大小、预热和同步边界。实际实现一致、写回量发生预期变化且延迟有相应变化时，才按已批准的比较规则判断 C1。若算子和写回量一起变，该观察用于比较两组配置，机制归因待补隔离对照。
- **实际检查及开放前提** | configuration-comparison 局部试跑核了配置、分支与产物路径。正式输入的算子身份仍需逐组查，轨迹运行和计时运行也要核相同的配置与实现选择。找不到有效隔离对照时，带实际情况回审 C1 的取证范围。
- **关联取证与证据** | configuration-comparison 四组配置测量待开跑确认。C1 的隔离对照另列任务，当前无相关正式读数。

## 顺序、依赖和审阅

- 运行安排 | baseline-timing 已完成。先用实际 diff、配置及局部试跑审阅 configuration-comparison。获准后运行正式计时与轨迹采集；C1 隔离条件满足后再开展相应对照。
- 用户审阅 | 提议展示 c91b7e4..8d34a2f 的配置及分派改动，说明测量边界和各结果的解释范围。仅局部检查已批准。正式启动、具体投入和 C1 隔离对照待确认。
- 开跑前核查 | 复查各组生效配置与测量入口，确认命令绑定 8d34a2f，确认审批覆盖本次组别和预算。正式采集时保存实际算子及写回证据。
```
