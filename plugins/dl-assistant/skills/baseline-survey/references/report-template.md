# 选型报告与执行交接模板

保存 `baseline-survey.json`、`report.md` 和按需使用的 `facts/`。默认日期目录不覆盖新调查，尊重用户指定位置。日期使用本次实际时间，无法确认时保留未知，不能复制示例日期。

本报告记录调查结果、条件推荐与实际决定；不是运行验收。以下是未完成调查的结构示例，null/空数组/未调查状态必须由实际材料逐步填写，不能当作已完成选型。

## baseline-survey.json

```json
{
  "schema_version": 2,
  "direction": null,
  "created_at": null,
  "updated_at": null,
  "intent": null,
  "source_spec": null,
  "resource_constraint": null,
  "requirements": [
    {
      "id": "R1",
      "need": null,
      "mandatory": true,
      "rationale": null,
      "source_refs": []
    }
  ],
  "search_scope": {
    "checked_at": null,
    "queries": [],
    "sources": [],
    "inclusion_reasons": [],
    "exclusions": [],
    "limitations": []
  },
  "sources": [],
  "paper_metrics": [],
  "validation_targets": [],
  "candidates": [
    {
      "id": "B1",
      "repo": null,
      "url": null,
      "revision": null,
      "revision_status": "unresolved",
      "roles": [],
      "repo_role": null,
      "official": null,
      "official_source_refs": [],
      "research_fit": [
        {
          "requirement_id": "R1",
          "assessment": "unknown",
          "finding": null,
          "basis_type": null,
          "source_refs": [],
          "unverified": [],
          "effect_on_choice": null
        }
      ],
      "exec_chain": {
        "train": null,
        "eval": null,
        "data": null,
        "measurement": null,
        "source_refs": [],
        "runtime_validated": false
      },
      "method_insertion_point": null,
      "env_deps": {
        "key_deps": [],
        "compile_risks": [],
        "uncommon": [],
        "source_refs": []
      },
      "weights": {
        "identity": null,
        "url": null,
        "revision": null,
        "config": null,
        "availability": "unknown",
        "aligns_code_version": null,
        "source_refs": [],
        "download_validation": "not_performed",
        "load_validation": "not_performed"
      },
      "dataset": {
        "identity": null,
        "url": null,
        "version": null,
        "split": null,
        "protocol": null,
        "aligns_paper": null,
        "source_refs": [],
        "runtime_validated": false
      },
      "licenses": {
        "code": {
          "terms": null,
          "source_refs": []
        },
        "weights": {
          "terms": null,
          "source_refs": []
        },
        "data": {
          "terms": null,
          "source_refs": []
        },
        "use_constraints": [],
        "unresolved": []
      },
      "community_reports": [],
      "build_cost": {
        "assessment": "unknown",
        "basis": null,
        "unknowns": []
      },
      "adapt_cost": {
        "changes": [],
        "changes_core_method": null,
        "basis": null,
        "unknowns": []
      },
      "eligibility": "unassessed",
      "key_risks": []
    }
  ],
  "recommendation": {
    "status": "needs_more_information",
    "by_use": [],
    "combination_checks": [],
    "repo": null,
    "reason": null,
    "limitations": []
  },
  "decision": {
    "status": "pending",
    "primary_candidate_id": null,
    "repo": null,
    "repo_role": null,
    "components": [],
    "reason": null,
    "user_response": null,
    "date": null,
    "conditions": []
  },
  "self_checks": {
    "requirements": [],
    "recommendation": []
  },
  "verification_tasks": [],
  "revisions": []
}
```

### 需求、来源与候选

