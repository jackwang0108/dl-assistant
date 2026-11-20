# 网络与镜像策略（跨 skill 共享）

> 中期 skill（`code-project-setup` / `code-paper-reproduction` / `code-idea-execution`）在国内 GPU 服务器上跑，
> 都要面对 GitHub / HuggingFace / PyPI / conda 的可达性问题。这份讲**通用网络策略**——
> 怎么探网络、配代理 / 镜像、直连失败怎么交接。各 skill 在自己的 Report 里记录本次采用的策略值。

## 进长任务前先探网络

避免后续装包 / 下载反复失败。检查可达性 + 现有代理 / 镜像配置：

```bash
# 可达性
curl -sI https://github.com | head -1
curl -sI https://huggingface.co | head -1
curl -sI https://pypi.org | head -1

# 现有配置（别急着改，先看）
env | grep -iE 'proxy|hf_endpoint|pip_index'
conda config --show channels
git config --get http.proxy
which aria2c wget curl 2>/dev/null
```

## 原则

- **默认用临时环境变量或项目内配置**（`export`、`.env`、项目的 pip.conf），**不擅自改全局**
  （`~/.condarc` / `~/.gitconfig` / shell profile）——全局配置影响服务器上所有人 / 所有项目。
  需持久写全局**先问用户**。
- Report 记录本次采用的代理 / 镜像 / 下载策略（哪些资源走镜像、哪些 blocked）。

## 常用镜像 / 加速（结合实际网络验证可用再用）

```bash
# HuggingFace 镜像（权重 / dataset 下载）
export HF_ENDPOINT=https://hf-mirror.com

# PyPI 镜像（pip 装包）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <pkg>

# conda 频道（按需，谨慎改全局 channels）
```

> 镜像源会变、会挂——上面是常用候选，**实际用时先 curl 探一下通不通**再用，别盲信。

## 直连下载失败的处理

**不反复盲试**（重试几次还失败就别耗），立即把可手动执行的命令 / URL 交给用户：

```text
直连下载失败。请手动执行（或换网络 / 代理后重试）：
  <失败时的完整命令 / 下载 URL>
完成后告诉我，我继续验证。
```

## blocked-by-network 标记

检测到无代理 / 镜像、且某资源直连失败时，Report 把该资源标 `blocked-by-network`，
**不因网络阻塞环境安装之外的流程**（其他不依赖该资源的步骤照跑）。

> 边界：网络问题只是"下不到 / 装不上"，不是"跑不通"——别把网络阻塞当成代码 / 环境本身的故障。
