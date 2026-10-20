# PillarMSF 复现规格与假设台账

本项目以论文原方法为目标。当前文件用于固定研究规格和记录歧义，模型模块由助手实现并由用户审核；它们不表示模型已经实现、训练已完成或论文指标已经复现。JSON 是研究规格，不是可直接启动训练的完整配置。`null` 表示尚未确认，不表示数值为零或功能关闭。

规范整合更新：2026-10-20。本文归并研究依据、候选实现与未决问题，不改变模型、损失、数据或训练默认。当前阶段和审核状态见 [进度总览](进度总览.md)，规则见 [实现与执行边界](implementation_boundary.md)。

论文来源：`C:\Users\zengzihang\Downloads\SPPCSPC+noIoU+downsample.zip\papers\Multi-Scale Point Cloud Fusion-Driven .docx`。方法依据第 III 节及 Fig.3–7；训练依据 IV.A；指标依据 IV.B；对照值依据 Table I–III；消融依据 Table VI–VIII。

另有中英对照阅读材料 `C:\Users\zengzihang\Downloads\Multi-Scale Point Cloud Fusion-Driven 中英对照.docx`。阅读记录可补充歧义线索，不能代替原文、作者配置或实际源码证据。

## 来源标记

- `paper`：论文明确给出，或图示明确表达的关系。
- `future_det_inherited`：论文未完整说明，沿用经审计、固定版本的 FutureDet 参考协议。必须保留继承记录。
- `engineering_assumption`：为使规格可实现而作出的初始工程选择，未获作者确认。
- `pending` / JSON `null`：证据不足，实施相关模块前需要补齐。

## 论文固定目标

| 项目 | 规格 |
| --- | --- |
| 数据 | nuScenes；多个历史帧点云变换到当前帧坐标系 |
| 原始点特征 | x、y、z、反射强度、相对当前帧的时间差；编码器可能增加的特征需另行核对 |
| ROI | x/y 为 [-51.2, 51.2] m；z 为 [-5, 3] m |
| Pillar | (0.125, 0.125, 8.0) m；动态编码、MLP 与 max-pooling |
| 主干 | Stage1–4 为稀疏 2D 残差模块；Stage5 为普通 2D 残差深度扩展；输出 Stage3/4/5 |
| A-FPN | 空洞率 1、6、12、18；深层分支 concat 后卷积；按 Fig.6 逐级上采样相加；最后统一到 stride8 拼接 |
| 预测 | 当前及未来热图、框状态；未来时域 3 秒；逆向贪心匹配生成轨迹 |
| 损失 | Gaussian focal 的 α=2、β=4；L1 框回归；DIoU；总损失 Lhm + 0.25 Lpre + 0.25 LDIoU |
| 训练 | AdamW、one-cycle；峰值 LR=1e-3、weight decay=0.01、momentum 范围 [0.85, 0.95]；batch2；20 epochs |
| 增强 | x/y 随机翻转；scale=[0.95,1.05]；rotation=[-π/8,π/8]；faded GT copy-paste |
| 采样关闭 | 第 20 轮关闭 GT sampling；零基 epoch 对应 19。此前具体 fading schedule 未说明 |
| 评价 | K=1/5 是候选轨迹数量；检测中心距离阈值 0.5/1/2/4 m；静止、线性、非线性三类；预测使用 APf 联合评价 |

## FutureDet 继承默认

正式默认 `nsweeps=20`，来源是 FutureDet 参考流程，论文没有给出历史 sweep 数量。调试可单独降低 sweep 数，但必须标记为调试覆盖；不能把 10 或其他调试值写成原论文事实。

正式目标类别采用 `car`，继承已审计的 FutureDet car 协议。名义 keyframe 间隔采用 `future_dt_s=0.5`；`future_steps=7` 包含当前时刻和 6 个未来时刻，偏移为 `[0, 0.5, 1, 1.5, 2, 2.5, 3]` 秒。因此该字段不能读成 7 个未来时刻。以上来源为 FutureDet 参考配置与 nuScenes keyframe 节奏，不是 PillarMSF 正文明确给出的离散采样参数；几何变换和关联仍使用 metadata 中实际时间戳。

数据划分、运动类别规则、未来标签 mask、GT 目标编码、候选分组和评分、APf 成功判据及评价代码继续使用经审计、固定版本的 FutureDet 协议。参考配置见 `configs/official_futuredet_reference.json`。已核实的继承值应写入配置并注明来源；作者细节未确认或尚未完成配置映射的项保留为 `null`。

