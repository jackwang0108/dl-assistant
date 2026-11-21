export const meta = {
    name: 'paper-review',
    description: '模拟投稿同行评审：按投稿领域分配 N 个独立黑盒 reviewer（通才+偏向×评审哲学双分化，组合从池子选不固定）并行深读 PDF + 检索对比，按刻度锚点子维度先行打分；1 个魔鬼代言人（不受防火墙约束）专攻致命指控；可选 1 个合规审稿人对照 authorkit 查 desk reject 项；1 个 AC/AE 对照原文核查 + 裁决指控 + 区分度检查，综合 meta-review 与录用倾向。子 agent 各自审完即落盘（防中途崩丢），主会话只汇总 problem-list。',
    phases: [
        { title: 'Review', detail: 'N reviewer + 魔鬼代言人（+可选合规）并行：黑盒深读 PDF + paper-search 检索 + 锚点打分' },
        { title: 'Meta', detail: 'AC/AE 对照 PDF 核查 + 裁决指控 + 区分度检查 → meta-review + 录用倾向' },
    ],
};

// ── 入参（由 SKILL Step 1 准备好后经 args 传入）──
// args.pdfPath             : string   —— 论文成品 PDF 的本地绝对路径（reviewer 黑盒唯一论文输入）
// args.reviewDir           : string   —— 落盘目录 <paper根>/review/ 的绝对路径（子 agent 各自审完即落盘）
// args.venue               : string   —— 目标会议/期刊（如 "CVPR" / "TPAMI"）
// args.subjectArea         : string   —— 投稿领域/track（真实会议按领域分配审稿人；reviewer/AC 背景锚定该领域）
// args.venueForm           : string   —— 对应 references 文件的评审表单内容（运行时注入，决定 schema 真实维度/刻度）
// args.firewallForm        : string   —— fairness-firewall.md 全文（公正性防火墙，reviewer 写 weakness 时过墙）
// args.calibrationForm     : string   —— calibration.md 全文（刻度锚点 + 打分校准 + AC decision matrix + 区分度检查）
// args.reviewerLeanings    : string[] —— reviewer 专长偏向标签，Step 1 从偏向池组合推荐后传入，长度 = reviewer 数
// args.reviewerPhilosophies: string[] —— reviewer 评审哲学标签（哲学池），和 leaning 组合分化防同模型塌缩
// args.leaningForms        : string[] —— 选中的偏向档案全文（references/pool/leanings/*.md），与 reviewerLeanings 平行；缺省退化为标签
// args.philosophyForms     : string[] —— 选中的哲学档案全文（references/pool/philosophies/*.md），与 reviewerPhilosophies 平行（按取模后的 index 对齐）
// args.enableDevilAdvocate : boolean  —— 魔鬼代言人开关，缺省 true（用户 Step 1 可关）
// args.authorkitPdfPath    : string?  —— authorkit 自带说明 PDF 路径；给了就启用合规审稿人（desk reject 视角）
// args.reviewSchema        : object   —— 按 venue 真实维度/刻度定的 REVIEW schema（SKILL 按 venueForm 实例化后传入）
// args.metaSchema          : object   —— 按 venue 真实录用机制定的 META schema
//
// ⚙️ 兼容性归一化：不同 Workflow harness 对 args 的注入形式不一致——
// Claude Code 原生 Workflow 把 args 注入为对象；部分接入层（如 zai/glm 等）会把 args
// 序列化为 JSON 字符串注入到脚本全局。直接对字符串解构会得到全 undefined 字段，触发
// 下方必填校验误报。这里统一归一化为对象，对原生环境零影响（typeof === 'string' 为 false
// 时走原 args ?? {} 路径）。
const _args = typeof args === 'string' ? JSON.parse(args) : (args ?? {});
const {
    pdfPath,
    reviewDir,
    venue,
    subjectArea,
    venueForm,
    firewallForm,
    calibrationForm,
    reviewerLeanings = ['偏理论严谨', '偏实验充分', '偏应用落地', '偏 novelty/写作'],
    reviewerPhilosophies = [
        '严苛挑剔——任何主张都要看见证据，默认怀疑，吹毛求疵但讲依据',
        '鼓励创新——重视新视角新机制，宽容验证不充分，愿为冒险工作说话',
        '实用主义——看能不能落地、复现、用得上，重视工程与可复现',
        '理论纯粹——推导要干净、假设要显式、机制要说清为什么 work',
    ],
    leaningForms = [],
    philosophyForms = [],
    enableDevilAdvocate = true,
    authorkitPdfPath,
    reviewSchema,
    metaSchema,
} = _args;

