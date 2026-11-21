# 清理 + 优化执行报告模板（code-idea-prepare · cleanup-report）

> CIP 的人读执行报告。机读在 `cleanup.json`（末尾）。保存 `cleanup-report.md`。精简，不冗长。
> **活文档**：cleanup-spec 确认后即建立，随执行逐节回填——每批清理/优化当场写「目的 / 做了什么 / 预期结果 / 实际结果 / 是否成功」，不留到最后一次性补写。「结论先行」节交付时定稿。
> 技术术语保留，整体中文。

---

````markdown
# Cleanup Report: <repo-name>

> 由 code-idea-prepare 产出。机读在 cleanup.json；本份是人读叙事（清理+优化过程、性能验证、uncovered 交接）。

## 0. 结论先行（交付时定稿）

- 性能验证：**通过（严格相等 ±0.1%，验证级别 <reduced/eval/full>）** / **全退 baseline-reproduced**
- execution 从 `<baseline-prepared / baseline-reproduced>` 切；迭代命令 <cmd> post-cleanup 已验证可用：是/否
- tag 链：`code-pruned` → `quality-improved`（若有）→ `baseline-prepared` / 或全退（无 tag）

## 1. 执行摘要

- 评分结论：清理必要度 {高/中/低} / 质量优化空间 {高/中/低}
- 三分类统计：死代码删 {X} / 潜伏不确定 {Y}（uncovered）/ 核心路径 {Z}
- 清理效果：删 {X} 文件 / {Y} 行 / {N} 依赖
- 质量优化：健壮性 {X} 处 / 减抽象 {Y} 处 / 鲁棒性 {Z} 处（即停确认）
- coverage 明细 + 热路径地图：`coverage/`（含 hot-path.md，execution 必看）

## 2. 清理执行记录（随批回填，详见 cleanup.json）

### Batch 1：<删低风险文件>

- 目的：...
- 做了什么：删了 X/Y/Z（commit <sha>）
- 预期结果：smoke 通过，管道不崩
- 实际结果：smoke 通过 / 失败回滚（原因）
- 是否成功：是 / 否（否则 spec 已标不可删）

### Batch 2：...

（每批一节，当场回填，不留到最后补）

## 3. 质量优化清单（详见 cleanup.json）

健壮性 / 减抽象 / 鲁棒性各改了什么（减抽象是否落在训练热路径）。鲁棒性即停项附用户决策（做/不做 + 理由）。

## 4. uncovered 代码清单（交 execution，必看）

reproduction 未覆盖 + 不确定是死是潜伏的代码。execution 碰到时心里有数（可能是要用的接口，也可能是潜伏 bug）：

| 代码位置 | 为什么未覆盖 | 备注（疑似什么） |
|---|---|---|
| `utils/init_weights.py` | registry 注册，coverage 没跑到 | 疑似影响初始化，execution 用到再确认 |

## 5. 性能验证

验证级别 = 迭代级别：<reduced / eval / full>。基准（reproduction.json 冻结 target / reduced_setting.baseline_result）vs 清理/优化后，全指标对照 ±0.1%：

| 配置 | 指标 | reproduction 基准 | 清理/优化后 | 差异 | 在 band? |
|---|---|---|---|---|---|

噪声判断依据：noise_floor / reduced_setting.noise_floor（std 多少、怎么测的）。
失败的话记回退过程（排随机 / 二分定位 / 回滚 / 全退）。

## 6. commit + tag 历史

清理/优化的 commit 序列 + 中间 tag（`code-pruned` / `quality-improved`）+ 最终（`baseline-prepared` / 全退）。

## 7. 下游交接

- execution 从 `baseline-prepared` 切（或 `baseline-reproduced`，若全退）
- **uncovered 清单 execution 必看**——这些代码 reproduction 没验过
- **hot-path.md execution 必看**——改模块前先查在不在训练热路径上（在 = 每轮迭代都执行到；不在 = 要自己补验证）
````

---

## cleanup.json（机读，execution 消费）

```json
{
  "inherits": {
    "reproduction": "docs/code-paper-reproduction/<repo>-<日期>/reproduction.json",
    "setup": "docs/code-project-setup/<repo>-<日期>/setup.json",
    "repo": { "commit": "<sha>", "branch": "code/baseline-cleanup" },
    "frozen_components": ["eval 协议", "metric 实现", "数据 split", "official checkpoint 血缘"],
    "mutable_components": ["loss", "架构", "数据增强", "优化器"],
    "known_pitfalls": ["official ckpt 是 EMA 权重，execution 对比实验注意血缘"]
  },

  "score": {
    "cleanup_necessity": "high | medium | low",
    "quality_space": "high | medium | low"
  },

  "classification": {
    "dead_code": { "files": 0, "lines": 0 },
    "uncovered": 0,
    "core_path": 0
  },

  "cleanup": {
    "files": [],
    "deps": [],
    "functions": []
  },

  "quality": {
    "robustness": [],
    "deabstract": [],
    "stability": []
  },

  "protected_iteration_infra": [
    "configs/xxx_reduced.py（reduced setting config）",
    "data/subset_sampler.py（数据集等比采样）"
  ],

  "uncovered_code": [
    { "path": "<path>", "reason": "<为什么未覆盖>", "note": "<疑似什么>" }
  ],

  "performance": {
    "verification_level": "reduced | eval | full",
    "baseline": {},
    "after": {},
    "in_band": true,
    "verdict": "passed | full_rollback"
  },

  "tags": ["code-pruned", "quality-improved", "baseline-prepared"],

  "handoff": {
    "execution_branch_from": "baseline-prepared | baseline-reproduced",
    "iteration_command": "<execution 每轮迭代的命令（有 reduced 用 reduced）>",
    "iteration_verified": true,
    "hot_path": "coverage/hot-path.md"
  }
}
```

---

## 模板使用说明

- **机读区是契约**：`classification` / `cleanup` / `quality` / `uncovered_code` / `performance.verdict` / `tags` / `handoff` 下游 execution 直接读。
- **`inherits.frozen_components` / `mutable_components` / `known_pitfalls`**：从 `reproduction.json` 原样继承——execution 读 cleanup.json 一处就能拿到迭代边界和坑清单。
- **`protected_iteration_infra`**：本次识别出的迭代设施（reduced config / 缩放开关），execution 改 idea 时也别误删。
- **`performance.verification_level`**：验证级别 = 迭代级别（reduced / eval / full）；execution 据此知道自己的迭代起点验过没有。
- **`handoff.iteration_verified`**：迭代命令 post-cleanup 可用且数字对齐才为 true——execution 的第一个迭代起点是已验证的。
- **uncovered 是给 execution 的预警**：让 execution 知道哪些代码 reproduction 没验过，碰到时谨慎。
- **verdict=full_rollback 时诚实记录**：execution_branch_from 回到 baseline-reproduced，CIP 本轮无产出；tags 无 baseline-prepared。
