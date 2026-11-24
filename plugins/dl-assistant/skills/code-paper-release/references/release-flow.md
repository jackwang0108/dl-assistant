# Release 单阶段全流程

`code-paper-release` 的详细流程——论文写完/接收后（CPE 跑完实验、writing-paper 写完论文），从完整中期 repo 抽取重写成干净发行版，一次性做到开源。

> 整理代码、验收和发布组成一次流程。论文实验在原研究仓库运行，性能基准直接使用 code-paper-experiment 数据包中的全量实验实测结果。无需在原研究仓库重新测量。

## Step 1：确认最终方法版本

agent 自己读懂仓库（查阅研究仓库的内部记录，对内视角）：

1. 读 `docs/research/research-rounds.json` 和 Git 记录，找到候选发布轮次及对应代码。
2. **由用户确认最终方法版本**。结合 `claims.json`、`research-spec.md` 和相关实验，提供可定位的 commit 或 tag。用户确认后，核对它与论文中的最终方法是否一致。
3. 读所选轮次的 `research-plan.md`、`claim-code-map.md`、`execution-conclusion.md` 和 `execution-conclusion.json`。沿观察引用查实际 run 的命令、配置、环境和 commit。
4. 读 CPS/CPR 产物拿环境与 baseline 可信度：`setup.json` + `report.md`（conda env、ready 命令、数据/checkpoint 路径）、`reproduction.json` + `report.md`（双轨可信度判定）。

> 若最终方法节点的 baseline 在 `reproduction.json` 里判「不可信/未复现」，先告知用户——发行版会把不可信 baseline 一起发出去。是否继续用户定。

### 研究仓库长什么样（agent 探究的对象）

来自 `code-idea-execution` 的产物结构：

- **`docs/research/research-rounds.json`** 记录研究轮次、实际代码起点和交接 commit 或 tag。研究过程默认沿 `main` 推进。
- **每轮目录**保留研究说明、plan、代码映射、论点记录、执行结论及实际实验。用 `claim-code-map.md` 定位实现，用 `execution-conclusion.{md,json}` 追到支撑结论的实验和 run。
- **运行与资产位置**以实际运行记录为准。发布清单引用复核过的命令、配置、代码与权重。

## Step 2：分层抽取 + 逐层验证（按公开读者可获得的资料整理）

在 GPU 服务器一个**全新仓库** `git init`（不沿用研究仓库的提交历史），中期 repo 当**只读参照**，只把「baseline 主干 + 最终方法 idea 增量」干净重写。**从这步起产出物按外部读者可获得的资料编写——假设读者只有 PDF。**

> 新仓库是独立仓库（不塞进中期 repo 项目根，否则 history 缠在一起泄露）。位置由用户定——动手前确认。

**抽什么**（`claim-code-map.md` 当地图）：baseline 跑最终方法必需的主干 + 最终方法实现存活 claim 的增量 + 主表对应的 train/eval 入口、config、data loader、metric 实现。

**仅保留发布所需文件**。内部研究记录（`docs/research/`）、未发表方向、无关实验脚手架、运行残留和原仓库提交历史留在研究仓库。

**保留所需代码的原目录结构**。去除上面列出的内容后，保留其余代码的原有位置。统一搬入 `src/` 等目录需要修改导入路径，可能影响复现。若有必要局部重组，例如用论文概念为模块改名，由助手提议、用户确认。删除未使用的代码，并在 README.md 和 AGENTS.md 中说明目录及模块与论文组件的对应关系。

### 抽取验证手册（核心：每层整理后与原仓库对照验证，不过不进下一层）

逐层验证完成后再做全量回归——按依赖分五层，每层抽完**当场和中期 repo 原地对照**，判据过了才进下一层。这样 Step 5 的全量回归从「唯一的关」变成「最后一道关」，挂了也能立刻定位是哪一层引入的。

| 层 | 抽什么 | 验证判据（对照源 = 中期 repo 原地） | 未通过时检查什么 |
|---|---|---|---|
| 1 环境 | conda env 固化 | 所有相关模块均可导入（`python -c "import <各模块>"`） | 遗漏所需文件 / 依赖漏进 environment.yml |
| 2 数据 | data loader + transform | 同一 batch 两边对照：shape 一致 + 数值一致 | 漏抽/改坏预处理、transform、augmentation |
| 3 模型 | 模型代码 | **权重等价 + 前向一致**：load 发布 checkpoint 必须 `strict=True` 过；固定输入两边各跑一次前向，logits 数值对齐（容差 ~1e-5） | state_dict key 对不上（漏抽模块/改名改坏）；前向不一致（漏抽组件/初始化路径不同） |
| 4 推理 | eval 入口 + metric | 小样本（百级）eval 指标趋势合理，和中期 repo 同子集指标对齐 | metric 实现漏抽/改坏、评测协议不一致 |
| 5 训练 | train 入口 | smoke：overfit 单 batch / 几步 iteration，loss 正常降、出 checkpoint | 训练链路漏抽（optimizer/scheduler/loss） |