if (!pdfPath || !reviewDir || !venue || !subjectArea || !venueForm || !firewallForm || !calibrationForm) {
    throw new Error('paper-review 需要 args.pdfPath / args.reviewDir / args.venue / args.subjectArea / args.venueForm / args.firewallForm / args.calibrationForm（由 SKILL Step 1 准备）');
}

// ── Step 2：N reviewer + 魔鬼代言人（+可选合规）并行、独立、黑盒 ──
// 黑盒纪律：只拿 PDF 路径 + 评审表单 + 防火墙/校准，绝不给 claim tree / manifest / 作者意图。
// 但黑盒 ≠ 只读这一篇——真审稿人会调动领域知识 + 主动检索同领域工作判 novelty / baseline 公平性。
// 偏向×哲学双分化：N 个都是同一模型，单靠"偏向"会塌缩成雷同意见；加一层评审哲学强制口味分歧。
const reviewerPrompt = (lean, philosophy, leanForm, philosophyForm, i) =>
    `你是 ${venue}「${subjectArea}」方向的一位资深审稿人，正在评审一篇投稿（真实评审按投稿领域分配审稿人——你就是该领域背景的专家）。论文成品 PDF 在本地路径：${pdfPath}。

你是一个能审全文的**通才审稿人**，但带两个分化锚（档案全文如下，按它塑造你的口味与判据——不是各管一段，而是都通读全文、只是口味与确信度不同）：

# 你的专长偏向档案
${leanForm ?? lean}

# 你的评审哲学档案
${philosophyForm ?? philosophy}

confidence 据你对该领域的把握自定。
你看不到作者的任何视角（没有 claim tree、没有设计意图、没有作者解释）——和真实盲审一样，只有这篇 PDF。

# 报告语言（硬约束）
你的报告用**简体中文**撰写；venue 术语、评分维度名、方法名保留英文原文。

# 你要像真审稿人一样工作，分两个动作：

## 动作 A：深读本篇（用 pdf-mcp）
自己按需翻 PDF：\`pdf_open\` 固定 PDF 快照后用 \`pdf_outline\` 看目录定位 Experiment/Related Work/消融在第几页 → \`pdf_search\`（"Table 1"/"compared with"/"baseline"/"ablation"/"GPU"）跳到主表和关键论断 → \`pdf_read\` 读所在页**文字**（baseline 列表/数字/年份大多在文字层，直接读文字最准）；仅当主表排版复杂（多列合并、文字层错乱）才 \`pdf_render\` 渲染整页用看的兜底。**但图必须用看的**：teaser/机制图（通常在 1-3 页）+ 主结果图/定性图所在页**必渲染**——箭头方向、模块对号、图文是否一致，文字层读不出来，真实审稿人会盯图挑。

不是泛泛扫一遍，而是按下面这些**真审稿人会数会挑的具体判据**逐项核——别只给"方法不错/实验扎实"这种空话：

**实验严谨性（数得出来的事实）**：
- **baseline 最新年份**：对比方法里最新的是哪年？比近 1-2 年方法=强；只比 ResNet/YOLO 等多年前烂大街方法=弱信号。
- **baseline 数量 + 是否含 SOTA**：主表横向比了几个？有没有「${subjectArea}」领域公认的当前 canonical 强方法？只比 1-2 个老的、回避强 baseline=可疑。
- **实验规模**：几个 benchmark/数据集、算力投入（GPU 数/训练量/模型规模）。
- **related work 新鲜度**：引文里有没有近期工作？只引老文=可能脱节。

**方法与分析（顶会评判的刀刃，比刷点更重要）**：
- **消融是否避重就轻**：有没有**故意不消融最关键的组件**、只消融无关紧要的来凑数？这是最常见的藏拙手法，重点挑。
- **分析实验有没有 insight**：除了刷点，有没有揭示"**为什么 work**"的分析？还是只有 main table、没有 why？只有主表没有机理分析的工作，significance 要打折。
- **claim 立不立得住**：实验是否充分支撑 claim、有没有过度声称、假设是否过强、指标定义是否标准。
- **story telling**：intro 把问题讲清楚了吗、动机是否成立。
- **图-文一致性**（渲染看图）：teaser/机制图的箭头/模块/标签跟正文说的对不对；定性图有没有只挑好看的、误导性对比。

**⚠️ 可复现性风险（行为信号，客观预警）**：**不开源 + 回避强 baseline + 消融避重就轻**——三者叠加时明确标 ⚠️"复现风险偏高"写进 weaknesses。这是按行为给的预警，不针对任何作者/机构/国别。

## 动作 B：检索同领域工作做对比（用 paper-search）—— 这是判 novelty 和 baseline 公平的硬前提
真审稿人不会只看一篇就下 novelty 判断。你**必须**用 paper-search 主动检索——**以「${subjectArea}」为检索域**（查询带上该领域关键词；novelty / baseline 公平性 / significance 都在该领域内判，不是泛泛全领域）：
- **novelty 核查**：搜这篇的核心思想/方法，看近 1-2 年有没有人已经做过同样或高度相似的事。
  有起点的话追正向引用（谁引了它的前身、做了什么）。"我没见过" 不是 novelty 证据，"检索后确认没人做过" 才是。
- **baseline 公平性**：搜该任务/数据集近 1-2 年的 SOTA，判断作者选的 baseline 是不是 recent / closest / canonical，
  还是挑了个弱的、老的、对自己有利的来比。
- **significance**：这个方向是红海（已 5+ 篇顶会在做）还是有真空白？
检索来的论文标题/结论必须真实来自工具返回，不编造。把检索结论写进你的 strengths/weaknesses/questions。

# 顺带核对参考文献章节（真实审稿人的严谨性检查）：
有没有正式会议/期刊论文却以 arXiv 预印本充当正式引用、条目缺 venue/格式不齐、引用编号与正文对不上——写进 weaknesses/questions。

# 评分纪律（公正性防火墙 + 打分校准）—— 写 weakness 和打分时必须遵守：
- **公正性防火墙**：任何 weakness 先过墙——有七类问题是「缺陷但不致命」（没超 SOTA / 有 limitations / 本可再做实验 / 缺开源 / 写作小瑕疵 / novelty 空口断言 / 没在某数据集验证）。这些**可以写进 weakness 提改进建议，但绝不能当 fatal flaw 来压低分数**。完整清单和用法见下方防火墙全文。
- **打分校准**：致命类（novelty 被检索证伪 / claim 过度声称实验不支撑 / 方法根本性错误 / RW 严重脱节）才降大分；防火墙那七类扣分问题只降小分。**给低分必须在 weakness 里有对应硬伤——低分无依据 = 评审不合格**。完整致命/扣分两分类 + 刻度锚点见下方校准全文。

# 打分程序（防中庸塌缩，硬约束——校准不是把分都往中段赶）：
1. **子维度先行**：先按评审表单逐项打子维度分，每项对照校准全文的刻度锚点给一句话依据；overall 由子维度 + 锚点**推出**——不许直接拍 overall。
2. **对比定位发问**：打 overall 前先回答「这篇相对 ${venue} 典型录用论文和典型拒稿论文，更像哪一边？」，把答案写进报告。
3. **完成度计入**：半成品（实验残缺 / 章节未完成 / 图表占位）→ presentation 与 contribution 子维度必须先低，overall 不许停在中段。
4. **分数要有区分度**：发现了硬伤就必须体现在分数上——不许弱点写一堆、分数全给中段安全分。

# 公正性防火墙（全文）
${firewallForm}

# 打分校准 + AC 决策框架（全文；你用刻度锚点 + 打分校准部分，AC 决策框架供你了解最终怎么被综合）
${calibrationForm}

# 产出（只生成意见，不给修改方案——改怎么改是 writing-paper-response 的活）：
严格按下面这份 ${venue} 真实评审表单的评分维度和刻度评审，输出 summary（公平复述）/ strengths / weaknesses / questions。

# weakness 建档硬门槛（verbatim-quote anti-skim + 可验收条件）：
每条 weakness 必须带：
1. **verbatim_quote**——问题所指的**逐字原文引用 + 页码**。引不出原文 = 没读，这条不许写（汇总时会被机器丢弃）。引用短而准，别整段抄。
2. **close_criterion**——「改成什么样这条就算关闭」的可验收条件（如「Table 2 增加与 X 在 Y 设定下的对比」）。写不出可验收条件的空泛批评（「实验不够充分」式）不许建档——把批评具体化到能验收才是真意见。
（question 是发问不是指控，不强制这两项；锚定具体段落的问题仍应带原文引用。）

# 最后一步（必须做）：落盘
把你的完整评审渲染成 markdown 写到文件 ${reviewDir}/reviews/reviewer-${i + 1}.md，结构：评分表（子维度 + overall + 一句话理由）→ 对比定位 → summary → strengths → weaknesses（每条带 verbatim_quote + location + 过墙标注 + close_criterion）→ questions → confidence → 检索结论 → 参考文献核对（用写文件工具，目录不存在先建）。**落盘完成才算审完**——主会话不代你落盘。

# 评审表单
${venueForm}`;

