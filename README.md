# PillarMSF 论文复现

当前执行边界（2026-10-16）：全部实际训练在服务器进行，包含 mini、短训练与 CPU 训练。本机仅用于代码构建、阅读及默认轻量 CPU 调试；CUDA 扩展和 GPU 整网验收留给服务器。现有 WSL 环境与报告保留为历史记录；服务器尚未租用，预算未定。

第一版以固定版本 FutureDet 为主执行框架，优先复用数据、标签、现有训练流程、预测头、解码及评价；参考 PillarNet 接入编码器和稀疏主干，由助手完成全部论文模块和必要适配，你负责进度、代码与实现假设审核。完整重写 runner 或 SDK 不是第一版前置任务。按[实现与审核边界](docs/implementation_boundary.md)逐个小任务推进：先说明范围并由你确认，实施后报告差异与验证证据，停下来供你审核；不会因认可总体路线而一次性实现所有模块。

## 当前从这里开始

- [分阶段执行计划](docs/execution_plan.md)：具体步骤、验收与当前进度。
- [服务器租用前清单](docs/server_preflight.md)：按需租用、资源与首次运行要求。
- [工作记录](docs/work_log.md)：已执行事项和未验证边界。

2026-10-13已完成阶段0准备；2026-10-15更新分工：助手实现、用户审核。下一开发阶段是L1最小执行工程与接口，需先拆成小任务逐项确认，不等待服务器选型。2026-10-16 已更新执行与审核说明，L1仍未实施。AutoDL候选比较并行，尚未取得具体实例配置；未创建实例或支付。

## 已有与未完成

- 三个参考仓库已固定提交，见 [来源](docs/upstream_sources.md)。参考仓库保持原样，适配在后续执行工作副本或自有模块中完成。
- [复现规格](docs/reproduction_spec.md)和 [研究配置](configs/pillarmsf_spec.json)区分论文事实、继承默认与实现假设；JSON 不是可启动训练的完整配置。
- 自有模型目录尚无实现，见 [模块接口](src/pillarmsf/README.md)。
- nuScenes 尚未下载，服务器尚未配置，没有训练或 APf 复现结果。
- 此前本机通过有限的 Torch CUDA、spconv 和非空 Pillar native 算子检查；这不代表 FutureDet 已跑通或服务器已验证。

先完成L线代码、独立CPU检查和服务器交付材料；有GPU及数据后按G线验证环境、mini、完整batch、短训练与评价，最后开展正式训练和独立消融。代码完成不等同GPU或真实数据已验收；开始实现不要求先达到论文FutureDet数值。

复用边界见 [复用清单](docs/reuse_map.md)，模型接口和歧义见 [规格台账](docs/reproduction_spec.md)，native 限制见 [兼容性记录](docs/compatibility.md)。

## 历史本机环境

WSL2 环境保留为既有验证记录，不承担本机训练；以下入口仅用于查阅或已说明的调试，不是当前必须执行的步骤。安装与自检记录见 [环境记录](docs/environment.md)。如需主动复查，在 Windows PowerShell 可使用原入口：

```powershell
wsl -d PillarMSF-Ubuntu22 -u pillar -- bash --rcfile /mnt/d/ai_study/PillarMSF/scripts/interactive.bashrc -i
```

服务器迁移时保留源码、配置、来源锁和构建说明，重新建立环境；不将现有 venv、绝对路径和 native `.so` 当作已验证的服务器环境。