> **第 3 层是整个验证体系的核心机制**——不用训练、不等全量，就能在跑长任务前抓住绝大多数抽取错误。`strict=True` 不过或前向对不齐，先修层 3，别往下走。

**重写质量**（外部读者 真正需要）：可读（模块命名对应论文 method concept、删死代码删未用参数）/ 可维护（清晰目录、入口明确）/ 论文↔代码可对照（核心模块标论文公式/section）/ 一键复现导向。

本步同时起草 `README.md` 和 `AGENTS.md`（模板：`readme-template.md` / `agents-template.md`）——运行命令占位，Step 5 回归后回填实测命令与数字定稿。

> 定位相关实现的代码索引**对内**（读 claim-code-map 知抽哪些），重写出来的代码文档**对外**——绝不把 claims.json / spec / plan / conclusion / 探索历史写进发行版。

## Step 3：conda 环境 + Docker A/B

**conda 环境须独立复现论文主表**。`environment.yml` 是环境的源，Dockerfile 基于它构建保证一致。

1. **conda（必做，第一可复现层）**：从实际可跑环境固化干净 `environment.yml`/`requirements.txt`（只留发行版真正用到的依赖）。**不依赖 Docker 就能跑通主表**（HPC 场景）。
2. **数据/权重策略**：小数据/小权重镜像内自动下载；大数据不进镜像、留详细准备说明（`docs/data_preparation.md`）+ 挂载；Volume 挂载为主。
3. **Docker 训练镜像 A**。挂载数据做短程训练，检查环境可用、数据可读、loss 下降并生成 checkpoint。镜像 A 的验收只要求通过这些训练检查。
4. **Docker 推理镜像 B**（主验证关）：**挂载发布权重 → 推出主表 metrics**。**通过参数指定权重的挂载路径**——支持作者发布 / 外部读者 自训两种来源，镜像 B 也可使用镜像 A 训练得到的权重。

## Step 4：基准汇总 + 建回归测试

**基准从 CPE 数据包汇总**（全量实验实测结果，无需在原研究仓库重新测量）：

1. 读 `paper-results.json` 的批次和修订，按论文主表对应的 exp_id 查已核统计、实际执行、配置及原始读数，取适用于所发布版本的结果。
2. **基准记录** `docs/perf-baseline.json`：按 `perf-baseline-template.json` 生成（`metrics[]` + `reproduce` + `provenance`）。checkpoint 下载地址：发布后的下载链接（Step 6 回填）；CPE 侧 GPU 路径从 `paper-results.json` 核对。
3. **回归脚本** `scripts/perf-regression.sh`：一键跑——复现主表 → 读 `perf-baseline.json` 比对 → 逐项报告 pass/fail（落容差内）。

## Step 5：跑回归验论文主表性能（用户确认容差）

**回归测试以论文主表为目标**。基准取自 code-paper-experiment 的全量实验实测结果。

**用户确认容差**：agent 按 metric 类型推荐默认（分类 top-1 ±0.1~0.3、检测 mAP ±0.2），最终由用户确认。

三关：
1. **conda 复现主表**（必须首先通过的验证）：干净 conda + 发行版代码 + 发布权重复现主表 → 比对基准容差。**不过不合格，回 Step 2 查抽取/重写哪里漏了或改坏了。**
2. **Docker B 复现主表**（确认封装无偏差）：镜像 B 挂权重复现 → 比对基准容差。
3. **Docker A smoke**（检查短程训练能否运行）：镜像 A 挂数据跑训练 → 环境对、loss 降、出 checkpoint。

**与论文 PDF 核对**。将发行版复现的指标逐项与论文主表比较，差异须在用户确认的容差内。

**不一致排查**：
- 回归挂了（repo 复现 ≠ 基准）→ 抽取/重写漏了（回 Step 2），或基准汇总错了（重对 CPE 数据包）。
- 对外对不上（repo 复现 ≠ PDF）→ CPE 数据本身问题（回 CPE），或论文主表誊写问题。

## Step 6：定稿 README.md 和 AGENTS.md + 权重发布

