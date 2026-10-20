# 当前执行边界与历史环境记录

更新：2026-10-20。本机可按批准的小任务准备数据、做 GPU 推理和调试；全部实际训练仍在服务器进行。服务器尚未就绪，预算和实例由用户决定。当前进度见 [进度总览](进度总览.md)。

| 地点 | 当前安排 |
| --- | --- |
| 本机 | 源码/配置编辑、Git 操作、语法与独立接口检查、CPU 数据准备和标签审计、轻量数值/形状/梯度调试，以及按批次批准的 GPU 推理和调试 |
| 服务器 | 全部实际训练（含 CPU、mini、短训练）、训练闭环与正式 GPU 验收、显存/吞吐及正式实验 |

本机的模块梯度检查不包含优化器训练。方向许可不等于某次运行已获批准；安装依赖、处理数据和执行 GPU 任务仍按 [实现与执行边界](implementation_boundary.md) 先说明范围、确认后实施，遇到版本或任务偏离先停下说明。

## 当前本机环境与数据

- 使用现有 WSL `PillarMSF-Ubuntu22` 和 `/home/pillar/venvs/pillarmsf`，已用于 mini 数据准备；不能将整个 WSL 环境称为仅供历史参考。
- mini 数据根为 `/home/pillar/data/nuscenes/`，两份索引在 `mini_forecast/`。10 月 19 日只读检查确认文件存在和大小，没有重新生成或复核样本统计，详见 [数据说明](../data/README.md)。
- `/home/pillar/build/pillar_ops` 等构建副本及旧自检报告属于历史证据，不代表当前数据链、模型或服务器已经验收。
- 本批仅用现有 venv 的 `pip list --format=json`、`pip freeze` 只读查询包信息并同步配方、快照与说明；没有安装、卸载或升级依赖，没有导入 Torch/SDK 或重跑 CUDA、数据和模型任务。

## 当前安装配方与版本快照（2026-10-20）

- [requirements-core.txt](../environment/requirements-core.txt) 保留原有6项固定依赖，新增 mini 准备使用的10项直接依赖：OpenCV headless、pyquaternion、tqdm、shapely、matplotlib、scikit-learn、pillow、cachetools、pandas、motmetrics。精确版本来自本次查询，以该文件为准，不倒写为10月18日已完整记录的版本。
- [requirements-resolved.txt](../environment/requirements-resolved.txt) 保存本次真实 `pip freeze` 输出，包括传递依赖；freeze 默认不列部分引导工具，setuptools、wheel 的固定值仍在 core。该文件是环境记录，不是完整可移植锁或服务器安装入口。
- 本次包信息为 `numpy 1.26.4`、`torch 2.5.1+cu121`、`spconv-cu120 2.3.6`，与原固定值一致。此处只说明包元数据，不能升级为当前导入、CUDA 或整网验证通过。
- 现有 [install_python.sh](../environment/install_python.sh) 先安装 Torch cu121，再读取 core 和安装本地项目，因此无需新增安装入口；[constraints-torch.txt](../environment/constraints-torch.txt) 继续只约束 nvjitlink，NumPy 由 core 固定。本批未执行安装脚本，也未做重新安装验收。
- 安装脚本仍限定 `pillar` 用户、Ubuntu 22.04 和 `/mnt/d/ai_study/PillarMSF` 等本机约定；不是通用服务器部署脚本。服务器需按目标设备与路径适配后验收。

本次 freeze 的项目条目是 `-e git+https://github.com/zzh20061105/PillarMSF-reproduction.git@bf3d213b1c1e588aa83cb238ac221a0cd0920ace#egg=pillarmsf_reproduction`。它记录 pip 识别到的 Git 来源和 HEAD，不包含当前未提交改动，也不表示工作区与该提交完全一致；现有 editable 项目位置由 `pip list` 查询为 `/mnt/d/ai_study/PillarMSF`。迁移时应使用待用户审核保存的实际源码，不直接用这条 freeze 项替代项目交付。

已有mini生成入口仍显式加载固定reference SDK；2.2合成评价检查仅在本次进程显式加载third_party/nuscenes-forecast/python-sdk，不改全局PYTHONPATH或已安装包。core不另装同名现代nuscenes-devkit。OpenPCDet/PillarNeXt 及 torch_scatter 等仍为候选，不因整理而提前安装或当作已完成适配。运行与版本偏离历史见 [工作记录](work_log.md)。

### 10 月 18 日依赖变更记录

此前会话记录安装了 `opencv-python-headless 4.10.0.84`、`pyquaternion`、`tqdm`、`shapely`、`matplotlib`、`scikit-learn`、`Pillow`、`cachetools`、`pandas`、`motmetrics 1.4.0` 及连带包；使用约束保留 `numpy 1.26.4`、`torch 2.5.1+cu121`、`spconv 2.3.6`。这些是原会话的安装与有限检查记录，本批没有重测运行状态。

原记录中 `motmetrics 1.1.3` 因 Python 3.10 移除 `collections.Iterable` 无法导入，执行时改为 `1.4.0`。安装任务已获批，但该换版未事先获批；目前只记录导入兼容处理，不能据此认定 tracking 评价正确，也不在本批自动回退。

本次已补齐 core 的直接依赖和实际 freeze 记录；历史 `validation.json`、`pillar_ops_validation.json` 等运行报告保持原样，不因新快照更新为新的验证结果。

## 服务器迁移边界

`environment/` 保存安装配方、依赖版本和历史证据，不是服务器已就绪的证明。取得实例后，按真实 OS、GPU、驱动、Toolkit、编译器和路径重建环境、重编扩展并验收。不复制本机 venv 或 `.so` 作为可用服务器环境；含本机绝对路径的 mini 索引也需在目标路径重新生成。服务器准备见 [server_preflight.md](server_preflight.md)。

下文保留此前 WSL 安装及有限检查的原始记录。旧命令、硬件和“通过”只对应当时范围；其中“尚未下载”“在服务器运行数据与模型”等旧状态由上文更新，不作为当前默认启动流程或任务授权。

---

# 历史 WSL 环境与复现入口

以下为历史记录；当前环境、数据状态和运行边界以上文为准。

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
- NumPy 1.26.4；2.2已在SDK工作副本替换评价六处np.float并通过合成样例，地图np.bool保持原样、暂不测试；完整评价仍待验
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

历史安装日志在 `environment/logs/`，当时运行结果见 `environment/validation.json`。`environment/requirements-resolved.txt` 已在2026-10-20刷新为当前包快照，不再是这次历史验证时点的版本清单。

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
