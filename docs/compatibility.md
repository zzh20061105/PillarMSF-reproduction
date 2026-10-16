# PillarNet 扩展兼容性记录

## 固定来源与目标

参考仓库：`VISION-SJTU/PillarNet`（MIT）。固定提交：[`0634209fb889c24104d758eae153b9ff4aa0240a`](https://github.com/VISION-SJTU/PillarNet/commit/0634209fb889c24104d758eae153b9ff4aa0240a)，提交日期 2022-10-14。

项目环境目标：WSL2 Linux、Python 3.10、PyTorch 2.5.1 cu121、CUDA Toolkit 12.1、GCC/G++ 11。当前选用 `spconv-cu120==2.3.6`；2.3.8 不作为本项目已确认可安装版本。项目主干候选 C=64 是论文结构复现参数，不能据此改变官方 PillarNet 固定通道。Torch/spconv 安装成功、扩展编译成功和论文复现成功是不同验证层次。

[PyTorch 官方版本表](https://pytorch.org/get-started/previous-versions/)列出 Torch 2.5.1 cu121。[spconv 官方 README](https://github.com/traveller59/spconv)说明 spconv 2.x 不依赖 PyTorch 二进制，并支持 CUDA 同大版本不同小版本共存；因此 cu120 wheel 与 cu121 Torch 是候选组合，仍需本机前向/反向验证。[CUDA 12.1 官方 Linux 表](https://docs.nvidia.com/cuda/archive/12.1.1/cuda-installation-guide-linux/index.html)包含 Ubuntu 22.04 的 GCC 11.3。

## 构建边界

仅构建 `det3d/ops/pillar_ops`。脚本从项目中的 `references/PillarNet` 复制扩展到 `/home/pillar/build/pillar_ops`，检查固定 SHA 和参考源文件哈希；不改参考仓库，不删除已有构建目录，不把原 `det3d` 整包加入 PYTHONPATH，不将 Python 包装安装进项目。

编译入口是上游 `pillar_ops/setup.py`，使用 `CUDAExtension("pillar_cuda", ...)` 和 `BuildExtension`，收集 `src/*.cpp`、`src/*.cu`。需要 CUDA Toolkit 的 nvcc、C++ 编译器、Python 开发头文件、setuptools/wheel；ninja 可用于构建。spconv wheel 的 cumm 等依赖由安装器解析。此阶段不需要 CMake、APEX、DCN 或 ROI 扩展。

复制后的源代码只应用两处修改，均位于 `src/cuda_utils.h`：

1. 删除无实际调用的 `#include <THC/THC.h>`。Torch 2.5.1 已无该头文件。
2. 将 CHECK_CUDA 中的 `x.type().is_cuda()` 换为 `x.is_cuda()`。

未改 CUDA 算法、Python autograd 包装、激活、通道、网格计算或模型实现。构建记录及参考源文件 SHA-256 存在构建目录的 `.pillarmsf-build.json`，许可证副本为 `LICENSE.PillarNet`。

## 使用方法

在项目的 WSL 环境里激活 `/home/pillar/venvs/pillarmsf` 后运行：

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

## 仍未修复或未验证的问题

- N=0、无有效点或无有效 pillar：上游有零 block launch 及 `position[-1]` 等风险。自检明确跳过，不运行原空输入 kernel；后续包装需先定义空输入策略。
- kernels 写死 float32 与 int32；FP16/AMP 支持未验证。
- 上游 backward 用 `torch.cuda.FloatTensor` 分配梯度，默认 device 绑定未修复；kernels 未传入 PyTorch current stream、未设置 device guard。多 GPU 与非默认 stream 未验证。
- scatter max 输出初始化零；负特征会被截到零。原 ReLU 特征可为非负；若论文 LeakyReLU 涉及 pillar MLP，需先确认激活范围，再修正 max 初始化与空柱策略。重复相同最大值的梯度选取也未验证。
- kernel 只检查张量 H/W，没有严格物理 ROI 过滤，浮点到 int 的转换向零截断。物理 ROI、820 有效网格/832 存储形状和目标/解码对齐仍需实现后验证；按2026-10-15分工由助手实现、用户审核。
- CUDA 错误路径可 `exit(-1)` 结束进程；尚未替换为可控异常。
- 后续 rotated NMS 需要 `iou3d_nms_cuda`；纯 Torch DIoU 无需依赖该扩展。原样 import `det3d.models` 会通过 centernet_loss、point heads 导入 IoU 和 ROI native 扩展；新项目应按需封装。
- `x.type()` 和 `data<T>()` 在 Torch 2.5.1 仍存在但已弃用，不能将弃用警告等同于编译失败。Torch 2.5.1 的 GCC 版本检查表没有 CUDA 12.1 项，“no version bounds defined” 警告不代表 GCC 11 不兼容。

以上风险不在本次两处兼容性修改范围内。自检通过只证明这组小输入 native 操作可工作，不证明骨干、A-FPN、未来预测、DIoU、数据集、训练或 APf 指标已正确。

## 验证记录

本机已实际完成 Torch CUDA、spconv 2D 前反向及空样本 batch 检查；Pillar native 扩展已编译并通过分柱、flatten、gather 与 scatter max 的非空小输入检查。结果见 [基础环境报告](../environment/validation.json)、[Pillar 算子报告](../environment/pillar_ops_validation.json)，执行日志在 environment/logs/。参考 pillar_ops 源文件构建前后的 SHA256 一致。

已完成环境和非空 native 算子验证。后续先用 mini 接通 FutureDet 数据、标签、训练和评价链，再建立官方参考基线与论文 Pillar 消融基线，随后逐项接入 Stage5、A-FPN、DIoU、LeakyReLU，最后完成全量训练与消融。

Windows 克隆默认采用 CRLF，WSL Git 初次检查将它误判为整文件改动。已确认差异仅换行，并给三个新参考仓库设置本地 core.autocrlf=true；源码内容未改。新项目自有源码使用 LF 和 core.autocrlf=false。
