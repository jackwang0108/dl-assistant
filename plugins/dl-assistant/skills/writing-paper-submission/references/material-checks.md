# 按需调用的材料观察工具

官方要求与人工待办是主任务；辅助脚本不自动查官方指南、不改文件、不编译或安装工具。PDF/日志没有提供时直接交查询结果，不强制调用。

入口submission-check.sh调用同目录submission_check.py（Python标准库，PDF读取使用本机pdfinfo/pdffonts）。仅调用所选检查的工具，缺依赖/超时/输出无法解析如实报告，不自动安装或无限重试。

```bash
bash <skill目录>/scripts/submission-check.sh --pdf <PDF> --checks pages,fonts,metadata
bash <skill目录>/scripts/submission-check.sh --pdf <PDF> --checks pages --page-limit <正整数> --page-scope total --rule-ref <实际官方要求或记录位置>
bash <skill目录>/scripts/submission-check.sh --pdf <PDF> --checks pages --page-limit <正整数> --page-scope main --main-pages <正整数> --main-pages-basis <实际定位/计数依据> --rule-ref <实际官方要求或记录位置>
```

--checks支持pages/references/labels/fonts/metadata，逗号分隔；不传时有PDF则观察页数/字体/metadata，有日志则另查references/labels。--format json可保存机器记录，默认Markdown。输出含实际PDF/日志校验值、选定范围、工具观察和限制；记录原输出并关联所查要求，不把退出0当整体合规。

- 页数先观察PDF总页数；只有明确page-limit、计数口径及rule-ref才比较。正文页数是有依据的人工计数，不从refs起始页机械推算；范围需合理且不得超过总页数，缺依据则待核实。脚本不认证官方口径或定位理由真实。
- 日志仅扫描已识别警告。空、失败或无成功输出标志的日志不报告引用检查通过；日志/PDF对应需--build-record指向真实构建记录，含pdf_sha256、log_sha256、exit_code=0。校验不匹配为错误；未绑定只报告所见日志内容及未知，不当作当前PDF证据。构建记录是声明，不证明来源可信；仍需核实际构建过程。
- 字体报告可解析字体及emb标志，不把工具失败或空输出当全嵌。无字体记录仅报告观察，不代表PDF文本正确/可搜索。若适用官方要求必须嵌入，可用--require-embedded-fonts并提供--rule-ref；否则未嵌字体只作为需结合要求判断的观察。
- metadata完整保留pdfinfo可得字段，不按tex/latex等子串过滤姓名，也不由非空/空直接判身份是否合规。--double-blind旧标志仅要求人工核身份上下文，--camera-ready仅记录阶段，不默认必须填Author或删除Anonymous；两个标志可并用，实际身份要求仍由适用官方规则决定。

结果status为observed（取得有限观察）、meets_declared_rule（符合传入的特定规则）、issue_found（确认所查局部问题）、unverified（检查未完成）或error（输入/工具错误）。没有哪个状态等于整体平台合规。退出0表示所请求观察/有限比较已完成，1表示已发现局部问题或错误，2为用法/参数错误，3为无法完成所请求检查；已发现问题优先于未完成。日志扫描和字体等均有覆盖限制，未见警告不证明完整正确。

## 构建记录示例

先从已核构建结果取得真实退出状态和 PDF、日志路径。可以用 `shasum -a 256 "$paper_pdf" "$build_log"` 取两个实际文件的摘要。确认两份文件来自同一次成功构建后，保存以下字段。

```json
{
  "pdf_sha256": "<所查 PDF 的实际 SHA-256>",
  "log_sha256": "<同次构建日志的实际 SHA-256>",
  "exit_code": 0
}
```
