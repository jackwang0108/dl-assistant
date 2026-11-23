# 长任务托管与恢复（跨 skill 共享）

> 中期 skill（`code-project-setup` / `code-paper-reproduction` / `code-idea-prepare` / `code-idea-execution` / `code-paper-experiment`）都会遇到长任务：
> 几十 GB 下载、几小时训练、大 test set eval。这份讲**通用机制**——怎么让长任务活过 Claude 会话、
> 中断后怎么扫产物恢复。各 skill 的场景差异（session 前缀、长任务类型、恢复重点）见末尾「场景速查」。

## 核心模型：任务 detach 存活，agent 靠文件恢复

长任务**不能**用 `Bash(run_in_background)` —— 那是 Claude Code 的子进程，**会话一退就被杀，`--resume` 也不恢复**。
它只适合会话内分钟级的事（import、smoke、短 reduced run、sanity 诊断）。

> **亮线规则（不需要判断）**：预计 >5 分钟 / 会话断开重跑代价高的命令 → 一律 tmux detach；**拿不准时长就当长任务**。禁止前台干等。

几十 GB 下载、长训练、大 eval 用 **tmux 命令式 detach**：进程的父是 tmux server（systemd 级存活），
**脱离 Claude**，SSH 断开 / 会话退出都照跑。agent 不在长任务的临界路径上。

**真相源是磁盘文件**（log + sentinel + 落地的产物），不是 tmux 屏幕——判断"成没成"靠读文件，
不靠在场、不靠抓屏。这与 `dl-assistant`「产物即真相源、扫产物不靠状态文件」一脉相承。

## 启动：detached 跑长任务（agent 永不 attach）

**首选封装脚本** `dl-assistant/scripts/run-long.sh`（模板 + mkdir + sentinel 已固化，少记少错）：

```bash
bash <skills根>/dl-assistant/scripts/run-long.sh <前缀>-<task> <logdir> '<cmd>'
# 产物: <logdir>/<session名>.log + <logdir>/<session名>.EXIT_CODE
# 脚本会输出查看会话、日志和退出码的命令；命令在调用者当前目录执行，要换目录把 cd 写进 <cmd>
```

手写模板（理解机制 / 脚本不在手边时；`<task>` = 任务 slug，`<cmd>` = 要跑的命令，`<logdir>` = log 落地目录）：

```bash
tmux new-session -d -s <前缀>-<task> \
  'cd <repo> && mkdir -p <logdir> && ( <cmd> ) > <logdir>/<task>.log 2>&1; echo $? > <logdir>/<task>.EXIT_CODE'
```

- `-d` = 命令式 detach：会话一建出来就脱离，agent **不 attach**（没交互终端，attach 会卡住）。
- `mkdir -p` 先建 log 目录——不预建的话重定向会静默失败。
- stdout + stderr 落 `<task>.log`；退出码落 `<task>.EXIT_CODE` sentinel。
- session 名带 **skill 前缀 + task slug**（见场景速查），多个长任务不撞名、跨 skill 区分。
- 换别的 detach 工具（nohup / setsid / sbatch）同理，核心三件事不变：**进程脱离 Claude + 输出落文件 + 退出码落 sentinel**。

> 大文件下载优先 `aria2c -x 16`（多连接 + 断点续传），比 `wget` 稳；HF 权重用 `huggingface-cli download`
> （自带断点续传 + 配 `HF_ENDPOINT` 镜像）。

## 状态文件契约（真相源）

| 文件 | 含义 |
| --- | --- |
| `<task>.log` | 任务进展（stdout + stderr）|
| `<task>.EXIT_CODE` | 终态 sentinel：**不存在 = 还在跑**（或被强杀）；**存在 = 已结束**，内容 `0` 成功 / 非 `0` 失败 |
| 落地的产物（数据目录 / checkpoint / metric 文件） | 真实结果，验证/恢复要用 |

一句话：**`EXIT_CODE` 文件在不在 = 任务还在不在跑。**

## 查看会话、日志和退出码（任何一轮对话均可执行）

```bash
tmux has-session -t <前缀>-<task> 2>/dev/null && echo RUNNING || echo GONE   # session 还活着吗
tail -n 30 <logdir>/<task>.log                                                  # 看进展（直接读文件）
cat <logdir>/<task>.EXIT_CODE 2>/dev/null                                       # 终态（无输出 = 尚未结束）
```

多个并行任务时，`tmux ls 2>/dev/null | grep '^<前缀>-'` 看全部。

**禁止**：不 `tmux attach`（agent 没交互终端，会卡住）；不 `tmux capture-pane` 抓屏当数据源
（脆弱、受状态栏 / 颜色码干扰）——只读 `.log` 文件。

## 中断恢复：扫产物自恢复（不靠状态文件）

长任务常中途断：网络断、去手动下数据、换机器、会话超时、集群调度 kill。**重连后不重头来，
扫真实产物定位到哪一步**——这正是"Report 兼恢复入口"的落地。通用顺序：

1. **读上次的 Report**（若已起草）——它的机读交接区记了 env 名、哪些任务已验、数据 / checkpoint 路径，
   是恢复的总纲。没有就从下面的真实状态扫起。

