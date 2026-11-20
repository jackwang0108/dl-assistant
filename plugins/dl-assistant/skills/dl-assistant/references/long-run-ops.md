# 长任务托管与恢复（跨 skill 共享）

> 中期 skill（`code-project-setup` / `code-paper-reproduction` / `code-idea-prepare` / `code-idea-execution` / `code-paper-experiment`）都会遇到长任务：
> 几十 GB 下载、几小时训练、大 test set eval。这份讲**通用机制**——怎么让长任务在会话结束后继续运行、
> 中断后怎么扫产物恢复。各 skill 的场景差异（session 前缀、长任务类型、恢复重点）见末尾「场景速查」。

## 核心模型：任务 detach 存活，agent 靠文件恢复

预计超过 5 分钟或中断后重跑代价高的命令，应使用可独立于当前会话运行的任务管理方式，例如 tmux 或集群调度器。会话内后台工具是否能在会话关闭后继续运行，取决于宿主实现；未经确认时，不用于长任务。

tmux 后台任务通常能在 SSH 或 agent 会话断开后继续运行，但节点重启、进程被终止或服务器的会话清理策略仍会中断任务。它不保证任务成功。

通过日志、退出码文件与实际结果共同核实状态，不依赖终端画面。状态索引有助于恢复，但需要与进程和结果核对。

## 启动：detached 跑长任务（agent 永不 attach）

**首选封装脚本** `dl-assistant/scripts/run-long.sh`（模板 + mkdir + sentinel 已固化，少记少错）：

```bash
bash <skills根>/dl-assistant/scripts/run-long.sh <前缀>-<task> <logdir> '<cmd>'
# 产物: <logdir>/<session名>.log + <logdir>/<session名>.EXIT_CODE
# 每个attempt使用新session名；脚本拒绝复用已有日志、退出码或启动记录
# 命令在调用者当前目录执行，要换目录把 cd 写进 <cmd>
```

脚本保留 `<logdir>/.<session名>.launch/` 中的启动命令，以独占目录避免并发启动覆盖同一记录；该目录不是可自动清除的锁。即使启动失败也保留现场，核查后为新的尝试分配新名称。日志和退出码仍使用上面的扁平路径，退出码通过临时文件原子写入。命令退出0只表示进程结束，不能代替产物检查。

命令在 Bash 中执行；不要将凭据写进命令，使用项目已有的凭据配置。session名只用字母、数字、下划线和连字符。脚本不保存模型状态，也不推断训练恢复是否正确。使用其他调度器时同样要保留独立尝试身份、原日志和真实退出状态，不复用输出路径。

## 状态文件契约（核查依据）

| 文件 | 含义 |
| --- | --- |
| `<task>.log` | 任务进展（stdout + stderr）|
| `<task>.EXIT_CODE` | 终态 sentinel：**不存在 = 状态未知**（可能仍在运行，也可能已被强制终止）；**存在 = 已结束**，内容 `0` 成功 / 非 `0` 失败 |
| 保存的产物（数据目录 / checkpoint / metric 文件） | 真实结果，验证/恢复要用 |

`EXIT_CODE` 缺失时，继续检查 tmux session、相关进程与日志更新时间；退出码为 0 后仍需验证预期结果完整。

## 查状态：三项只读状态检查（任何一轮对话都能跑）

```bash
tmux has-session -t <前缀>-<task> 2>/dev/null && echo RUNNING || echo GONE   # session 还活着吗
tail -n 30 <logdir>/<task>.log                                                  # 看进展（直接读文件）
cat <logdir>/<task>.EXIT_CODE 2>/dev/null                                       # 退出码（无输出时需继续核查进程与日志）
```

多个并行任务时，`tmux ls 2>/dev/null | grep '^<前缀>-'` 看全部。

**禁止**：不 `tmux attach`（agent 没交互终端，会卡住）；不 `tmux capture-pane` 抓屏当数据源
（脆弱、受状态栏 / 颜色码干扰）——只读 `.log` 文件。

## 中断恢复：核查记录、进程与结果

长任务常中途断：网络断、去手动下数据、换机器、会话超时、集群调度 kill。**重连后不重头来，
扫真实产物定位到哪一步**——这正是"Report 兼恢复入口"的保存的。通用顺序：

1. **读上次的 Report**（若已起草）——它的机读交接区记了 env 名、哪些任务已验、数据 / checkpoint 路径，
   是恢复的总纲。没有就从下面的真实状态扫起。

2. **扫任务状态**：
   ```bash
   tmux ls 2>/dev/null | grep '^<前缀>-'        # 哪些还在后台跑
   for code in <logdir>/*.EXIT_CODE; do          # 只列已保存的退出记录；无匹配时不推断状态
     [ -f "$code" ] && cat "$code"
   done
   # 再按台账逐项核对每个attempt的session、日志、进程与实际产物，含没有退出记录的项
   ```

3. **识别任务意外终止**（长任务最常见的中断）：某任务 tmux session 已 GONE 但 `EXIT_CODE` 不存在
   = 状态未知；可能被终止，也可能任务另有进程。先核节点、进程/调度器和日志，不能仅凭session消失断定失败原因。未完整结束的数据只按实际范围解释，不当作完整结果。

