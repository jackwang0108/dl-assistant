# C 类：获取会议论文集

本技能支持以下 11 个会议：CVPR / ICCV / ECCV / NeurIPS(NIPS) / ICML / ICLR / AAAI / ACL / EMNLP / ACMMM / IJCAI。

按网站访问条件分为开放来源和受限来源。

## 网站与会议

| 网站 | 会议 | 开放度 |
| --- | --- | --- |
| CVF(`openaccess.thecvf.com`) | CVPR / ICCV | 开放 |
| `ecva.net` | ECCV | 开放 |
| `papers.nips.cc` | NeurIPS | 开放 |
| PMLR(`proceedings.mlr.press`) | ICML | 开放 |
| ACL Anthology(`aclanthology.org`) | ACL / EMNLP | 开放 |
| `ojs.aaai.org` | AAAI | 开放 |
| `ijcai.org/proceedings` | IJCAI | 开放 |
| **OpenReview(`openreview.net`)** | **ICLR** | 受限：网站受 Cloudflare 保护，官方 API 需要登录 |
| **ACM DL(`dl.acm.org`)** | **ACMMM** | 受限：需要付费访问或登录 |

## 开放类（CVF / ecva / nips / PMLR / ACL Anthology / AAAI / IJCAI）

- 获取会议论文列表，保存各篇标题和链接。
- 网站 URL 和页面结构可能随年份变化。首次查询某个会议和年份时，先核实 URL 和页面结构，再获取列表。
- 多数会议论文有 arXiv 版本。将标题转为小写、去除标点和副标题变体后比较。标题一致且至少一名作者的姓氏相同，才视为同一篇，并按 arXiv ID 写入 seen 供去重。只满足一项或两项都不满足时，标为 `unmatched`，留待人工核对。

## 受限类（OpenReview=ICLR / ACM DL=ACMMM）

- **OpenReview**：网站受 Cloudflare 保护。据用户实测，官方 API 需要登录。
  - 用户提供 OpenReview 账号凭证（cookie 或 token）时，使用官方 API。
  - 无法使用官方 API 时，按下节处理。
- **ACM DL**：需要付费访问，无法访问时按下节处理。

### 无法获取会议列表时

请用户提供会议论文清单，可用 URL、标题列表或 BibTeX。
多数 ICLR 和 ACMMM 论文有 arXiv 版本，A 类关键词查询可覆盖其中大部分。C 类查询作为补充。

## 跨源去重

各来源优先使用 arXiv ID 在 seen 中去重。同一篇论文即使既由 A 类查到预印本，又由 C 类查到会议版本，也只记录一次。没有 arXiv 版本时使用标题哈希或 DOI。

---

> OpenReview 的网站访问限制和官方 API 登录要求来自用户实测。第一次查询某网站、会议和年份时，核实具体 URL。
