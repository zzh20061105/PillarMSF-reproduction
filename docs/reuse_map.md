# 复用与自行实现边界

更新：2026-10-20。本表记录已核对的上游语义、接入位置和未决接口，不表示模型已接入。已有 mini 入口只覆盖 info 准备，其运行证据与审核状态见 [进度总览](进度总览.md)。模型代码与复用适配由助手完成、用户审核。所有 FutureDet 链接固定到 `960115e2d11e40c569c4fb9abc1f0e066e4a07b1`，forecast SDK 链接固定到 `300082bb4cb23df836c4fb7e3c9b0236e248d4f4`。许可与新增候选来源见 [upstream_sources.md](upstream_sources.md)。

| 流程 | 上游具体文件 | 可参考 / 复用的语义 | 必须适配或补齐 |
| --- | --- | --- | --- |
| nuScenes info 生成 | [tools/create_data.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/tools/create_data.py)、[nusc_common.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/nuscenes/nusc_common.py) | train / val tokens，历史 sweeps，annotation next 链，未来 GT 在当前 LiDAR 坐标系下的表示 | 消除绝对路径；正式 history=20；版本 / split / horizon / 字段 schema 的可追踪 manifest；末端 GT 策略 |
| 历史点云加载 | [loading.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/pipelines/loading.py) | 历史点云到当前 LiDAR 的刚体变换；追加 time_lag | 原始 5 浮点 x/y/z/intensity/ring 读前 4 维后追加时间；不要把 ring 当 time_lag。nsweeps 含当前扫描。起始缺失历史的复制策略应显式记录 |
| 增强与标签分配 | [preprocess.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/pipelines/preprocess.py) | 一致应用到所有未来 GT 的翻转 / 旋转 / 缩放；CenterNet heatmap 与索引 | 所有点、位置、velocity、yaw 的一致变换；stride 与范围共用配置；不要沿用本地 Argoverse 标签字段 |
| GT database 与采样 | [create_gt_database.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/utils/create_gt_database.py)、[sample_ops.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/core/sampler/sample_ops.py)、[builder.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/builder.py) | trajectory static / linear / nonlinear 采样分组、整条未来 GT 的一致操作 | 许可后再决定代码移植；enable 字段的真实开关；论文 faded sampling 与末段关闭调度；记录 rate 与 epoch，不宣称官方已有 faded 实现 |
| batch 组织 | [formating.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/pipelines/formating.py) | 模型输入 / 标注的契约与 Reformat | 优先复用现有 Reformat / collate；只适配实际接口差异，dataclass 重构不是前置任务；缓存保留版本与字段含义 |
| 预测头与损失 | [center_head.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/models/bbox_heads/center_head.py)、[centernet_loss.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/models/losses/centernet_loss.py) | shared 3x3、7 个时间头、递归 future feature、hm / reg / height / dim / rot / vel 语义 | 预测头与原损失优先复用，助手做必要适配及 DIoU；保留 recursive feature 语义；runner 按需复用并核对兼容性 |
| 解码、关联与导出 | [center_head.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/models/bbox_heads/center_head.py)、[nuscenes.py](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/det3d/datasets/nuscenes/nuscenes.py) | stride 解码、旋转 NMS、velocity_dense/backcasting、多未来分组、forecast_score、global box 序列化 | 拆出独立任务接口；移除硬编码路径；坐标转换与候选关联按实际 timestamp；固定分组、rerank 和 K 的语义 |
| joint APf / cohort / top-K | [loaders.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/common/loaders.py)、[evaluate.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/evaluate.py)、[algo.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/algo.py)、[data_classes.py](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/data_classes.py)、[cohort config](https://github.com/neeharperi/nuscenes-forecast/blob/300082bb4cb23df836c4fb7e3c9b0236e248d4f4/python-sdk/nuscenes/eval/detection/configs/detection_forecast_cohort.json) | 原作者 GT 筛选、cohort 与 joint APf 的统计逻辑 | 许可元数据矛盾；np.float 等兼容修补；隔离 nuscenes namespace；GT cache 指纹；输出报告中区分 joint mAPf 与 future-only AP |
| Pillar 编码 / backbone / A-FPN | 固定 [PillarNet](https://github.com/VISION-SJTU/PillarNet/tree/0634209fb889c24104d758eae153b9ff4aa0240a)；论文正文与 Fig.6 / Fig.7；OpenPCDet / PillarNeXt 为待锁定候选 | 多尺度编码、稀疏 stage、空洞块作为参考；各 stage 尺度作为接口 | 逐文件确认特征、坐标、通道、stride、残差和激活；不能仅凭同名类或相近参数量替换。A-FPN、Stage5和DIoU候选见研究规格；尚无模型实现 |
| 训练调度与检查点 | FutureDet 官方配置、train / trainer 按需复用 | epochs、optimizer、one-cycle、采样 epoch 策略的对照 | 优先复用配置加载、训练循环、optimizer 和 checkpoint；补 GT 调度和记录。首轮官方权重兼容处理按单独任务进行，完整重写、AMP/DDP仍后置；不整体安装旧依赖 |
| 官方权重对照 | 固定 [README 的预训练模型入口](https://github.com/neeharperi/FutureDet/blob/960115e2d11e40c569c4fb9abc1f0e066e4a07b1/README.md#pre-trained-models) | 首轮用官方 n3dtf 权重验证推理、关联和评价，不重新训练 FutureDet | 核对实际权重对应配置与来源；必要时处理 spconv 1→2 的 API / 权重布局。转换成功、真实推理和评价分别验收；mini只查链路，正式对照使用完整val |

## mini info 接入与执行副本

- `scripts/prepare_nuscenes_mini.py` 负责薄入口；原 `tools/create_data.py` 会连带导入 Waymo，并在 info 后创建 GT database，不能把它整段当作本任务入口。GT数据库仍是独立任务。
- `nusc_common.py` 的 `create_nuscenes_infos()` 支持 `v1.0-mini`。按文件加载可避开 `det3d.datasets` 的包初始化；该文件仍会导入真实 SDK 及其依赖，不能将此任务称为纯标准库数据处理。入口需清楚显示实际 `nuscenes` 来源，不能把上游宽泛 `try/except` 的提示当作完整错误解释。
- 当前脚本调用采用20 sweeps、7时刻、`filter_zero=True`，不传 `past`，沿用上游默认False；上游外层也未向 `_fill_trainval_infos()` 转传该参数。这不表示past模式已验收。不要随手改成1 sweep，现有路径会访问 `sweeps[0]`。
- 上游会访问地图和CAM_FRONT相关数据路径，即使 `BEV_MAP=False` 也不能只准备JSON。真实数据需核对元数据、引用的map PNG、LiDAR文件及CAM_FRONT目录；info生成不会证明所有点文件内容均可读取或标签已正确对齐。
- 输出为独立实验子目录下的 `infos_train_20sweeps_withvelo_filter_True.pkl` 与 `infos_val_20sweeps_withvelo_filter_True.pkl`；上游不创建该子目录。实际路径、现有产物与审核状态以数据说明和进度总览为准，不在本批重跑。
- 2.1已按批准范围建立 [third_party/FutureDet](../third_party/FutureDet)，来源见 [SOURCE.md](../third_party/FutureDet/SOURCE.md)：197个上游文件原样引入，排除6个旧.o，保留完整det3d/配置/tools及说明素材。references原件不改，副本尚未做兼容或接入运行入口；数据准备入口仍使用原显式参考路径，不设置全局PYTHONPATH。不能将FutureDet与PillarNet两个det3d根混入同一执行环境。

2.2的[SDK工作副本](../third_party/nuscenes-forecast)来自SDK已锁定提交`300082bb4cb23df836c4fb7e3c9b0236e248d4f4`，来源与唯一改动见[SOURCE.md](../third_party/nuscenes-forecast/SOURCE.md)。136个来源文件中仅algo.py六处np.float改为float；[检查入口](../scripts/check_forecast_sdk.py)在现有NumPy 1.26.4中通过两个手工car、7位置、K=1样例。匹配阈值、cohort、分母与数据保持原样；cohort/K=5和完整评价尚未验收。地图代码不改、暂不测试，当前参考配置仍关闭head地图融合；现有数据准备入口未切换到新SDK。

## 固定的数据与标签契约

正式输入默认 20 sweeps，包括当前扫描；10 sweeps 仅作为 debug 假设。未来 7 个时刻包含当前 keyframe，名义时间 [0,0.5,1,1.5,2,2.5,3] 秒。历史是 LiDAR sweeps，未来是带标注 keyframes；关联 / 坐标变换使用 metadata 的实际时间，不能把两者采样频率混淆。

输入点与未来GT的目标契约为当前LiDAR系，导出检测和forecast_boxes的目标契约为nuScenes global系。2026-10-20已对现有mini car info核对中心、[w,l,h]、完整三维速度旋转及编码yaw=-yaw-π/2，绝对容差1e-6均通过，见 [数据说明](../data/README.md)。点云加载/增强和真实导出仍未运行，不能将标签核对扩写为整条坐标链已验收。

当前past=False生成路径的info十二列为位置3、[w,l,h]3、速度xy两份、编码yaw两份；两组速度/yaw由同一数组重复拼接，不能解释成正向/反向量（纠正此前说明）。另存的gt_boxes_velocity/gt_boxes_rvelocity也都是同源完整xyz速度。未来尺寸按源码沿用当前ref_box；本fork SDK的孤立/超时速度估计返回零。本次mini car几何数值验证及边界见数据说明。AssignLabel中完整annotation target可到14维，标准dense头使用其中10维目标；这些维度未因本次说明纠错而改变。未来有效性与对象中心是否落网格的训练mask仍须区分。

FutureDet的points batch是带前置batch列的拼接点表，PillarNet动态reader接收逐样本点列表，适配位置须明确。head原始rot分支是sin/cos两通道，解码后为一个yaw；原始回归分支与含velocity的物理框字段不能混用。目标JSON的 `decoded_box_fields` 名称仍待对应接口任务澄清，本批不据此改字段。

## 末端标注与 mask

- FutureDet 训练 info 生成遇到 annotation next 为空，会复制最后一个 annotation 到后续时刻，没有真正的 future-valid mask。
- AssignLabel 的 mask 判断尺寸与中心是否在特征图内，不能解释为未来轨迹完整性。
- forecast SDK 的 forecast_annotation 在每次循环追加 box 后检查 next；任何一次为空即 stale 并丢弃整条 GT，包括第 7 个 box 已存在而 next 为空的情况。
- 初次官方对照保留并记录作者的训练与评价差异。若后续改成严格有效时间 mask，应作为明确的协议变体，不能悄悄改变原基线分母。

## 预测头的设计假设

官方 FutureDet VoxelNet baseline 的输入是 512 通道。PillarMSF 当前计划以正文 / Fig.6 的 A-FPN stride=8、12C 为准，C=64 时为 768 通道；shared 3x3 将其变为 64 通道。官方头没有 deblock 或 ConvTranspose 上采样，head、GT 和 decoder 均保持 stride=8。

第一个时间头使用 shared feature；后续时间头拼接固定 shared feature 与上一个时间头的 feature，再产生当前时间头的输出。这是 feature 递归，不是把上一步预测坐标直接喂回。保留该语义是对照 FutureDet 的关键；Fig.7 的 stride / deconv 差异仍是待确认的论文解释。2.78M 参数的静态计算接近性只能辅助检查，不能证明结构正确或据此随意加层。

## 轨迹关联与可选模板

固定FutureDet的 `velocity_dense` 分支调用 `tracker()`；car的 `reject_thresh=2` 与当前D=2m假设相符。这是复用官方关联路径的依据，不足以证明PillarMSF作者使用了所有相同候选分支。前向、反向、constant分支的组合仍按评价规格核对，不另写一套未经比较的解码器。

`trajectory.py` 可生成 `<classname>_trajectory.pkl`，但其数据版本、train split和路径有硬编码。`nuscenes.py` 外层会尝试加载模板并捕获缺失；实际模板后处理仅在 `postprocess=True` 时使用。既定协议关闭postprocess，因此模板不是标准 `velocity_dense` 的必需前置，不能为准备模板引入验证集GT或擅自开启后处理。若以后批准该变体，再明确模板数据来源与适配。

## 评价与验收边界

评价规格见 [evaluation_protocol.json](../configs/evaluation_protocol.json)。主指标取 SDK metrics_summary.json 的 mean_dist_faps_mr，分别报告 static_car / linear_car / nonlinear_car，再取三类算术平均并乘 100。mean_dist_faps 是 future-only precision 指标，不等价于 joint APf；包含 pedestrian 的 SDK 全类平均也不能直接当 car cohort macro。

K=1 / 5 使用相同导出预测与明确的分组策略。SDK 用 GT 在 top-K 候选中选择最低 FDE 的轨迹属于评价逻辑，禁止进入推理的候选筛选。static_only 必须为 false；实际源码会筛除动态预测，不能只按 README 理解为重新打分。association_oracle、jitter、postprocess 默认关闭。

上游存在两种缓存：FutureDet 的 nusc.pkl 和 SDK 的 gt.pkl，均未完整覆盖版本、路径、split 和 horizon。后续需要隔离或核对指纹；paths.example.json 的 cache_root 目前尚无代码消费，不能认为已替换上游硬编码缓存。

mini 的有限验收只覆盖实际运行到的接口；info生成不等于预测和评价链已打通。模型 shape / 参数量检查仅证明有限的静态性质。完整复现需要正式20 sweeps、完整split、训练、固定评价与真实结果；本文和JSON规格本身不构成这些验证证据。


## 时间对应与边界补充（2026-10-13）

训练GT沿annotation.next建立，预测导出按scene sample offset建立，SDK按列表位置比较。2026-10-20的1.2第一小批已对现有mini car实际核对token、实际间隔与末端处理：未发现非相邻前进；标注链提前结束后复制末端token，部分slot因此不对应仍存在的预期sample。分母、比例与边界见 [数据说明](../data/README.md)。结论只覆盖所查car info。第二小批已完成其当前LiDAR几何/编码数值核对，仍不认定点云/增强/真实评价已通过，不外推到完整数据。已批准的两小批审计到此交付；2.1工作副本已建立，2.2已完成SDK评价六处np.float兼容修改与合成样例检查，后续2.3再与真实预测及评价路径对照，不静默插值、改标签或评价分母。

当前检测匹配用 dist < threshold；末端 joint APf 的 miss_rate 仅在 dist > threshold 判 miss，因此末端通过条件为 <=。这个规格勘误不改变上游评价源码；具体值见 evaluation_protocol.json。
