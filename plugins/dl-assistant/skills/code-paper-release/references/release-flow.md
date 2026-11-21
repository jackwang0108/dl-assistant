# Release 单阶段全流程

`code-paper-release` 的详细流程——论文写完/接收后（CPE 跑完实验、writing-paper 写完论文），从完整中期 repo 抽取重写成干净发行版，一次性做到开源。

> **单阶段**：抽 repo + 验收开源合并为一次流程。CPE 在中期 repo 跑实验，release 从中期 repo 抽 repo 开源；基准直接用 CPE 的 full-scale 真数（从数据包汇总），不在屎山上重测。

## Step 1：认最终方法节点

agent 自己读懂仓库（读施工图，对内视角）：

1. 读 `idea_tree.json` + `git log --oneline --graph --all`，把 idea 树摆出来。
2. **用户指认最终方法节点**：树里哪个分支/tag 是锁定的最终方法（要做成发行版、写进论文的那个）？agent 结合 claims.json 终版存活 claim + 各版本 `01-idea-spec.md` 给推荐，但**发哪个由用户拍板**——发错整个发行版就错。
3. 读最终方法节点的版本目录（`01-idea-spec.md` / `02-research-plan.md` / **`03-claim-code-map.md`（抽取地图）** / `04-conclusion.md`）+ claims.json。**重点读 `04-conclusion.md`「可复现信息」**（复现命令 + 环境 + tag/commit）。
4. 读 CPS/CPR 产物拿环境与 baseline 可信度：`setup.json` + `report.md`（conda env、ready 命令、数据/checkpoint 路径）、`reproduction.json` + `report.md`（双轨可信度判定）。

> 若最终方法节点的 baseline 在 `reproduction.json` 里判「不可信/未复现」，先告知用户——发行版会把不可信 baseline 一起发出去。是否继续用户定。

### 研究仓库长什么样（agent 探究的对象）

来自 `code-idea-execution` 的产物结构：

- **idea = git 分支树**：根是 baseline，版本是分支 `idea/v<N>-<slug>`，method 锚点是 tag。
- **`ideas/idea_tree.json`** —— 谱系入口，认节点用它。
- **每个版本目录**：`01-idea-spec.md` / `02-research-plan.md` / `03-claim-code-map.md`（claim ID → file:line → 验证逻辑，**抽取地图**）/ `04-conclusion.md`（claim-证据 + golden_metrics）/ `00-from-previous-version.md`（v2+）。
- **`claims.json`** —— claim tree 脊柱，认存活 claim。
- **三方绑定**：git tag ↔ experiments/ 目录 ↔ conclusion 小节。checkpoint/runs 不进 git，靠 conclusion 与 pkg-meta.json 记路径。

## Step 2：分层抽取 + 逐层验证（follower 视角）

在 GPU 服务器一个**全新仓库** `git init`（history 归零），中期 repo 当**只读参照**，只把「baseline 主干 + 最终方法 idea 增量」干净重写。**从这步起产出物严格 follower 视角——假设读者只有 PDF。**

> 新仓库是独立仓库（不塞进中期 repo 项目根，否则 history 缠在一起泄露）。位置由用户定——动手前确认。

**抽什么**（`03-claim-code-map.md` 当地图）：baseline 跑最终方法必需的主干 + 最终方法实现存活 claim 的增量 + 主表对应的 train/eval 入口、config、data loader、metric 实现。

**不抽什么**（防泄露 + 防屎山）：其他分支 / 被否 idea / 未发表方向的代码目录注释；实验脚手架、`experiments/` 残留、版本目录施工文件（`00-04-*.md`）、`claims.json`、`idea_tree.json`、`runs/` 残留、死代码；任何 commit history。

**骨架继承原仓库（只删不搬）**：删掉上面这些后剩下的原仓库目录结构就是发行版骨架——**不为了好看把代码搬进统一目录**（搬目录 = 改 import = 引入回归风险，和「性能不掉」直接冲突）。局部重组（如某模块改名对论文概念）允许，但属「agent 提议、用户拍板」的可选项。干净感靠三点：死代码删净、模块命名对应论文概念、README/AGENTS.md 的「仓库地图」把 `目录/模块 ↔ 论文组件` 映射讲清楚。

### 抽取验证手册（核心：抽一层验一层，不过不进下一层）

别一次性抽完靠最后的全量回归一把验——按依赖分五层，每层抽完**当场和中期 repo 原地对照**，判据过了才进下一层。这样 Step 5 的全量回归从「唯一的关」变成「最后一道关」，挂了也能立刻定位是哪一层引入的。

