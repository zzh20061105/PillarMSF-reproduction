# 复用与自行实现边界

本表是实施路线图，尚未复制或执行上游模块。模型代码与复用适配由助手完成、用户审核；项目骨架与环境准备不替代算法实现。所有 FutureDet 链接固定到 `960115e2d11e40c569c4fb9abc1f0e066e4a07b1`，forecast SDK 链接固定到 `300082bb4cb23df836c4fb7e3c9b0236e248d4f4`。许可状态见 [upstream_sources.md](upstream_sources.md)。

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
| Pillar 编码 / backbone / A-FPN | PillarNet 来源由主项目登记；论文正文与 Fig.6 / Fig.7 | PillarNet 多尺度编码与稀疏 stage 作为参考；各 stage 尺度作为接口 | 助手实现并提交用户审核：C、stage channels、A-FPN concat 次序 / stride、残差、激活、head 接口；尚无实现 |
| 训练调度与检查点 | FutureDet 官方配置、train / trainer 按需复用 | epochs、optimizer、one-cycle、采样 epoch 策略的对照 | 优先复用配置加载、训练循环、optimizer 和 checkpoint，遇阻塞做局部或薄入口适配；补 GT 调度和记录，完整重写、AMP/DDP 与旧权重转换后置；不整体安装旧依赖 |

## 固定的数据与标签契约

正式输入默认 20 sweeps，包括当前扫描；10 sweeps 仅作为 debug 假设。未来 7 个时刻包含当前 keyframe，名义时间 [0,0.5,1,1.5,2,2.5,3] 秒。历史是 LiDAR sweeps，未来是带标注 keyframes；关联 / 坐标变换使用 metadata 的实际时间，不能把两者采样频率混淆。

输入模型的点坐标和各未来 GT 坐标都在当前 LiDAR 系；导出的检测与 forecast_boxes 在 nuScenes global 系。必须核对 w/l/h 顺序、旧 Det3D yaw=-yaw-π/2 转换、velocity 的坐标系与时间单位。

上游 info box 字段包含位置 3、尺寸 3、正向速度 2、反向速度 2、正向 yaw 1、反向 yaw 1，共 12 维。AssignLabel 中完整 annotation target 可到 14 维；标准 dense 头使用其中 10 维目标。不要以数组长度猜含义或直接沿用本地改版字段。未来有效性应有单独的审计标记，与对象中心是否落在网格内的训练 mask 分开。

## 末端标注与 mask

- FutureDet 训练 info 生成遇到 annotation next 为空，会复制最后一个 annotation 到后续时刻，没有真正的 future-valid mask。
- AssignLabel 的 mask 判断尺寸与中心是否在特征图内，不能解释为未来轨迹完整性。
- forecast SDK 的 forecast_annotation 在每次循环追加 box 后检查 next；任何一次为空即 stale 并丢弃整条 GT，包括第 7 个 box 已存在而 next 为空的情况。
- 初次官方对照保留并记录作者的训练与评价差异。若后续改成严格有效时间 mask，应作为明确的协议变体，不能悄悄改变原基线分母。

## 预测头的设计假设

官方 FutureDet VoxelNet baseline 的输入是 512 通道。PillarMSF 当前计划以正文 / Fig.6 的 A-FPN stride=8、12C 为准，C=64 时为 768 通道；shared 3x3 将其变为 64 通道。官方头没有 deblock 或 ConvTranspose 上采样，head、GT 和 decoder 均保持 stride=8。

第一个时间头使用 shared feature；后续时间头拼接固定 shared feature 与上一个时间头的 feature，再产生当前时间头的输出。这是 feature 递归，不是把上一步预测坐标直接喂回。保留该语义是对照 FutureDet 的关键；Fig.7 的 stride / deconv 差异仍是待确认的论文解释。2.78M 参数的静态计算接近性只能辅助检查，不能证明结构正确或据此随意加层。

## 评价与验收边界

评价规格见 [evaluation_protocol.json](../configs/evaluation_protocol.json)。主指标取 SDK metrics_summary.json 的 mean_dist_faps_mr，分别报告 static_car / linear_car / nonlinear_car，再取三类算术平均并乘 100。mean_dist_faps 是 future-only precision 指标，不等价于 joint APf；包含 pedestrian 的 SDK 全类平均也不能直接当 car cohort macro。

K=1 / 5 使用相同导出预测与明确的分组策略。SDK 用 GT 在 top-K 候选中选择最低 FDE 的轨迹属于评价逻辑，禁止进入推理的候选筛选。static_only 必须为 false；实际源码会筛除动态预测，不能只按 README 理解为重新打分。association_oracle、jitter、postprocess 默认关闭。

上游存在两种缓存：FutureDet 的 nusc.pkl 和 SDK 的 gt.pkl，均未完整覆盖版本、路径、split 和 horizon。后续需要隔离或核对指纹；paths.example.json 的 cache_root 目前尚无代码消费，不能认为已替换上游硬编码缓存。

mini 验收仅证明接口能够打通。模型 shape / 参数量检查仅证明有限的静态性质。完整复现需要正式 20 sweeps、完整 split、训练、固定评价与真实结果；这四个规格文件没有完成任何运行或指标验证。


## 时间对应与边界补充（2026-10-13）

训练 GT 沿 annotation.next 建立，预测导出按 scene sample offset 建立，SDK 按列表位置比较。源码没有保证逐位 sample_token 和时间一致；尚未审计实际 mini 数据，不能断言已发生错位。阶段2必须逐项检查 tokens、实际间隔、跳跃与末端处理，发现问题先报告，不静默插值或改评价分母。

当前检测匹配用 dist < threshold；末端 joint APf 的 miss_rate 仅在 dist > threshold 判 miss，因此末端通过条件为 <=。这个规格勘误不改变上游评价源码；具体值见 evaluation_protocol.json。