Gaussian target、局部极大值、score 阈值、NMS、GT 数据库采样配置以及优化器未说明项也需要审计参考配置。AdamW 与 one-cycle 的实际封装须核对：峰值 LR 不是恒定 LR；momentum 的实现不能未经检查就等同 SGD 动量。

固定 FutureDet n3dtf 配置已记录 `adam, fixed_wd=True`、`moms=[0.95,0.85]`、`div_factor=10`、`pct_start=0.4` 和 `grad_clip=35`，详见 `official_futuredet_reference.json`。它们可作为后续继承候选，但不等于 PillarMSF 论文逐项给出，也未在本批补填目标 JSON。解耦 weight decay 的 Adam 包装仍需核对 beta、参数分组和调度实现，不能直接等同于任意版本的 AdamW 默认参数；参考配置也没有已核实的 faded GT 关闭调度。

## 初始工程假设

| 项目 | 当前选择 | 依据和边界 |
| --- | --- | --- |
| 基础通道 | C=64 | 按图示及该 C 估算 head 约 2.783M，与 Table III 的 2.78M 接近；这支持该选择但不能唯一证明 C 或完整 head 结构 |
| 网格 | 有效 820×820；存储 832×832 | 102.4/0.125=819.2；有效格数取 ceil，最后边界 cell 部分有效，再向正 x/y 补齐到 16 的倍数。ROI 不变，padding 不扩大物理范围 |
| 尺寸 | Stage3/4/5 存储尺寸为 208/104/52；A-FPN 输出 104×104×768 | Fig.6 的 stride4/8/16 关系与 12C 拼接，加上 C64 和 832 存储网格推得；解码必须过滤物理 ROI 外的位置 |
| A-FPN 连接 | 按 Fig.6 实现 | Stage3/4 经 1×1 Conv；Feature1 两次 2×2 stride2 反卷积逐级相加得到 Feature2/3；Feature3 经 3×3 stride2 Conv、Feature1 另经 2×2 stride2 反卷积后与 Feature2 拼接 |
| 预测头接入 | input=768、shared=64、time_count=7、forecast_feats=true、extra_upsample=false | 起始设计沿用官方 FutureDet head 的共享通道与递归未来特征方案，输入由官方 VoxelNet 的 512 改为目标 A-FPN 的 768；这是接入设计假设，不是作者完整 head 实现证据。内部参考见 `configs/official_futuredet_reference.json` |
| 激活 | LeakyReLU 暂取 negative_slope=0.01 | 论文只说“通常 0.01”；backbone 单元使用已明确，pillar/neck/head 的替换范围未完整确认 |
| Batch | 单卡 global batch2、无梯度累积 | 论文列 RTX3080 12G，但未直接定义 global/per-device；该解释需记录，不能宣称作者已确认 |
| 匹配阈值 | D=2 m | 论文描述“通常 2 米”，暂作默认，未获作者实际配置确认 |

网格取整和 padding 是工程策略。若获得作者配置，必须重新核对边界、张量尺寸和坐标映射，不能静默改变 ROI 或 pillar 分辨率。

## DIoU 规格

默认 `bev2d_axis_aligned`，另保留 `axis_aligned_3d` 候选。正文将 IoU 描述为交并面积，因此二维解释有较直接的文字依据；论文没有明确 DIoU 的维度，也未说明旋转框如何处理，默认尚未获作者确认。

- 二维默认使用 [x±l/2, y±w/2] 的轴对齐代理矩形、xy 中心距离和二维最小包围框对角线。
- 三维候选参考已有 PillarNet 风格实现：体积 IoU、xyz 中心距离和三维包围框对角线。
- 两种候选均忽略 yaw；它们不等同旋转框真实 IoU。yaw 仍由框回归损失监督。
- 在有效 GT 中心位置提取已解码的米制预测框；有效对象取平均、mask 无效未来标签、空目标返回可求导零，属于工程约定。
- 当前/未来时刻如何归约及分母 epsilon 尚未确认，实施前应固定并记录；不要根据验证集最优结果倒推作者定义。

