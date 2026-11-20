# 官方版本、复用范围与本项目约定

## 来源与原文保留

本skill的 `upstream/wandb-primary/` 来自 [wandb/skills](https://github.com/wandb/skills) 的 commit `10aac21c75e7bced8fb5dd760e49e7d0ff0f87dc`，安装路径为 `skills/wandb-primary`。该目录原文及脚本未改，额外附仓库根 LICENSE；Apache-2.0 和原文件版权声明保留。逐文件校验值见 [来源清单](upstream-manifest.json)。维护时审阅差异并显式升级固定commit，不在运行时拉main。

这是上游第三方内容，保留它的原始措辞/示例供核对；本项目新增的规则使用直接表述。接入说明、身份约定和检查器是 dl-assistant 的补充，不冒称 W&B 官方发布或认证。

## 直接复用什么

按任务读取官方 SDK、RUN_LOGS、Artifact 资料和相应脚本。运行查询可用官方 MCP；已有 SDK 脚本可调用官方 `wandb_helpers.get_api`、`scan_history` 等，不另维护同功能包装。修改训练入口时使用官方 SDK，保留仓库现有 logger。未经验证的其他官方功能不因随包存在而成为已支持功能。

本次重点检查 SDK 读取、日志、产物与 helper 的使用方式，以及主说明/假设生成中的研究规则；不声称完整审计所有 Weave/Launch/Automation/写操作模块。它们保留为上游资料，不在当前 Models-only 工作范围内。

官方脚本的一些前提需注意：
- `get_api`/部分查询直接读取 `WANDB_BASE_URL`，未设置时可能默认云端；所有调用前先核内网地址及实际生效值。
- `scan_history` 多key读取保留 SDK 的共同存在行语义；异步记录的多个指标不能因共同查询为空就断言没有数据。分别读并保留 step 关系，不伪造插值。max_rows 要为正整数，达到上限记录覆盖不足，不称全量。
- `compare_configs` 用显示名作为结果字段；两个 run 显示名相同时会覆盖一侧值。此时按完整 run ID 分列实际 config，而不是把该 helper 的结果当完整比较。
- SDK文档中的 3σ、平台阈值、训练/验证比例只是示例启发式，不作为通用数据有效或科学裁决标准。
- 依赖及最低版本按所用功能核对；官方 skills README 与 MCP 的 SDK 下限不完全相同，不能因为 MCP 能启动就保证所有 skill helper 可用。

## 不采用的上游研究规则

官方主说明及 `HYPOTHESIS_GENERATION.md` 中存在默认并查 runs/Weave、推断领域先验、穷尽信号、必须定位具体原因、单变量二元检验等规则。对本项目，它们不改变用户已确定的研究流程：

1. 当前使用自托管 Models；不因宽泛查询就初始化未部署的 Weave 或云端组件。
2. 先验来自已记录研究问题、原文和可检查推理；不能仅从项目名推断成已确立事实。
3. 允许原因未知、竞争解释和无法区分；取证受实际预算与信息价值限制，不无限调查到“找到罪因”。
4. 设计由重要未知与可识别性决定，不强制单变量、固定数量或二元结果；不因一个读数不变就宣告机制被排除。
5. 新实验、参数搜索、部署和外部写入遵循当前任务的具体授权；官方操作示例不自动增加预算或授权。

这是沿用用户已经确定的 dl-assistant 研究/内网要求，非对官方 API 能力的否定。研究设计和判断继续由 idea-find/iterate负责，批准实验由 execution/论文实验实施。
