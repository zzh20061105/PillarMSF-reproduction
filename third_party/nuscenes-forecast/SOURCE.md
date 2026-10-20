# nuscenes-forecast工作副本来源

- 上游：https://github.com/neeharperi/nuscenes-forecast
- 固定提交：`300082bb4cb23df836c4fb7e3c9b0236e248d4f4`，短号`300082bb`。
- 引入日期：2026-10-20。
- 本地参考原件：`references/nuscenes-forecast/`，保持不变。
- 工作副本：`third_party/nuscenes-forecast/`，由PillarMSF主仓库管理，没有独立.git。
- 引入136个Git跟踪来源文件，共1,462,801字节；不复制.git、缓存或未跟踪内容。另加本来源文件，共137文件。
- 原LICENSE.txt与setup元数据保留；两者许可标注不一致，已有来源记录保留此事实，不新增统一授权判断。

## 本批唯一源码适配

`python-sdk/nuscenes/eval/detection/algo.py`六处`.astype(np.float)`改为`.astype(float)`，新增一行中文注释。float仍对应原float64数组类型，匹配、阈值、误差与分母算法保持原样；其余135个来源文件与参考原件一致。

用户明确暂缓地图修改和测试。`utils/map_mask.py`保持原样，其中旧`np.bool`只登记为待实际需求触发的兼容项，本批未调用或验收地图接口。

## 运行与验证范围

项目的`scripts/check_forecast_sdk.py`只在当前进程显式加入本副本的python-sdk路径，并核对实际导入来源；不安装SDK，不修改全局PYTHONPATH，现有mini生成入口仍使用显式reference路径。

现有WSL venv、NumPy 1.26.4中，手工car、7位置、K=1的完全匹配/不匹配样例通过；报告为项目outputs/checks/forecast_sdk_compatibility.json。nusc=None，不读取真实数据或调用地图，不运行模型或训练。该结果不代表完整NuScenesEval、cohort、K=5、mini推理或论文指标通过。

原setup/requirements保留但未执行；环境以主项目environment/为准。后续改动由主仓库Git记录。