// ── 魔鬼代言人：不受防火墙约束的「检察官」，唯一任务是找能杀死这篇的指控，条条附证据 ──
const devilPrompt =
    `你是 ${venue}「${subjectArea}」方向审稿团里的魔鬼代言人（devil's advocate）。论文成品 PDF 在本地路径：${pdfPath}。

你的唯一任务：**尽一切可能找到能杀死这篇论文的指控**。你不受公正性防火墙约束——别的审稿人必须校准，你负责把最坏的攻击全部摆出来，自有 AC 逐条裁决哪些成立。你看不到作者视角（和盲审一致），但有 PDF 和检索工具。

报告用**简体中文**撰写（术语保留英文原文）。

# 攻击面（逐项排查，用 pdf-mcp 深读 + paper-search 检索举证）：
- **novelty 证伪**：检索核心思想/方法，找已发表的高度相似工作（附标题/年份/相似点）——最致命。
- **方法根本性错误**：推导错误、实验设置不公平（故意给 baseline 劣势）、指标定义不标准导致结论不可信。
- **claim 过度声称**：intro/conclusion 许诺的，experiment 没兑现。
- **数据/评估问题**：数据泄漏嫌疑、test set 调参嫌疑、评估协议不公。
- **baseline 不公平**：检索该任务 SOTA，查作者是不是挑了弱的/老的来比。
- **复现风险信号**：不开源 + 回避强 baseline + 消融避重就轻三者叠加。

# 纪律：
每条指控**必须附证据**（PDF 页码/章节，或检索结果的论文标题），不许空口指控。宁多勿漏——不成立的由 AC 排除，漏掉是你的失职。

# 最后一步（必须做）：落盘
把指控清单渲染成 markdown 写到 ${reviewDir}/devil-advocate.md（每条：指控类型 / 指控内容 / 证据 / location）。**落盘完成才算完**。`;

