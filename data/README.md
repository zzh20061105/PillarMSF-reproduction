# nuScenes 数据位置与状态

更新：2026-10-20。1.1基本审核和1.2时间/几何两小批已交付，所查mini car数值核对通过；2.1的FutureDet工作副本已建立，未改本页数据/审计结果。2.2已完成SDK评价六处np.float适配与合成检查，未读取或修改本页数据；地图修改与测试暂缓。下一步先确认2.3官方权重及推理接入范围，完整trainval尚未准备。

## 路径

- 发行版：`PillarMSF-Ubuntu22`。
- 数据根：`/home/pillar/data/nuscenes/`；元数据在 `v1.0-mini/`。
- 索引目录：`/home/pillar/data/nuscenes/mini_forecast/`。
- Windows 承载位置：`D:\WSL\PillarMSF-Ubuntu22\ext4.vhdx`，是 WSL 虚拟磁盘，不是可以直接拼接 Linux 路径的普通数据目录。
- 原压缩包：`C:\Users\zengzihang\Documents\v1.0-mini.tgz`，是否删除由用户决定。

## 1.1 本次基本审核结果

2026-10-20在现有 WSL venv 中只读反序列化两份索引，结合 mini 的 sample/scene 元数据和固定 SDK 的 mini 划分检查；未重新生成索引。

| 项目 | train | val |
| --- | --- | --- |
| 文件 | `infos_train_20sweeps_withvelo_filter_True.pkl` | `infos_val_20sweeps_withvelo_filter_True.pkl` |
| 实际大小 | 51,586,227 字节 | 16,350,319 字节 |
| 帧级 info 条数 | 323 | 81 |
| 场景数 | 8 | 2 |
| 当前帧 car 目标条数（跨帧累计） | 4,082 | 2,056 |
| 去重后引用的 LiDAR 文件路径 | 3,147，均存在 | 788，均存在 |
| 前视相机文件路径 | 323，均存在 | 81，均存在 |

- 每个 split 内 token 唯一，train/val token 交集为0；全部404个 token 都能在 mini 元数据中找到，场景集合分别等于固定 SDK 的 mini_train/mini_val。
- 全部404条 info 各有19个历史 sweep 记录，加当前帧是20 sweeps。记录数检查不代表历史点云内容或变换数值已经验证。
- 全部404条的 `gt_boxes` 形状均为 `[N,7,12]`，`gt_names` 和 `gt_boxes_token` 均为 `[N,7]`。N 是该帧保留目标数；7包含当前时刻和6个未来时刻，不是7个未来时刻。
- 按上游拼接代码，12列由位置3、尺寸3、两组二维速度4、两组航向2组成。1.1仅确认基本结构，后续时间及几何数值核对结果见下文；没有改变上游编码。
- info生成按当前注释的LiDAR与radar点数之和大于0过滤，不在此阶段只保留car。本次当前帧标签计数为：train car/pedestrian/ignore = 4,082/3,068/4,066，val = 2,056/1,260/540。正式car筛选在后续Preprocess中按配置执行，未在本批运行。上述目标数是跨帧目标条数，不是独立车辆数量。
- 索引中的点云/相机路径均能找到文件；本次未读取这些原始文件的内容，也未加载模型或运行推理。

## 生成入口与审核边界

[prepare_nuscenes_mini.py](../scripts/prepare_nuscenes_mini.py) 是薄入口：默认mini、20 sweeps、7时刻，显式加载固定forecast SDK，按文件加载FutureDet的nusc_common，调用其create_nuscenes_infos并保留filter_zero=True；不构建GT数据库。脚本和上游参考原件本次均未修改，也未重跑。源码调用关系见 [复用清单](../docs/reuse_map.md)。

1.1未发现阻碍基本结构审核的实际问题；上游空注释分支存在不同数组形状，当前mini没有触发，不能把统一形状推广到所有数据。1.2两小批的时间和几何核对见下文，各自的有限证据均不代替评价链验收。

## 1.2 第一小批：car未来时间与末端复制

2026-10-20，使用新增的 [audit_nuscenes_temporal.py](../scripts/audit_nuscenes_temporal.py) 在现有WSL venv实际运行。输入仅为两份既有info和mini的sample/sample_annotation元数据；没有重生成或修改标签。

