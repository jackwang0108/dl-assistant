# 自托管部署与内网验证

## 选定可验证的单机服务

先检查已有服务、设备架构、Docker/磁盘与可用内存、网络和当前项目环境。官方文档已弃用单容器部署，但旧 server README 仍有 `wandb/local` 示例；两者不能合并成“任何镜像都可免费长期离线使用”。新部署核对选定版本的实际启动、授权和更新限制；无法取得授权/镜像/兼容版本时记录受阻，不擅自改用云端或安装 Kubernetes。

镜像固定到 tag+digest 并记平台；amd64 镜像在 ARM 机器上需要显式模拟运行，观察不能代替目标 Linux 服务器验证。预先获取镜像和 Python 包，通过允许的方式带入内网。安装阶段允许联网不表示实验阶段依赖外网。数据持久卷、备份及恢复位置明确；已有实例不重建、不删卷、不覆盖其数据库。临时测试用独立容器/项目/卷和本机端口，结束只清理本次生成的资源。

本轮候选与验证结果见 [验证记录](validation-report.json)。那是维护环境的实测范围，不能冒充用户服务器已部署；尚未通过的版本不写进项目为可用版本。

项目非敏感配置建议保存到 `docs/wandb/tracking.json`：

```json
{
  "schema_version": 1,
  "deployment": "self_managed",
  "base_url": "http://wandb.internal:8080",
  "entity": "实际本地团队或用户",
  "project": "实际科研项目",
  "server_image": null,
  "server_platform": null,
  "sdk_version": null,
  "mcp_revision": null,
  "credential_source": "私有配置位置或环境变量名称，不含值",
  "verification": {
    "sdk_write": "not_checked",
    "api_read": "not_checked",
    "mcp_read": "not_checked",
    "restart_persistence": "not_checked",
    "external_network_disabled": "not_checked",
    "evidence_refs": []
  }
}
```

上面的配置仅作示例。填写前请实际核对实例、项目和使用的版本。每项状态可用 passed/failed/blocked/not_checked，记录命令/环境、时间和证据；通过接口查到记录后，仍须单独验证断开外网时能否运行。

## SDK 地址和故障处理

进程环境设置 `WANDB_BASE_URL=<内网实例地址>`，`WANDB_API_KEY` 从该实例取得；使用正常在线记录模式。保留必要的 NO_PROXY（内网主机/地址），不要让外网代理误转内网连接。SDK 初始化前校验实际生效地址，防止仓库硬编码或旧登录配置覆盖；不静默回退 `api.wandb.ai`。

W&B 的 offline 模式只在本地保存待同步数据，不启动可供 MCP 查询的服务。服务不可达时先保留本地实验输出、attempt、预分配 run ID 和日志目录；按此前批准的故障处理方案决定继续还是暂停，记录 offline/pending。补同步前检查实例/项目/run ID 和远端已有记录，防止重复；运行 `wandb sync` 后，仍须独立查询并核对远端记录。同步失败无需重新训练。

## 官方 MCP 独立部署

训练服务器不必运行 MCP；MCP 进程只需能连接相同内网实例。可在 agent 所在机器用 STDIO，通过内网或已授权隧道访问。容器内 localhost 是该容器本身，要用实际可达地址。单容器 W&B 没有 `/mcp` 不代表不能集成：官方 MCP 可以单独运行，不假定旧 server 镜像自带 MCP。

固定已核对源码 commit/安装包及依赖锁定，预装在本地环境，运行时不使用会临时下载源码的 `uvx --from ...@main`。不整包安装官方 skills 覆盖 dl-assistant 的研究规则；本项目已在 `upstream/wandb-primary/` 固定官方 skill 和脚本，按 [适配说明](official-adaptation.md) 选用操作部分。本项目补充实验与运行的对应关系，以及需要保存的验证记录，官方工具负责访问实际数据。

按已核接口配置环境，值来自本地实例，下面不包含任何凭证值：

```text
WANDB_BASE_URL=<内网W&B地址>
WANDB_API_KEY=<通过私有配置注入>
WANDB_MCP_TOOL_PROFILE=models-only
WANDB_MCP_ACCESS_MODE=read-only
MCP_WORKLOAD_PROFILE=local
WANDB_MCP_PROXY_DOCS=false
MCP_ANALYTICS_DISABLED=true
WEAVE_DISABLED=true
```

models-only 只用于实验跟踪，不需要 Weave/Agent Lens/ARIA。禁用外网文档代理和分析遥测是配置步骤，仍须在禁外网条件下验证导入、启动和实际查询；第三方依赖也可能尝试连接。不要宣称仅设环境变量就完成网络隔离。确需上传分析或创建报告时沿用用户已有授权，再启用对应写能力。

维护时查到的官方 MCP 候选 v0.4.3：tag 对象 `33304f18eb24a0ff759f2a481b00e2aaed9f6a51`，解引用 commit `465ea99c421f741187c7b20812a1f5b02de6b792`。这是源码定位，是否可安装/可用以验证记录为准，不将 main 文档当固定版本承诺。主要查询能力为项目发现、run 配置/summary、历史序列、run 比较、Artifact 版本；实际名称、参数与分页限制通过 MCP discovery 核实，不把工具返回的“诊断”当确定机制解释。

## 最小验收

在唯一测试项目中，以 SDK 上传一份明确配置、几步已知指标和一个小文件；通过 API 和 MCP 分别按 run ID 查询，核对记录对应的运行、完整指标数值和产物校验值。关闭外网后重复关键路径；服务重启后再次读取同一 run 和产物。模拟服务不可达，检查本地数据保留以及恢复后的补同步和去重。测试退出码、同步状态和科学数据有效性分别记录。

任何一项未执行或失败，保留具体限制。数据写入成功而 MCP 不兼容时，继续保存 SDK/本地数据并核查官方接口，不伪造查询成功；可用已有 SDK/API 辅助取证并说明来源，但不能称 MCP 已验证。

## 官方来源

- [Server 镜像与旧单机说明](https://github.com/wandb/server)
- [部署与授权说明](https://github.com/wandb/docs/blob/main/platform/hosting/enterprise-licenses.mdx)
- [官方 MCP 源码和配置](https://github.com/wandb/wandb-mcp-server)
- [官方 skills](https://github.com/wandb/skills)
- [SDK 初始化](https://docs.wandb.ai/models/ref/python/functions/init/)
