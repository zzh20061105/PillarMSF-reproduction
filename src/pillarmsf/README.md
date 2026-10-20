# 项目自有源码与候选接口

更新：2026-10-20。这里是项目自有 Python 源码目录，目前只有占位目录和初始化文件，尚无下表中的模型实现。助手负责实现和复用适配，用户审核；每个小任务先说明并获批，代码添加必要中文注释。当前阶段和状态见 [进度总览](../../docs/进度总览.md)，规则见 [implementation_boundary.md](../../docs/implementation_boundary.md)，方法依据和未决项见 [reproduction_spec.md](../../docs/reproduction_spec.md)。

FutureDet工作副本已按2.1批准范围放在 [third_party/FutureDet](../../third_party/FutureDet)，来源见 [SOURCE.md](../../third_party/FutureDet/SOURCE.md)；当前197个上游文件原样保留，尚未做兼容或导入接入。本目录用于自有PillarMSF模块，后续在明确接口处与副本配合；references保持原样，不把多份det3d混入全局PYTHONPATH。

下表是候选模块及接口提示，用来讨论职责；不是已实现能力、完整张量契约或最终目录结构。通道、形状和损失解释须结合研究规格中的来源与假设，在对应模块任务中核对，不由本次整理定案。表内 backbone 的 Stage 指网络层级，与研究阶段1—5不同。

| 候选目录 | 候选职责 | 接口提示与待核对内容 |
|---|---|---|
| data/ | 复用 FutureDet nuScenes 数据与标签协议 | 点特征列、GT、时间和 batch 索引按上游协议核对 |
| models/encoder/ | Pillar 编码器及边界过滤 | 物理 ROI 内的点到稀疏二维柱特征；C=64 为当前规格候选 |
| models/backbone/ | 多尺度骨干和 Stage5 | 原接口候选 F3/F4/F5 通道256、空间208/104/52；Stage5 细节待核 |
| models/neck/ | A-FPN | 原输出候选768×104×104；隐藏通道等细节待核 |
| models/head/ | 复用 FutureDet 时间预测头 | 原工程候选 T=7、shared=64；与数据、标签和官方权重接口分别核对 |
| losses/ | L1、focal 与 DIoU | mask、归约、框几何及激活范围需明确；不在此更改既有默认 |
| evaluation/ | 复用 K=1/5 APf 协议 | 核对分组、关联、排序、导出与指标口径 |

本机可按获批任务做代码构建、CPU 检查和数据准备，以及 GPU 推理与调试；所有实际训练均在服务器，包括 CPU/mini/短训练。历史 native 小输入检查不能代替当前环境或整网验收。首轮正式训练仅服务器 B4 完整模型20轮，FutureDet 用官方权重推理/评价对照而不重训；B0—B3 是否补做后定。具体任务、运行和验收依现行阶段逐项确认。
