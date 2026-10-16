# 助手实现、用户审核的模块

这里是项目自有Python源码目录。按2026-10-15新分工，全部模块实现、复用适配和测试由助手完成，用户审核进度和代码。参考仓库保持原样，不自动加入全局PYTHONPATH。

| 后续目录 | 助手实施内容 | 输入与输出约定 |
|---|---|---|
| data/ | 接入 FutureDet nuScenes 数据与标签协议 | 每样本 N×5 点、GT、时间及 batch 索引；不把 Argoverse 加载器当 nuScenes |
| models/encoder/ | Pillar 编码器及边界过滤 | 物理 ROI 内的点 → C=64 稀疏二维柱特征 |
| models/backbone/ | 阶段 1–4 与稠密阶段 5 | F3/F4/F5 通道 256，空间 208/104/52 |
| models/neck/ | 按 Fig.6 实现 A-FPN | 三尺度 → 768×104×104；隐藏通道待核 |
| models/head/ | 接入 FutureDet 时间预测头 | 7 个时间点；shared=64，输出各框参数与热力图 |
| losses/ | L1、focal 与 DIoU | mask、归约、旋转框解释要写明 |
| evaluation/ | 接入 K=1/5 APf | 保留分组、关联、排序与指标协议 |

当前仍仅有目录与约定，上述模型尚未实现。可以先完成代码和独立CPU检查；Pillar CUDA、整网前反向、真实mini和训练评价在服务器获得后按顺序验收。见 ../../docs/execution_plan.md。
