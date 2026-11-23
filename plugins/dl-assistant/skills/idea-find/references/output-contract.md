# 产出契约：目录 / spec.json / 落盘次序

这一份管**三个阶段共同使用的规则**——目录怎么摆、决策日志 `spec.json` 长什么样、落盘按什么次序、谁写哪个文件。主会话和子 agent 落盘前都以这里为准。

**单个落盘文件的字段模板不在这份**——它们跟着各自的干活流程走：找方向流程在 `direction.md`、七个文件模板（seed-card / pitch / survey-channel / literature / 方向-main / 方向-importance / 方向-verify）在 `templates/direction-*.md`；挖方法流程在 `method.md`、三个文件模板（note / 路线-main / 挑错）在 `templates/method-*.md`；spec+plan 草稿 + 两层 初始 claim 树在 `spec-draft.md`。派子 agent 时，只把它要写的那个模板文件连同路径一起放进 prompt。

> **语言总规范**：所有落盘文件的正文（md 正文、json 字符串值）一律**中文**；论文名 / 方法名 / 数据集 / 指标 / 代码路径等专有名词保留英文。论文标识——通用规范见 `dl-assistant` SKILL.md「所有技能共用的规则」。

---

## 一、目录结构

一轮 idea-find = 一个 idea 文件夹，**保存目录写死 `<项目>/docs/idea-find/`**（Step 1 不再问用户）。产出是跨机器交接物（GPU 上 execution 要读 spec+plan 草稿），需要时找用户弄过去（跨机器交接通用规范见 `dl-assistant`）。

**机读 / 人读分工**：中间产物里流程化消费、用户一般不读的写 **JSON**（`spec.json`、`idea-seed.json`、`survey-channels/*.json`、`literature.json`、`-importance.json`、`-verify.json`）；叙事性论证和最终交付留 **Markdown**（pitch、方向/路线 main、深读 note、问题清单、specs/ 草稿）。

```
<项目>/docs/idea-find/
└── <日期>-<topic-slug>/                  # 如 2026-07-01-video-temporal-referring/
    ├── spec.json                          # 决策日志：起点/雏形卡 + pitch 决策 + 每次讨论的拍板决策（机读）
    ├── idea-seed.json                     # 雏形卡（Step 1 通过对话明确问题产出，含 wedge 资源与专长；schema 见 templates/direction-seed-card.md）
    │
    ├── layer1-方向/
    │   ├── pitches/                       # Step 2 初步构想清单：一 pitch 一份，未保留的构想也留（带杀的理由）
    │   │   ├── pitch-1-<slug>.md          #   （schema 见 templates/direction-pitch.md）
    │   │   └── pitch-2-<slug>.md
    │   ├── survey-channels/               # Step 3 调研通道子 agent 原始产出（一通道一份）
    │   │   ├── fresh.json                 #   查阅近 12 个月的工作 + 记录已发表的相关工作（schema 见 templates/direction-survey-channel.md）
    │   │   ├── closest.json               #   最接近工作评估 + 引用追踪
    │   │   └── negative.json              #   方法可能行不通的证据 + 跨域现成解法
    │   ├── literature.json                # 文献台账 + 空白矩阵（主会话合并通道结果；记录各候选问题已有的研究及其完成程度；schema 见 templates/direction-literature.md）
    │   ├── 方向1-<slug>/                  # 一方向一子目录
    │   │   ├── 方向1-<slug>-main.md       #   主会话成型（Step 4）→ 充实子 agent 更新（问题侧）
    │   │   ├── 方向1-<slug>-importance.json # 重要性独立预审（Step 5，schema 见 templates/direction-importance.md）
    │   │   └── 方向1-<slug>-verify.json   #   充实子 agent 的查重留痕
    │   └── 方向2-<slug>/
    │       ├── 方向2-<slug>-main.md
    │       ├── 方向2-<slug>-importance.json
    │       └── 方向2-<slug>-verify.json
    │
    ├── papers/                            # 论文库：一论文一子目录，pdf + note 同处，可跨方向复用
    │   ├── <论文A-slug>/
    │   │   ├── <论文A-slug>.pdf           #   源文件（Step 8 按方向下载 / 挖方法阶段增量补）
    │   │   └── <论文A-slug>-note.md       #   深读证据笔记（schema 见 templates/method-note.md）
    │   └── <论文B-slug>/
    │       ├── <论文B-slug>.pdf
    │       └── <论文B-slug>-note.md
    │
    ├── layer2-<方向slug>/                 # 只为选定方向开；多方向各一份、互不覆盖
    │   ├── 路线1-<slug>/                  # 一路线一子目录
    │   │   └── 路线1-<slug>-main.md       #   主会话建骨架（Step 10）→ 细化子 agent 做实（方法侧）
    │   ├── 路线2-<slug>/
    │   │   └── 路线2-<slug>-main.md
    │   └── 挑错/                          # 独立检查方案跨路线（按视角切，不属于任何单条路线）
    │       ├── 挑错-feasibility.md
    │       └── 挑错-assumption.md
    │
    └── specs/                            # 准 spec+plan 草稿 + 初始的两层 claim 树：一方向三份
        ├── <方向slug>-idea-spec-draft.md
        ├── <方向slug>-idea-plan-draft.md
        └── <方向slug>-claim-tree-draft.json
```

