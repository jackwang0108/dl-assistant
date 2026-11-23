# 数据集就绪详述（code-project-setup）

> 对每个数据集把"找 + 下 + 对齐版本 + 转格式 + 改路径 + 构建测试子集 + 验证 loader"跑通，
> 让数据真正能被 repo 的 loader 读到、且和论文协议对得上。SKILL 讲流程，本份讲**常见问题及自动处理方法**。
>
> **基调：自动化优先**——agent 自己查版本对齐、配代理、下、转格式、改硬编码路径、构建测试子集、验证 loader，
> 只在必须人工时停（账号 / license 同意 / 内网 / 链接失效）。用户做科研最痛的就是数据集这一摊破事，
> 本份的目标是让用户尽量不用管。

## 8 类常见问题（按遇到顺序）

### 1. 格式转换
repo 要 COCO，你手上是 VOC / YOLO / 自定义 → 写转换脚本，annotation schema 逐字段对齐
（bbox 格式 xyxy vs xywh、类别 id 映射、分割 mask 编码）。转换脚本留进产出目录备查。

### 2. repo 自带预处理脚本
很多 repo 有 `preprocess.py` / `prepare_data.sh`：依赖（matlab、特定库、子模块）、参数、输出目录结构、
**和论文协议对不对**。先读懂它要什么输入、产什么输出，再跑；输出结构和 loader 期望对不上是常见问题。

### 3. split / 划分
官方 split 还是自定义切？切法（random / 固定 seed）和论文对不对得上？有没有 train / val 泄漏？
多 seed 复现要确认 split 固定（否则跨 seed 不可比）。

### 4. 路径硬编码
config / 脚本里 `data_root: /home/author/data/xxx` 写死，有的 repo **多处写死**（config + 脚本 + 默认参数），
漏改一处报 "file not found"。**全文搜 data_root / data_dir / 数据集名**，逐处确认改全。

### 5. 下载源 / 校验
大文件分块、镜像、md5 校验、断点续传、账号（Kaggle / Google Drive 权限 / 网盘 / license 同意 / 内网）。
走 `dl-assistant/references/long-run-ops.md` 托管大下载（tmux detach + 断点续传）。
下完校验完整性（大小 / checksum）再算就绪。

### 6. loader 隐式假设（未报错却返回零个样本的原因）
dataloader 假定目录结构 / 文件名规则（如 `img_000001.jpg`、`images/train/`、`annotations/instances_train.json`），
**目录或文件名不符合要求时，加载器可能不报错却返回零个样本。** Layer 2 数值正确性检查要覆盖这种情况，因为 smoke 输出可能全零或含 NaN。
验证数据加载器确实能读到 1-2 个真实样本。

### 7. 数据集版本一致性
v1 vs v2 标注有改动、split 调整、metric 定义变化——和论文报的数字对不上。
查论文 / README 声明的版本，对齐；和 `baseline-survey` 的数据集维度衔接（survey 远程预判版本，setup 实测对齐）。
不一致在 Report 标出来。

### 8. 测试子集构建方法（smoke run 要用）
为 Layer 3 smoke run 要构建小规模测试子集，保持其分布和格式与全量数据一致：
固定 seed 抽样、保持目录结构 / annotation 格式、loader 用同一套代码能读。
测试子集构建方法记进 Report，方便复现 smoke 实验。

## 自动化边界：什么时候停（必须人工）

agent 能自动做：查版本、配代理、下公开数据、转格式、改路径、构建测试子集、跑预处理脚本、验证 loader。

**必须停下交用户**（这些不是 agent 能绕过的）：
- Kaggle / Google Drive 权限 / 网盘提取码 / 内网数据 → 要用户的账号 / token
- license 同意 / 需点击同意条款 → 要用户本人同意条款
- 链接失效 / 数据不公开 / 需申请 → 要用户找替代源或申请

遇到这些，把**具体的资源名 + 来源 + 需要什么 + 放哪 + 期望目录结构**一次性告诉用户，
用户完成后 agent 接着验证。

## 数据集速览：挑 3-5 个真实样本（产 datasets-intro 用）

数据集就绪时，给每个数据集挑 3-5 个真实样本，让用户直观看到"这数据长啥样"
（用户痛点：不知道这些数据集都是啥）。方法：

- **跑 loader 取样**：用 repo 真实 loader（不是另写一套），取 3-5 个 sample。- **图片样本**：复制到 `images/`（`<dataset>-sample-N.<ext>`），datasets-intro.md 相对路径引用。
- **文本 / 表格样本**：直接在 md 里贴前几行 / 小表格。
- **每个样本配一句标注**：这个 sample 体现了什么（检测框、分割 mask、难例、类别分布）。

详见 `dataset-report-template.md`。
