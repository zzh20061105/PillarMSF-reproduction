# 参考源码来源检查（已冻结）

说明更新：2026-10-20。`L1-1` 是该工具开发时的历史任务代号，不属于现行阶段1—5的编号。用户已于2026-10-18决定冻结 `scripts/check_sources.py`，不再扩展或反复投入；本次只整理说明，未修改或运行脚本。当前流程见 [进度总览](进度总览.md)，执行规则见 [implementation_boundary.md](implementation_boundary.md)。

本入口只核对参考源码的身份、固定版本和当前改动状态；模型实现、依赖兼容、服务器、数据及训练均不在验收范围内。

## 文件职责与调用关系

- `environment/source-lock.json`：既有来源锁，记录每份仓库的 name、url 和完整 commit。
- `scripts/check_sources.py`：项目自有检查入口，读取来源锁并调用只读 Git 查询。
- `references/<name>`：本机参考原件，检查过程中保持原样；此目录被主项目 Git 忽略，克隆主项目后需另行准备参考源码。

调用顺序为：解析参数 → 读取并校验来源锁 → 核对各仓库 → 汇总结果和退出码。不会导入 det3d、Torch、spconv 或 nuScenes SDK，也不会执行训练 Python 配置。

## 保留的调用说明

以下是既有入口用法，供需要时查阅，不是当前必须执行的步骤。在具体任务获批后，可在 Windows PowerShell 中调用：

    python D:\ai_study\PillarMSF\scripts\check_sources.py
    python D:\ai_study\PillarMSF\scripts\check_sources.py --help

脚本默认按自身位置定位项目；检查另一个项目目录时，用 `--project-root <目录>` 指定。脚本使用 Python 标准库和 PATH 中的 Git，语法兼容 Python 3.10；不需要安装本项目或模型依赖。

## 具体检查与结果

1. 来源锁为非空列表，名称合法且不重复，提交为完整 40 位 SHA。
2. 参考目录存在，且是真正的 Git 仓库根目录，防止误读父仓库。
3. HEAD 与来源锁一致，origin 指向同一 GitHub owner/repo。
4. 当前无已暂存、未暂存或未跟踪的改动；被 Git 忽略的文件不计入。

GitHub HTTPS、`git@github.com:owner/repo.git` 和 `ssh://git@github.com/owner/repo.git` 按相同仓库身份比较，允许省略末尾 `.git`。此规则仅比较配置地址，不联网验证远程服务器。输出使用标准化仓库名，不打印原始 origin 或 Git 错误内容，避免回显嵌入式凭据。

来源锁中的 `clean` 是历史记录，不能代替本次 Git 状态查询。

| 退出码 | 含义 |
| --- | --- |
| 0 | 来源锁列出的仓库全部通过本次来源检查 |
| 1 | 至少一份仓库缺失、身份/版本/状态不符，或该仓库 Git 查询失败 |
| 2 | 来源锁无法读取或不合法，或 PATH 中无 Git |

发现问题只报告，保留现场；脚本不下载、不 fetch/reset、不改 Git 配置，不创建数据或输出目录。

## 与现行流程的关系

FutureDet 和 PillarNet 都有名为 det3d 的包。该检查不修改 PYTHONPATH，也不把它们拼接导入。现行方向是在项目内建立 FutureDet 工作副本，具体布局和复用文件在阶段2对应小任务中说明并确认；本工具不是该步骤的实现，也不作为继续项目的新增前置任务。

原开发批次的检查命令、实际 Python 版本与结果见 [工作记录](work_log.md) 的历史 `L1-1` 条目。来源检查通过只说明所列仓库在当次查询时满足检查条件，不能据此认定依赖兼容、模型运行或任何研究阶段已经完成。
