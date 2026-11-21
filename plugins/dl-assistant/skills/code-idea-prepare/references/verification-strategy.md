# 验证策略（coverage 收集 + smoke + 性能验证 + 失败回退）

> CIP 验证四件套：coverage 收集（识别核心路径 vs 未覆盖 + 热路径落盘）→ 每批 smoke（管道不崩）→ 性能验证（验证级别 = 迭代级别，严格相等 ±0.1%）→ 失败回退（循环定位 + 回滚）。
> 契约：清理/优化后性能与 reproduction 基准**严格相等（±0.1%）**。

## 1. coverage 收集（三分类的基础 + 热路径地图）

按 `reproduction.json` 的内容选 coverage 命令——目的是跑出核心路径分三类 + 产出热路径地图，**不是验性能**：

| 情形 | coverage 命令 |
|---|---|
| 有 `reduced_setting`（要重训且 full 超迭代预算） | `reduced_setting.command`——**首选**：短，且覆盖训练 + 评测整条链 |
| training-free（无训练链） | `ready_commands.eval`——eval 链就是全部核心路径 |
| 无 reduced、有 `train_scaled`（分流 C 缩规模 b） | `ready_commands.train_scaled` |
| 无 reduced、full 在迭代预算内 | `ready_commands.train`（覆盖到即可，可提前截断） |

```bash
python -m coverage run --source=<pkg> <上表选出的命令>
python -m coverage report --show-missing    # 哪些代码没跑到
```

三分类：

- **核心路径**（coverage 覆盖）→ CIP 可清理 + 优化（动完重验性能）
- **未覆盖 + 静态无引用**（grep/import 图/动态 import 排查都无）→ 死代码，删
- **未覆盖 + 有引用**（不确定）→ 潜伏区，记 uncovered 不动
- **迭代设施例外**：`ready_commands` / `reduced_setting` 命令链触及的文件与缩放开关（模型大小档位 / 数据子集），即使未覆盖也按核心路径对待，不删不改（见 SKILL.md「迭代设施保护」）

**热路径落盘**：coverage 明细（模块/文件级覆盖报告）存到 cleanup 目录的 `coverage/`，并整理一份 `hot-path.md`——哪些模块在训练链上、大致在执行链的什么位置。execution 改模块前查它：在热路径上 = 每轮迭代都会执行到、验证便宜；不在 = 改动不会被迭代循环覆盖，要自己补验证。

> **coverage 失真警示（非纯 Python 项目）**：C++/CUDA 扩展里的 kernel、多进程 dataloader 的子进程代码，Python coverage 统计不到——跑出来"未覆盖"可能是假阴性。此时改用 **import 级覆盖**（哪些模块真被 import 到）+ **人工标注不可覆盖区**（扩展算子、子进程路径逐个确认用途），别把假阴性当死代码删。

## 2. smoke 分级（每批清理/优化后验管道不崩）

首选 `setup.json` 的 `ready_commands.train_smoke`（CPS 验过的分钟级冒烟命令）；命令不存在或粒度不够时，按下表现组：

| 改动类型 | smoke 粒度 | 耗时 |
|---|---|---|
| 删独立脚本 | 主入口 `--help`（无 ImportError） | 10s |
| 删函数/类 | 跑到第一个 batch（forward + backward） | 1-3min |
| 删依赖 | 重装 + import 检查 + 一个 batch | 5-10min |
| 删模型组件 | 加载模型 + forward 一个 batch | 2-5min |
| 质量优化（减抽象/健壮性） | 同"删函数/类"粒度 | 1-3min |

**通过标准**：无 ImportError / AttributeError / NameError，能完成 forward + backward。**smoke 不验性能**（留给完整验证）。
**失败**：回滚该批 + spec 标不可删/不可改。

## 3. 性能验证（验证级别 = 迭代级别）

契约：**性能严格相等（±0.1%）**。execution 将在哪个配置上迭代，就在哪个配置上验——不是"reduced 验趋势 + full 抽验"，否则 execution 拿到的迭代起点本身没验过：

| 情形 | 验证配置 | 基准 | 噪声判断 |
|---|---|---|---|
| 有 `reduced_setting` | 同 reduced 配置、同 seed | `reduced_setting.baseline_result` | `reduced_setting.noise_floor` |
| training-free | eval 链（official eval） | 冻结 `target` 块的 `eval_reproduced`（±`tolerance_band`） | eval 确定性即可（对照 `determinism`） |
| 无 reduced、full 在迭代预算内 | full 训练 | 冻结 `target` 块的 `training_reproduced`（±`tolerance_band`） | `noise_floor`（跨 seed std） |

- 同 seed/配置重跑（对照 `reproduction.json` 的 `determinism`：seeds / cudnn / worker seed）
- 清理/优化后数字 vs 基准，全在 band 内 → 通过
- 验证级别显式记进 `cleanup.json` 的 `performance.verification_level`（`reduced` / `eval` / `full`）；迭代命令 post-cleanup 可用且数字对齐 → `handoff.iteration_verified: true`
- full / reduced 多 seed 是小时级长任务：tmux 托管，机制见 `dl-assistant/references/long-run-ops.md`（session 前缀 `cip-<repo>-`）

## 4. 失败回退（循环，直到通过或全退）

性能不符时，**循环**处理（不是一次走完）：

1. **排随机性**：对照 `determinism`（seed/cudnn）多 seed 跑，用 `noise_floor`（或 `reduced_setting.noise_floor`）判是不是噪声（单 seed ±band 内偏差可能只是噪声）
2. **确认非噪声 → 二分定位罪魁**：逐 commit / 逐 batch，定位哪个清理/优化引入了偏差
3. **回滚罪魁**：cleanup-spec / quality-spec 标"不可删/不可改"，重验
4. **回循环**：重验还失败 → 继续二分定位下一个罪魁 → 回滚 → 重验（可多轮）
5. **底线（退出条件）**：定位不到根因 / 回滚到 `baseline-reproduced` 仍失败 → **全退 `baseline-reproduced`**，CIP 本轮失败，不打 `baseline-prepared`，execution 从 `baseline-reproduced` 切

> 底线原则：**CIP 是锦上添花（清理+优化），不能破坏可信 baseline**。无法定位/修复 → 整轮回退。失败的代价是"没清理没优化"，不是"baseline 变差"。

### 常见失败根因

| 症状 | 可能根因 | 处理 |
|---|---|---|
| 清理后 metric 偏 | 误删动态 import/registry 引用的代码 | 二分定位 + 回滚 + 标不可删 |
| 优化后 metric 偏 | 鲁棒性优化（epsilon/clamp）改了数值 | 回滚该优化 + 标语义风险 |
| 随机偏差（±band 内） | 单 seed 噪声 | 多 seed + noise_floor 确认，非真差不回滚 |
| 精简依赖后崩 | 传递依赖（被删包间接提供的） | 恢复依赖 |
| reduced 命令跑挂 | 误动迭代设施（数据子集开关 / reduced config） | 恢复 + 列入保护清单 |
| 找不到根因 | 复杂交互 / 环境漂移 | 全退 baseline-reproduced |
