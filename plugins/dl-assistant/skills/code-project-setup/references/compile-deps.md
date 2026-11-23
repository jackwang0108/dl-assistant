# 编译型依赖处置（compile-deps）

> DL setup 最高频的整夜阻塞：需要现场编译 CUDA 算子的依赖。主文 SKILL.md 只说"走这里"，
> 这里放可操作的版本对齐、常见算子装法、失败诊断顺序、替代方案及处理顺序。

## 编译型依赖的版本与架构要求

普通 `pip install numpy` 是下预编译 wheel，秒装。但 `mmcv-full` / `detectron2` / `flash-attn` /
`apex` / `deformable attention` 这类**带 CUDA/C++ 扩展**的包，pip 装时要**现场用 nvcc 编译**，
编译型依赖安装时需要核对以下四项的兼容性。

```
PyTorch 版本  ×  PyTorch 编译时绑定的 CUDA 版本  ×  机器上的 CUDA Toolkit(nvcc)  ×  gcc/g++ 版本
```

这些设置不兼容时，可能导致编译失败，也可能在编译成功后出现运行时段错误（segfault）或找不到符号。

## 第一步：先对齐版本，别急着装

装任何编译型依赖前，先采集这四个真值：

```bash
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda)"  # torch 及其绑定的 CUDA
nvcc --version            # 机器上的 CUDA Toolkit 版本（编译用的就是它）
nvidia-smi                # 驱动支持的 CUDA 上限（≥ nvcc 版本即可）
gcc --version             # gcc 版本（CUDA 各版本对 gcc 上限有要求）
```

**对齐铁律**：`torch.version.cuda` 应当与 `nvcc` 的 CUDA 版本**一致或兼容**。常见错误是 conda 里
torch 绑的是 CUDA 11.8，但 `nvcc` 是系统的 12.x —— 编译时用了 12.x 的 nvcc 去链 11.8 的 torch，符号对不上。

> 解法通常是**让 conda 环境内自带匹配的 CUDA toolkit**：`conda install -c nvidia cuda-toolkit=11.8`（或对应版本），
> 让环境内的 nvcc 和 torch 绑定的 CUDA 一致，而不是依赖系统全局 nvcc。装前把这个决策记进 Setup Spec。

gcc 上限速查（编译失败报 `unsupported GNU version` 时查这个）：CUDA 11.x 通常需 gcc ≤ 10/11，
CUDA 12.x 需 gcc ≤ 12/13。版本太新要 `conda install gcc_linux-64=<v>` 装个旧的，或 `CC=/path/to/gcc-11`。

## 常见算子的已知安装方法与兼容性问题

> 优先使用官方预编译 wheel 或二进制包。没有合适的预编译版本时，再考虑从源码编译。

### mmcv / mmcv-full（OpenMMLab 系：mmdet/mmseg/mmpose…）

- **首选预编译**：用官方 wheel index，按 torch+cuda 选行，避免本地编译：
  ```bash
  pip install mmcv -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html
  ```
  （把 `cu118`/`torch2.1` 换成你的真实组合；组合不在表里才退本地编译）
- **注意**：`mmcv` 1.x vs 2.x 与 `mmdet` 2.x vs 3.x 严格绑定，搭配错误的版本会导致 import 失败。先确认 repo 要的是哪代。
- **注意**：`mmcv` 与 `mmcv-full` 是历史上的两个包名，老 repo 写 `mmcv-full`，新版合并了。按 repo 年代定。

### detectron2

- **首选预编译**：官方给 torch×cuda 矩阵的 wheel index，照查：
  ```bash
  python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu118/torch2.1/index.html
  ```
- **注意**：matrix 覆盖的 torch 版本有限，torch 太新只能从源码 `git+https://...` 编译，按前面的版本与架构检查再编译。

### flash-attn