const devilSchema = {
    type: 'object',
    properties: {
        accusations: {
            type: 'array',
            items: {
                type: 'object',
                properties: {
                    type: { type: 'string' },
                    claim: { type: 'string' },
                    evidence: { type: 'string' },
                    location: { type: 'string' },
                },
                required: ['type', 'claim', 'evidence'],
            },
        },
    },
    required: ['accusations'],
};

// ── 合规审稿人（可选）：desk reject 视角，论文 PDF × authorkit 逐项核硬合规 ──
const compliancePrompt =
    `你是 ${venue} 的 desk reject 审查员。论文成品 PDF 在本地路径：${pdfPath}；${venue} 官方 authorkit 说明 PDF 在本地路径：${authorkitPdfPath}（合规要求的权威来源，以它为准）。

用 pdf-mcp 读两份 PDF，逐项核对 authorkit 列出的**硬性要求**：页数、版式与字体、匿名（双盲）、引用与参考文献格式、图表公式格式、checklist 与声明材料——以 authorkit 实际列出为准， authorkit 没写的项不要自创。只报硬合规问题，不评内容质量。

报告用**简体中文**撰写（术语保留英文原文）。

# 最后一步（必须做）：落盘
把合规检查报告渲染成 markdown 写到 ${reviewDir}/compliance-review.md（对照表：检查项 / authorkit 要求 / 论文实际 / 结果 / location + 问题汇总，每条建议 severity：desk reject 级如页数超、匿名泄露 = 致命；版式小瑕疵 = 改进）。**落盘完成才算完**。`;