**为什么这样分**：

- `pitches/` 保留**全部** pitch（含未保留的构想）——候选构想清单是由用户筛选构想的第一现场，未保留的构想带着理由是复盘素材，也是 pitch 已被前人充分解决时回 Step 2 重新考虑未选的候选的池子。
- `literature.json` 是**文献台账**（分组 + 空白矩阵 + 最接近评估，覆盖所有用户保留的 pitch，机读）；`papers/<论文>/<论文>-note.md` 里的证据笔记是**深读产物**（一论文一份，主会话按需回取）。台账 + 深读笔记，对应"摘要走上下文、全文留磁盘"。
- `survey-channels/` 保留各通道子 agent 的**原始产出**——合并是主会话做的，原始件留着才可审计"合并时丢了什么、改判了什么"。
- `papers/` **一论文一子目录，PDF 和笔记放一起**——换方向做挖方法时，同一篇论文的 PDF 和深读笔记直接复用，不重下、不重读。这是"零信息损失"的复用红利。
- `layer1-方向/方向N-<slug>/` 和 `layer2-<方向slug>/路线N-<slug>/` **一个方向/路线一个子目录**——该方向/路线的所有产物（正文、查重、将来可能追加的东西）集中在同一个目录，方便核对和补充。
- `layer2-<方向slug>/` **按方向命名**——同一份找方向产物可喂养多个方向的挖方法（串行），各自独立落盘、互不覆盖。
- 挑错放 `layer2-<方向slug>/挑错/`——它按视角切、检查全部路线、不属于任何单条路线，所以独立成目录。
- `specs/` 单独成目录——可能同时为多个方向产 spec+plan 草稿，集中放一处。

---

## 二、落盘次序 + 谁写谁

**落盘次序**（每一步的产出即一个文件）：

1. Step 1 主会话 → 建文件夹 + 起点对齐（venue/资源硬门槛）+ 确认可用资源与专长 + 检查已有的研究线索 + 通过对话明确问题 + **判断从哪一步开始**（fast / divergent / red-light-exit）→ 写 `idea-seed.json` 雏形卡（含 wedge + entry_track）+ 写 `spec.json` 起点段。
2. Step 2 **主会话**（**已有成型构想跳过**：用户成型 idea 直接记录到 pitch-1，来源: 用户）→ 仅有大致方向：**先收集用户提出的 pitch** → 产主会话补充候选（池子总量 5-8 个）→ 各写 `pitches/pitch-N-<slug>.md`（来源字段必填）→ 由用户筛选构想（用户来源的只能由用户本人放弃）→ 未保留的构想在文件末尾记下原因 → 写 `spec.json` pitch 决策段（含用户提出构想的记录）。
3. Step 3 调研通道子 agent×(2-3) → 各写 `survey-channels/<channel>.json`，返紧凑摘要；主会话合并去重（arXiv ID 归一化）→ 写 `literature.json`（分组 + 空白矩阵 + 最接近评估）。
4. Step 4 **主会话**读 literature.json + 用户保留的 pitch → 方向成型 → 各建 `方向N-<slug>/` 子目录、写 `方向N-<slug>-main.md`（三项必填内容 + 强依赖论文清单）。
5. Step 5 重要性独立预审（1 个）→ 写各方向 `方向N-<slug>-importance.json`（重要性漏洞清单），返结论。
6. Step 6 充实子 agent×N（每方向一个）→ 更新 `方向N-<slug>-main.md`（问题侧充实）+ 写 `方向N-<slug>-verify.json`（查重留痕），返通过/丢弃 + 依据。
7. 讨论①（Step 7）拍板 → 主会话更新 `spec.json`（方向决策段：chosen 方向 + 先挖哪个）。
8. Step 8 → 主会话按选定方向强依赖清单**下载 PDF 到 `papers/<论文>/<论文>.pdf`**，方向文件里标记。
9. Step 9 深读子 agent×N（每篇 PDF 一个）→ 写 `papers/<论文>/<论文>-note.md`，返证据摘要。
10. Step 10 **主会话**读证据摘要 → 全局生成 2-3 条路线骨架（四问 + 先例自检 + 首个验证实验）→ 各建 `路线N-<slug>/`、写 `路线N-<slug>-main.md`。
11. Step 11 细化子 agent×N（每路线一个）→ 更新 `路线N-<slug>-main.md`（方法侧做实），返摘要。
12. Step 12 负责独立检查的 agent×(1-3)（按视角，验证完备性必查）→ 写 `layer2-<方向slug>/挑错/挑错-<视角>.md`，返漏洞摘要。
13. Step 13 主会话按检查结果修改路线 → 更新 `路线N-<slug>-main.md`（v2 + 「问题与修改记录」节）；需要新证据时派补充证据的子 agent（不落新文件，证据追加进对应 note.md）。
14. 讨论②（Step 14）拍板 → 主会话更新 `spec.json`（方法决策段：chosen 路线）。
15. Step 15-17 → 主会话写 `specs/<方向slug>-idea-spec-draft.md` + `specs/<方向slug>-idea-plan-draft.md` + `specs/<方向slug>-claim-tree-draft.json`（初始的两层 claim 树）。