1. **README.md / AGENTS.md 定稿**：更新 Step 2 的初稿——运行命令逐条换成 Step 5 回归实测过的命令，主表数字照 PDF（已核过），训练资源从 `paper-results.json` GPU 小时用量记录拿。两份文件命令必须一致。
2. **权重发布**：发布用 checkpoint 上传 Hugging Face Hub（或用户指定存储），记录下载链接 + sha256；链接回填 README / AGENTS.md / `perf-baseline.json` 的 `reproduce.checkpoint`。
3. **LICENSE**：由用户确认哪种（MIT / Apache-2.0 / ...），落 `LICENSE` 文件；README 附上 BibTeX 引用。

## Step 7：防泄露自查 + GitHub 开源

**防泄露自查**（对内研究仓库的内部记录痕迹绝不能漏到对外）——人工核对并运行自动扫描：

- Git 提交历史不含内部信息（全新仓库、开发期 commit 无内部信息）。
- 无其他分支 / 被否 idea / 未发表方向的代码目录注释。
- 无内部研究文件，包括 `docs/research/` 的轮次索引、执行结论、决定和实验台账。
- 无 `runs/` 残留、无死代码、无定义未用参数。
- **自动扫描项目**（开源前必跑，结果记进 RELEASE_REPORT）：
  ```bash
  # secret 扫描（或 gitleaks detect）
  grep -rniE "(api[_-]?key|secret|password|token|wandb|hf_[A-Za-z0-9])" \
    --include="*.py" --include="*.sh" --include="*.md" --include="*.yml" .
  # 内部路径扫描（按用户实际环境调整模式）
  grep -rnE "(/home/|/data/|/mnt/|/nas/|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)" \
    --include="*.py" --include="*.sh" --include="*.md" --include="*.yml" .
  # 作者/机构信息（双盲场景）
  grep -rniE "(<姓名>|<机构>|<邮箱域名>)" .
  ```

**GitHub 定稿开源**：

1. 更新 `RELEASE_REPORT.md`（按 `release-report-template.md`）：节点认定、基准、三关回归、对外验收、防泄露自查（含自动扫描结果）、权重发布。
2. **开源前清理（必做，防泄露）**——`RELEASE_REPORT.md` 含内部信息，开发期 commit message 也可能带内部痕迹。agent 列清理清单（删 `RELEASE_REPORT.md` 留底到 repo 外 / 删 `.git` / `git init` / 首个 commit = 干净开源版）→ **用户确认** → agent 执行。
3. push GitHub（公开/私有用户定），论文挂这个 repo 地址。
4. 汇报：发行版已开源，**自带回归测试 + 已验过论文主表性能**，外部读者 拿 PDF + repo 能一键复现主表。

## Step 8（可选，默认推荐）：GitHub Pages 项目页

顶会论文的项目页是 外部读者 第一入口。repo 开源后做一页**高级、美观的科研展示页**，放在**同仓库 `docs/`**（GitHub Pages 从 main 的 `/docs` 开）——外部读者 clone 一次代码和页面全有，用户开一下仓库设置即可访问。

**内容来源**：agent 组装初稿——标题/作者/abstract/bibtex 从论文 PDF 提，主表从 `perf-baseline.json` 提，定性图从 CPE 数据包 `figures/` 提；teaser 终稿图、demo 视频等论文终稿素材**用户给**，agent 不自己造。

**制作原则**（只定原则，具体设计 agent 发挥、用户审美裁决）：

- **目标是展示，不是文档**——一页让人看懂「这是什么工作、效果多好、怎么引用」；排版美观优先，纯静态或带交互均可。
- **单文件自包含优先**——`docs/index.html` 为主，不引重型框架；交互需要时可用 vanilla JS 或 CDN 轻量库。
- **媒体文件的存放规则**：图片、小视频、小音频直接进 `docs/` 随仓库走；**大视频传 YouTube 嵌 iframe**，大音频同理外链——避免媒体文件过度增加仓库体积。
- **内容按外部读者可获得的资料编写**——页面只含 PDF + 发行版已公开的信息，防泄露要求同 Step 7。
- **用户审完再公开**——内容/素材/美观由用户裁决，审过才开 Pages（Settings → Pages → main `/docs`），给 URL 并回填 README 链接。

## 验证原则（贯穿）

- **基准用 CPE 全量实验实测结果**：从 CPE 数据包 paper-results.json 汇总，不做占位。
- **conda 是必须首先通过的验证**：HPC 无 Docker 权限，发行版必须 conda 独立跑通主表。
- **A/B 验证不对称**：A 检查短程训练能否正常运行、B（挂权重）核对推理指标能否复现主表。
- **容差**：agent 按 metric 类型推荐默认，**由用户确认**。
- **repo 自带回归测试**：交付前已验证可在容差内复现论文主表，不是临时动作。
- **README.md 和 AGENTS.md 使用相同的实测命令**：README（人读）与 AGENTS.md（agent 读）的运行命令都来自 Step 5 实测，改一处同步另一处。
