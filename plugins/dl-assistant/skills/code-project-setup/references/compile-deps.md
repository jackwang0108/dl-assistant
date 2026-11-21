# 编译型依赖处置（compile-deps）

> DL setup 最高频的整夜阻塞：需要现场编译 CUDA 算子的依赖。主文 SKILL.md 只说"走这里"，
> 这里放可操作的版本对齐、常见算子装法、失败诊断顺序、fallback 链。

## 为什么编译型依赖这么坑

普通 `pip install numpy` 是下预编译 wheel，秒装。但 `mmcv-full` / `detectron2` / `flash-attn` /
`apex` / `deformable attention` 这类**带 CUDA/C++ 扩展**的包，pip 装时要**现场用 nvcc 编译**，
成功与否取决于一条**四方都得对齐**的链：

```
PyTorch 版本  ×  PyTorch 编译时绑定的 CUDA 版本  ×  机器上的 CUDA Toolkit(nvcc)  ×  gcc/g++ 版本
```

任意一环错位，要么编译直接失败，要么**编译过了但运行时 segfault / 符号找不到**（更坑，是静默的）。

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

## 常见算子的已知装法与坑

> 优先级永远是：**先找官方预编译 wheel/二进制，编译是 fallback**。下面每个都给"先试预编译"的路子。

### mmcv / mmcv-full（OpenMMLab 系：mmdet/mmseg/mmpose…）

- **首选预编译**：用官方 wheel index，按 torch+cuda 选行，避免本地编译：
  ```bash
  pip install mmcv -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html
  ```
  （把 `cu118`/`torch2.1` 换成你的真实组合；组合不在表里才退本地编译）
- **坑**：`mmcv` 1.x vs 2.x 与 `mmdet` 2.x vs 3.x 严格绑定，串版本会 import 就炸。先确认 repo 要的是哪代。
- **坑**：`mmcv` 与 `mmcv-full` 是历史上的两个包名，老 repo 写 `mmcv-full`，新版合并了。按 repo 年代定。

### detectron2

- **首选预编译**：官方给 torch×cuda 矩阵的 wheel index，照查：
  ```bash
  python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu118/torch2.1/index.html
  ```
- **坑**：matrix 覆盖的 torch 版本有限，torch 太新只能从源码 `git+https://...` 编译，回到四方对齐。

### flash-attn

- **首选预编译**：从 GitHub Releases 下对应 `torch+cuda+python+abi` 的预编译 wheel（文件名里全标了），
  直接 `pip install <wheel-url>`，**别裸 `pip install flash-attn`**（会拉源码编译，几十分钟且常 OOM）。
- **坑**：编译需要大量内存，并行编译易把机器 OOM，必要时 `MAX_JOBS=4 pip install flash-attn --no-build-isolation`。
- **坑**：abi（`cxx11abiTRUE/FALSE`）要和 torch 的对上，错了 import 时报 undefined symbol。

### apex（NVIDIA 混合精度，老 repo 常见）

- 现代 PyTorch 自带 `torch.cuda.amp`，**很多 repo 其实不再需要 apex**——先确认 repo 是不是只用了 amp 部分，能换则换。
- 真要装：`pip install -v --no-build-isolation --config-settings "--build-option=--cpp_ext --cuda_ext" git+https://github.com/NVIDIA/apex`
- **坑**：apex 对 torch×cuda 极敏感，是最容易整夜失败的之一。装不上时优先评估"能否绕过"。

### deformable attention / 自定义 CUDA 算子（DETR 系、论文自带 op）

- 通常 repo 自带 `models/ops/` + 一个 `make.sh` 或 `setup.py build`，要现场编译：
  ```bash
  cd <repo>/models/ops && sh make.sh   # 或 python setup.py build install
  ```
- **坑**：这类 op 写死了某个旧 torch 的 C++ API，torch 太新会编译报错（API 改名/弃用）。
  这时看 issue 区有没有人给新 torch 的 patch，或考虑降 torch 版本到 repo 要求。
- **验证编译真成功**：编译过 ≠ 能用。`python -c "import <repo的op模块>"` 不报 undefined symbol 才算成。

## 编译失败的诊断顺序

报错时**别盲改重试**，按这个顺序定位：

1. **读真实报错的第一处 error**（不是最后一屏的 warning 瀑布）。常见关键词定位：
   - `unsupported GNU version` → gcc 太新，装/指定旧 gcc。
   - `nvcc fatal: unsupported gpu architecture` → `TORCH_CUDA_ARCH_LIST` 没设对你的卡（如 A100 是 `8.0`）。
   - `undefined symbol: ...` → torch/cuda/abi 没对齐，编译用的和运行的不是一套。
   - `cuda.h: No such file` / `nvcc not found` → 环境内没有 CUDA toolkit，`conda install cuda-toolkit`。
   - `killed` / OOM → 并行编译爆内存，`MAX_JOBS=4` 降并行。
2. **核对四方对齐**（torch.version.cuda vs nvcc vs gcc 上限 vs arch list）。九成编译失败是这里。
3. **去 repo issue 区搜报错关键词** —— 这类坑别人大概率踩过，常有现成解法/patch。

## Fallback 链（什么时候放弃硬编译）

按这个顺序退，走到底还不行才是**死结上报点**（停下把情况整理给用户，不无限重试烧时间）：

1. **预编译 wheel/二进制**（首选，上面每个算子都给了）。
2. **conda 内对齐 CUDA toolkit + gcc** 后重新本地编译。
3. **降版本对齐**：把 torch 降到 repo 明确要求的版本（很多老 repo 就吃某个旧 torch），用对应的预编译算子。
4. **绕过该依赖**：评估这个 op 是不是非用不可（如 apex 能换成 torch amp）。
5. **走到这还不行** → 死结上报：把四方版本真值 + 第一处 error + 已试过的路子整理给用户，
   让人决定（换 repo？联系作者？用作者提供的 docker？）。不在工程执行区无限重试烧时间。

> 与 baseline-survey 的衔接：survey 的"环境依赖分析"若已预判某算子编译难（标了依赖地雷），
> Setup Spec 就把它列为重点，进工程执行区直接走预编译/对齐路子，不走一遍盲试。
