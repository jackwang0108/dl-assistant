# 期刊评审参考 · 修订循环派

`writing-paper-review` Step 2/3 用。期刊评审和会议是**两套机制**——不是单轮 accept/reject，而是 **major/minor revision 多轮循环**，AE（副编辑）把关，无固定 deadline。模拟投期刊时，reviewer 和"AC"（这里是 AE）产出的不是"录用/拒"，而是**修订决定 + 必须解决的问题清单**。

## 与会议的根本区别（先理解，再模拟）

| | 会议 | 期刊 |
|---|---|---|
| 轮次 | 单轮（+1 次 rebuttal） | **多轮循环**（审→改→复审） |
| 决定类型 | accept / reject | **+ Major / Minor Revision** |
| 把关人 | AC / 委员会 | **AE（副编辑）→ SE → EIC** |
| 周期 | 几个月、有 deadline | 一年+、无 deadline |
| 作者回应 | 短 rebuttal（限字数） | **详细 response letter，逐条标页码行号** |

## 决定刻度（IEEE Trans 系：TPAMI / TIP / TVCG / TMM / T-RO）

reviewer/AE 推荐之一：
- **Accept**：可直接发表
- **Minor Revision**：基本接受，改小问题，**改后通常不再送审**
- **Major Revision（Reject/Resubmit）**：有价值但有重大问题，**改完同一批审稿人复审**（包括之前给拒的那些）。
- **Reject（不再考虑）** / **Reject and submit to another journal**

**Major Revision 是 IEEE Trans 大多数论文的"成人礼"**。关键事实（写进 AE 人设）：
- 复审由**原班审稿人**做，他们已读过稿子——含糊/回避的回复当场被识破。
- IEEE Trans 系**通常只给一次重投机会**，第二轮要么 accept（或 minor）要么 reject，不再给二次 major。
- response letter 必须**逐条回应、标出每处改动的页码行号、引用每张新增图表**。

## 决定刻度（Springer / 其他：IJCV / IJRR / AURO 等）

EIC 基于 **2+ 审稿人报告** 定 accept / reject / revision。IJCV 双盲、首次决定约 8-15 周。机制同样是 revision 循环，措辞可能是 "Reconsider after Major/Minor Revision"。

## 决定刻度（JMLR：ML 顶刊，开放评审）

JMLR 走 Action Editor（AE）制 + 公开。同样 revision 循环（Accept / Conditional Accept / Reject），AE 综合审稿人意见，强调理论/方法严谨与可复现。

## 模拟产出（写进 Step 3 期刊分支）

投期刊时，"meta-review"应是一封 **AE 决定信**：
1. 推荐决定：Accept / Minor Revision / **Major Revision** / Reject（按目标刊刻度）
2. **必须解决的问题清单**（major points）+ 次要问题（minor points），编号、可逐条回应
3. 提示作者：复审是原班人马，response letter 要逐条标页码——这直接 handoff 给 `writing-paper-response`（它本就产逐条回应 + response letter）。

> 期刊审同样**只审不改**。判定"需要补实验/补理论"的 major point，和会议一样：标出来，交 `writing-paper-response` → `code-idea-execution` 补。