口径：轨迹数M是“当前帧×car目标”的条数，不是独立车辆数；未来位置数P=6M，不含当前位置。跳帧事件指annotation正常前进后，新sample不是前一sample的直接next；slot错位则是该位置的sample与从当前帧沿sample.next走相应步数的预期sample不同。二者分开计数。末端复制须同时满足annotation token重复和annotation.next为空。

| 项目 | train | val |
| --- | --- | --- |
| 轨迹数M / 未来位置数P | 4,082 / 24,492 | 2,056 / 12,336 |
| 有末端复制的轨迹 / M | 1,235 / 4,082 = 30.25% | 583 / 2,056 = 28.36% |
| 末端复制位置 / P | 4,427 / 24,492 = 18.08% | 2,120 / 12,336 = 17.19% |
| 标注链在场景末帧结束：复制轨迹 / 位置 | 372 / 1,323 | 308 / 1,114 |
| 标注链在场景结束前终止：复制轨迹 / 位置 | 863 / 3,104 | 275 / 1,006 |
| 发生非相邻前进的轨迹 / 过渡事件数 | 0 / 0 | 0 / 0 |
| 仍有预期场景sample的未来位置数A | 22,978 | 10,999 |
| sample不对应的未来位置 / A | 2,913 / 22,978 = 12.68% | 783 / 10,999 = 7.12% |
| 场景已结束、无预期sample的位置 | 1,514 | 1,337 |

本次所有所选car轨迹的当前annotation均对应当前sample，整条链instance/scene一致，后续token符合annotation.next或链尾重复。未发现非相邻前进；可比较位置的sample不对应均来自标注链提前结束后的末端复制。这是上游生成规则的量化，不能直接称为新引入的标签错误，更不在本批自动修标签或改评价分母。

“复制根因”与“预期sample是否存在”是两条统计轴：train有191个、val有223个提前结束后的复制位置同时已经超出场景，不能把场景末帧结束的复制数直接等同无预期sample的位置数。轨迹类别可能重叠，不能将各类轨迹比例直接相加。

按本次car非复制前进位置统计，实际相邻时间步train为0.399197–0.599957s，中位0.499888s；val为0.399259–0.599961s，中位0.499881s。0.5s是名义节奏，不能替代元数据实际时间，也不能把该统计外推为全数据集固定间隔。

例如train的一条轨迹在第3个未来位置仍引用偏移1.050097s的末端annotation，而预期sample的偏移为1.549402s；这不是1.549402s的新观测。完整token示例及每个未来位置的实际偏移统计保存在本地报告中，aligned示例仅表示该单个位置对齐。

运行命令（WSL）：

```bash
/home/pillar/venvs/pillarmsf/bin/python -B /mnt/d/ai_study/PillarMSF/scripts/audit_nuscenes_temporal.py --dataroot /home/pillar/data/nuscenes
```

默认报告：项目内 `outputs/audits/nuscenes_mini_temporal.json`，由现有.gitignore排除，不提交Git，可运行脚本重建。脚本约121行，带中文注释，不加载完整SDK、地图、GPU或模型，不增加依赖。已用三条可手算的小轨迹检查一次跳帧影响多个slot、提前结束跨过场景末端、场景末端复制的计数关系；真实运行成功退出。

第一小批统计仅针对生成后info中当前类别为car的轨迹，未应用训练ROI、后续点数过滤、增强或损失mask，不能当作训练最终有效监督比例或指标影响。它只检查时间；几何数值见第二小批，评价端行为仍未验证。

原“约27%”为口径未完整记录的临时抽查，历史保留，不再作为正式比例；当前使用上表明确分母的结果。34s耗时与6.2GB峰值仍是此前info生成的历史记录，本次没有重测。

## 1.2 第二小批：当前LiDAR坐标与框编码

2026-10-20，新增并实际运行 [audit_nuscenes_geometry.py](../scripts/audit_nuscenes_geometry.py)（138行、必要中文注释）。从mini的sample、sample_annotation、sample_data、ego_pose、calibrated_sensor、sensor六张原始JSON表重建当前LiDAR变换及期望框，不调用SDK的Box变换或info生成函数，不读取原始点云/图像。