const complianceSchema = {
    type: 'object',
    properties: {
        issues: {
            type: 'array',
            items: {
                type: 'object',
                properties: {
                    item: { type: 'string' },
                    requirement: { type: 'string' },
                    actual: { type: 'string' },
                    location: { type: 'string' },
                    severity: { type: 'string' },
                },
                required: ['item', 'requirement', 'actual', 'severity'],
            },
        },
    },
    required: ['issues'],
};

// 扇出：reviewerLeanings 长度决定 reviewer 数；魔鬼代言人/合规按开关追加，索引可还原。
const tasks = reviewerLeanings.map((lean, i) => () => {
    const pIdx = i % reviewerPhilosophies.length;
    return agent(
        reviewerPrompt(lean, reviewerPhilosophies[pIdx], leaningForms[i], philosophyForms[pIdx], i),
        {
            label: `reviewer-${i + 1}:${lean}`,
            phase: 'Review',
            ...(reviewSchema ? { schema: reviewSchema } : {}),
        },
    );
});
if (enableDevilAdvocate) {
    tasks.push(() => agent(devilPrompt, { label: '魔鬼代言人', phase: 'Review', schema: devilSchema }));
}
if (authorkitPdfPath) {
    tasks.push(() => agent(compliancePrompt, { label: '合规审稿人', phase: 'Review', schema: complianceSchema }));
}

const results = await parallel(tasks);
const nR = reviewerLeanings.length;
const reviews = results.slice(0, nR).filter(Boolean);
let _idx = nR;
const devil = enableDevilAdvocate ? results[_idx++] : null;
const compliance = authorkitPdfPath ? results[_idx++] : null;
const accusations = devil?.accusations ?? [];
const complianceIssues = compliance?.issues ?? [];