**谁写谁**（并发安全的关键）：

- **子 agent 只写自己那一个文件**——并发不冲突。
- **pitch、方向骨架和路线骨架由主会话先写、充实/细化子 agent 再更新**——生成是判断（主会话全局做），充实是体力活（子 agent 各管一份）。
- **survey-channels/ 是子 agent 的原始产出，literature.json 由主会话合并**——子 agent 不直接写台账，合并/去重/改判是主会话的判断活。

---

## 三、spec.json schema（决策日志 · 承载 pitch 决策 + 两次讨论的决策）

`spec.json` 是**决策日志**（机读，复盘时才翻）：记起点/资源/资源与专长/雏形卡、pitch 用户筛选的过程，以及每次讨论"选了什么、为什么这么选"。

```json
{
  "topic": "{topic}",
  "created": "{日期}",
  "origin": {
    "起点": "一篇论文 / 方法 / 领域 / 现象 + URL",
    "目标会议": "CVPR 级",
    "资源": "8 卡",
    "筹码": "算力 X / 吃透的工具 Y / 独特见解 Z（wedge 摘要）",
    "种子来源": ["paper-card:docs/paper-reading/...", "ls:docs/literature-survey/...", "dt:...", "用户直给"],
    "entry_track": "fast / divergent / red-light-exit——清晰化对话后判定的轨态（fast = 用户带成型 idea 来，跳 Step 2 pitch 池；divergent = 走 Step 2 空场征集 + 补丁池）"
  },
  "pitch_decision": {
    "空场征集": "发散轨 Step 2 开头的征集记录：用户抛了几个 pitch / 用户说没有 / 用户原话摘要（快轨记 '跳过：用户成型 idea 直落 pitch-1'）",
    "产的pitch": ["pitch-1-<slug>", "pitch-2-<slug>", "..."],
    "各pitch来源": {"pitch-1": "用户", "pitch-2": "补丁候选"},
    "用户杀了哪些+理由": {"pitch-1": "不像能发的", "..."},
    "用户补的pitch": ["pitch-6-<slug>"],
    "幸存": ["pitch-2-<slug>"]
  },
  "direction_decision": {
    "展示的候选方向": ["方向1", "方向2"],
    "用户选定": ["d1"],
    "选定理由": "为什么选它",
    "打磨要点": "用户质疑了哪条、主会话补了什么证据、结论怎么变",
    "挖方法次序": "先挖 d1，收敛后再挖 d2",
    "选题理由快照": {
      "基于什么信号": "pitch 三件套（痛点/武器/主表预览）+ gap 证据（literature.json 哪格空白）+ 重要性判断（预审结论）+ 趋势位置（生命周期哪段）",
      "预期": "当时判断做成什么样算成——如 C1 成立 + 主性能 +X",
      "当时承认的风险": "哪些不确定性是明知仍选的"
    }
  },
  "method_decisions": {
    "d1": {
      "展示的候选路线": ["路线1", "路线2"],
      "挑错关键漏洞": "各视角清单摘要",
      "用户选定": "r1（+ 一起打磨中怎么改的）"
    }
  }
}
```

> `pitch_decision` 和 `选题理由快照` 必写——这两段是选题复盘的唯二对照物，不写它们，复盘时"当时怎么想的"就只剩记忆偏差。`spec.json` 记的是**判断的过程**：由用户筛选构想和一起打磨留下的痕迹，比结论更值钱。
