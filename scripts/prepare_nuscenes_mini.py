"""Generate nuScenes forecast infos by reusing the pinned FutureDet code.

只生成 train/val info，不构建 GT 数据库，不修改 references/ 下的上游原件。
用法（WSL 中）：
    python scripts/prepare_nuscenes_mini.py --dataroot /home/pillar/data/nuscenes
    python scripts/prepare_nuscenes_mini.py --dataroot ... --check-only
"""

import argparse
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 上游 info 过程实际会读取的目录：元数据、关键帧与历史 LiDAR、地图，
# 以及前视相机记录（上游对 CAM_FRONT 调用了 get_sample_data）。
REQUIRED_SUBDIRS = ("samples/LIDAR_TOP", "sweeps/LIDAR_TOP", "samples/CAM_FRONT", "maps")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataroot", required=True, type=Path,
                        help="nuScenes 根目录，其下应有 v1.0-mini/、samples/、sweeps/、maps/")
    parser.add_argument("--version", default="v1.0-mini",
                        choices=["v1.0-mini", "v1.0-trainval"],
                        help="数据版本，默认 v1.0-mini")
    parser.add_argument("--experiment", default="mini_forecast",
                        help="输出子目录名，位于 dataroot 下，默认 mini_forecast")
    # 20 sweeps 与 7 个时刻继承 FutureDet 配置（论文未写明），不要随意改动。
    parser.add_argument("--nsweeps", type=int, default=20)
    parser.add_argument("--timesteps", type=int, default=7)
    parser.add_argument("--sdk-root", type=Path,
                        default=PROJECT_ROOT / "references/nuscenes-forecast/python-sdk",
                        help="锁定版本 forecast SDK 的 python-sdk 目录")
    parser.add_argument("--futuredet-root", type=Path,
                        default=PROJECT_ROOT / "references/FutureDet",
                        help="锁定版本 FutureDet 仓库根目录")
    parser.add_argument("--check-only", action="store_true",
                        help="只检查目录与导入，不生成 info 文件")
    return parser.parse_args()


def check_dataroot(dataroot, version):
    # 缺目录时一次性列出全部缺失项，避免上游运行到一半才报错。
    missing = [d for d in (version,) + REQUIRED_SUBDIRS if not (dataroot / d).is_dir()]
    if missing:
        sys.exit(f"[错误] {dataroot} 缺少目录：{', '.join(missing)}")


def import_locked_sdk(sdk_root):
    # 上游 nusc_common.py 用裸 try/except 导入 nuscenes，失败时只打印一句提示，
    # 真实原因被吞掉。这里先显式导入，并确认加载的是锁定 SDK 而不是其他版本。
    sys.path.insert(0, str(sdk_root))
    try:
        import nuscenes
        from nuscenes.eval.detection.evaluate import NuScenesEval  # noqa: F401  上游同样会导入
    except ImportError as exc:
        sys.exit(f"[错误] 导入 forecast SDK 失败：{exc!r}")
    loaded = Path(nuscenes.__file__).resolve()
    if sdk_root.resolve() not in loaded.parents:
        sys.exit(f"[错误] 加载的 nuscenes 不是锁定 SDK：{loaded}")
    print(f"[信息] nuscenes 来自 {loaded.parent}")


def load_nusc_common(futuredet_root):
    # 按文件加载，避开 det3d 包初始化（那会连带导入模型、CUDA 算子等无关模块）。
    path = futuredet_root / "det3d/datasets/nuscenes/nusc_common.py"
    spec = importlib.util.spec_from_file_location("futuredet_nusc_common", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    args = parse_args()
    dataroot = args.dataroot.resolve()
    # 先验证导入链，再检查数据目录：数据未下载时也能单独确认环境是否就绪。
    import_locked_sdk(args.sdk_root)
    nusc_common = load_nusc_common(args.futuredet_root)
    check_dataroot(dataroot, args.version)
    if args.check_only:
        print("[信息] 检查通过（--check-only，未生成文件）")
        return

    # 上游函数只往 dataroot/experiment 下写文件，不负责创建该目录。
    out_dir = dataroot / args.experiment
    out_dir.mkdir(exist_ok=True)
    # 不传 past：上游 create_nuscenes_infos 并未把它传给 _fill_trainval_infos。
    # filter_zero=True 与 FutureDet 正式流程一致。
    nusc_common.create_nuscenes_infos(
        str(dataroot), version=args.version, experiment=args.experiment,
        nsweeps=args.nsweeps, filter_zero=True, timesteps=args.timesteps)

    for split in ("train", "val"):
        name = f"infos_{split}_{args.nsweeps:02d}sweeps_withvelo_filter_True.pkl"
        path = out_dir / name
        size = f"{path.stat().st_size / 1e6:.1f} MB" if path.exists() else "未生成"
        print(f"[结果] {path}  {size}")


if __name__ == "__main__":
    main()
