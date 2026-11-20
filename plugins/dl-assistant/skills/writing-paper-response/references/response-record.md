# 意见、行动与回复记录（schema_version=2）

保存response-state.json；输入改变后保留旧快照并更新，不覆盖旧交接目录。路径相对记录所在目录或绝对路径，sha256须来自实际文件。无需为每次讨论制造多个重复报告，结构化记录及必要说明即可。

## 输入和范围

- response_id唯一；stage=plan/handoff/final。paper_root为实际论文项目目录，只有交付改稿行动时必须明确；PDF可能在编译目录，不能据其所在文件夹猜项目根。
- paper：{path,sha256}为被评论稿件；current_paper同结构，可null表示仍以原稿回复。不是永远以新稿覆盖旧稿。
- sources：[{id,kind,path,sha256}]。kind=review/comments/manuscript/evidence/research_record/execution_record/policy/authorization/verification/analysis；ID唯一。核查意见、实际完成和官方规则时指向实际来源，不凭文件名认定内容。
- scope_comment_ids：本次实际处理的原意见ID，可是部分；原意见仍完整登记，范围外自动列not_checked。
- comments：[{id,source_id,source_item_id,location,text}]。source_item_id指review清单problem ID，普通原文可null。review来源必须是指定schema2 problem-list并与paper.sha256匹配，其全部问题都登记为comments，再用scope选择本轮范围；不能先删掉不想处理的问题。真实审稿/内部意见直接保存原文，不伪装模拟清单。

## units：可独立判断的关切

每项{id,comment_ids,concern,assessment,disposition,rationale,action_ids,coverage_status,scope_change}。

assessment含finding_status、reasoning、evidence_refs、unknowns、prior_belief、observation、updated_belief、core_unresolved。finding_status=confirmed/partially_supported/unsupported/unverified，判断对象是意见，不是无条件接受上游标签。evidence_refs每项{source_id,location,observation}，支持缺失范围或图表/公式，不强制逐字原句。

disposition=clarify/edit/supplement/research/not_adopt/defer；类别只供组织，core_unresolved为真时用research/defer并保留未决。coverage_status=unaddressed/partially_addressed/addressed/unresolved；addressed只指关切已回应，不等于科学解决。scope_change为真时另有value_reassessment，说明范围变化后新增、价值和剩余未知，并触发impact_checks。

## actions：实际处理工作

每项{id,unit_ids,owner,kind,description,target,acceptance_criterion,depends_on,approval,status,outputs,verification,reason}。

owner=writing-paper/code-idea-iterate/writing-paper-submission/writing-paper-response；kind=text_edit/visual_edit/supplementary_evidence/research_decision/compliance_check/reply_only。research_decision归iterate，其余依实际职责；response只交研究目标，不越权设计/执行核心实验。

approval={status:pending/approved/declined,basis,source_refs}。既有授权可沿用并记录，不额外要求每条签字；不能由沉默或讨论过推导approved。

status=proposed/approved/in_progress/completed/verified/blocked/cancelled；阻塞/取消写reason。outputs为实际来源ID数组，verified需outputs和verification。verification={status:pending/passed/failed,source_refs,basis}，passed需可得核查材料，且实际完成与验收吻合；元数据不能代替读材料。

completed指产物已完成但尚未核查；verified指已按此行动验收，不能推出全部研究成立。失败核查不标verified，历史完成事实保留在旧快照/实际来源记录，新任务不抹掉旧实验。

## replies：按关切组织的回复

每项{unit_id,status,statements,check}，status=draft/checked。statements每项{id,kind,text,evidence_refs,action_ids}，kind=position/evidence_statement/completed_action/planned_action/limitation。文本由这些语句渲染，额外加入事实后也要重新核查。

completed_action要求关联行动全部verified；planned_action要求已获相应批准，且语句明确未来和限制。evidence_statement需实际证据。source/action存在只证明引用完整，脚本不能判句子与材料真正相符，check必须读取语义与上下文。

## 跨意见影响、冲突与三处自查

impact_checks每项{id,trigger_unit_ids,affected,check}。affected每项{kind,id,reason,status,evidence_refs}；kind=reply/action/paper_section/claim/visual/research_record，status=pending/reviewed/updated/not_affected；reply/action的ID须指本记录真实对象。范围/主张/条件变化时列影响并说明处理，不只写“已检查全文”。

conflicts每项{id,unit_ids,action_ids,description,status,decision,evidence_refs}，status=unresolved/resolved；已解决需实际决定与依据。不能让相互冲突的方案同时标可执行。

self_checks含plan/handoff/final三个位置，每项{status,basis,unknowns,effect}，status=clear/limited/needs_revision。plan阶段只强制plan检查，handoff增加handoff，final三项皆需。关键缺陷needs_revision使当前输出保留partial；limited说明为何仍能进行指定行动。不需要额外独立JSON或子agent。

## 官方规则、输出与边界

policy={status:verified/unknown/not_applicable,source_refs,scope,reason,planned_actions_allowed}。verified需实际policy来源；允许的承诺、字/页数等仍需读官方要求，脚本只核声明和引用。final计划承诺仅在明确批准且适用规则允许时保留；不能用它代替当前证据。无目标或内部回复可not_applicable并说明原因。

检查脚本生成不可变response-state.json交接快照、response-map.md、revision-brief.json、rebuttal-letter.md、validation.json。快照中的材料路径改为实际绝对路径，revision-brief.response_ref指向该快照及校验值；后续更新当前记录不改写已批准交接版本。源材料仍须按项目约定保留，快照不等于备份了所有原始大文件。plan为partial讨论材料，不派任务；handoff输出已批准且就绪的writing-paper行动，未就绪项保留原因；final逐项核指定范围、回复与行动、跨意见状态/规则，未解决科学问题可如实回复，不要求强行关闭。

revision-brief保留旧中文字段并新增schema_version/response_ref/paper快照、item id/unit_ids/approval/status/depends_on；使用新ID去重/接续，不按数组顺序推导已批准或重复启动。writing-paper回传{response_id,action_id,status,outputs,verification,当前稿版本/位置}，response读实际文件再更新，不只采信口头“改完了”。

退出0：所声明当前阶段的记录检查完成；1：结构/引用/版本/状态矛盾；2：用法错误；3：plan或未就绪/部分完成。输入错误不生成交接目录；输出目录已存在则拒绝覆盖。0不证明自然语言真实性、官方合规、科学判断或已发送。
