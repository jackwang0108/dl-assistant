# C：会议 proceedings 抓取

**只考虑 11 个顶会**(其他不做):CVPR / ICCV / ECCV / NeurIPS(NIPS)/ ICML / ICLR / AAAI / ACL / EMNLP / ACMMM / IJCAI。

按 host 分**开放类**和**受限类**。

## host → 会议

| host | 会议 | 开放度 |
| --- | --- | --- |
| CVF(`openaccess.thecvf.com`) | CVPR / ICCV | 开放,好抓 |
| `ecva.net` | ECCV | 开放 |
| `papers.nips.cc` | NeurIPS | 开放 |
| PMLR(`proceedings.mlr.press`) | ICML | 开放 |
| ACL Anthology(`aclanthology.org`) | ACL / EMNLP | 开放 |
| `ojs.aaai.org` | AAAI | 开放 |
| `ijcai.org/proceedings` | IJCAI | 开放 |
| **OpenReview(`openreview.net`)** | **ICLR** | 受限:Cloudflare 反爬,官方 API 要登录 |
| **ACM DL(`dl.acm.org`)** | **ACMMM** | 受限:付费墙 / 登录 |

## 开放类（CVF / ecva / nips / PMLR / ACL Anthology / AAAI / IJCAI）

- 抓 proceedings 列表(各 paper 标题 + 链接)。
- **各 host 每年的 URL / 页面结构会变,不写死**:**首次跑某 venue+年份时先 probe 实际 URL 和页面结构**,再抓,不凭记忆编 URL(防漂移)。
- 映射到 arxiv ID:大多有 arxiv 版本,匹配上就进 seen 去重。**匹配规则**(防误并):标题归一化(小写、去标点、去副标题变体)后相等,**且**至少一名作者姓匹配,才算同一篇;只中一条或都不中 → 标 `unmatched` 留人工看,不硬并。

## 受限类（OpenReview=ICLR / ACM DL=ACMMM）

- **OpenReview**:网站走 **Cloudflare 托管、有反爬**;**官方 API 走通要登录账号**(用户实测告知)。两条路:
  - (a) 用户提供 OpenReview 账号凭证(cookie / token)→ 走官方 API。
  - (b) 不走 → fallback。
- **ACM DL**:付费墙,同 fallback。

### Fallback（抓不到时）

让用户直接给 proceedings 清单(URL / 标题列表 / BibTeX)。
**且 ICLR / ACMMM 论文绝大多数有 arxiv 版本 → A 关键词源会兜住大部分**,C 只作为补充,不必死磕。

## 跨源去重

无论哪个 host 抓到,统一映射到 arxiv ID(优先)进 seen 去重——同一篇被 A 当 arxiv 预印本抓过、又被 C 当会议论文抓到,**只算一条**。少数无 arxiv 版本的 → 标题哈希 / DOI。

---

> 写这页的依据:OpenReview 的 Cloudflare + 官方 API 登录要求是**用户实测告知**,不是凭空写;各 host 具体 URL 模式**不硬编码**,首次用时 probe。
