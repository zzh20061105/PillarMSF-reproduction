"""从元数据重建mini car标签，核对当前LiDAR坐标、尺寸、速度和yaw；不改标签。
WSL：python -B scripts/audit_nuscenes_geometry.py --dataroot /home/pillar/data/nuscenes
报告默认写入outputs/audits/nuscenes_mini_geometry.json，不运行SDK或模型。
"""
import argparse
import json
import pickle
from collections import Counter
from pathlib import Path

import numpy as np
from pyquaternion import Quaternion

ATOL = 1e-6
GROUPS = ("center_m", "size_m", "velocity_xy_mps", "velocity_xyz_mps",
          "yaw_encoded_rad", "yaw_periodic_rad")


def reference_frame(pose, sensor):
    # ego→global与LiDAR→ego先组合，再求逆；所有未来框共用当前帧这个变换。
    re = Quaternion(pose["rotation"]).rotation_matrix
    rc = Quaternion(sensor["rotation"]).rotation_matrix
    return (re @ rc).T, np.asarray(pose["translation"]) + re @ sensor["translation"]


def global_velocity(ann, tables):
    annotations, samples = tables["sample_annotation"], tables["sample"]
    if not ann["prev"] and not ann["next"]:
        return np.zeros(3), "isolated_zero"
    first = annotations[ann["prev"]] if ann["prev"] else ann
    last = annotations[ann["next"]] if ann["next"] else ann
    # 保留本fork SDK的浮点运算次序、双边/单边差分和超时归零规则。
    dt = samples[last["sample_token"]]["timestamp"] * 1e-6 - samples[first["sample_token"]]["timestamp"] * 1e-6
    centered = bool(ann["prev"] and ann["next"])
    if dt > (3.0 if centered else 1.5):
        return np.zeros(3), "gap_zero"
    return (np.asarray(last["translation"]) - first["translation"]) / dt, "centered" if centered else "one_sided"


def encode_box(ann, current_size, rotation, origin, global_v):
    center = rotation @ (np.asarray(ann["translation"]) - origin)
    velocity = rotation @ global_v  # 先旋转完整xyz速度，再取xy；不减ego速度。
    orientation = rotation @ Quaternion(ann["rotation"]).rotation_matrix
    yaw = -np.arctan2(orientation[1, 0], orientation[0, 0]) - np.pi / 2
    # wlh沿用当前框；两组速度/yaw按上游拼接重复，不解释成正反向量。
    return np.r_[center, current_size, velocity[:2], velocity[:2], yaw, yaw], velocity


def audit(infos, tables, lidar):
    stats = {k: {"max_abs": 0.0, "failed_positions": 0, "nonfinite_values": 0} for k in GROUPS}
    counts = Counter(tracks=0, positions=0, future_annotation_size_differs_from_current=0)
    modes, failures = Counter(), {}
    for info in infos:
        sd = lidar[info["token"]]
        rotation, origin = reference_frame(tables["ego_pose"][sd["ego_pose_token"]],
                                         tables["calibrated_sensor"][sd["calibrated_sensor_token"]])
        for index, names in enumerate(info["gt_names"]):
            if names[0] != "car":
                continue
            tokens = info["gt_boxes_token"][index]
            current = tables["sample_annotation"][str(tokens[0])]
            if current["sample_token"] != info["token"]:
                raise ValueError("当前annotation与info不对应：" + info["token"])
            counts["tracks"] += 1
            for slot, token in enumerate(tokens):
                ann = tables["sample_annotation"][str(token)]
                global_v, mode = global_velocity(ann, tables)
                expected, velocity = encode_box(ann, current["size"], rotation, origin, global_v)
                actual = info["gt_boxes"][index, slot]
                if len(tokens) != 7 or actual.shape != (12,):
                    raise ValueError("仅支持已审核的7时刻×12列info")
                modes[mode] += 1
                counts["positions"] += 1
                if slot and np.max(np.abs(np.asarray(ann["size"]) - current["size"])) > ATOL:
                    counts["future_annotation_size_differs_from_current"] += 1
                errors = {"center_m": actual[:3] - expected[:3],
                          "size_m": actual[3:6] - expected[3:6],
                          "velocity_xy_mps": actual[6:10] - expected[6:10],
                          "velocity_xyz_mps": np.r_[info["gt_boxes_velocity"][index, slot] - velocity,
                                                   info["gt_boxes_rvelocity"][index, slot] - velocity],
                          "yaw_encoded_rad": actual[10:12] - expected[10:12]}
                errors["yaw_periodic_rad"] = (errors["yaw_encoded_rad"] + np.pi) % (2 * np.pi) - np.pi
                for kind, error in errors.items():
                    finite = np.isfinite(error)
                    peak = float(np.max(np.abs(error[finite]))) if finite.any() else 0.0
                    stat = stats[kind]
                    stat["max_abs"] = max(stat["max_abs"], peak)
                    stat["nonfinite_values"] += int((~finite).sum())
                    if not finite.all() or peak > ATOL:
                        stat["failed_positions"] += 1
                        if kind not in failures:
                            failures[kind] = {"sample": info["token"], "annotation": str(token),
                                              "slot": slot, "max_finite_abs": peak,
                                              "nonfinite_values": int((~finite).sum())}
    return {"counts": dict(counts), "velocity_modes": dict(modes), "errors": stats,
            "passed": counts["positions"] > 0 and all(s["failed_positions"] == 0 for s in stats.values()),
            "first_failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataroot", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] /
                        "outputs/audits/nuscenes_mini_geometry.json")
    args = parser.parse_args()
    root = args.dataroot.resolve()
    # 只读原始JSON；sample.data是SDK运行时添加的，按sensor与keyframe重建LiDAR索引。
    tables = {}
    for name in ("sample", "sample_annotation", "sample_data", "ego_pose", "calibrated_sensor", "sensor"):
        records = json.loads((root / "v1.0-mini" / f"{name}.json").read_text())
        tables[name] = {r["token"]: r for r in records}
    lidar = {}
    for sd in tables["sample_data"].values():
        cs = tables["calibrated_sensor"][sd["calibrated_sensor_token"]]
        if sd["is_key_frame"] and tables["sensor"][cs["sensor_token"]]["channel"] == "LIDAR_TOP":
            lidar[sd["sample_token"]] = sd
    report = {"scope": "mini car metadata-to-info only; no point cloud/augmentation/evaluation/model",
              "dataroot": str(root), "absolute_tolerance": ATOL,
              "size_order": "w,l,h; current annotation size held for all seven positions",
              "yaw_encoding": "-atan2(local_orientation[1,0], local_orientation[0,0])-pi/2",
              "velocity_policy": "pinned fork differences; isolated/gap zero; no ego velocity subtraction",
              "splits": {}}
    for split in ("train", "val"):
        path = root / "mini_forecast" / f"infos_{split}_20sweeps_withvelo_filter_True.pkl"
        with path.open("rb") as stream:
            infos = pickle.load(stream)
        result = audit(infos, tables, lidar)
        result.update(info_path=str(path), info_bytes=path.stat().st_size)
        report["splits"][split] = result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "splits": report["splits"]}, indent=2))
    if not all(value["passed"] for value in report["splits"].values()):
        raise SystemExit("审计存在超限、非有限值或空结果，参见已保存报告")


if __name__ == "__main__":
    main()
