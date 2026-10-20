"""审计现有 mini info 的 car 未来时间序列；不修改标签，不运行模型。
WSL 用法：
    python -B scripts/audit_nuscenes_temporal.py --dataroot /home/pillar/data/nuscenes
默认报告写入项目 outputs/audits/nuscenes_mini_temporal.json（不提交Git）。
"""
import argparse
import json
import pickle
from collections import Counter
from pathlib import Path
from statistics import median

KINDS = ("terminal_repeat", "repeat_at_scene_end", "repeat_before_scene_end",
         "nonadjacent_advance", "sample_mismatch")


def summarize(values):
    return {"count": len(values), "min": min(values), "median": median(values),
            "max": max(values)} if values else {}


def audit(infos, samples, annotations):
    # tracks按当前帧×car目标计数；slots只含六个未来位置，不含当前位置。
    counts = Counter({f"{kind}_{unit}": 0 for kind in KINDS for unit in ("tracks", "slots")})
    counts.update(dict.fromkeys(("tracks", "future_slots", "scene_available_slots",
                                "slots_beyond_scene_end", "repeat_with_scene_future_slots",
                                "repeat_beyond_scene_end_slots"), 0))
    offsets, intervals, examples = [[] for _ in range(6)], [], {}
    for info in infos:
        anchor = samples[info["token"]]
        expected, cursor = [], anchor["token"]
        for _ in range(6):
            cursor = samples[cursor]["next"] if cursor else ""
            expected.append(cursor)  # 空串表示场景已经结束，不能当成真实未来帧。
        for names, tokens in zip(info["gt_names"], info["gt_boxes_token"]):
            if names[0] != "car":
                continue
            track = [annotations[str(token)] for token in tokens]
            if len(track) != 7 or track[0]["sample_token"] != anchor["token"]:
                raise ValueError("时刻数或当前annotation与info不对应：" + anchor["token"])
            if any(a["instance_token"] != track[0]["instance_token"] or
                   samples[a["sample_token"]]["scene_token"] != anchor["scene_token"] for a in track):
                raise ValueError("轨迹跨instance或跨scene：" + anchor["token"])
            counts["tracks"] += 1
            track_flags = set()
            for slot, (prev, ann, target) in enumerate(zip(track, track[1:], expected), 1):
                # 上游沿annotation.next前进；没有next时保留末端annotation。
                if ann["token"] != (prev["next"] or prev["token"]):
                    raise ValueError("info不符合annotation.next链：" + ann["token"])
                before, actual = samples[prev["sample_token"]], samples[ann["sample_token"]]
                dt = (actual["timestamp"] - before["timestamp"]) / 1e6
                elapsed = (actual["timestamp"] - anchor["timestamp"]) / 1e6
                counts["future_slots"] += 1
                counts["scene_available_slots" if target else "slots_beyond_scene_end"] += 1
                intervals.append(dt)
                offsets[slot - 1].append(elapsed)
                events = []
                if ann["token"] == prev["token"]:
                    cause = "repeat_at_scene_end" if not actual["next"] else "repeat_before_scene_end"
                    events.extend(("terminal_repeat", cause))
                    counts["repeat_with_scene_future_slots" if target else "repeat_beyond_scene_end_slots"] += 1
                else:
                    if dt <= 0:
                        raise ValueError("非复制annotation的时间未前进：" + ann["token"])
                    if actual["token"] != before["next"]:
                        events.append("nonadjacent_advance")
                # 错位按slot对照当前sample.next序列；没有预期未来帧时不计错位。
                if target and actual["token"] != target:
                    events.append("sample_mismatch")
                for kind in events:
                    counts[kind + "_slots"] += 1
                    track_flags.add(kind)
                for kind in events or (["aligned"] if target else []):
                    if kind not in examples:
                        examples[kind] = {
                            "anchor_sample": anchor["token"], "start_annotation": track[0]["token"],
                            "slot": slot, "previous_sample": before["token"],
                            "actual_annotation": ann["token"], "actual_sample": actual["token"],
                            "expected_sample": target or None, "actual_offset_s": elapsed,
                            "expected_offset_s": (samples[target]["timestamp"] - anchor["timestamp"]) / 1e6
                            if target else None, "step_dt_s": dt}
            for kind in track_flags:
                counts[kind + "_tracks"] += 1
    return {"counts": dict(sorted(counts.items())), "successive_actual_dt_s": summarize(intervals),
            "positive_actual_dt_s": summarize([dt for dt in intervals if dt > 0]),
            "actual_offsets_s": {str(i + 1): summarize(v) for i, v in enumerate(offsets)},
            "examples": {kind: examples.get(kind) for kind in ("aligned",) + KINDS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataroot", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] /
                        "outputs/audits/nuscenes_mini_temporal.json")
    args = parser.parse_args()
    root = args.dataroot.resolve()
    # 直接读元数据，避免初始化整个SDK、地图或模型；pickle仅用于本项目既有info。
    tables = {}
    for table in ("sample", "sample_annotation"):
        records = json.loads((root / "v1.0-mini" / f"{table}.json").read_text())
        tables[table] = {record["token"]: record for record in records}
    report = {"scope": "mini car temporal audit only; no coordinates/evaluation/training",
              "dataroot": str(root),
              "denominators": {"tracks": "current-frame x car object; not unique instances",
                               "future_slots": "tracks x 6; excludes current slot",
                               "sample_mismatch": "slots with existing expected sample; tracks with any such mismatch"},
              "splits": {}}
    for split in ("train", "val"):
        path = root / "mini_forecast" / f"infos_{split}_20sweeps_withvelo_filter_True.pkl"
        with path.open("rb") as stream:
            infos = pickle.load(stream)
        report["splits"][split] = audit(infos, tables["sample"], tables["sample_annotation"])
        report["splits"][split].update(info_path=str(path), info_bytes=path.stat().st_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "splits": {
        split: value["counts"] for split, value in report["splits"].items()}}, indent=2))


if __name__ == "__main__":
    main()
