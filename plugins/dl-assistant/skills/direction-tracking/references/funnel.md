# 漏斗：R1 相关性筛 + R2 量化卡 + 合成

## R1 方向相关性筛（命门）

子 agent 分片读摘要(+ 必要时轻量元数据),拿**方向配置**(`direction` + `keywords` + 种子主题)当尺子,判每篇:

- **相关** → 进 R2。
- **不相关** → 砍(已在 seen,不进 library)。

**不打分**,只"相关 / 不相关 + 一句理由"。砍 A 假阳(关键词命中但主题偏了)、B 假阳(引用了种子但主题不沾)。

> 这是本 skill 跟 arxiv-daily 的本质区别:arxiv-daily"方向只置顶绝不丢",本 skill **relevance 是主滤**。

### 派子 agent（R1 分片）

- **派前过用户**:说清"X 篇候选,分 a 片做 R1 相关性筛",点头再发。
- 子 agent 一律 `general-purpose`,禁 `Explore`(要读摘要判相关 + 落盘,Explore 读不了 PDF/写不了文件)。
- 每 shard 输入:一批候选(标题 + 摘要 + 元数据)+ 方向配置。
- 每 shard 输出:每篇 相关/不相关 + 一句理由,**落盘**;返回主会话精简清单。

## R2 量化卡

子 agent 下 PDF 读 Experiment + Related Work,出量化卡:baseline 年份 / 数量、SOTA 情况、实验规模、算力、可复现性。

**判据复用 arxiv-daily round2**(见 `arxiv-daily-paper/references/round2-quantitative.md`),**不重造、不镜像**。

- **C 调轻**:顶会已 peer-review,读摘要 + 元数据做轻量卡即可,不下 PDF。
- 弱 / 不可复现 → 砍。

### 派子 agent（R2 分片）

- **派前过用户**:说清"R1 过了 Y 篇,R2 量化卡分 b 片",点头再发。
- 子 agent 一律 `general-purpose`,禁 `Explore`(要下 PDF 读 Experiment + 落盘)。
- 每 shard 输入:一批候选 PDF(R1 通过的)。
- 每 shard 输出:每篇量化卡(按 arxiv-daily round2 字段),**落盘**。

## 合成 digest（主会话，不是子 agent）

把 R1"为啥相关" + R2 质量要点揉成 digest 条目(canonical 格式见 `output-contract.md`),标「值得深读」flag(交棒 `paper-reading`)。

runs digest 末尾加**「交棒候选」节**:3-5 篇,每篇带 arXiv ID + 具体推荐理由(优先「值得深读」flag 篇 + 种子演化提名篇;推荐理由禁"很相关"式废话,写清为什么值得 PR 深读 / IF 当种子)——flag 散在条目里,汇总成一节下游直接消费更顺。

**不做 full 精读**——精读是 `paper-reading` 的活,本 skill 只标 flag。

---

## 控量（bootstrap / C volume 爆时）

- **bootstrap B**:cap 近 N(默认 ~50,见 lifecycle.md)。
- **C 大会**(如 CVPR ~2000 篇):R1 分片 + 必要时按关键词预筛 / 采样,别整批烧 token。
- **常规增量**:窄方向一周几篇到十几个,通常不用控量。

## 派前过用户 gates

- **常规增量**:漏斗开工前**一次性过**("N 候选,准备 R1×a + R2×b,开跑?")。
- **bootstrap / C 量大**:R1 完加**中途汇报**("X/Y 篇相关,进 R2?")再继续。