- intent用具体目标说明，如原样复现、选择本轮实现、测量分析、数据准备；不按旧idea_form二分类限制目标。source_spec引用实际问题/计划及版本，无草案可null并说明用户目标。
- requirements逐项列R编号、必要能力、来源和是否必要；mandatory=false为偏好。候选research_fit映射这些需求，不只评代码质量。报告不应删除未满足的必要项让推荐看起来成立。
- sources每项含id、kind（paper/code/config/release/community/provided_result）、location（URL或实际文件路径）、revision、accessed_at（带时区）、read_scope。事实引用source_refs，并在finding或facts笔记给精确章节/文件:函数/配置位置；多份来源有不同版本时分别记录。
- repo/url指候选仓库，revision优先准确commit/release revision；revision_status=resolved/unresolved，未固定版本不能宣称复现版本已确定。official为true/false/null，需来源，不能用false表示未知。
- roles数组按实际用途填comparison/implementation/measurement/data_preparation，可多选。repo_role保留baseline/substrate旧名称：只是主要用途的兼容摘要，baseline表示比较方法，substrate表示实验实现/工具；混合或无法诚实概括可null。**验证目标不能仅由该字段推算。**
- research_fit.assessment=supported_by_sources/mismatch/unknown/not_applicable；basis_type=documentation/source_inspection/community_report/provided_run_result，多个依据写多条或在说明中分开。源码可见支持不代表本次运行已验证；provided_run_result须记录原运行条件和来源，不能变成本skill亲自验证。
- 调查完整但必要条件不满足可eligibility=excluded；适合按来源推荐可eligible；关键运行未知但可用明确的准备任务验证可conditional；调查不足为unassessed。eligible也不表示已经可运行或可用于研究结论。not_applicable说明原因，不用来跳过确实必要的要求。
- exec_chain只填实际查到的相关路径，无关路径null并说明不适用；本次不运行，runtime_validated=false。其他已提供结果放来源中，不改成调查已运行。

### 资产、协议与成本

weights.availability=unknown/listed/restricted/not_provided/reported_unavailable，分别表示未查明、发现发布信息、需授权、明确未提供或来源报告不可得。listed不等于完整下载可用；download/load_validation在本次均为not_performed。无需权重时在说明标不适用，不编造链接。

aligns_code_version、aligns_paper为true/false/null：依来源核实的匹配/不匹配/未知，并给依据和静态核查范围，不能由文件名推断。数据版本/split、预处理、排除与指标差异留protocol，运行后的真实性另验。多个权重/数据资产在候选详情中按身份分别列，不把多个版本混进同一条身份记录；需要独立选择时为不同配置建立不同候选ID。

licenses分别记录实际代码/权重/数据条款与针对当前用途的明确限制，未知保留。build_cost可写low/medium/high/unknown及依据；adapt_cost列实际改动与是否改变核心方法，不能只用“小改”掩盖设计缺失。不编造GPU耗时/显存。

community_reports每项记录source_refs、日期、被报告版本/权重/数据/配置/指标、结果、处理状态、是否重复转述及适用限制。没有报告留空并说明搜索范围，不能写成“没有问题”。

### 参考结果与验证目标

paper_metrics仅填实际查到的论文结果，每项含metric、数值/单位、dataset及split、模型/权重/配置、预处理和聚合方式、来源及表格行/位置。不是所有选型都有论文指标；未知不补数字。

validation_targets按验证对象记录id、candidate_id、requirement_ids、要验证的行为/性能、协议、reference及source_refs、适用范围和未知。参考可以是论文行、匹配的发布结果、已知答案或其他有依据的验证；无恰当参照时说明需定义，不随便选model zoo分数。不由仓库角色决定复现目标，不将预测值填成参考结果。

### 推荐、决定与组合

recommendation.status=recommended/needs_more_information/no_suitable_candidate。by_use每项写用途、候选ID、必要需求、推荐理由/来源、替代与不选理由、限制；没有候选可如实不推荐。推荐补调查或先做准备验证时明确行动，不称研究适配已确认。

组合时combination_checks逐项记录组件ID、接口/数据划分/预处理/单位/版本/许可匹配依据、未知及影响。无需组合则空数组。单一候选也可以有多种用途，不强制一个综合排名。

decision.status=pending/selected/declined/deferred；selected只能来自用户实际选择，填user_response、理由、时间、条件及components。每个component含candidate_id、roles、revision、配置/权重/数据身份及对应验证目标；primary_candidate_id可作为主要实现入口，不代表其他组件可以省略。未选择时repo、primary_candidate_id等保持null；“继续调查”不转成selected。

兼容旧入口的decision.repo/repo_role和recommendation.repo仅定位主要仓库，不完整表达组合、条件或验证目标。setup与reproduction已同步需求/多组件/实测任务接收，其他旧消费者仍需核对语义，交接显式说明schema_version=2；若接收方只读旧字段，先核对全部组件/条件，不能丢弃新字段后宣称已兼容。没有主要仓库的纯数据选型可null，不能为了旧字段虚构一个仓库。

