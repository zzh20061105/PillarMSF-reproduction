# 上游来源与版本

更新：2026-10-20。固定来源与参考配置沿用既有版本；2.1已从本地FutureDet原件建立项目内工作副本，没有重新下载或联网更新。2.2另建立forecast SDK工作副本，仅适配评价六处np.float并通过两个合成评价样例；地图修改与测试暂缓。已有mini入口仍调用原显式参考路径；这些不代表模型或真实数据完整评价可运行。当前状态见 [进度总览](进度总览.md)，本文与JSON是来源及设计规格。

## 固定参考来源

| 项目 | 固定版本 / 状态 | 用途 | 许可证核对结果 |
| --- | --- | --- | --- |
| [FutureDet](https://github.com/neeharperi/FutureDet) | `960115e2d11e40c569c4fb9abc1f0e066e4a07b1` | 执行主体；nuScenes 历史点云、未来标签、GT 采样、递归 future feature 预测头、关联与结果序列化 | 固定版本完整 Git 树中未发现 LICENSE / NOTICE / COPYING。部分文件头注明继承 Det3D 的 MIT 代码；这不等于 FutureDet 全仓库已提供 MIT 授权。已用于mini索引准备；后续直接移植按实际文件核对来源与许可。 |
| [nuscenes-forecast](https://github.com/neeharperi/nuscenes-forecast) | `300082bb4cb23df836c4fb7e3c9b0236e248d4f4`，main 的核对快照 | joint APf、K=1 / 5、运动 cohort 分类与未来 GT | [LICENSE.txt](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/LICENSE.txt) 标明 Apache-2.0；[setup.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/setup/setup.py) 的 metadata 标明 CC-BY-NC-SA-4.0 / non-commercial。保留两处原文及此不一致，工作副本不新增统一许可判断；对外发布前仍需澄清适用授权。 |
| [PillarNet](https://github.com/VISION-SJTU/PillarNet) | `0634209fb889c24104d758eae153b9ff4aa0240a` | Pillar 编码、稀疏主干、Stage5候选与native算子参考 | 固定版本 [LICENSE](https://github.com/VISION-SJTU/PillarNet/blob/0634209fb889c24104d758eae153b9ff4aa0240a/LICENSE) 为MIT；该commit已存在于来源锁与兼容记录，本文同步补登。保留参考原件，不据此认定其结构等同于PillarMSF。 |

以上三份固定来源由 `environment/source-lock.json` 登记。commit是Git某次提交的版本编号，用来确定那次源码状态；FutureDet短号960115e2对应上表完整编号，不是本次临时生成。锁中的clean字段是历史状态，不要求每批重跑冻结的来源工具。

2.1已建立 [FutureDet工作副本](../third_party/FutureDet)，以既有完整提交为基线：197文件与本地参考原件内容一致，另加 [SOURCE.md](../third_party/FutureDet/SOURCE.md)，排除6个旧.o且不复制.git；原件本次仍干净。副本后续由主仓库记录改动，本次尚未暂存/提交/上传，未安装、编译或运行上游代码。原作者注释与声明保留，不新增或推断上游授权。

2.2已建立[forecast SDK工作副本](../third_party/nuscenes-forecast)，复制固定原件的136个Git跟踪文件，不复制.git、缓存或未跟踪文件，另加[SOURCE.md](../third_party/nuscenes-forecast/SOURCE.md)。仅algo.py六处类型别名替换及一行中文注释，135个来源文件保持原样，包括map_mask.py；地图修改和测试由用户明确暂缓。原件保持干净；许可证和setup元数据原文保留，没有安装上游requirements或切换现有数据生成入口。

FutureDet [README](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/README.md) 明确引用 [Det3D 的固定版本](https://github.com/poodarchu/Det3D/tree/56402d4761a5b73acd23080f537599b0888cce07)。新项目沿用类似接口便于理解与对照，不承诺旧 runner 或 CUDA 扩展可直接使用。

当前旧项目已经改为 Argoverse：共享 loading / Preprocess / AssignLabel 和旧 forecast SDK 的部分加载、评价存在 Argoverse 假设。它可提供组织方式与局部实现参考，不能标作官方 nuScenes baseline 或直接作为论文数据与评价协议。

## 待锁定的补充来源线索

以下为既有调研线索，尚未写入来源锁、未接入本项目；表中可变链接只供定位。实际复用前需固定commit、具体文件和许可，并核对特征、坐标、网格、通道及stride，不能按仓库名直接替换模块。本批不重查星数、最新提交、远程可用性或性能。

| 项目 | 可考察的文件或模块线索 | 未完成事项与边界 |
| --- | --- | --- |
| [OpenPCDet](https://github.com/open-mmlab/OpenPCDet) | `pcdet/models/backbones_3d/vfe/dynamic_pillar_vfe.py`、`spconv_backbone_2d.py`；动态pillar VFE与PillarRes18主干 | 既有调研记录根许可为Apache-2.0，具体版本和文件许可待锁定；`torch_scatter`方案可减少自编pillar_ops的移植，但仍有torch_scatter、spconv与设备依赖。须核对不同VFE类的特征和坐标接口，不声称等价替换或无需任何原生扩展 |
| [PillarNeXt](https://github.com/qcraftai/pillarnext) | `ASPPNeck`、`IouRegLoss` / `bbox3d_overlaps_diou`、`SparseResNet` | 既有调研记录为CC BY-NC-SA 4.0，复制前核对具体版本及文件声明；空洞率和损失系数可作线索，不能据此认定完整颈部、3D DIoU或主干就是作者实现 |
| [MarfredBarrera/FutureDet](https://github.com/MarfredBarrera/FutureDet) | spconv 2.x适配思路、`convert_spconv_checkpoint.py`线索 | 版本、实际diff和许可尚未锁定；其mini/权重评价成功是上游自述，未独立验证。只作现代化补丁参考，不整体引入、不照抄未核对的转换规则 |
| [PillarNet-LTS](https://github.com/VISION-SJTU/PillarNet-LTS) | 后续PillarNet实现的备查线索 | 未锁commit、未比较差异；不自动替换现有PillarNet原件 |
| [CenterPoint](https://github.com/tianweiy/CenterPoint) | 单帧检测、几何与旋转NMS的补充参考 | 既有来源记录为MIT；尚未锁commit，实际移植应固定版本并保留对应声明，首轮无需整体引入 |

此前检索没有取得可作为实现依据的PillarMSF/PillarVTP公开作者代码；这是已知证据的边界，不是对所有公开渠道的穷尽结论。Stage5、q、DIoU和激活等未决项仍按 [研究规格](reproduction_spec.md) 处理。

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

参考配置另有 `samples_per_gpu=1`、`fixed_wd=True`、`moms=[0.95,0.85]`、`div_factor=10`、`pct_start=0.4`。它们与目标batch2及未完整给出的论文训练细节分别记录；参考值可用于后续继承选择，不把二者合写为所有超参数和采样实现均一致。

## 官方预训练权重与首轮对照

固定FutureDet [README的Pre-trained Models入口](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/README.md#pre-trained-models) 指向作者权重目录。首轮已确定用官方n3dtf权重验证推理、`velocity_dense`轨迹关联和SDK K1/K5评价，不重新训练FutureDet。实际取得的权重、配置对应关系、必要的spconv兼容处理与结果需要逐项留证；README链接本身不证明下载、转换或运行成功。

阶段2的mini评价只验证链路，完整val用于正式对照；FutureDet论文数值不是mini验收门槛。权重兼容处理按单独任务说明，不因其被列入路线就自动运行推理或转换全部旧权重。

## PillarMSF 目标与官方参考的边界

固定FutureDet为执行主体，工作副本已建立在third_party/FutureDet；references原样保留。后续具体适配逐批确认，当前197文件为未经算法改动的来源基线，尚未接入执行入口。自有模块放src/pillarmsf，参考PillarNet及待锁定候选的编码/主干/损失；两个同名det3d包不能拼进全局PYTHONPATH。

目前 A-FPN 接口设计假设是按正文与 Fig.6 输出 stride=8、12C；候选 C=64，因此 head 输入 768。保留 FutureDet 的 shared 3x3 768->64 和递归 future feature 语义，头与 GT / decoder 同为 stride=8。官方 [center_head.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/models/bbox_heads/center_head.py) 本身没有额外 deblock 上采样。本地旧版新增的 deblock 不能机械迁入，以免二次改变步长。Fig.7 与 Fig.6 的差异应继续列为论文接口解释假设；不能仅为凑参数量而加 projection / downsample。

上述通道数、论文参数量推算仅是静态设计依据，未运行模型，不构成结构唯一性或科学复现证据。

## 兼容性记录

FutureDet README 的原环境是 Ubuntu 18.04 / Python 3.7.10 / PyTorch 1.8.1 / CUDA 10.1 / cuDNN 7.6.5 / spconv 1.0 / APEX。这些是上游历史值，不是当前安装方案；现有WSL与目标服务器的实际版本、配方及验证层次见 [环境说明](environment.md)。

- [FutureDet requirements](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/requirements.txt) 和 [SDK requirements](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/setup/requirements.txt) 含旧版本限制与未锁定依赖，不能直接整体用于现代环境。
- SDK [algo.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/algo.py) 使用 np.float。该别名从 [NumPy 1.24](https://numpy.org/doc/1.24/release/1.24.0-notes.html) 起失效，因此 NumPy 1.x 并不自动保证旧 SDK 可运行；后续按语义局部替换，记录 patch，不作全局 monkey patch。
- [NumPy 1.26.4](https://numpy.org/devdocs/release/1.26.4-notes.html) 支持 Python 3.9-3.12，可列为 Python 3.10 的候选；这只说明 Python 版本范围，不代表整个项目已兼容。
- forecast SDK 的包名是 nuscenes-devkit，版本 1.0.7，与现代 devkit 使用同一 nuscenes import namespace。后续通过隔离的 evaluator / adapter 保持来源清楚，不能盲目共装后依赖导入顺序。
- spconv 1->2 的API / 权重、NMS扩展与runner按实际阻塞适配；官方权重兼容属于阶段2单独任务。AMP/DDP不属于默认首版，不能把上游APEX要求机械搬到单卡流程。

mini数据只用于打通实际检查到的接口；论文指标需要固定版本、完整split及一致评价协议。首轮PillarMSF B4在服务器完整训练20轮；FutureDet正式对照使用官方权重在完整val评价。精确达到FutureDet论文参考数值不是开始实现PillarMSF的硬前置；正式报告仍保留参考配置、权重来源和差异说明。阶段1—5及当前审核状态只在进度总览维护。