式(6)为 `1 - IoU + ρ²/c²`；原始 DIoU 论文也以二维矩形定义该公式：[Distance-IoU Loss 原文](https://csdwren.github.io/papers/2020_aaai_DIoU.pdf)。这支持二维解释，但不能替代 PillarMSF 作者实现证据。

## 两种基线与消融顺序

1. **FutureDet 参考基线**：首轮加载官方预训练权重验证推理、解码与评价，并在完整验证集形成对照，不重新训练 FutureDet。必要的权重兼容处理按单独小任务实施。
2. **论文 Pillar 消融基线**：Pillar 编码＋原始 ResNet18＋预测头；以 ReLU 起步，不启用深度扩展、A-FPN 或 DIoU。

| 组别 | 深度扩展 D | A-FPN | DIoU | LeakyReLU |
| --- | --- | --- | --- | --- |
| B0 基线 | 关闭 | 关闭 | 关闭 | 关闭 |
| B1 | 开启 | 关闭 | 关闭 | 关闭 |
| B2 | 开启 | 开启 | 关闭 | 关闭 |
| B3 | 开启 | 开启 | 开启 | 关闭 |
| B4 完整方法 | 开启 | 开启 | 开启 | 开启 |

以上是 Table VI–VIII 的组别定义，不表示本轮全部训练。首轮仅在服务器训练 B4 完整模型20轮；B0—B3 是否补做，按完整模型结果、预算和后续批准决定。若补做，各组固定数据、训练预算和评价协议，独立训练并保存配置与实验记录，不从一组连续微调后充作独立消融。当前没有完成这些训练。

## 必须保留的歧义与报告差异

1. **颈部参数量**：4.13M 仅对应空洞分支宽度 q=256、C64、Conv＋BN 等静态假设。q=384/512 分别约5.446M/6.758M，Table III 报告6.83M；Fig.5 未标分支宽度，selected 保持 null。q 不改变最终768通道接口。不能为补差额增加 Fig.6 未画出的平滑层；这些估算不是运行统计。
2. **Stage5**：正文描述普通残差模块有三个 Conv＋BN＋LeakyReLU 单元；模块重复数、kernel、stride 与 shortcut 投影的完整规格仍待核对。
3. **A-FPN 称谓**：正文交替使用 Attention-based、Atrous、Adaptive；结论提及 dynamic weighted fusion，未给定义。先采用 Fig.6 明确连接，不凭称谓增加 attention 或可学习融合权重。
4. **K 的措辞**：一处误称 K=5 为 prediction horizon；评价部分明确 K 是 top-K 候选数，预测时域仍为 3 秒。
5. **K1 主表/消融表不一致**：Table I 完整模型为 69.3/30.0/11.4/36.9；Table VI 全开为 69.3/29.6/11.4/36.8。分别保留，不臆造差异原因。
6. **训练细节**：初始/最终 LR、pct_start、div_factor、final_div_factor、β₂、eps、WD 分组、seed、AMP、gradient clipping、drop_last、预训练及 GT fading schedule 未完整给出。

7. **A-FPN 增益的表述（阅读记录线索，待原文复核）**：旧阅读记录称正文的K5增益为3.1个百分点，而Table VII的37.8→40.2对应2.4个百分点。本轮未对原DOCX复核；后续须核对两处原文与对照条件，不据此补造结果。
8. **深度扩展的检测结果（阅读记录线索，待原文复核）**：旧阅读记录称Table VIII某组加入D后mAPdet为75.2→74.8。本轮未对原DOCX复核，不能据此概括为所有指标均提高或降低。

主表参考值为 mAPf(K1)=36.9%、mAPf(K5)=40.4%、mAPdet=76.6%。这些是既有规格中的论文报告值，不是本项目测得结果，也不构成精确复现已完成的证据。另有旧阅读记录称同表FutureDet对照为33.5% / 35.6% / 74.9%；该新增线索本轮未对原DOCX复核，待原文复核后再作为正式对照引用。

## 待批准的实现候选

下列候选保留后续阅读所得依据，尚未替代本文和 JSON 原值。进入对应模块前，需说明具体版本、接口、论文依据及验证范围，再单独确认。

| 候选 | 依据与用途 | 当前边界 |
| --- | --- | --- |
| Stage5 参照 PillarNet `conv5`，不加 shortcut | 一个 3×3 stride2 Conv 加两个普通 dense Conv block，可作为三个 Conv＋BN＋激活单元的结构候选。既有 C64 静态估算为 Stage1–4 约6.46M、Stage1–5约8.232M，接近 Table III 的8.23M | 论文称其为残差模块，而该 `conv5` 无 shortcut；identity shortcut 可不增加参数，参数量吻合不能确定连接。无 shortcut 方案仅为待批准候选，重复数、kernel、stride 与残差规格仍未定 |
| DIoU 参照 PillarNeXt `IouRegLoss` / `bbox3d_overlaps_diou` | 三维轴对齐、忽略 yaw 的实现是候选；损失结构与0.25系数可作线索 | 具体源码版本尚未锁定；同一系数不足以唯一确定几何。当前默认仍为 `bev2d_axis_aligned`，不在本批切换到3D |
| 将 pillar、neck、head 的激活一并替换为 LeakyReLU(0.01) | 可作为全局激活方案的讨论对象 | 当前只确认 backbone 的替换范围；全局替换及斜率仍待对应任务批准，不能因使用新来源就顺带生效 |

Fig.7 既有阅读记录的 head 输入为 `(H/16, 4C)` 并画有反卷积，与 Fig.6 的 `(H/8, 12C)` 输出存在接口歧义。当前保留 stride8、768→64、无额外反卷积的接入假设，不把它改写为作者实现已确认。A-FPN 分支宽度 q 继续未知，不能为匹配6.83M参数而增加图中未给出的模块。

## 现行执行路线与证据边界（2026-10-20）

研究编号统一为阶段1—5：准备数据 → 验证评价链 → 实现 PillarMSF → 服务器小规模闭环 → 正式训练与对比；子任务采用1.1、1.2等格式。旧 L/G 与 P0—P5 不再作为现行执行顺序，历史执行记录保留在工作日志。阶段安排只在 [进度总览](进度总览.md) 维护。

执行主体优先使用固定 FutureDet，数据、现有 runner、预测头、解码和 forecast SDK 按需复用。本机按批准批次进行 CPU 数据准备、轻量检查与 GPU 推理调试；所有实际训练，包括 CPU、mini 和短训练，均在服务器进行。服务器尚未就绪，预算未定，优先按需省钱。

阶段2先加载官方权重验证推理、轨迹解码与评价链，必要的权重兼容处理不再笼统后置；全面重写 runner/SDK、AMP 与 DDP 不属于默认首版范围。mini 只验证链路与小规模闭环，正式指标使用完整验证集；尚无本项目测得的 APf。

B0、B1 未开启 A-FPN 时的颈部及预测头输入仍待定；PillarVTP 的1.77M不能直接认定为本论文消融基线。各组是独立模型配置，不是从B0连续微调到B4。

20 sweeps、7位置与0.5秒名义节奏保持继承记录。2026-10-20的mini car时间审计未发现非相邻annotation前进，但量化了链尾重复及其造成的slot/sample不对应，见 [数据说明](../data/README.md)。第二小批已按1e-6绝对容差验证42,966个mini car框位置的当前LiDAR中心、wlh、速度与yaw编码，超限/非有限数均为0；重复速度/yaw字段是同源拼接，尺寸沿用当前ref_box、孤立/超时速度归零是已核对的上游继承规则。它不证明作者方法正确或完整数据/点云/增强/真实评价已通过。本批保留标签和原有方法默认，训练末端复制与评价末端丢弃差异留到阶段2结合真实输出对照。

参考配置中的 `samples_per_gpu=1` 与本项目 batch2 的解释需分别记录；faded GT sampling 的关闭调度仍需实现和验收。已记录的上游 one-cycle 值不等于 PillarMSF 作者完整配置已确认，不在本批补填训练参数。

## 协作与同步

实现、适配与验证由助手承担，用户审核范围、进度、代码和假设。每个小任务先说明并确认，完成后报告差异与未验证项、停审；发生版本或范围偏离先说明。

同批更新实际受影响的 README、进度、环境配方与研究规格，并简要追加工作记录。只保留与任务相关、能够识别实际错误的检查，不为假想风险扩建防御框架；来源工具冻结。完整规则见执行边界，本台账与 JSON 仍不是可运行训练配置。

Stage5 结构、DIoU 维度/归约和激活替换范围等方法选择仍待对应任务确认。候选依据已归入本文；来源线索见 [上游来源](upstream_sources.md)，具体复用与接口见 [复用边界](reuse_map.md)。本批未改变 JSON 中的方法默认，也未运行模型或实验。