4. **定位断点 + 只补未完成的**：对照本 skill 的阶段（setup 的三层验证 / reproduction 的逐目标验证 /
   execution 的实验进度），**只补未完成的，不重跑已验证的**。

5. **半截任务的处理**：
   - **下载半截**：`aria2c` / `huggingface-cli` 自带断点续传，重发同一命令即续；裸 `wget` 用 `wget -c`。
   - **训练半截**：核checkpoint身份、完整性及模型/优化器/调度器/随机状态恢复范围，按批准设计选择续跑或重跑。每次另建attempt并记来源，不覆盖旧结果。
   - **大 eval 半截**：很多框架支持已算样本缓存 / 分片续算，优先用；没有就重跑（eval 通常比训练便宜）。
   - 续 / 重跑后**验证完整性**（大小 / checksum / metric 落在预期量级 / loader 能读）再算就绪。

> 纪律：恢复永远靠「扫保存的文件 + 读 Report + 读 sentinel」，**状态文件必须与日志和实际结果一致**。

## 可选增强：Monitor 盯 log（仅会话在场时）

会话开着、想任务跑完或出错时实时弹通知，可起 Monitor 盯 log。**filter 必须同时覆盖成功与失败信号**——
否则任务崩了没有一行匹配，Monitor 永不触发，agent 静默空等一个永远不来的信号：

```bash
tail -F <logdir>/<task>.log \
  | grep -E -i 'done|complete|saved|finished|100%|traceback|error|failed|timeout|oom|out of memory|nan|killed|no space|exception'
```

`tail -F`（大写）survives 日志轮转 / 重建；正则覆盖进展里程碑 + 成功终态 + 崩溃 / 中止终态，三者齐全。

Monitor 是 **session-bound**：会话退出瞬间就被杀，`--resume` 不恢复。所以它是"此刻想实时弹通知"的
**临时便利，绝不是跨 session 基础设施**。跨 session 恢复永远靠三项只读状态检查。

> 可用性限制：需 Claude Code v2.1.98+；Bedrock / Vertex / Foundry 不可用；禁遥测
> （`DISABLE_TELEMETRY` / `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`）时不可用。命中就退回纯文件轮询，
> 不影响恢复。
>
> **平台注记**：Monitor 是 Claude Code 专属工具；其他宿主（如 Kimi Code）无 Monitor——等价物是**定时轮询**（cron / 手动三项只读状态检查）。会话内后台任务的存活范围取决于宿主，未经验证不能用于需要跨会话存活的长任务。主机制（tmux detach + sentinel + 三项只读状态检查）平台无关，不受影响。

## 磁盘容量检查

下载 / 训练前**必估磁盘**：

```bash
df -h <target_partition>     # 目标盘剩多少
# 对照：数据集声称大小 + 解压膨胀（tar.gz 解压常翻倍）/ checkpoint 数 × 单个大小
```

- 不够先清理或换盘再跑，别下 / 训到一半 `no space left` 把任务和产出都搞坏。
- 解压型数据（ImageNet 这类）记得**算上解压后体积**，常是压缩包的 1.5-2 倍。
- 训练 checkpoint 记得设保留上限（`max_keep_ckpts` 之类，只留 best + last），别每个 epoch 都留。
- **磁盘写满是致命故障**：发现将满**停下报告用户**，不自行删可能有用的东西。

---

## 场景速查（各 skill 的差异）

| skill | session 前缀 | 长任务典型类型 | 恢复重点（扫什么） | 半截怎么续 |
| --- | --- | --- | --- | --- |
| **code-project-setup** | `setup-dl-<slug>` | 大数据 / 权重下载、偏长 smoke run | conda env 在不在、数据 / checkpoint 保存的没、上次 Report 写到哪 | 下载断点续传（aria2c / hf-cli） |
| **code-paper-reproduction** | `repro-<repo>-<run>` | 按明确目标批准的评测、训练或行为验证 | 每次run的退出状态/日志/结果、目标和协议版本、实际代码/config/资产 | 先核现有任务与完整性；按实际实现支持的方式恢复并保留新run/attempt |
| **code-idea-prepare** | `cip-<repo>-` | 按实际变更需要的行为/接口/结果验证，不默认完整训练 | 改前/改后实际状态、变更—验证对应记录、运行日志/退出与证据范围 | 核任务状态与条件；只处理本次可识别改动，不自动整体重置到旧tag |
| **code-idea-execution** | `ex-<slug>-<exp>` | 几小时长训练（多 seed） | 实验目录的 train.log / EXIT_CODE、各 seed checkpoint、metrics.json + `experiments/index.json` 台账 | 从 checkpoint `--resume` 续训 |
| **code-paper-experiment** | `cpe-<exp_id>-` | full-scale 多 seed 训练（贵、长） | 各 exp 的 `meta.json` 状态、包级 `results.json` 增量、runs/seed-* 的 log + checkpoint | 按续跑协议：已完成不重跑、中断的按重连规则恢复、恢复不了重跑该 seed 并记 deviation |

> 各 skill 在自己 SKILL 里只需声明：本 skill 的 session 前缀、长任务类型、恢复时扫什么——
> 通用机制（detach / sentinel / 三项只读状态检查 / 扫产物恢复 / Monitor / 磁盘容量检查）全看本份。
