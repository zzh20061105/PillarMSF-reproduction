# 上游来源与版本

核对日期：2026-10-10。本文与 configs 下的两个 JSON 仅为来源记录与设计规格；未导入上游模块，未实现模型、数据管线或评价器，也未验证训练与指标。

## 固定参考来源

| 项目 | 固定版本 / 状态 | 用途 | 许可证核对结果 |
| --- | --- | --- | --- |
| [FutureDet](https://github.com/neeharperi/FutureDet) | `960115e2d11e40c569c4fb9abc1f0e066e4a07b1` | nuScenes 历史点云、未来标签、GT 采样、递归 future feature 预测头、关联与结果序列化 | 固定版本完整 Git 树中未发现 LICENSE / NOTICE / COPYING。部分文件头注明继承 Det3D 的 MIT 代码；这不等于 FutureDet 全仓库已提供 MIT 授权。当前只作为算法与接口参考，直接移植前按文件核对来源与许可。 |
| [nuscenes-forecast](https://github.com/neeharperi/nuscenes-forecast) | `300082bb4cb23df836c4fb7e3c9b0236e248d4f4`，main 的核对快照 | joint APf、K=1 / 5、运动 cohort 分类与未来 GT | [LICENSE.txt](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/LICENSE.txt) 标明 Apache-2.0；[setup.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/setup/setup.py) 的 metadata 标明 CC-BY-NC-SA-4.0 / non-commercial。记录此不一致，后续复制或发布前澄清具体文件的授权，暂不把全仓库一概标为某一许可。 |
| [CenterPoint](https://github.com/tianweiy/CenterPoint) | 目前仅参考，尚未记录仓库 commit | 单帧检测、几何、旋转 NMS、现代兼容实现的补充参考 | [LICENSE](https://github.com/tianweiy/CenterPoint/blob/master/LICENSE) 为 MIT；实际移植应固定 commit 并保留对应声明。 |
| PillarNet | 主项目另行锁定来源版本 | Pillar 编码与稀疏主干参考 | 本文件不替代主项目的来源 / 许可记录，尚未在此登记 commit。 |

FutureDet [README](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/README.md) 明确引用 [Det3D 的固定版本](https://github.com/poodarchu/Det3D/tree/56402d4761a5b73acd23080f537599b0888cce07)。新项目沿用类似接口便于理解与对照，不承诺旧 runner 或 CUDA 扩展可直接使用。

当前旧项目已经改为 Argoverse：共享 loading / Preprocess / AssignLabel 和旧 forecast SDK 的部分加载、评价存在 Argoverse 假设。它可提供组织方式与局部实现参考，不能标作官方 nuScenes baseline 或直接作为论文数据与评价协议。

## 官方 FutureDet 参考规格

权威配置为 [nusc_centerpoint_forecast_n3dtf_detection.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/configs/centerpoint/nusc_centerpoint_forecast_n3dtf_detection.py)，本地规格文件是 [official_futuredet_reference.json](../configs/official_futuredet_reference.json)。

| 项目 | 固定版本源码值 |
| --- | --- |
| 检测类别 | car，单类别 heatmap |
| 输入 | 20 sweeps，包括当前扫描与 19 个历史扫描；每点 5 维 x / y / z / intensity / time_lag |
| 预测时间 | timesteps=7，包含当前时刻；名义上 0 到 3 秒，keyframe 间隔约 0.5 秒 |
| 模型 | VoxelNet，VoxelFeatureExtractorV3，SpMiddleResNetFHD，RPN |
| 头输入 / 共享通道 / 输出步长 | 512 / 64 / 8 |
| 点云范围 / voxel size | [-54,-54,-5,54,54,3] / [0.075,0.075,0.2] |
| 头分支 | reg=2、height=1、dim=3、rot=2、vel=2、hm=1 |
| 训练 | 20 epochs，one-cycle lr_max=0.001，Adam，wd=0.01，grad_clip=35 |
| 测试 | score_threshold=0.1，旋转 NMS IoU=0.2，pre=1000，post=83，max_per_img=500 |

README 的数据目录示例写 10 sweeps，但所核对主配置写 20 sweeps。正式 PillarMSF 默认采用 20 sweeps；10 sweeps 仅可作为明确命名、与正式结果分开的 debug 假设。扫描数量不是 20 个 0.5 秒 keyframe，不能据此把历史窗口解释成 10 秒。

官方 PointPillars 变体是另一份 [配置](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/configs/centerpoint/nusc_centerpoint_pp_forecast_n3dtf_detection.py)：PFN [64,64]，head 输入 384，output stride=4。不得将它与上述 VoxelNet baseline 混写，也不得把本地 768 通道的目标设计标成官方 FutureDet 配置。

GT sampler 配置的 enable=False 不能单独证明采样已关闭：固定版本的 [builder](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/builder.py) 与 [Preprocess](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/pipelines/preprocess.py) 没有按该字段实现完整的开关语义。该版本也没有核实到按最后 epoch 关闭的 faded GT 调度。论文要求的 faded sampling 必须在后续实现阶段显式补齐并记录开始 / 关闭 epoch。

## PillarMSF 目标与官方参考的边界

计划采用独立 PyTorch / Det3D 风格接口项目。参考 FutureDet 的任务语义和评价；参考 PillarNet 主干；PillarMSF 的 A-FPN、残差、激活与 DIoU 等由助手实现、用户审核。

目前 A-FPN 接口设计假设是按正文与 Fig.6 输出 stride=8、12C；候选 C=64，因此 head 输入 768。保留 FutureDet 的 shared 3x3 768->64 和递归 future feature 语义，头与 GT / decoder 同为 stride=8。官方 [center_head.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/models/bbox_heads/center_head.py) 本身没有额外 deblock 上采样。本地旧版新增的 deblock 不能机械迁入，以免二次改变步长。Fig.7 与 Fig.6 的差异应继续列为论文接口解释假设；不能仅为凑参数量而加 projection / downsample。

上述通道数、论文参数量推算仅是静态设计依据，未运行模型，不构成结构唯一性或科学复现证据。

## 兼容性记录

FutureDet README 的原环境是 Ubuntu 18.04 / Python 3.7.10 / PyTorch 1.8.1 / CUDA 10.1 / cuDNN 7.6.5 / spconv 1.0 / APEX。这些值不是新项目安装方案，也未证明在 Windows、Python 3.10 或 spconv 2 上可运行。

- [FutureDet requirements](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/requirements.txt) 和 [SDK requirements](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/setup/requirements.txt) 含旧版本限制与未锁定依赖，不能直接整体用于现代环境。
- SDK [algo.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/algo.py) 使用 np.float。该别名从 [NumPy 1.24](https://numpy.org/doc/1.24/release/1.24.0-notes.html) 起失效，因此 NumPy 1.x 并不自动保证旧 SDK 可运行；后续按语义局部替换，记录 patch，不作全局 monkey patch。
- [NumPy 1.26.4](https://numpy.org/devdocs/release/1.26.4-notes.html) 支持 Python 3.9-3.12，可列为 Python 3.10 的候选；这只说明 Python 版本范围，不代表整个项目已兼容。
- forecast SDK 的包名是 nuscenes-devkit，版本 1.0.7，与现代 devkit 使用同一 nuscenes import namespace。后续通过隔离的 evaluator / adapter 保持来源清楚，不能盲目共装后依赖导入顺序。
- spconv 1->2 的 API / 权重、旧 APEX -> PyTorch AMP、NMS 扩展与 runner 均属后续适配项。本阶段没有实施或验证这些迁移。

mini 数据只用于打通接口与检查；论文指标需要固定版本、完整 trainval split、完整训练与一致评价协议。精确复现 FutureDet 33.5 / 35.6 不是开始实现 PillarNet / A-FPN 的硬前置；正式报告仍应有可追踪的参考 baseline / 控制实验与差异说明。

