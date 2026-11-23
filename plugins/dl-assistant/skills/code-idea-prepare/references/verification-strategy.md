# 验证策略（coverage 收集 + smoke + 性能验证 + 失败回退）

> 先收集覆盖率确认哪些代码实际执行，再在每批清理或优化后做 smoke 测试。完成后用后续迭代的实际配置核对性能是否严格相等（±0.1%）。验证失败时定位并回滚相关改动。
> 契约：清理/优化后性能与 reproduction 基准**严格相等（±0.1%）**。

## 1. coverage 收集（三分类的基础 + 迭代命令执行到的模块与位置）

按 `reproduction.json` 的内容选 coverage 命令——用于确定代码分类，并记录迭代命令执行到的模块及位置。性能另在第 3 节验证：

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
- **未覆盖 + 有引用**（不确定）→ 用途未确认，原样保留并记入 uncovered
- **保护后续命令所需的文件和开关**：`ready_commands` / `reduced_setting` 命令链触及的文件与缩放开关（模型大小档位 / 数据子集），即使未覆盖也按核心路径对待，不删不改（见 SKILL.md「保护迭代所用的文件、配置和开关」）

把模块或文件级覆盖率报告存到 `coverage/`，并在 `hot-path.md` 记录迭代命令会执行哪些模块，以及这些模块在训练流程中的位置。后续实现前查这份文件。若改动涉及迭代命令未覆盖的模块，需要补充相应验证。

> **coverage 失真警示（非纯 Python 项目）**：C++/CUDA 扩展里的 kernel、多进程 dataloader 的子进程代码，Python coverage 统计不到——跑出来"未覆盖"可能是假阴性。此时改用 **import 级覆盖**（哪些模块真被 import 到）+ **人工标注不可覆盖区**（扩展算子、子进程路径逐个确认用途），别把假阴性当死代码删。

## 2. smoke 分级（每批清理/优化后检查受影响的命令和代码能否运行）

首选 `setup.json` 的 `ready_commands.train_smoke`（CPS 验过的分钟级试运行命令）；命令不存在或粒度不够时，按下表选择测试范围：

| 改动类型 | smoke 粒度 | 耗时 |
|---|---|---|
| 删独立脚本 | 主入口 `--help`（无 ImportError） | 10s |
| 删函数/类 | 跑到第一个 batch（forward + backward） | 1-3min |
| 删依赖 | 重装 + import 检查 + 一个 batch | 5-10min |
| 删模型组件 | 加载模型 + forward 一个 batch | 2-5min |
| 质量优化（简化不必要的抽象层/健壮性） | 同"删函数/类"粒度 | 1-3min |

**通过标准**：无 ImportError / AttributeError / NameError，能完成 forward + backward。**smoke 不验性能**（留给完整验证）。
**失败**：回滚该批 + spec 标不可删/不可改。

## 3. 用后续迭代的实际配置验证性能

性能要求严格相等（±0.1%）。使用后续实际迭代的配置进行验证，配置和复现基准按下表选取。

| 情形 | 验证配置 | 基准 | 噪声判断 |
|---|---|---|---|
| 有 `reduced_setting` | 同 reduced 配置、同 seed | `reduced_setting.baseline_result` | `reduced_setting.noise_floor` |
| training-free | eval 链（official eval） | 冻结 `target` 块的 `eval_reproduced`（±`tolerance_band`） | eval 确定性即可（对照 `determinism`） |
| 无 reduced、full 在迭代预算内 | full 训练 | 冻结 `target` 块的 `training_reproduced`（±`tolerance_band`） | `noise_floor`（跨 seed std） |

- 同 seed/配置重跑（对照 `reproduction.json` 的 `determinism`：seeds / cudnn / worker seed）
- 清理/优化后数字 vs 基准，全部在容差范围内 → 通过
- 验证级别显式记进 `cleanup.json` 的 `performance.verification_level`（`reduced` / `eval` / `full`）；迭代命令 post-cleanup 可用且数字对齐 → `handoff.iteration_verified: true`
- full / reduced 多 seed 是小时级长任务：tmux 托管，机制见 `dl-assistant/references/long-run-ops.md`（session 前缀 `cip-<repo>-`）

## 4. 失败回退（循环，直到通过或退回原基线）

性能不符时，**循环**处理（不是一次走完）：

1. **检查差异是否来自随机波动**：对照 `determinism`（seed/cudnn）多 seed 跑，用 `noise_floor`（或 `reduced_setting.noise_floor`）判是不是噪声（单个 seed 的差异落在容差范围内时，可能只是随机波动）
2. **二分定位**。确认差异超出随机波动后，按提交或批次定位引入偏差的改动
3. **回滚引入偏差的改动**：cleanup-spec / quality-spec 标"不可删/不可改"，重验
4. **重验仍失败时继续定位**。按提交或批次二分定位下一项改动，回滚后再次验证，可重复多轮
5. **底线（退出条件）**：定位不到根因 / 回滚到 `baseline-reproduced` 仍失败 → **整轮退回 `baseline-reproduced`**，CIP 本轮失败，不打 `baseline-prepared`，execution 从 `baseline-reproduced` 切

> 无法定位或修复清理引入的偏差时，回退整轮改动，保留复现已验证的起点。

### 常见失败根因

| 症状 | 可能根因 | 处理 |
|---|---|---|
| 清理后 metric 偏 | 误删动态 import/registry 引用的代码 | 二分定位 + 回滚 + 标不可删 |
| 优化后 metric 偏 | 鲁棒性优化（epsilon/clamp）改了数值 | 回滚该优化 + 标语义风险 |
| 容差范围内的随机波动 | 单 seed 噪声 | 多 seed + noise_floor 确认，非真差不回滚 |
| 精简依赖后崩 | 传递依赖（被删包间接提供的） | 恢复依赖 |
| reduced 命令跑挂 | 误动迭代设施（数据子集开关 / reduced config） | 恢复 + 列入保护清单 |
| 找不到根因 | 复杂交互 / 环境漂移 | 整轮退回 baseline-reproduced |
