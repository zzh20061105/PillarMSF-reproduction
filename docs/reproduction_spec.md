# PillarMSF 复现规格与假设台账

本项目以论文原方法为目标。当前文件用于固定研究规格和记录歧义，模型模块由助手实现并由用户审核；它们不表示模型已经实现、训练已完成或论文指标已经复现。JSON 是研究规格，不是可直接启动训练的完整配置。`null` 表示尚未确认，不表示数值为零或功能关闭。

论文来源：`C:\Users\zengzihang\Downloads\SPPCSPC+noIoU+downsample.zip\papers\Multi-Scale Point Cloud Fusion-Driven .docx`。方法依据第 III 节及 Fig.3–7；训练依据 IV.A；指标依据 IV.B；对照值依据 Table I–III；消融依据 Table VI–VIII。

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

1. **FutureDet 参考基线**：验证数据、训练入口、解码与评价协议，并作为主表对照对象。
2. **论文 Pillar 消融基线**：Pillar 编码＋原始 ResNet18＋预测头；以 ReLU 起步，不启用深度扩展、A-FPN 或 DIoU。

| 组别 | 深度扩展 D | A-FPN | DIoU | LeakyReLU |
| --- | --- | --- | --- | --- |
| B0 基线 | 关闭 | 关闭 | 关闭 | 关闭 |
| B1 | 开启 | 关闭 | 关闭 | 关闭 |
| B2 | 开启 | 开启 | 关闭 | 关闭 |
| B3 | 开启 | 开启 | 开启 | 关闭 |
| B4 完整方法 | 开启 | 开启 | 开启 | 开启 |

以上顺序对应 Table VI–VIII。各组固定数据、训练预算和评价协议；每组独立保存配置与实验记录。当前没有完成这些训练。

## 必须保留的歧义与报告差异

1. **颈部参数量**：4.13M 仅对应空洞分支宽度 q=256、C64、Conv＋BN 等静态假设。q=384/512 分别约5.446M/6.758M，Table III 报告6.83M；Fig.5 未标分支宽度，selected 保持 null。q 不改变最终768通道接口。不能为补差额增加 Fig.6 未画出的平滑层；这些估算不是运行统计。
2. **Stage5**：正文描述普通残差模块有三个 Conv＋BN＋LeakyReLU 单元；模块重复数、kernel、stride 与 shortcut 投影的完整规格仍待核对。
3. **A-FPN 称谓**：正文交替使用 Attention-based、Atrous、Adaptive；结论提及 dynamic weighted fusion，未给定义。先采用 Fig.6 明确连接，不凭称谓增加 attention 或可学习融合权重。
4. **K 的措辞**：一处误称 K=5 为 prediction horizon；评价部分明确 K 是 top-K 候选数，预测时域仍为 3 秒。
5. **K1 主表/消融表不一致**：Table I 完整模型为 69.3/30.0/11.4/36.9；Table VI 全开为 69.3/29.6/11.4/36.8。分别保留，不臆造差异原因。
6. **训练细节**：初始/最终 LR、pct_start、div_factor、final_div_factor、β₂、eps、WD 分组、seed、AMP、gradient clipping、drop_last、预训练及 GT fading schedule 未完整给出。

主表参考值为 mAPf(K1)=36.9%、mAPf(K5)=40.4%、mAPdet=76.6%。这些是论文报告值，不是本项目测得结果，也不构成精确复现已完成的证据。

## 执行路线与阶段0更新（2026-10-13）

当前采用服务器执行，服务器未租，预算未定且优先按需省钱。执行主体优先使用固定 FutureDet，数据、现有 runner、预测头、解码和 forecast SDK 按需复用；全面重写、旧权重转换、AMP 与 DDP 后置。首轮目标是 FP32 单卡 mini 闭环，不要求精确达到主表参考指标才开始论文模块。

B0、B1 未开启 A-FPN 时的颈部及预测头输入仍待定；PillarVTP 的1.77M不能直接认定为本论文消融基线。各组是独立模型配置，不是从B0连续微调到B4。

20 sweeps、7位置与0.5秒名义节奏保持继承记录。GT 的 annotation.next 与预测 sample offset 不保证时间逐位对应，需实际 mini 审计，不能凭实际时间戳字段存在即认为对齐。训练末端复制与评价末端丢弃差异初次对照保留并记录。

执行细则见 [execution_plan.md](execution_plan.md)；这份台账仍不是可运行配置。

## 2026-10-15分工与无服务器推进补充

用户不再手写模型；实现、接口适配、配置、验证和实验支持由助手承担。论文新增模块由助手按原方法实现，不要求另创新算法。没有服务器可先完成代码、独立CPU检查和部署材料；真实CUDA整网、吞吐、短训练和完整实验保留待验。执行路线改为L/G两线，详细步骤见execution_plan.md；不更改本文论文事实或未确认的结构参数。
