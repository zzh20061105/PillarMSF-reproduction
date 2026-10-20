# PillarMSF 论文复现

更新：2026-10-20。当前从 [复现进度总览](docs/进度总览.md) 开始查看。AI 负责代码实现与适配，用户掌握范围、设计和进度；每个小任务先说明并确认，完成后报告并停审，见 [实现与执行边界](docs/implementation_boundary.md)。

项目目标是复现 PillarMSF。固定 FutureDet 提供数据、标签、训练循环、预测头、解码与 forecast SDK 参考；新模块按论文实现或适配。已确认现代环境栈、首轮完整模型B4加官方权重对照；FutureDet工作副本已按2.1批准范围建立在third_party/FutureDet，后续适配与方法默认仍逐项审核。

## 当前从这里开始

- [进度总览](docs/进度总览.md)：当前位置、五阶段路线、待审核与待批准事项。
- [工作记录](docs/work_log.md)：具体执行、历史偏离与有限验证证据。
- [环境说明](docs/environment.md)：当前本机/服务器边界和历史环境记录。
- [实现与执行边界](docs/implementation_boundary.md)：审批、运行地点、文档同步与精简工程规则。

阶段2.1已完成源码落地，用户已同意进入2.2：[FutureDet工作副本](third_party/FutureDet)包含197个原样上游文件及一份 [来源说明](third_party/FutureDet/SOURCE.md)，参考原件不改；尚未安装、导入或运行该副本。阶段1已批准范围内的mini时间/几何核对结果见 [数据说明](data/README.md)。2.2已建立[forecast SDK工作副本](third_party/nuscenes-forecast)，仅将评价algo.py六处np.float替换为float；两个手工评价样例在现有NumPy 1.26.4环境通过，待用户审核。地图代码与测试暂缓，真实推理和完整评价尚未开始；下一步先明确2.3官方权重与推理接入范围。

现行研究阶段统一编号为1—5，子任务采用1.1、1.2等格式；工程整理批次不另算研究阶段。主线为数据与标签 → 官方权重评价链 → PillarMSF 模型 → 服务器小规模闭环 → 正式实验，具体状态以进度总览为准。

首轮正式训练仅在服务器训练完整模型 B4，计划20轮；FutureDet 对照使用官方预训练权重推理和评价，不重新训练 FutureDet。B0—B3 消融是否补做，后续按结果、预算和批准范围决定。mini 只作数据、接口和小规模闭环检查；mini 短训练也在服务器进行，正式指标对照使用完整验证集。

## 已有与未完成

- 三个参考仓库已固定提交，见 [来源](docs/upstream_sources.md)。参考原件保留；FutureDet后续适配在项目内工作副本进行，自有PillarMSF模块放在src/pillarmsf。
- [复现规格](docs/reproduction_spec.md)和 [研究配置](configs/pillarmsf_spec.json)区分论文事实、继承默认与实现假设；JSON 不是可启动训练的完整配置。
- 自有模型目录尚无实现，见 [模块接口](src/pillarmsf/README.md)。
- mini 已位于本机 WSL `/home/pillar/data/nuscenes/`，索引在 `mini_forecast/`，见 [数据说明](data/README.md)。完整 trainval 尚未准备，服务器未就绪。
- 官方权重推理、轨迹解码与评价、自有PillarMSF模型实现及全部实际训练尚未开始，没有本项目测得的APf。
- 来源检查工具已冻结保留；不再作为复现主线的开发或教学任务。
- 此前本机通过有限的 Torch CUDA、spconv 和非空 Pillar native 算子检查；这不代表 FutureDet 已跑通或服务器已验证。

推进主线为：mini 数据与标签核对 → 官方权重推理、解码和评价链 → PillarMSF 模型 → 服务器小规模闭环 → 正式训练与对比。用户已允许本机 CPU 数据准备与 GPU 推理/调试；具体运行仍需对应批次确认。全部实际训练（含 CPU、mini、短训练）在服务器进行。

复用对照见 [复用清单](docs/reuse_map.md)，方法事实、候选与假设集中在 [规格台账](docs/reproduction_spec.md)，实际执行历史集中在工作记录。Stage5、DIoU 等具体方法选择仍单独待批；参数量接近不等于结构已获作者确认。[算子兼容记录](docs/compatibility.md) 仅保留历史 native 验证证据，不是默认运行任务。

每批同步实际受影响的既有README、进度、配方或规格并追加工作日志；日常步骤不另建Markdown。确有必要的新专题说明统一放docs/notes/，目录在实际需要时创建；依赖的固定来源说明随依赖保存。只做任务相关检查，不扩建假想防御或重复全仓核查；来源检查工具保持冻结。

## 目录与环境

- `configs/`：研究规格、协议和路径示例；不是可直接训练的完整配置。
- `src/pillarmsf/`：自有PillarMSF模块位置，目前仍为占位；与上游工作副本分开。
- `scripts/`：工程入口；已有mini索引生成、car未来时间及几何编码审计脚本，以及[SDK合成评价检查](scripts/check_forecast_sdk.py)。
- `references/`：固定上游原件，不随主仓库提交，不混用两套det3d。
- `third_party/FutureDet/`：主仓库管理的可修改工作副本；当前为197文件的上游基线及SOURCE.md，后续按任务适配。
- `third_party/nuscenes-forecast/`：固定预测评价SDK工作副本，来源及六处兼容修改见[SOURCE.md](third_party/nuscenes-forecast/SOURCE.md)；地图适配和测试暂缓。
- `environment/`：来源锁、安装配方和历史报告；`data/`、`outputs/` 仅跟踪说明或占位，不提交数据和结果。

当前本机使用 WSL `PillarMSF-Ubuntu22` 和 `/home/pillar/venvs/pillarmsf`。现有 [安装入口](environment/install_python.sh) 读取 [直接依赖配方](environment/requirements-core.txt)，Torch cu121 单独安装；[pip freeze 快照](environment/requirements-resolved.txt) 按现有环境最近一次只读查询保存。安装入口仍含本机路径与用户约定，快照不包含未提交代码，均不能直接当作服务器部署已通过。本批未执行安装。

迁移服务器时按实际设备和源码重建环境、重新生成绝对路径索引；本机 venv 和 `.so` 不能代替服务器验收。Git 提交与上传由用户审核后决定。
