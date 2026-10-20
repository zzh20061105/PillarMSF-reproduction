"""用手工轨迹检查工作副本中的评价函数；不读真实数据，不运行地图或模型。

WSL现有venv：python -B scripts/check_forecast_sdk.py
默认报告：outputs/checks/forecast_sdk_compatibility.json；结果仅代表合成样例。
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path,
                        default=PROJECT_ROOT / "outputs/checks/forecast_sdk_compatibility.json")
    args = parser.parse_args()

    # 只影响本次进程；明确使用可修改SDK，避免误用reference或pip里的同名包。
    sdk_root = (PROJECT_ROOT / "third_party/nuscenes-forecast/python-sdk").resolve()
    sys.path.insert(0, str(sdk_root))
    import numpy as np
    import nuscenes
    from nuscenes.eval.common.data_classes import EvalBoxes
    from nuscenes.eval.common.utils import center_distance
    from nuscenes.eval.detection import algo
    from nuscenes.eval.detection.data_classes import DetectionBox

    loaded = Path(nuscenes.__file__).resolve()
    if not loaded.is_relative_to(sdk_root) or not Path(algo.__file__).resolve().is_relative_to(sdk_root):
        raise RuntimeError(f"SDK导入路径不符合本次检查范围：{loaded}")

    def make_boxes(offset):
        # 7位置含当前和6个未来位置；所有字段明确给值，不依赖数据集或地图。
        common = dict(size=(2.0, 4.0, 1.5), rotation=(1.0, 0.0, 0.0, 0.0),
                      velocity=(1.0, 0.0), detection_name="car", detection_score=1.0,
                      attribute_name="vehicle.parked")
        trajectory = [DetectionBox(sample_token=f"synthetic-{i}",
                                   translation=(float(i) + offset, 0.0, 0.0), **common)
                      for i in range(7)]
        outer = DetectionBox(sample_token="synthetic-0", translation=(offset, 0.0, 0.0),
                             forecast_boxes=trajectory, **common)
        boxes = EvalBoxes()
        boxes.add_boxes("synthetic-0", [outer])
        return boxes

    errors = ("trans_err", "vel_err", "scale_err", "orient_err", "attr_err",
              "avg_disp_err", "final_disp_err", "miss_rate")
    cases = []
    for name, offset, expected in (("perfect_match", 0.0, 1.0),
                                   ("no_match", 20.0, 0.0)):
        # 当前这条accumulate路径不访问nusc；K=1，不覆盖cohort或多候选选择。
        result = algo.accumulate(None, make_boxes(0.0), make_boxes(offset),
                                 "car", center_distance, 2.0, forecast=7, K=1,
                                 cohort_analysis=False, oracle=False)
        for values in (result.precision, result.precision_mr, *result.forecast_precision):
            if values.shape != (101,) or values.dtype != np.dtype("float64"):
                raise AssertionError("评价数组应为101项float64")
            np.testing.assert_allclose(values, expected, rtol=0, atol=1e-12)
        if len(result.forecast_precision) != 7:
            raise AssertionError("应返回7个位置的forecast precision")
        if expected == 1.0:
            # 至少一个真匹配才会进入六处浮点转换；同时检查误差与召回率。
            np.testing.assert_allclose(result.recall, np.linspace(0, 1, 101), rtol=0, atol=1e-12)
            np.testing.assert_allclose(result.confidence, 1.0, rtol=0, atol=1e-12)
            for field in errors:
                np.testing.assert_allclose(getattr(result, field), 0.0, rtol=0, atol=1e-12)
            np.testing.assert_allclose([result.rec_val, *result.rec_fval], 1.0, rtol=0, atol=1e-12)
        score = algo.calc_fap_mr(result, min_recall=0.1, min_precision=0.1)
        np.testing.assert_allclose(score, expected, rtol=0, atol=1e-12)
        cases.append({"case": name, "passed": True, "expected_precision": expected,
                      "synthetic_joint_fap_mr": float(score)})

    # 只有全部断言通过才写成功报告；合成分数不能作为mini或论文复现结果。
    report = {"scope": "synthetic_car_accumulate_K1_only", "numpy_version": np.__version__,
              "sdk_file": str(loaded), "algo_file": str(Path(algo.__file__).resolve()),
              "cases": cases, "map_checked": False, "real_data_checked": False,
              "model_checked": False, "training_run": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[通过] 两个合成评价样例；NumPy {np.__version__}；SDK来自 {loaded.parent}")
    print(f"[报告] {args.report}")


if __name__ == "__main__":
    main()