| 层 | 抽什么 | 验证判据（对照源 = 中期 repo 原地） | 挂了查什么 |
|---|---|---|---|
| 1 环境 | conda env 固化 | 全链路 import 绿（`python -c "import <各模块>"`） | 漏抽文件 / 依赖漏进 environment.yml |
| 2 数据 | data loader + transform | 同一 batch 两边对照：shape 一致 + 数值一致 | 漏抽/改坏预处理、transform、augmentation |
| 3 模型 | 模型代码 | **权重等价 + 前向一致**：load 发布 checkpoint 必须 `strict=True` 过；固定输入两边各跑一次前向，logits 数值对齐（容差 ~1e-5） | state_dict key 对不上（漏抽模块/改名改坏）；前向不一致（漏抽组件/初始化路径不同） |
| 4 推理 | eval 入口 + metric | 小样本（百级）eval 指标趋势合理，和中期 repo 同子集指标对齐 | metric 实现漏抽/改坏、评测协议不一致 |
| 5 训练 | train 入口 | smoke：overfit 单 batch / 几步 iteration，loss 正常降、出 checkpoint | 训练链路漏抽（optimizer/scheduler/loss） |

> **第 3 层是整个验证体系的核心机制**——不用训练、不等全量，就能在跑长任务前抓住绝大多数抽取错误。`strict=True` 不过或前向对不齐，先修层 3，别往下走。

**重写质量**（follower 真正需要）：可读（模块命名对应论文 method concept、删死代码删未用参数）/ 可维护（清晰目录、入口明确）/ 论文↔代码可对照（核心模块标论文公式/section）/ 一键复现导向。

本步同时起 `README.md` 和 `AGENTS.md` 骨架（模板：`readme-template.md` / `agents-template.md`）——命令链占位，Step 5 回归后回填实测命令与数字定稿。

> 抽取地图**对内**（读 claim-code-map 知抽哪些），重写出来的代码文档**对外**——绝不把 claims.json / spec / plan / conclusion / 探索历史写进发行版。

## Step 3：conda 环境 + Docker A/B

**主次：conda 第一可复现层，Docker 是它上面的封装。** `environment.yml` 是环境的源，Dockerfile 基于它构建保证一致。

1. **conda（必做，第一可复现层）**：从实际可跑环境固化干净 `environment.yml`/`requirements.txt`（只留发行版真正用到的依赖）。**不依赖 Docker 就能跑通主表**（HPC 场景）。
2. **数据/权重策略**：小数据/小权重镜像内自动下载；大数据不进镜像、留详细准备说明（`docs/data_preparation.md`）+ 挂载；Volume 挂载为主。
3. **Docker 训练镜像 A**：挂载数据后能训。验证只验「训得动」（环境对/数据通/loss 降/出 checkpoint），**不要求 A 重训精确复现主表**。
4. **Docker 推理镜像 B**（主验证关）：**挂载发布权重 → 推出主表 metrics**。**权重路径挂载参数不写死**——支持作者发布 / follower 自训两种来源，A 训出权重喂 B 衔接。

## Step 4：基准汇总 + 建回归测试

**基准从 CPE 数据包汇总**（full-scale 真数，不在屎山上重测）：

1. 读 CPE 数据包三件套：`results.json`（逐实验 mean±std + signal 判定）+ `experiments-actual.json`（实际跑了哪些）+ `pkg-meta.json`（权重/log 指针 + GPU-hours 台账），schema 见 `code-paper-experiment/references/templates/data-pkg-schema.json`。主表对应的 exp_id 汇总 mean±std 成基准。
2. **基准记录** `docs/perf-baseline.json`：按 `perf-baseline-template.json` 生成（`metrics[]` + `reproduce` + `provenance`）。checkpoint 指针：发布后的下载链接（Step 6 回填）；CPE 侧 GPU 路径从 `pkg-meta.json` 核对。
3. **回归脚本** `scripts/perf-regression.sh`：一键跑——复现主表 → 读 `perf-baseline.json` 比对 → 逐项报告 pass/fail（落容差内）。

## Step 5：跑回归验论文主表性能（用户拍板容差）

**回归标准 = 能复现论文主表的性能**（基准是 CPE full-scale 真数）。

**用户拍板容差**：agent 按 metric 类型推荐默认（分类 top-1 ±0.1~0.3、检测 mAP ±0.2），用户最终拍板。

三关：
1. **conda 复现主表**（第一道必过关）：干净 conda + 发行版代码 + 发布权重复现主表 → 比对基准容差。**不过不合格，回 Step 2 查抽取/重写哪里漏了或改坏了。**
2. **Docker B 复现主表**（确认封装无偏差）：镜像 B 挂权重复现 → 比对基准容差。
3. **Docker A smoke**（确认训得动）：镜像 A 挂数据跑训练 → 环境对、loss 降、出 checkpoint。

