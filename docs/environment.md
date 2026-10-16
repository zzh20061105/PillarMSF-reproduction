# 当前执行边界与历史环境记录

更新：2026-10-16。全部实际训练在服务器进行，本机只进行代码构建、阅读与调试。服务器尚未租用、配置或验证；预算和实例由用户决定。

| 地点 | 当前安排 |
| --- | --- |
| 本机 | 源码/配置编辑、Git 操作、语法与独立接口检查、小规模 CPU 数值/形状/梯度调试；不启动任何训练 |
| 服务器 | CUDA 原生算子及 GPU 整网验收、真实数据完整闭环、mini/短训练、正式训练、显存/吞吐及正式评价 |

本机的模块梯度检查不包含优化器训练。现有 WSL 可保留作历史参考或已说明的轻量调试；本轮不重装、不升级、不删除环境，也不运行已有 CUDA 自检。环境变更或运行任务按 implementation_boundary.md 的小任务确认规则执行。

environment/ 保存安装配方、依赖版本和历史证据，不是服务器已就绪的证明。现有依赖只作服务器候选；取得实例后按真实 OS、GPU、驱动、Toolkit、编译器和路径重建环境、重编扩展并验收。不复制本机 venv 或 .so 作为可用服务器环境。

下文是历史本机 WSL 的安装及有限检查记录，旧命令、硬件和“通过”均只对应当时范围，不是当前默认启动流程。服务器准备见 [server_preflight.md](server_preflight.md)。

---

# 历史 WSL 环境与复现入口

此前已建立 WSL2 发行版 `PillarMSF-Ubuntu22`，Ubuntu 22.04.5 LTS。

| 位置 | 用途 |
|---|---|
| Windows `D:\ai_study\PillarMSF` / Linux `/mnt/d/ai_study/PillarMSF` | 唯一源码与规格目录 |
| `D:\WSL\PillarMSF-Ubuntu22\ext4.vhdx` | 新发行版磁盘，Linux home 与软件包存在这里 |
| `/home/pillar/venvs/pillarmsf` | 专用 Python venv |
| `/home/pillar/build/pillar_ops` | Pillar native 算子构建副本 |
| `/home/pillar/data/nuscenes` | 建议数据位置，尚未下载 |

源代码先在 D 盘便于 Windows 编辑；大量点云读取、编译中间文件与 venv 使用 WSL 的 Linux 文件系统。将来迁移服务器时以源码与来源锁定文件重建环境，不复制 Windows 的 `.so` 文件。

## 固定候选版本

- Python 3.10（Ubuntu 系统补丁版本以自检为准）
- PyTorch 2.5.1，官方 cu121 wheel
- CUDA Toolkit 12.1，仅工具包，不安装 Linux NVIDIA 驱动
- spconv-cu120 2.3.6（此 CUDA wheel 的版本与 CPU spconv 发布号不同）
- NumPy 1.26.4，旧 SDK 的 np.float 仍需后续局部适配
- nvidia-nvjitlink-cu12 12.1.105，额外固定这一原本无版本上限的 CUDA 依赖
- GCC/G++ 11，CMake、Ninja；native 目标架构 8.9，MAX_JOBS=2

PyTorch wheel 与 Toolkit 的运行时来源分别记录；spconv 的 cu120 与 Torch cu121 是同一 CUDA 大版本下的候选组合，历史本机有限检查仅作候选证据，服务器仍需重新验收。[PyTorch 发布组合](https://pytorch.org/get-started/previous-versions/)、[spconv 安装说明](https://github.com/traveller59/spconv)、[NVIDIA Toolkit 与驱动包区别](https://docs.nvidia.com/cuda/archive/12.1.0/cuda-installation-guide-linux/index.html#package-manager-metas)

不直接安装旧 FutureDet 的整份 requirements、APEX、DCN 或现代 nuscenes-devkit。训练与评价需要的包在接入数据链时按实际导入选择，避免替换 forecasting SDK 的同名 namespace。

## 安装记录

官方 Ubuntu 镜像来自 [Canonical WSL Jammy](https://cloud-images.ubuntu.com/wsl/jammy/current/)，导入前校验 SHA256，结果见 `environment/rootfs.sha256`。

```powershell
wsl --import PillarMSF-Ubuntu22 D:\WSL\PillarMSF-Ubuntu22 D:\ai_study\PillarMSF\environment\downloads\ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz --version 2
wsl -d PillarMSF-Ubuntu22 -u root -- bash /mnt/d/ai_study/PillarMSF/environment/bootstrap_system.sh
wsl -d PillarMSF-Ubuntu22 -u pillar -- bash /mnt/d/ai_study/PillarMSF/environment/install_python.sh
```

第一条仅用于重建不存在的发行版，不对已注册的同名环境重复导入。`pillar` 是专用普通用户，没有设置 sudo 密码；系统维护可以在 Windows 用 `wsl -d PillarMSF-Ubuntu22 -u root` 明确进入新发行版。已有 Ubuntu 与 Windows Conda 环境保留。

## 验证范围

安装日志在 `environment/logs/`，具体版本与运行结果分别见 `environment/requirements-resolved.txt`、`environment/validation.json`。

环境自检覆盖小型 Torch CUDA 前反向、spconv 2D 子流形及下采样卷积前反向、保留空样本 batch、nvcc 版本。Pillar 算子另有独立构建与非空 FP32/int32 自检；参考源码保持原样。

这些检查不代表 FutureDet 已跑通，也不代表论文模型、nuScenes 评价或 APf 数值已复现。完整数据链、rotated NMS、空柱/负特征/ROI边界、AMP 和多 GPU 留待后续验证。

## 本机预算

显卡为 RTX 4070 Laptop 8GB，主机内存约32GB。上述为此前本机硬件记录。当前已选择在服务器运行数据与模型；服务器正式 batch2 能否容纳仍需实测，不能用梯度累积替代后宣称训练设置完全一致。

WSL 的 `df` 显示的是虚拟磁盘容量上限，真实余量以 Windows D 盘为准。全量 nuScenes 尚未下载，当前磁盘需要先为环境、mini 和缓存留空间，完整训练数据另行安排。

## 历史本机实测结果（不代表当前服务器）

| 检查 | 结果 |
|---|---|
| Torch CUDA 前向/反向 | 通过 |
| spconv SubMConv2d、SparseConv2d 前向/反向 | 通过 |
| 稀疏卷积保留空样本的 batch=3 | 通过 |
| Pillar native 编译、分柱、flatten、gather/max 前反向 kernel | 通过，仅非空 FP32/int32、单 GPU 默认 stream |

Python 3.10.12，Torch 2.5.1+cu121，spconv-cu120 2.3.6，cumm-cu120 0.4.11，nvcc 12.1.105，GCC 11.4.0。日志中的 AMP 弃用、编译器检查表缺项及未使用变量是警告；本次检查均以成功退出和报告断言为依据。

默认用户通过 `wsl --manage PillarMSF-Ubuntu22 --set-default-user pillar` 设置，无需停止现有发行版。Git safe.directory 仅加入本项目及三个参考路径。
