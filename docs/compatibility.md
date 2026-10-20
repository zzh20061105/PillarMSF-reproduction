# PillarNet 扩展兼容性记录

说明更新：2026-10-20。本文保留早期 PillarNet native 扩展构建与小输入检查的技术证据，不是整网实现或当前环境验收报告。当前使用现代环境栈、以 FutureDet 为执行主体；PillarNet 是编码器/主干与扩展的候选参考，尚不能据此认定最终会直接采用这些扩展。阶段与状态见 [进度总览](进度总览.md)，环境配方见 [environment.md](environment.md)，执行边界见 [implementation_boundary.md](implementation_boundary.md)。

## 固定来源与历史构建目标

参考仓库：`VISION-SJTU/PillarNet`（MIT）。固定提交：[`0634209fb889c24104d758eae153b9ff4aa0240a`](https://github.com/VISION-SJTU/PillarNet/commit/0634209fb889c24104d758eae153b9ff4aa0240a)，提交日期 2022-10-14。

此前构建环境：WSL2 Linux、Python 3.10、PyTorch 2.5.1 cu121、CUDA Toolkit 12.1、GCC/G++ 11、`spconv-cu120==2.3.6`；2.3.8 不属于这次历史验证的已安装版本。项目主干候选 C=64 见研究规格，不能据此改变官方 PillarNet 固定通道。Torch/spconv 安装成功、扩展编译成功和论文复现成功是不同验证层次。

原构建选型依据：[PyTorch 官方版本表](https://pytorch.org/get-started/previous-versions/)的 Torch 2.5.1 cu121、[spconv 官方 README](https://github.com/traveller59/spconv)的 2.x 二进制与 CUDA 兼容说明，以及 [CUDA 12.1 官方 Linux 表](https://docs.nvidia.com/cuda/archive/12.1.1/cuda-installation-guide-linux/index.html)的 Ubuntu 22.04/GCC 11.3。cu120 wheel 与 cu121 Torch 的组合不能只凭版本名保证兼容；历史有限实测见下文，当前 WSL 和服务器仍需按获批任务验收。本批未联网复核这些页面。

## 历史构建边界与保留入口

既有脚本仅构建 `det3d/ops/pillar_ops`：从项目中的 `references/PillarNet` 复制扩展到 `/home/pillar/build/pillar_ops`，检查固定 SHA 和参考源文件哈希；不改参考仓库，不删除已有构建目录，不把原 `det3d` 整包加入 PYTHONPATH，不将 Python 包装安装进项目。这是脚本职责说明，不代表当前 WSL 或服务器已存在同一路径的可用扩展。

编译入口是上游 `pillar_ops/setup.py`，使用 `CUDAExtension("pillar_cuda", ...)` 和 `BuildExtension`，收集 `src/*.cpp`、`src/*.cu`。需要 CUDA Toolkit 的 nvcc、C++ 编译器、Python 开发头文件、setuptools/wheel；ninja 可用于构建。spconv wheel 的 cumm 等依赖由安装器解析。此阶段不需要 CMake、APEX、DCN 或 ROI 扩展。

复制后的源代码只应用两处修改，均位于 `src/cuda_utils.h`：

1. 删除无实际调用的 `#include <THC/THC.h>`。Torch 2.5.1 已无该头文件。
2. 将 CHECK_CUDA 中的 `x.type().is_cuda()` 换为 `x.is_cuda()`。

未改 CUDA 算法、Python autograd 包装、激活、通道、网格计算或模型实现。构建记录及参考源文件 SHA-256 存在构建目录的 `.pillarmsf-build.json`，许可证副本为 `LICENSE.PillarNet`。

## 保留的调用方法（本批未执行）

以下为原入口用法。是否复用此扩展、目标环境与具体运行范围仍按小任务确认，不作为本批后续动作。确认目标 WSL 环境和路径后，既有构建入口为：

```bash
bash /mnt/d/ai_study/PillarMSF/scripts/build_pillar_ops.sh
```

脚本默认使用 `/home/pillar/venvs/pillarmsf/bin/python`，可通过 PYTHON 指定同一目标环境的解释器。CUDA_HOME 默认 `/usr/local/cuda-12.1`；TORCH_CUDA_ARCH_LIST 默认 8.9，MAX_JOBS 默认 2。移到其他 GPU 时必须按实际 GPU 调整架构，不应直接照搬 8.9。

构建脚本会强制重新编译扩展，再自动运行自检。全部自检成功后默认写入项目的 `environment/pillar_ops_validation.json`，包含 UTC 时间、环境、扩展路径、通过项目和未验证边界；可用 `--output` 指定输出位置。失败会抛出异常，执行日志用于判定本次失败，已有成功报告不会被覆盖，因此应核对报告时间。需要单独重跑自检时：

```bash
PYTHONPATH=/home/pillar/build/pillar_ops \
  /home/pillar/venvs/pillarmsf/bin/python \
  /mnt/d/ai_study/PillarMSF/scripts/check_pillar_ops.py
```

自检按指定构建目录直接加载 `pillar_cuda`，不 import `det3d`。它使用 CUDA device 0、默认 stream、非空 FP32 特征和 int32 索引，检查分柱的 [batch,y,x] 位置与点柱对应、flatten、gather 前向及重复索引的梯度累加、scatter max 前向及梯度核。gather 使用 PyTorch index_select/index_add 对照；scatter 使用 PyTorch max/autograd 对照。它直接调用 native 反向核，不验证上游 Python autograd Functions 的集成。

## 原实现的已知风险与未验证边界

- N=0、无有效点或无有效 pillar：上游有零 block launch 及 `position[-1]` 等风险。自检明确跳过，不运行原空输入 kernel；后续包装需先定义空输入策略。
- kernels 写死 float32 与 int32；FP16/AMP 支持未验证。
- 上游 backward 用 `torch.cuda.FloatTensor` 分配梯度，默认 device 绑定未修复；kernels 未传入 PyTorch current stream、未设置 device guard。多 GPU 与非默认 stream 未验证。
- scatter max 输出初始化零；负特征会被截到零。原 ReLU 特征可为非负；若论文 LeakyReLU 涉及 pillar MLP，需先确认激活范围，再修正 max 初始化与空柱策略。重复相同最大值的梯度选取也未验证。
- kernel 只检查张量 H/W，没有严格物理 ROI 过滤，浮点到 int 的转换向零截断。物理 ROI、820 有效网格/832 存储形状和目标/解码对齐仍需在对应获批模块实现后验证。
- CUDA 错误路径可 `exit(-1)` 结束进程；尚未替换为可控异常。
- 后续 rotated NMS 需要 `iou3d_nms_cuda`；纯 Torch DIoU 无需依赖该扩展。原样 import `det3d.models` 会通过 centernet_loss、point heads 导入 IoU 和 ROI native 扩展；新项目应按需封装。
- `x.type()` 和 `data<T>()` 在 Torch 2.5.1 仍存在但已弃用，不能将弃用警告等同于编译失败。Torch 2.5.1 的 GCC 版本检查表没有 CUDA 12.1 项，“no version bounds defined” 警告不代表 GCC 11 不兼容。

以上风险不在历史两处兼容性修改范围内，也未在本次文档整理中修复。自检通过只证明那次环境中的这组小输入 native 操作可工作，不证明骨干、A-FPN、未来预测、DIoU、数据集、训练或 APf 指标已正确。若后续直接采用这些扩展，应在涉及的任务中决定修复与验证范围；选择其他实现也需说明来源及适配边界。

## 历史验证记录

两份已有报告的 UTC 时间分别为 **2026-10-10 16:02:25** 和 **2026-10-10 16:07:34**，记录的设备为本机 RTX 4070 Laptop GPU。此前完成了 Torch CUDA、spconv 2D 前反向及空样本 batch 检查；Pillar native 扩展编译后通过了分柱、flatten、gather 与 scatter max 的非空小输入检查。报告见 [基础环境报告](../environment/validation.json)、[Pillar 算子报告](../environment/pillar_ops_validation.json)，历史执行日志在 `environment/logs/`。原构建记录为参考 pillar_ops 源文件构建前后的 SHA256 一致。本批仅读取已有报告时间，未重跑检查；它们不证明2026-10-18后当前 WSL 的 native 集成或任何服务器环境已通过。

当前按 [进度总览](进度总览.md) 的阶段1—5推进：先审核数据，再用官方 FutureDet 权重验证推理与评价链，随后分模块实现 PillarMSF、在服务器短训练并进入正式训练。首轮正式训练只做服务器 B4 完整模型20轮；FutureDet 官方权重用于评价对照，不重训，B0—B3 是否补做留待后续批准。本机数据准备与获批 GPU 推理/调试可按任务开展，所有实际训练均在服务器。

历史换行处理记录：Windows 克隆采用 CRLF，WSL Git 初次检查将其显示为整文件改动；当时确认差异仅换行，并给三个参考仓库设置本地 core.autocrlf=true，源码内容未改。项目自有源码采用 LF 和 core.autocrlf=false。这里保留处理经过，本批未修改或重新检查参考仓库配置。
