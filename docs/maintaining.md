# 维护与发布

- `plugins/dl-assistant/skills/` 是插件 skill 源码。保留各 skill 之间的相对路径。
- `mcp-servers/` 包含四个独立 Python 项目。变更依赖时在对应目录更新 `uv.lock`。
- `.agents/plugins/marketplace.json` 声明本地插件来源。更新对外分发的插件时同步检查清单和版本。
- `scripts/setup-mcp.py` 安装依赖并输出设置。用户自己的配置应保存在仓库之外。

## 验证

先按 README 安装并运行 stdio 自检。修改 MCP 时，在对应服务目录运行：

```bash
uv sync --locked --extra dev --python 3.12
uv run --locked --extra dev pytest -q -m 'not live'
```

各服务的联网测试以及 Docling、Overleaf、W&B 的真实服务验证，按各自说明显式开启。跨 skill 文件交接测试：

```bash
python3 -m unittest discover -s plugins/dl-assistant/skills/dl-assistant/scripts -p 'test_*.py'
```

## GitHub 发布

从这份独立 Git 仓库发布。检查暂存文件后提交，创建 GitHub 仓库，再设置远端并推送。公开前由维护者确认自有代码的许可证和第三方材料的分发权限。

W&B 上游资料及许可证保存在 [wandb-primary](../plugins/dl-assistant/skills/wandb/upstream/wandb-primary/SKILL.md)，汇报 skill 保留 [上游 MIT 许可证](../plugins/dl-assistant/skills/research-presentation/LICENSE)。PDF MCP、TeX MCP 的许可证声明见各自 `pyproject.toml`。整体项目的许可证由维护者选定。