本批覆盖train 4,082条、val 2,056条当前car轨迹的七个位置，共28,574 / 14,392个框位置，合计42,966。七个位置包含当前位置和末端复制位置，不能与时间审计的六个未来位置分母混用，也不代表42,966个独立观测。

绝对容差统一为1e-6（位置/尺寸用m、速度用m/s、角度用rad），按float64重建；所有组的超限位置数和非有限数均为0。

| 最大绝对误差 | train | val |
| --- | --- | --- |
| 中心，m | 4.5475e-13 | 4.7606e-13 |
| 尺寸，m | 0 | 0 |
| 两份xy速度，m/s | 4.9738e-14 | 8.3489e-14 |
| 两个另存xyz速度字段，m/s | 4.9738e-14 | 8.3489e-14 |
| 原始编码yaw，rad | 8.8818e-16 | 1.7764e-15 |
| 按2π周期比较yaw，rad | 8.8818e-16 | 1.7764e-15 |

本次核实的继承契约：

- 当前及未来框都用当前帧LiDAR对应的ego_pose和calibrated_sensor，将全局中心变换到当前LiDAR系；z为几何中心，此生成过程没有改成框底部高度。
- info十二列为 `[x,y,z,w,l,h,vx,vy,vx,vy,-theta-pi/2,-theta-pi/2]`。两份速度和yaw是同源重复；字段名称带r不能证明它是反向量。此前复用清单“正向/反向”的说法已纠正，数组列数和算法未改。
- 尺寸按源码沿用当前ref_box的[w,l,h]。本次所查未来annotation尺寸与当前尺寸不同的项为0，因此数值结果本身不能独立区分“沿用当前”与“逐帧取尺寸”；该策略由源码确认，不外推完整数据。
- 速度先按全局三维位置及实际时间作前后邻差分，再完整旋转到当前LiDAR系，不减ego速度，最后取xy存入两份字段；两个另存的速度字段均含完整xyz，已一并核对。
- 本fork SDK对孤立annotation或时间跨度超限返回零向量，区别于其docstring中的NaN表述；单边跨度上限1.5s，双边3s。本次差分模式按框位置计数：train双边22,492、单边6,047、孤立归零35；val双边11,500、单边2,864、孤立归零28；跨度超限归零未在本次car数据触发。零估计不等于目标实测静止。
- theta由完整局部朝向矩阵第一列投影的atan2(y,x)得到，存储值为-theta-pi/2；同时核对原始编码误差和周期角误差，未用简单角度相减代替三维旋转。

运行命令（WSL）：

```bash
/home/pillar/venvs/pillarmsf/bin/python -B /mnt/d/ai_study/PillarMSF/scripts/audit_nuscenes_geometry.py --dataroot /home/pillar/data/nuscenes
```

默认报告为本地 `outputs/audits/nuscenes_mini_geometry.json`，由现有.gitignore排除；包含字段误差、位置数、差分模式和首个失败位置。本次真实运行退出0。已用非交换的ego/sensor 90度旋转、完整三维速度、差分/归零手算样例检查公式，并以单框中心偏移1cm确认脚本确实能检出错误；没有新增测试框架或测试文件。

本次只证明所查mini car info与固定上游生成规则的数值一致性，不证明点云内容/历史配准、增强、后续目标编码、真实预测导出、评价或训练已通过；也不证明论文方法正确。没有修改原始数据、索引、生成脚本、参考源码、环境或方法参数，末端复制继续按前批记录保留。

1.2已批准的两小批到此交付，用户已同意进入阶段2；2.1已建立third_party/FutureDet，尚未接入运行入口，现有数据准备脚本的参考路径保持原值。2.2已建立SDK工作副本并通过纯手工评价样例，未运行真实数据评价或地图测试。下一步先确认2.3官方权重及推理接入范围；评价端对应关系和末端处理后续结合真实预测另验，不继续扩建审计工具。

原始执行与本次结果见 [工作记录](../docs/work_log.md)。

索引记录WSL绝对路径，迁移机器后需在目标路径重新生成。本机CPU数据处理及GPU推理/调试的具体任务仍逐批确认，全部实际训练在服务器。本目录只跟踪数据说明，不提交原始数据、索引、GT缓存或检查点。当前阶段与状态见 [进度总览](../docs/进度总览.md)。
