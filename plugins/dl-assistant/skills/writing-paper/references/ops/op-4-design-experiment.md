# 目标 4：design-experiment（规划或追加一批实验）

## 何时用

两个触发：**首批**（蓝图初建确认后——产 plan-v1）和**追加**（state 的 `experiments.new_needs` 攒了一批、或来了急的、或修改清单含补实验项、或配置冻结后开主表批——产 plan-vN+1）。实验计划**版本化递增，不一次定死**。

## 读哪些

- `references/templates/paper-experiment-plan-template.md`（人读区）+ `.json`（机读 schema）。
- `_draft/blueprint.md`（contribution → 要哪些实验证明）。
- `paper-state.json`（`experiments.new_needs` 待规划需求、已有批次、数据依赖、deadline）。
- 中期论文准备材料（**配置冻结状态**：locked config 有没有——决定 v1 要不要先装配置选定批）。

## 实验计划是什么（writing-paper ↔ CPE 契约）

- **writing-paper 定「要跑什么 + 为什么 + 谁先谁后」**（论文 claim 驱动 + 依赖拓扑）；**CPE 跑「怎么跑」**（full config + 多 seed，按依赖拓扑排程）。
- **论文 claim ≠ claims.json 原始 claim**：plan 里的 claim 是 storytelling 层（blueprint 的 contribution/分析），ref C-ID 作证据底盘，但本身是 paper-facing 的。
- **plan 是起点，不是契约**——CPE 跑时会加/改实验；最终以 CPE 的 `experiments-actual.json`（实际跑了哪些）为准，ingest-results 按实际对齐。

## 子动作

1. **推导实验套件：claim × 攻击面矩阵**。对每个 contribution，站在 reviewer 角度列它会受到的攻击，逐格决定「这格要不要实验、要哪个」：
    | 攻击面 | reviewer 的问法 | 典型实验 |
    |---|---|---|
    | 主性能 | 凭什么说比 baseline 好？ | 主表（标准 benchmark × 强 baseline） |
    | 组件有效性 | 每个组件都有用吗？ | 组件消融（逐组件去掉/替换） |
    | 机制 | 为什么 work？ | 机制分析 / 可视化 / 统计探针 |
    | 泛化 | 换个数据集/setting 还行吗？ | 跨数据集 / 跨 setting 实验 |
    | 效率代价 | 速度快吗、代价多大？ | 效率表（速度/显存/参数量） |
    | 公平性 | 和 baseline 同预算吗？ | 同 budget 对照 |
    | 定性展示 | 长什么样？ | case study / 可视化对比 / 失败案例 |
    矩阵写进 plan（哪格由哪个 exp_id 填）——**防空洞**（某 contribution 没实验撑，写作时才发现）也**防冗余**（三个实验重复证明同一格）。定性维度对 vision 类论文几乎是刚需，定性样本正好走真实样本资产通道（`schematic-figure.md`）。
2. **标实验间依赖（拓扑排序）**。每个实验标 `depends_on`：
    - **排序铁律：配置未冻结，主表不开跑**。中期收口没冻结配置 → v1 必须先装**配置选定批**（全量设置下的组件消融 + 超参选定）；主表 `depends_on` 配置选定实验，用已确认的固定配置和多个随机种子完成正式测量——主表用拍脑袋配置跑 = headline 数字非最优，发现时主表重跑、对比/消融/数字回填全牵连，灾难级返工。
    - **定性实验 `depends_on` 主 run**（要用它的 checkpoint 产出可视化）。
    - 无依赖的（各消融臂之间、各 baseline 之间）标并行——CPE 按依赖拓扑在多卡机器上排程，该并行的并行、该等待的等待，GPU-hours 不烧在等上。
    - **同一实验结果可用于多个位置**：组件消融按正规协议跑（全量 + 多 seed）= 配置决策依据 + 论文消融表（不跑两遍）；超参搜索 = 选定配置 + 附录敏感性分析。
    - **test peeking 红线**：配置决策只用 validation split——用 test 调参是学术不端级错误。
