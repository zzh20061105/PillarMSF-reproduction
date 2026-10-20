# FutureDet工作副本来源

- 上游：https://github.com/neeharperi/FutureDet
- 固定提交：`960115e2d11e40c569c4fb9abc1f0e066e4a07b1`。
- 提交编号是上游某次Git提交的版本标识，可据此找到同一份源码；短写为`960115e2`。
- 复制日期：2026-10-20。
- 本地参考原件：`references/FutureDet/`，保留不改。
- 工作副本：`third_party/FutureDet/`，后续按获批任务逐项适配。
- 本次原样引入197个上游文件（源码、配置、脚本与文档素材），另加本文件，共198文件；原作者注释及声明保留。
- 不复制上游.git；副本由PillarMSF主仓库管理，本次未暂存、提交或上传。
- 上游setup.sh/requirements.txt保留原文，当前安装配方以主项目environment/为准；本次未安装、编译或运行模型。
- 已有数据准备入口继续按原显式路径使用参考源码；本批未切换导入路径，也不设置全局PYTHONPATH。
- 后续改动由主仓库Git记录；这份来源编号标记复制基线，不承诺后续适配文件仍与上游相同。

排除的6个上游旧编译产物：

- `det3d/ops/dcn/build/temp.linux-x86_64-cpython-37/src/deform_conv_cuda.o`
- `det3d/ops/dcn/build/temp.linux-x86_64-cpython-37/src/deform_conv_cuda_kernel.o`
- `det3d/ops/iou3d_nms/build/temp.linux-x86_64-cpython-37/src/iou3d_cpu.o`
- `det3d/ops/iou3d_nms/build/temp.linux-x86_64-cpython-37/src/iou3d_nms.o`
- `det3d/ops/iou3d_nms/build/temp.linux-x86_64-cpython-37/src/iou3d_nms_api.o`
- `det3d/ops/iou3d_nms/build/temp.linux-x86_64-cpython-37/src/iou3d_nms_kernel.o`

仅完成源码复制与内容核对，环境兼容、官方权重、推理和评价仍待对应任务验证。