**对外比对 PDF**：release repo 复现的主表 vs 论文 PDF 主表，落用户拍板的容差内。**这是 follower 视角的真实验收**——读者拿 PDF + 发行版能不能复现论文数字。

**不一致排查**：
- 回归挂了（repo 复现 ≠ 基准）→ 抽取/重写漏了（回 Step 2），或基准汇总错了（重对 CPE 数据包）。
- 对外对不上（repo 复现 ≠ PDF）→ CPE 数据本身问题（回 CPE），或论文主表誊写问题。

## Step 6：门面定稿 + 权重发布

1. **README.md / AGENTS.md 定稿**：Step 2 的骨架回填——命令链逐条换成 Step 5 回归实测过的命令，主表数字照 PDF（已核过），训练资源从 `pkg-meta.json` GPU-hours 台账拿。两份文件命令必须一致。
2. **权重发布**：发布用 checkpoint 上传 Hugging Face Hub（或用户指定存储），记录下载链接 + sha256；链接回填 README / AGENTS.md / `perf-baseline.json` 的 `reproduce.checkpoint`。
3. **LICENSE**：用户拍板哪种（MIT / Apache-2.0 / ...），落 `LICENSE` 文件；README 挂 bibtex 引用块。

## Step 7：防泄露自查 + GitHub 开源

**防泄露自查**（对内施工图痕迹绝不能漏到对外）——人工核对 + 机扫双管：

- git history 干净（全新仓库、开发期 commit 无内部信息）。
- 无其他分支 / 被否 idea / 未发表方向的代码目录注释。
- 无施工文件：`claims.json` / `00-04-*.md` / `idea_tree.json` / `experiments/` 台账。
- 无 `runs/` 残留、无死代码、无定义未用参数。
- **机扫清单**（开源前必跑，结果记进 RELEASE_REPORT）：
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

1. 更新 `RELEASE_REPORT.md`（按 `release-report-template.md`）：节点认定、基准、三关回归、对外验收、防泄露自查（含机扫结果）、权重发布。
2. **开源前清理（必做，防泄露）**——`RELEASE_REPORT.md` 含内部信息，开发期 commit message 也可能带内部痕迹。agent 列清理清单（删 `RELEASE_REPORT.md` 留底到 repo 外 / 删 `.git` / `git init` / 首个 commit = 干净开源版）→ **用户确认** → agent 执行。
3. push GitHub（公开/私有用户定），论文挂这个 repo 地址。
4. 汇报：发行版已开源，**自带回归测试 + 已验过论文主表性能**（闭环），follower 拿 PDF + repo 能一键复现主表。

## Step 8（可选，默认推荐）：GitHub Pages 项目页

顶会论文的项目页是 follower 第一入口。repo 开源后做一页**高级、美观的科研展示页**，放在**同仓库 `docs/`**（GitHub Pages 从 main 的 `/docs` 开）——follower clone 一次代码和页面全有，用户开一下仓库设置即可访问。

**内容来源**：agent 组装初稿——标题/作者/abstract/bibtex 从论文 PDF 提，主表从 `perf-baseline.json` 提，定性图从 CPE 数据包 `figures/` 提；teaser 终稿图、demo 视频等论文终稿素材**用户给**，agent 不自己造。

**制作原则**（只定原则，具体设计 agent 发挥、用户审美裁决）：

- **目标是展示，不是文档**——一页让人看懂「这是什么工作、效果多好、怎么引用」；排版美观优先，纯静态或带交互均可。
- **单文件自包含优先**——`docs/index.html` 为主，不引重型框架；交互需要时可用 vanilla JS 或 CDN 轻量库。
- **媒体策略写死**：图片、小视频、小音频直接进 `docs/` 随仓库走；**大视频传 YouTube 嵌 iframe**，大音频同理外链——repo 不被媒体文件撑肥。
- **内容严格 follower 视角**——页面只含 PDF + 发行版已公开的信息，防泄露要求同 Step 7。
- **用户审完再公开**——内容/素材/美观由用户裁决，审过才开 Pages（Settings → Pages → main `/docs`），给 URL 并回填 README 链接。

## 验证原则（贯穿）

- **基准用 CPE full-scale 真数**：从 CPE 数据包 results.json 汇总，不做占位。
- **conda 是第一道必过关**：HPC 无 Docker 权限，发行版必须 conda 独立跑通主表。
- **A/B 验证不对称**：A 验训得动、B（挂权重）验推得准。
- **容差**：agent 按 metric 类型推荐默认，**用户拍板**。
- **repo 自带回归测试**：交付即闭环（已验性能不掉），不是临时动作。
- **双门面同真相源**：README（人读）与 AGENTS.md（agent 读）的命令链都来自 Step 5 实测，改一处同步另一处。