### 选型自查与首批实测任务

self_checks.requirements记录需求明确性与来源，recommendation记录研究适配、证据版本、未知分工、推荐与决定。每项含check、status(clear/limited/needs_revision)、finding、source_refs或报告位置、unknowns、effect；直接在本报告保存，不新增自查JSON或脚本。报告已有完整依据可引用，不抄两遍。needs_revision先解决或改为有限调查/准备建议，不能登记为研究已就绪。

verification_tasks每项记录：

- id、candidate_ids、requirement_ids和source_refs。
- known：survey已核实的文件/配置/协议与范围。
- unknown：剩余未知，不写泛泛“确认可用”。
- why_runtime：为何必须下载/加载/运行，不能通过当前调查解决。
- owner：code-project-setup / code-paper-reproduction / code-idea-execution；需先改科学设计则标research_discussion，不作为可直接运行任务。
- check：具体对象、配置/数据条件、要观察什么、依据明确的判定方式及不能证明什么。
- depends_on、资源依据/未知、允许的准备范围、status（pending/blocked/completed等实际状态）、不符合时的return_to。

当前可静态核实但未取得的材料是调查缺口，记在unknowns并说明原因；不能填成一项“实测任务”就视为调查已完成。调查阶段verification_tasks不填本次已completed；后来接收真实验证结果时留独立来源/修订，不覆盖原本未验证的事实。

revisions保存时间、旧推荐/决定、变化原因、新证据与受影响组件。跨机器文件缺失保持缺失，不凭路径声称已取得。

## report.md

```markdown
# 当前任务的代码、模型与数据选型
> 目标、调查时间、代码/资料版本、读取范围与限制；本次未安装、未下载实验资产、未运行。

## 1. 本轮到底需要什么
当前问题/复现目标、所需证据与R需求、必要条件/偏好、资源与用途；调查前适配性自查及未决项。

## 2. 搜索与候选范围
上游/用户线索、查找范围、版本、纳入/排除依据；未覆盖信息及访问失败。一个/多个/无候选均如实说明。

## 3. 按研究需求比较
候选 | 用途 | 对各必要R需求的支持/不匹配/未知及出处 | 关键工程条件 | 未运行部分 | 当前选择影响

## 4. 候选详情及事实来源
研究适配；读到的真实入口/配置/调用关系；依赖；模型/权重/数据身份及协议；分别的许可；社区报告条件；改动/成本依据与未知。

## 5. 按用途的推荐与反对理由
哪个适合复现、哪个适合当前取证或测量；可选组合及兼容条件。agent推荐、尚待查证、没有合理候选时的建议。

## 6. 推荐前自查与实际用户决定
判断—来源/版本—未知—对当前行动的影响；needs_revision如何处理。用户实际选择或pending/deferred，不把推荐填成决定。

## 7. 准备与验证交接清单
主要入口与全部组件：仓库URL/commit、角色、权重/数据/config、来源与未验证条件。
逐项首批实测任务：已知/未知、为何运行、对象/条件、观察/判定、负责人/依赖/资源、不符合时返回位置。
当前仍可调查的缺口单列，不能推给setup冒充实测任务。未运行命令明确为候选入口。

## 8. 版本变化与下一步
调查或实测新证据改变了什么；下一步是补调查、用户选择、准备验证、返回设计还是停止。声明交接格式、实际接收范围及历史记录中尚未核实的映射。
```

调查报告可完成但不推荐任何仓库；有选择也不表示研究已能开跑。后续按实际准备、相应可信度核验、必要代码阅读与批准计划进入execution，不因一份选型报告跳过这些步骤。

## 研究条件核对（与本轮用途有关时）

引用条件记录的路径和版本，写明目标与实际条件、必须保留项的代码/配置/数据位置及检查证据、未知/偏差、所查范围和不能外推的内容。记录下一次目标条件验证的触发点或不适用理由。按本 skill 职责分别说明静态调查、准备、阅读或实际运行，不能将尚待检查项写成已落实；条件或假设变化后重新核对。