// ── Step 3：AC/AE 综合（吃 N 份结构化 review + 指控清单 + 合规问题，对照 PDF 核查 + 裁决 + 区分度检查 + decision matrix）──
const acPrompt =
    `你是 ${venue}「${subjectArea}」方向的 AC/AE，正在裁决一篇投稿。论文成品 PDF 在本地路径：${pdfPath}。
下面是 ${reviews.length} 份独立审稿意见、${accusations.length} 条魔鬼代言人指控${authorkitPdfPath ? `、${complianceIssues.length} 条合规检查结果` : ''}。

报告用**简体中文**撰写（venue 术语、评分维度名保留英文原文）。

你和 reviewer 同一口径的黑盒——看不到作者视角（claim tree / manifest / 设计意图）。但你手上既有 N 份意见、又有论文 PDF，要像真实 AC 一样**对照原文核查**：
- reviewer 指出的问题是否成立、是否误读了原文（borderline 尤其要自己用 pdf-mcp 翻原文确认）；
- reviewer 之间分歧时，结合原文判断该信谁，不是简单平均；
- 对 novelty / baseline 公平性这类关键争议，可以自己用 paper-search 以「${subjectArea}」为检索域交叉核实 reviewer 的判断对不对。

# 额外动作一：裁决魔鬼代言人的指控（逐条，不许批量略过）
对每条指控：对照 PDF 原文 + 公正性防火墙（下方全文）+ 必要时 paper-search 核实——
- **成立** → 写进 major_points（致命类），problem-list 里标 type=指控成立；
- **不成立** → 记入 meta-review 的「已排除指控」清单，每条写一句为什么不成立。**这份清单对作者有价值——它是 rebuttal 防线的预演，不许省略。**

${authorkitPdfPath ? `# 额外动作二：合规问题分流
合规审稿人的结果（下方）按 desk-reject 级别分流：页数超/匿名泄露这类 → major_points（致命）；版式小瑕疵 → minor_points（改进）。
` : ''}
# 额外动作${authorkitPdfPath ? '三' : '二'}：区分度检查（防和稀泥）
若 reviewer 的 overall 挤在同一分段（如全 borderline）——meta-review 必须显式回答「**为什么这篇不是明显的 accept 或明显的 reject**」，并给出明确倾向。不允许把 borderline 当默认安全出口。评分本身有区分度则注明即可。

按 ${venue} 的真实录用决策机制综合——**不是简单平均分数，而是按下方 decision matrix 三动作（核查意见成立 → 分歧信谁 → 致命硬伤检验）+ 决策表 + AC 准则综合**：
- 会议：出 meta-review + 录用倾向（该 venue 真实刻度，如 accept/borderline/reject 或 SA…SR）；
- 期刊：出 AE 决定信（accept / major revision / minor revision / reject）+ major/minor points 编号清单。

# 公正性防火墙（全文；裁决指控时用）
${firewallForm}

# 打分校准 + AC 决策框架（全文；你主要用 decision matrix 部分综合）
${calibrationForm}

# 评审机制
${venueForm}

# 各审稿意见（结构化）
${JSON.stringify(reviews)}

# 魔鬼代言人指控清单（待你逐条裁决）
${JSON.stringify(accusations)}
${authorkitPdfPath ? `
# 合规检查结果（待你按 desk-reject 级别分流）
${JSON.stringify(complianceIssues)}
` : ''}
# 最后一步（必须做）：落盘
把 meta-review + 录用倾向/决定 + rationale + 评分一览 + 核查与裁决（含**已排除指控**清单）+ 区分度检查 + major/minor points 渲染成 markdown 写到 ${reviewDir}/meta-review.md（用写文件工具，目录不存在先建）。**落盘完成才算综合完**。

# major/minor points 纪律：
每条 point 保留 reviewer 的 verbatim_quote（逐字原文引用 + 页码）并给 close_criterion（「改成什么样这条算关闭」的可验收条件）——reviewer 没给的由你补写；reviewer 引用对不上原文的，整条不成立（按误读处理）。这两条是 problem-list 的必填字段，缺了汇总时会被丢弃。`;

const metaReview = await agent(acPrompt, {
    label: 'AC/AE',
    phase: 'Meta',
    ...(metaSchema ? { schema: metaSchema } : {}),
});

// 子 agent 已各自落盘（reviews/reviewer-N.md + devil-advocate.md + compliance-review.md? + meta-review.md）；
// 返回值供 Step 4 汇总 problem-list.json + 汇报用。
return { reviews, meta: metaReview, accusations, compliance: complianceIssues };
