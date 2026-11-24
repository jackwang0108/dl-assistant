# 编译型依赖安装与验证

本文件说明怎样确认正式入口实际需要哪些编译型依赖，选择适合目标环境的安装方式，根据构建和运行证据排错，并验证所需算子能在实际入口中工作。

供[运行手册 Step 4](workflow.md#step-4-建立或恢复-setup-分支准备环境权重和数据)准备环境，以及 Step 5 实跑入口时使用。已有选型报告指出兼容性风险时，按同一仓库版本、入口与设备核对，再写入准备规格。

## 1. 优先准备并启用作者提供的编译算子

作者同时提供编译实现和默认实现时，**优先准备并启用作者提供的编译实现**。逐个检查本轮确认的正式入口及其可选模式。当前项目支持、目标环境兼容且入口可启用的编译算子都准备到位，例如训练和推理分别支持的扩展。作者可能为速度、显存占用或特定功能选择该实现，具体收益在本机测到后再记录。

从入口报告的调用链出发，回查入口配置、依赖声明、扩展导入和运行时分派。记录每个算子的源码或包、哪些入口会用到、怎样启用、什么情况下会回退。检查启动时要加载的扩展，也查只在特定模式、数据类型或输入条件下调用的扩展。同一个扩展被多个入口使用时共用安装，按各入口实际配置核是否启用。

默认先用已核实的作者预编译产物或项目官方镜像启用同一编译实现。没有匹配产物时，只要项目支持、工具链兼容且在本轮资源内，就构建固定版本的源码。默认实现作为有依据的临时方案。编译路径确实受阻时，说明失败原因、影响的入口、回退对行为和比较的可能影响，并按批准范围处理。能独立准备的其他入口继续。将默认实现通过和编译实现就绪分别记录。

## 2. 核对实际运行和构建环境

用计划采用的解释器和实际运行机器采集。容器或调度任务在相同环境中核对。先查项目 commit、依赖或锁文件、设备和框架，再按需查源码编译工具。只用 CPU 或已匹配的二进制产物时，按项目实际要求检查。

```bash
git rev-parse HEAD
uname -sm
"$setup_python" -V
"$setup_python" -c 'import sys; print(sys.executable)'
"$setup_python" -m pip debug --verbose
# 项目使用 PyTorch 时
"$setup_python" -c 'import torch; print("torch:", torch.__version__, "build CUDA:", torch.version.cuda); print("C++ ABI:", torch.compiled_with_cxx11_abi() if hasattr(torch, "compiled_with_cxx11_abi") else "check build config"); print("visible CUDA devices:", [(torch.cuda.get_device_name(i), torch.cuda.get_device_capability(i)) for i in range(torch.cuda.device_count())])'
# NVIDIA 目标机器
nvidia-smi
# 构建 PyTorch CUDA 扩展且项目使用 cpp_extension 时
"$setup_python" -c 'from torch.utils.cpp_extension import CUDA_HOME; print(CUDA_HOME)'
command -v nvcc c++
nvcc --version
c++ --version
```

分别记录框架构建所用 CUDA、驱动版本、目标 GPU 架构、Python/平台标签、扩展需要的 ABI 和构建日志中实际调用的工具链。`nvidia-smi` 的 CUDA 字段反映驱动能力，Toolkit 则看实际使用的 `nvcc`。若构建日志显示另一个 `nvcc` 或主机编译器，用日志中的路径复查其版本。工具链能否编译目标架构、主机编译器能否使用，按该 Toolkit 版本核对。 [NVIDIA CUDA 安装指南](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/) · [PyTorch 扩展构建说明](https://docs.pytorch.org/docs/main/utils/cpp_extension.html)

## 3. 选安装方式并固定来源

### 预编译包或镜像

先从项目锁定版本的文档或官方发布记录找到适用产物。对照包版本、Python、OS/架构、框架、CUDA、C++ ABI 和目标 GPU 支持范围。使用官方镜像时，也核镜像 tag 或 digest、宿主驱动与实际算子。

若作者使用单独的 wheel 链接页，先限定二进制产物做探测。以下变量从本轮 spec 和官方发布记录取得。用干净的检查目录，避免读到旧 wheel。作者使用普通包索引时，按实际索引查询。

```bash
"$setup_python" -m pip download --only-binary=:all: --no-deps \
  --no-index --find-links "$wheel_page" --dest "$wheel_dir" "$locked_package"
ls -lh "$wheel_dir"
```

从实际文件名和发布记录核匹配条件。在计划指定的环境中安装核过的 wheel，检查依赖和实际导入位置。查不到匹配文件时，回查当前版本的发布范围，再选择源码或镜像。若是下载路径失败，按[网络与镜像](../../dl-assistant/references/network-mirror.md)排查。

### 源码构建

锁定实际源码 commit 或 release。先读作者的 build 文件、脚本、官方安装指令和项目依赖。用日志确认实际使用的编译器、CUDA 工具链、构建后端、架构参数与输出目录。按该版本说明选择是否需要构建隔离及如何注入编译参数。预计超过 5 分钟、时长不确定或重跑代价高时，按[运行手册](workflow.md#长任务启动与恢复)托管。记录完整命令、环境、首个错误与实际产物路径。

### 按仓库的构建方式准备算子

从正式入口的导入或分派位置找到实际算子，再沿调用查谁负责构建它。先看作者给的安装命令及其包装脚本，再用下面的搜索定位构建文件和源码。根据实际项目缩小搜索目录，打开匹配文件确认调用。

```bash
rg --files -g 'pyproject.toml' -g 'setup.py' -g 'CMakeLists.txt' \
  -g 'CMakePresets.json' -g 'Makefile' -g '*.cu' -g '*.cuh' -g '*.cpp'
rg -n 'CUDAExtension|CppExtension|BuildExtension|torch\.utils\.cpp_extension|find_package\(Torch|scikit_build_core|@triton\.jit' .
```

同一仓库可能组合几种工具。例如 `pip` 启动构建后端，后端调用 CMake，CMake 再生成 Ninja 构建规则。沿真实命令追到最终产物，记录使用的后端、启用算子的开关、目标设备和产物加载位置。

#### 安装时构建的 PyTorch C++ / CUDA 扩展

- **怎样识别。** `setup.py` 或构建模块使用 `CppExtension`、`CUDAExtension`、`BuildExtension`。打开定义，确认扩展模块名、源文件和构建开关，核作者命令是否会编入本轮入口使用的目标。
- **怎样执行。** 在锁定源码和已选解释器下，按作者说明执行安装。从详细日志确认实际使用的 PyTorch、编译器和架构参数。若项目明确要求在目标环境内使用已安装的 PyTorch 构建，并且该环境已有构建依赖，才按版本说明使用 `--no-build-isolation`。PyTorch 使用 Ninja 构建且确有内存压力时，再根据可用资源设 `MAX_JOBS`。 [PyTorch 扩展构建说明](https://docs.pytorch.org/docs/stable/cpp_extension.html)
- **怎样验。** 用同一解释器确认扩展模块来自刚准备的环境，再在目标设备调用本轮入口使用的算子。FlashAttention 可用入口实际采用的 dtype 和形状核 attention 后端。Apex 可按实际使用的融合优化器或归一化功能核构建开关和调用。 [FlashAttention 安装说明](https://github.com/Dao-AILab/flash-attention#installation-and-features) · [NVIDIA Apex 扩展说明](https://github.com/NVIDIA/apex#from-source)

#### CMake 构建的原生库或 Python 扩展

- **怎样识别。** 从作者脚本、`CMakeLists.txt`、preset 或 `pyproject.toml` 中找到实际构建入口，例如由 `scikit-build-core` 调用 CMake。查看谁选择 Python、框架库、CUDA 编译器、架构和需要生成的目标。 [CMake 命令手册](https://cmake.org/cmake/help/latest/manual/cmake.1.html) · [scikit-build-core 说明](https://scikit-build-core.readthedocs.io/en/latest/)
- **怎样执行。** 优先沿用作者的 preset、安装命令或包装脚本。项目直接使用 CMake 时，以下是配置与构建的命令形态，将项目指定参数填进对应命令。更换解释器、编译器或 Toolkit 后，使用独立的构建目录，并核 `CMakeCache.txt` 和详细日志确认选择生效。 [CMake 命令手册](https://cmake.org/cmake/help/latest/manual/cmake.1.html)

  ```bash
  cmake -S "$source_dir" -B "$build_dir"
  cmake --build "$build_dir" --verbose
  ```

- **怎样验。** 确认生成了预期目标，并由项目规定的安装或打包步骤放到加载路径。回到正式入口用的解释器和设备，检查实际加载的库或扩展路径，再运行最小调用。仅在构建目录看到文件时，将状态记为已构建。

#### 首次调用才编译的扩展或 kernel

- **怎样识别。** 查 `torch.utils.cpp_extension.load`、`load_inline` 或 Triton 的 `@triton.jit` 定义及调用点。把触发编译的正式入口、设备、输入形状、dtype 和实际缓存或构建目录记进计划。 [PyTorch 运行时构建](https://docs.pytorch.org/docs/stable/cpp_extension.html) · [Triton JIT](https://triton-lang.org/main/python-api/generated/triton.jit.html)
- **怎样执行和验收。** 在最终运行环境用会命中编译分支的输入触发首次调用，记录编译日志或可确认的缓存证据、实际后端、输出及用时。需要验证重复运行时，用同一条件再跑一次，分别记录首次与后续调用。复查旧产物影响时，可在项目支持的前提下指定独立缓存目录，保留原有缓存。调用只命中默认实现时，回查配置和分派条件。

仓库还有其他构建方式时，从作者支持的脚本和实际构建日志追踪同一组问题。确认谁构建、生成什么、由哪个入口加载，随后在目标设备验证编译实现。

## 4. 按失败阶段排查并复验

先保留**失败的命令、工作目录、实际解释器或容器、退出状态和完整日志**。按最后一个有证据通过的步骤定位失败阶段。安装没有取到 wheel、编译中断、导入失败和 GPU 第一次调用失败各有不同的检查入口。找到最早一条能解释当前失败的具体报错，回读它之前的命令、路径和参数。并行构建的日志可能交错，先把报错和对应的编译单元或子命令对齐。

### 取包或解析失败

如果日志还没进入编译，先看实际请求的源、包名与版本，以及下载到的是 wheel 还是源码包。用 `"$setup_python" -m pip debug --verbose` 查看解释器接受的平台和 Python 标签，再按本文件的二进制探测命令复查。若错误是连接、权限或镜像缺文件，走[网络与镜像](../../dl-assistant/references/network-mirror.md)。环境具备匹配产物时重新下载；确实缺 wheel 时，按固定版本选择源码构建或项目已有的容器方案。

### 编译或链接失败

从构建日志找首个失败的子命令及上下文。以下命令用于定位日志行，随后阅读实际段落。

```bash
rg -ni -C 4 'fatal error|unsupported|not found|cannot find|killed|out of memory|no space|error:' "$build_log"
```

- **找不到 `nvcc`、头文件或库。** 查失败命令实际使用的工具链路径和 `-I`、`-L`，再查构建后端解析到的 Toolkit。记录目录确实缺文件，还是构建用错了工具链。按项目版本修正路径或补齐依赖，复跑同一构建。
- **`unsupported GNU version` 或 `unsupported gpu architecture`。** 从日志取实际编译器及架构参数，用对应的 `nvcc --version`、主机编译器版本、设备 compute capability 和该 Toolkit 官方支持范围对照。若是错误选到了另一套工具链，先修选择路径。若编译器确实不支持目标组合，按批准范围更换为支持目标的版本或产物。 [NVIDIA 主机编译器支持](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/) · [PyTorch CUDA 扩展构建](https://docs.pytorch.org/docs/main/utils/cpp_extension.html)
- **编译进程被杀、内存或磁盘不足。** 先查构建日志和调度器终止原因，并用 `df -h "$build_dir"` 核实际构建盘。确认内存压力和构建后端支持后，才降低并行数，例如 PyTorch Ninja 构建可限定 `MAX_JOBS`。保留新一次的资源设置与日志。 [PyTorch 扩展构建并行选项](https://docs.pytorch.org/docs/main/utils/cpp_extension.html)

### 安装完成，但导入或链接到运行库失败

遇到 `undefined symbol`、动态库找不到或导入就崩溃时，先核解释器与包的安装位置。用实际包名运行 `"$setup_python" -m pip show "$package_name"`，从 traceback、包目录或构建产物定位出错的扩展。Linux 的 `readelf -d "$extension_file"` 可以列出依赖声明与搜索路径。再对照框架版本、C++ ABI 和运行时实际找到的库，确定是载入了旧扩展、运行库路径冲突，还是当前产物确实不匹配。处理对应原因后，从同一目录和解释器复验导入，再做最小调用。 [Detectron2 安装排错](https://detectron2.readthedocs.io/en/latest/tutorials/install.html#common-installation-issues)

### 导入通过，但在 GPU 调用时失败或回退

遇到 `no kernel image` 时，先用本文件的设备探测命令核实际设备和 compute capability，再检查当前加载扩展的构建参数、来源和目标架构覆盖。确认当前产物确实缺目标支持后，用匹配的作者产物，或按该项目支持的方式重编。确认配置回退时，则查实际分派条件，例如数据类型、形状、设备、开关和导入路径。恢复后先复跑同一最小调用，再跑受影响的正式入口，检查这次确实启用了编译实现。 [Detectron2 GPU 架构排错](https://detectron2.readthedocs.io/en/latest/tutorials/install.html#common-installation-issues) · [PyTorch CUDA 架构选项](https://docs.pytorch.org/docs/main/utils/cpp_extension.html)

每次重试记录「新发现的证据、这次改什么、如何判断修复」。同一错误没有新依据、继续会超出批准投入、需要改系统设置或影响研究条件时，写明具体阻塞和仍能推进的入口。降框架、换算子、改混合精度或临时使用默认实现时，按 workflow 说明影响并在需要时回 Step 3 确认。

## 5. 逐层验证最终使用的算子

1. **包安装和模块导入。** 从实际解释器核包版本、模块路径及可用的扩展。记录真正导入的二进制。
2. **目标设备上的最小调用。** 用入口所需的数据类型、设备和代表性输入调用算子，核输出结构和有出处的预期行为。适用时利用项目现有测试或可信参考。数值容差缺少依据时记录实际观察与待核项。
3. **从正式入口验证分派。** 用入口的实际配置试跑，结合项目日志、分派检查、可用的运行轨迹或明确的调用记录，确认本次执行走到了作者的编译实现。发现回退时查配置开关、输入条件与实际导入路径。编译实现覆盖哪些入口就记哪些，其他条件留待实测。

在 `setup-report.md` 记录入口编号、所选实现、包或源码身份、构建命令及选项、目标设备、最小调用、正式入口运行证据与仍受阻范围。速度和显存只有实际测过才填写，并带上输入与运行条件。

## 示例 · 导入成功，GPU 调用仍报 no kernel image

以下为虚构的 `edge-vision` 自带算子。源码有编译实现和默认实现，E01 推理及 E03 训练在相应配置中可启用编译实现。

1. 在目标机器用指定环境检查 PyTorch、设备 compute capability 和实际加载的扩展。包安装和导入都通过，E01 调用作者的算子时报 `no kernel image`。报告分别记录导入通过和 GPU 调用失败。
2. 查原扩展对应的构建日志和产物来源。此例日志只显示为另一种架构生成 kernel，未覆盖目标卡。固定版本的作者产物没有匹配构建，核项目说明、实际 `nvcc` 和 C++ 编译器是否支持目标架构。
3. 在当前批准的工具链和资源范围内，按项目构建方式为目标设备重编固定版本。预计构建时间较长，用 tmux 托管。保存架构参数、日志、退出码和产物位置。重新从同一解释器核导入路径，再用真实入口所需的设备和数据类型做最小调用。
4. 复跑 E01 的单张推理和 E03 的最小训练检查。根据运行证据核两者实际启用编译实现，分别记录推理输出和训练更新。若目标路径仍受阻，按影响规则说明是否临时用默认实现以及哪些结论需等编译实现验证。
