# 落盘契约

一个方向 = 一个 `track-<方向slug>/` 常驻夹,**每次 run 更新同一个夹子**(累积,不是按日期摊)。

## 目录树

保存目录写死 `<项目>/docs/direction-tracking/`:

```
docs/direction-tracking/track-<方向slug>/
├── config.yaml       方向配置(用户可手改)
├── seen.jsonl        已拉过的论文全清单(带源,去重真相源,含被漏斗砍掉的)
├── library.md        累积库:只收通过漏斗的论文(digest 条目格式,随时间长大)
├── runs/<日期>-<HHmm>.md   每次 run 的 digest(带时间,同日多次 run 不互相覆盖)
└── meta.json         last_run 水位 + 进度索引
```

## config.yaml（用户可手改）

```yaml
direction: "一句话说清这方向在研究什么"
keywords:                # 关键词(主匹配,A 源用)
  - referring expression segmentation
synonyms:                # 同义词组(可选,治术语漂移;每组内 OR)
  - [referring image segmentation, RES]
seeds:                   # 起手 2-5 篇种子 arxiv ID(B 源用);可演化——run 时 skill 提名、用户确认才加(防引用网络漂移)
  - 2304.07899
  - 2305.01511
created: 2026-07-13
```

`<方向slug>` 从 `direction` 生成,用户可改。用户后续可加 / 删关键词、种子(配置演化)。

## seen.jsonl（去重真相源，带源）

每行一个 JSON,**所有拉过的论文都记**(含被漏斗砍掉的):

```json
{"id":"2406.12345","source":"A:referring expression segmentation","date":"2026-07-13"}
{"id":"2407.00123","source":"B:2304.07899","date":"2026-07-13"}
{"id":"2405.00077","source":"C:CVPR2026","date":"2026-07-13"}
```

- `source`:`A:<关键词>` / `B:<种子ID>` / `C:<会议年份>`。
- **accepted 还是 rejected 不单独存**:在 `library.md` 里 → accepted;不在 → rejected。可推导,不存冗余状态。
- **dedup key**:`id` 优先 arxiv ID;无 arxiv 版本的极少数会议论文 → 标题哈希 / DOI(标 `id: "titlehash:..."`)。

## library.md（累积库，人 + 下游读）

累积所有通过漏斗的论文,按 run 时间倒序追加。每篇一个 digest 条目(见下)。`idea-find` 把它当种子富矿扫。

## runs/`<日期>-<HHmm>`.md（本次 run digest）

本次 run 新进的论文(通过漏斗、本次首次进 library),同 digest 条目格式。**文件名带时间,同日多次 run(如上午增量 + 下午跑 C)不互相覆盖。**

结构:开头一段总览(这批新论文长啥样:几篇、哪几个子主题、整体信号)→ digest 条目 → 末尾**「交棒候选」节**(3-5 篇,arXiv ID + 具体推荐理由,供 `paper-reading` / `idea-find` 直接消费)。

## digest 条目格式（canonical，library 和 runs 都用）

```markdown
### <标题>
- arXiv: <id> — https://arxiv.org/abs/<id>
- 来源: <A 关键词 / B 种子ID / C 会议年份>
- 为啥相关: <一句话,R1 给的>
- 量化: <baseline 年份·数量 / SOTA / 规模 / 可复现,R2 给的;C 调轻>
- 值得深读   # 可选 flag,值得交棒 paper-reading 的标
```

## meta.json（续跑恢复 + 进度索引）

```json
{
  "slug": "referring-segmentation",
  "created": "2026-07-13",
  "last_run": "2026-07-13T14:30:00Z",
  "total_seen": 0,
  "total_library": 0
}
```

## 落盘次序（一次 run）

1. **抓取**(A / B / C)→ 候选合并去重;**新 ID 即刻追加进 `seen.jsonl`**(增量不重跑的保证——被砍的也已记下,下次不再拉)。
2. **漏斗**(R1 → R2)→ 通过的进 `library.md` + `runs/<日期>.md`。
3. **最后**更新 `meta.json`(`last_run=now`、counts)。

被 R1/R2 砍掉的:已在 step 1 进 seen,**不进 library**。
