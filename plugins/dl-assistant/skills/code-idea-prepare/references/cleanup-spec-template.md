# 清理方案 Spec 模板（code-idea-prepare · cleanup-spec）

> CIP 清理阶段（减法）的方案，**用户审过才执行**。只动 reproduction 覆盖的核心路径 + 确定的死代码。
> 潜伏不确定代码不进清理清单（记 uncovered 交 execution）；迭代设施受保护（不删）。
> 保存 `cleanup-spec.md`。技术术语保留，整体中文。

---

````markdown
# Cleanup Spec: <repo-name>

> 清理方案（减法）。审阅通过后才执行。有问题就改，改到确认再动手。

## 0. 评分摘要（来自探索阶段）

- 三分类统计：死代码 {X} / 潜伏不确定 {Y}（→ uncovered）/ 核心路径 {Z}
- 清理必要度：高 / 中 / 低
- 预估清理量：{文件数} 文件 / {行数} 行 / {依赖数} 包
- coverage 明细 + 热路径地图：`coverage/`（含 hot-path.md）

## 1. 性能基准（来自 reproduction.json，清理后必须严格相等）

| 实验配置 | 指标 | 基准值 | 允许波动 |
|---|---|---|---|
| <config> | <metric 精确定义> | <val> | ±0.1% |

- 基准来源：`reproduction.json` 的冻结 `target` 块（metric 精确定义 + tolerance_band + eval/training_reproduced）
- **验证级别 = 迭代级别**：execution 将在 <reduced / eval / full> 上迭代，本 spec 的性能验证就在该配置上做（有 `reduced_setting` 则基准用 `reduced_setting.baseline_result`，噪声判据用其 `noise_floor`）
- 核心入口（从 `reproduction.json` 的 `ready_commands` / `reduced_setting.command` 拿）：<命令>

## 2. 迭代设施保护清单（不删不改）

以下触及 `ready_commands` / `reduced_setting` 命令链，或是 scaling-law 迭代的缩放开关——即使 coverage 未覆盖、静态分析像死代码，也一律不删不改：

| 项 | 为什么是迭代设施 |
|---|---|
| `configs/xxx_reduced.py` | reduced setting 的 config（数据子集档位，模型容量不动） |
| `data/subset_sampler.py` | 数据集等比采样（scaling sweep 各点共用） |

## 3. 待删死代码（按风险分级）

### 低风险（静态确认无引用：grep + import 图 + 动态 import/registry 排查都无）

| 文件/函数/类 | 删除理由（附排查证据） | 行数 |
|---|---|---|
| `scripts/deprecated_eval.py` | 标注 DEPRECATED，grep 全代码无引用，无动态 import | 250 |

### 中风险（有引用但整条引用链都是死代码——整链删）

| 项 | 删除理由 | 潜在风险 | 验证 |
|---|---|---|---|
| `data/custom_sampler.py` + 引它的 config | config 本身也是废弃实验 | 动态加载？ | 删前 grep config 字符串字面量 |

### 高风险/暂不删（疑似死代码但无法静态确认 → 标 uncovered）

| 项 | 保留理由 | 后续 |
|---|---|---|
| `utils/init_weights.py` | 可能经 registry 影响初始化，静态查不到 | 记 uncovered，execution 碰到确认后再定 |

> 研究代码的坑：动态 import / registry / 配置驱动加载让静态分析不确定。**不确定的不删**（误删 execution 崩）。

## 4. 待精简依赖

| 包 | 删除理由（全代码无 import + pipdeptree 无传递依赖） | 验证方式 |
|---|---|---|
| `tensorboardX` | 已切原生 tensorboard | grep 无 import |

## 5. 待删配置 / 调试残留

| 项 | 处理 | 理由 |
|---|---|---|
| `configs/debug_*.yaml` | 删 | 临时调试配置，不在 reproduction |
| 注释代码块 | 删 | 死代码 |

## 6. 执行计划（分批，每批 smoke 通过才 commit）

### Batch 1：删低风险文件

- 目的：先清静态确认无引用的独立文件，风险最低，先验证 smoke 流程通畅
- 内容：§3 低风险表全部
- 预期：smoke（`train_smoke`）通过，管道不崩

### Batch 2：删函数/类

- 目的：清核心路径外的死函数/死类
- 内容：...
- 预期：smoke 通过，forward + backward 正常

### Batch 3：精简依赖（重装环境）

- 目的：...
- 内容：...
- 预期：重装后 import 检查 + 一个 batch 正常

### Batch 4：删中风险整链

- ...

### Batch 5：配置/调试残留

- ...

每批 smoke 不过 → 回滚该批 + 标不可删。

## 7. 用户确认

- [ ] 死代码清单（低/中风险）无异议
- [ ] 高风险/uncovered 清单认可（这些不删）
- [ ] 迭代设施保护清单认可（这些不删不改）
- [ ] 同意分批顺序
- [ ] 同意最终手动 review + merge
````

---

## 模板使用说明

- **清理只动确定的**：低/中风险（静态确认 + 整链确认）才删；高风险/不确定进 uncovered 不删。
- **迭代设施受保护**：`ready_commands` / `reduced_setting` 命令链 + 缩放开关一律不删——那是 execution 每轮迭代的载体。
- **动态 import 是头号误删风险**：研究代码常用 registry/importlib/配置驱动，删前必查字符串字面量 + `_target_`/`type` 字段。
- **每批 smoke 是硬约束**：不 smoke 不 commit，smoke 不过立即回滚该批。