- **首选预编译**：从 GitHub Releases 下对应 `torch+cuda+python+abi` 的预编译 wheel（文件名里全标了），
  直接 `pip install <wheel-url>`，**别裸 `pip install flash-attn`**（会拉源码编译，几十分钟且常 OOM）。
- **注意**：编译需要大量内存，并行编译可能耗尽内存，必要时 `MAX_JOBS=4 pip install flash-attn --no-build-isolation`。
- **注意**：abi（`cxx11abiTRUE/FALSE`）要和 torch 的对上，错了 import 时报 undefined symbol。

### apex（NVIDIA 混合精度，老 repo 常见）

- 现代 PyTorch 自带 `torch.cuda.amp`，**很多 repo 其实不再需要 apex**——先确认 repo 是不是只用了 amp 部分，能换则换。
- 真要装：`pip install -v --no-build-isolation --config-settings "--build-option=--cpp_ext --cuda_ext" git+https://github.com/NVIDIA/apex`
- **注意**：apex 对 torch×cuda 极敏感，是最容易整夜失败的之一。装不上时优先评估"能否绕过"。

### deformable attention / 自定义 CUDA 算子（DETR 系、论文自带 op）

- 通常 repo 自带 `models/ops/` + 一个 `make.sh` 或 `setup.py build`，要现场编译：
  ```bash
  cd <repo>/models/ops && sh make.sh   # 或 python setup.py build install
  ```
- **注意**：这类 op 写死了某个旧 torch 的 C++ API，torch 太新会编译报错（API 改名/弃用）。
  这时看 issue 区有没有人给新 torch 的 patch，或考虑降 torch 版本到 repo 要求。
- **验证编译真成功**：编译过 ≠ 能用。`python -c "import <repo的op模块>"` 不报 undefined symbol 才算成。

## 编译失败的诊断顺序

报错时**别盲改重试**，按这个顺序定位：

1. **定位完整日志中最先出现的错误**。常见关键词定位：
   - `unsupported GNU version` → gcc 太新，装/指定旧 gcc。
   - `nvcc fatal: unsupported gpu architecture` → `TORCH_CUDA_ARCH_LIST` 没设对你的卡（如 A100 是 `8.0`）。
   - `undefined symbol: ...` → torch/cuda/abi 没对齐，编译用的和运行的不是一套。
   - `cuda.h: No such file` / `nvcc not found` → 环境内没有 CUDA toolkit，`conda install cuda-toolkit`。
   - `killed` / OOM → 并行编译耗尽内存，`MAX_JOBS=4` 降并行。
2. **核对 PyTorch 所用的 CUDA 版本、nvcc、GCC 版本和 GPU 架构设置**（torch.version.cuda vs nvcc vs gcc 上限 vs arch list）。九成编译失败是这里。
3. **在仓库的 issue 区搜索报错关键词**，查看是否有已知解决办法或补丁。

## 编译失败时的替代方案及处理顺序

按下列顺序尝试替代方案。全部尝试后仍失败时，暂停操作并向用户报告。

1. **预编译 wheel/二进制**（首选，上面每个算子都给了）。
2. **conda 内对齐 CUDA toolkit + gcc** 后重新本地编译。
3. **降版本对齐**：把 torch 降到 repo 明确要求的版本（较早的仓库可能只支持指定旧版本），用对应的预编译算子。
4. **绕过该依赖**：评估这个 op 是不是非用不可（如 apex 能换成 torch amp）。
5. **仍无法解决时向用户报告**。列出 PyTorch 所用的 CUDA 版本、nvcc、GCC 版本、GPU 架构设置、第一处错误和已尝试的方案，
   让人决定（换 repo？联系作者？用作者提供的 docker？）。在这里停止重试。

> 与 baseline-survey 的衔接：survey 的"环境依赖分析"若已预判某算子编译难（标了依赖安装和兼容性问题），
> Setup Spec 就把它列为重点，进工程执行区直接走预编译/对齐路子，不走一遍盲试。
