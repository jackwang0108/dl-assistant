# 系统交接与行为验证

维护共享字段、检查脚本或科学决策规则时按影响选择验证，不因文档改字重复运行全部MCP测试。

## 文件与脚本

```bash
python3 -m unittest discover -s <skills根>/dl-assistant/scripts -p 'test_*.py'
python3 -m unittest discover -s <skills根>/code-idea-execution/scripts -p 'test_*.py'
python3 -m unittest discover -s <skills根>/code-paper-experiment/scripts -p 'test_*.py'
python3 -m unittest discover -s <skills根>/wandb/scripts -p 'test_*.py'
```

`test_system_handoff.py`用同一组合成材料经过研究自查、执行台账、论文实验包和写作数值核查，覆盖目录复制、离线恢复资料缺失、失败后续跑、来源变化和数值来源失效。研究判断和批准是测试输入，不是脚本自动作出的科研判断。W&B两项真实客户端测试默认跳过，需对应环境和明确开关；不能把跳过写成已验证真实服务。

`test_run_long.py`用隔离tmux替代程序验证历史保护、并发启动和退出状态。本次还用独立socket的真实tmux执行了命令与失败退出码检查；不得为测试清理用户tmux服务。

## 实际agent行为

逐例保留原请求、材料、回答、动作说明及实际产物。评估输入不带预期答案；维护者看实际输出与动作，不能只看自查JSON是否通过。

继续评估时使用全新隔离会话和临时目录，给出当前skill与最小原始材料，记录实际模型、权限、完整工具轨迹（若宿主提供）、输入/输出版本和代价。按实际部署模型补测陌生领域、长流程、反复用户“继续”、矛盾证据、关键条件缩减及写作后返回等情境；不需要运行真实GPU任务就能先测研究决定。评价是否定义问题、主动构想与推理、接受反证、重新评价收窄后的价值、保留未知及控制实际动作，不按模板完整度评分。

当前每skill仅一个合成情境、一次运行，所用模型未指定覆盖服务器较弱模型；不能据此宣布研究能力或长期遵守已验证。动作说明是agent自述，已与保存产物核对，但不等于完整工具轨迹。

## 部署检查

安装后核 paper-search、TeX、PDF、Overleaf 的实际工具列表与 capabilities，再做只读验证。源码目录存在时，工具仍可能由旧进程提供。W&B 自托管实例单独配置，并验证 SDK 写入和 MCP 读回。