2. **扫任务状态**：
   ```bash
   tmux ls 2>/dev/null | grep '^<前缀>-'        # 哪些还在后台跑
   for d in <logdir>/*/; do                       # 逐任务看 sentinel + log 末尾
     echo "== $d =="; cat "$d/EXIT_CODE" 2>/dev/null || echo "未结束"; tail -n 5 "$d"/*.log
   done
   ```

3. **判别异常死亡**（长任务最常见的中断）：某任务 tmux session 已 GONE 但 `EXIT_CODE` 不存在
   = 被 kill / OOM-killer / 节点重启杀掉，sentinel 没来得及写。**别当"还在跑"干等**——
   读它 log 末尾确认任务中断的原因（OOM？NCCL？被抢占？no space？），按下一步续跑或改配置重跑，
   **不把半截结果当数据**。

4. **定位断点 + 只补未完成的**：对照本 skill 的阶段（setup 的三层验证 / reproduction 的分流 /
   execution 的实验进度），**只补未完成的，不重跑已验证的**。

5. **半截任务的处理**：
   - **下载半截**：`aria2c` / `huggingface-cli` 自带断点续传，重发同一命令即续；裸 `wget` 用 `wget -c`。
   - **训练半截**：从最近 checkpoint + 框架的 `--resume` / `resume_from` 续跑（参数看 baseline repo 训练脚本），别从头重训。
   - **大 eval 半截**：很多框架支持已算样本缓存 / 分片续算，优先用；没有就重跑（eval 通常比训练便宜）。
   - 续 / 重跑后**验证完整性**（大小 / checksum / metric 落在预期量级 / loader 能读）再算就绪。

> 纪律：恢复永远靠「扫落地文件 + 读 Report + 读 sentinel」，**不引入 skill 专用状态文件**。

## 可选增强：Monitor 盯 log（仅会话在场时）

会话开着、想任务跑完或出错时实时弹通知，可起 Monitor 盯 log。**filter 必须同时覆盖成功与失败信号**——
否则任务崩了没有一行匹配，Monitor 永不触发，agent 静默空等一个永远不来的信号：

```bash
tail -F <logdir>/<task>.log \
  | grep -E -i 'done|complete|saved|finished|100%|traceback|error|failed|timeout|oom|out of memory|nan|killed|no space|exception'
```

`tail -F`（大写）survives 日志轮转 / 重建；正则覆盖进展里程碑 + 成功终态 + 崩溃 / 中止终态，三者齐全。

Monitor 是 **session-bound**：会话退出瞬间就被杀，`--resume` 不恢复。所以它是"此刻想实时弹通知"的
**临时便利，绝不是跨 session 基础设施**。跨会话恢复时，仍通过会话列表、日志和退出码核对状态。

> 可用性限制：需 Claude Code v2.1.98+；Bedrock / Vertex / Foundry 不可用；禁遥测
> （`DISABLE_TELEMETRY` / `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`）时不可用。命中就退回纯文件轮询，
> 不影响恢复。
>
> **平台注记**：Monitor 是 Claude Code 专属工具；其他宿主（如 Kimi Code）无 Monitor——等价物是**定时轮询**（cron / 手动查看会话、日志和退出码）。`run_in_background` 类会话内后台任务在各宿主都是 session-bound，同样不能用于长任务。主机制（tmux 后台会话、退出码文件和上述状态检查）平台无关，不受影响。

## 估算和管理长任务的磁盘空间

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
| **code-project-setup** | `setup-dl-<slug>` | 大数据 / 权重下载、偏长 smoke run | conda env 在不在、数据 / checkpoint 落地没、上次 Report 写到哪 | 下载断点续传（aria2c / hf-cli） |
| **code-paper-reproduction** | `repro-<repo>-<run>` | 大 test set eval、缩规模 full 训练、short-schedule（常多并行） | 各 run 的 sentinel + log、eval / 训练双轨数字、检查点的来源与恢复记录 | 训练从 checkpoint resume；eval 分片续算 |
| **code-idea-prepare** | `cip-<repo>-` | 分批清理/优化后的 smoke、完整性能验证（full / reduced 多 seed） | `cleanup.json` + report 任务台账、里程碑 tag（`code-pruned` / `quality-improved`）、性能验证 log | 失败回退循环（二分定位 → 回滚该批 → 重验），底线全退 `baseline-reproduced` |
| **code-idea-execution** | `ex-<slug>-<exp>` | 几小时长训练（多 seed） | 实验目录的 train.log / EXIT_CODE、各 seed checkpoint、metrics.json + `experiments/index.json` 台账 | 从 checkpoint `--resume` 续训 |
| **code-paper-experiment** | `cpe-<exp_id>-` | full-scale 多 seed 训练（贵、长） | 各 exp 的 `meta.json` 状态、包级 `results.json` 增量、runs/seed-* 的 log + checkpoint | 按续跑协议：已完成不重跑、中断的按重连规则恢复、恢复不了重跑该 seed 并记 deviation |

> 各 skill 在自己 SKILL 里只需声明：本 skill 的 session 前缀、长任务类型、恢复时扫什么——
> 本文件说明如何后台启动任务、记录退出码、查询状态、利用已有文件恢复任务、使用 Monitor，以及管理磁盘空间。