3. **独立查漏（reviewer 预演）**。套件设计完，以 reviewer 视角过一遍找缺口：baseline 太弱/太旧？缺 efficiency 表？seed 数够不够报方差？有没有失败分析（负结果在哪）？定性展示有没有？查完补完才进确认点。
4. **首批（v1）vs 追加（vN+1）**。v1 按依赖图装**长周期必做项**（配置未冻结则配置选定批优先 + 可并行的 baseline/主表准备），让 CPE 尽早开跑；写作中浮现的需求不硬猜。追加批：盘点 `experiments.new_needs` 凝成新一批，每实验标清来源需求可追溯。
5. **按模板产 `_draft/experiments/plan-vN.md`（人读：批次说明 + 验证覆盖矩阵 + 依赖拓扑 mermaid + 逐实验卡片 + 独立查漏记录——逐项请用户确认时查阅此文件）+ `plan-vN.json`（机读：全部字段，CPE 消费的单一读取源）**。每个实验在 json 里填：
    - **priority**（must/should/appendix，跟页数参考对齐）+ **type**（main/ablation/analysis/comparison/efficiency/qualitative）。
    - **expected_signal**（预注册 success bar——bar 的依据：同类工作中同类改动的**典型幅度** + bar 与 claim 强度匹配[claim 说"显著提升"bar 就不能定 0.1%]；否定信号回 design-story 重审）。
    - **fairness**（main/comparison 必填，baseline 公平条件）。
    - **baseline 纪律**（comparison 类）：同期 SOTA 必比；直接相关工作用官方报告数字还是自复现要说清（自复现注明条件）；baseline 用其原文最佳超参，不弱化。
    - **expected_cost**（预计成本 + **deadline 倒推**：这批必须几号前开跑才赶得上）。
    - **depends_on**（拓扑依赖）+ **output_to_paper**（主表/消融表/附录敏感性/定性图位——一处实验多处消费在这里体现）。
6. **登记数据依赖**：记录这批实验分别用于哪个章节、子论点或表格，写进 state 的 `experiments.data_dependencies`。
7. 和用户过计划（确认点：矩阵 + 依赖图 + 成本逐项过）。

## 产出

`_draft/experiments/plan-vN.md` + `plan-vN.json`（实验计划包，给 CPE：人读总览 + 机读字段）。

## 状态更新

`experiments.batches` 加一批（version/plan 路径/status）；`data_dependencies` 登记；`new_needs` 已规划的标 planned + batch 号。

## 确认点

- **计划满意才交 CPE**——plan 触发 full-scale 实验（高消耗：多卡多 seed 烧 GPU）。矩阵 + 依赖图 + 每个实验的配置与预计成本逐项过，用户点头才往下。跨机器交接不绑传输（找用户弄到 GPU 服务器，不管怎么传）。
- **配置冻结**（tuning 批数据回来后在 ingest-results 触发）：配置选定批的结果摆给用户 → 用户确认选定配置 → 才产主表批 plan。agent 不自己定配置——tuning 结果可能出人意料，这是判断，判断归人。

## CPE 消费 + 数据回

CPE 读 plan-vN，先产 run-spec.json（执行契约）再按 `depends_on` 拓扑排程（多卡并行无依赖实验），按 `experiments[]` 逐个跑（full config + 多 seed），数据落 `experiments/<exp_id>/`（目录契约：configs/scripts/runs/log 全量），**不动 claims.json**。跑完一批产**实验数据包**（`experiments-actual.json` + `results.json` + `pkg-meta.json`）回 writing-paper → 进 ingest-results（按批，不等全部跑完）。

## 易错点

- **配置未冻结，主表不开跑**——主表用未调优配置 = headline 非最优 + 全链路返工；配置选定批（组件消融 + 超参选定）先进 v1，配置冻结确认点用户确认。
- **一次实验多处消费**——组件消融既是配置依据又是论文消融表，别跑两遍；超参搜索进附录敏感性分析。
- **test peeking 是红线**——配置决策只用 validation split。
- **depends_on 标全**——CPE 靠它拓扑排程；漏标 = 该并行的串行等，GPU-hours 白烧。
- **预注册 expected_signal 防 cherry-pick**——bar 依据同类工作典型幅度 + claim 强度；否定信号回 design-story 重审，别 post-hoc 挑有利数字硬写。
- **fairness 进 CPE 契约**——main/comparison 的 baseline 公平条件写进 plan，CPE 照着跑。
- **priority 跟页数参考对齐**——must 先跑且进正文，should/appendix 页数紧时可挪可砍（定稿时压缩篇幅用户裁决）；别全是 must。
- **独立查漏后才交确认点**——别把带明显缺口的套件直接倒给用户。
- **数据依赖当场登记**——不然数据到了无法判断数据应写入何处、哪节还空着。
