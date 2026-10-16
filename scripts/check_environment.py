"""Small environment probe, not a model or paper accuracy test."""
import argparse
import importlib.metadata as md
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def probe():
    import numpy as np
    import torch
    import spconv.pytorch as spconv
    assert platform.python_version_tuple()[:2] == ("3", "10")
    assert torch.__version__ == "2.5.1+cu121", torch.__version__
    assert md.version("spconv-cu120") == "2.3.6"
    assert np.__version__ == "1.26.4"
    assert torch.cuda.is_available(), "CUDA device unavailable"
    torch.manual_seed(7)
    x = torch.tensor([[1., 2.], [3., 4.]], device="cuda", requires_grad=True)
    x.square().sum().backward()
    assert torch.equal(x.grad, 2 * x.detach())
    features = torch.randn(4, 8, device="cuda", requires_grad=True)
    indices = torch.tensor([[0, 1, 1], [0, 2, 2], [1, 3, 3], [1, 4, 4]],
                           dtype=torch.int32, device="cuda")
    sparse = spconv.SparseConvTensor(features, indices, [8, 8], batch_size=3)
    # Third sample is empty: the explicit batch size must survive the conversion.
    subm = spconv.SubMConv2d(8, 8, 3, padding=1, bias=False).cuda()
    down = spconv.SparseConv2d(8, 16, 3, stride=2, padding=1, bias=False).cuda()
    out = down(subm(sparse)).dense()
    assert list(out.shape) == [3, 16, 4, 4], list(out.shape)
    out.square().mean().backward()
    for grad in (features.grad, subm.weight.grad, down.weight.grad):
        assert grad is not None and torch.isfinite(grad).all()
        assert grad.abs().sum() > 0
    assert torch.count_nonzero(out[2]) == 0
    torch.cuda.synchronize()
    nvcc = shutil.which("nvcc")
    assert nvcc is not None, "nvcc absent from PATH"
    nvcc_version = subprocess.check_output([nvcc, "--version"], text=True).strip()
    assert "release 12.1" in nvcc_version, nvcc_version
    gpu = subprocess.check_output([
        "nvidia-smi", "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader"], text=True).strip()
    return {
        "python": platform.python_version(), "torch": torch.__version__,
        "torch_cuda": torch.version.cuda, "numpy": np.__version__,
        "spconv_cu120": md.version("spconv-cu120"),
        "cumm_cu120": md.version("cumm-cu120"), "gpu": gpu,
        "compute_capability": list(torch.cuda.get_device_capability()),
        "nvcc": nvcc_version,
        "gcc": subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0],
        "checks": {"torch_cuda_forward_backward": "passed",
                   "spconv_2d_subm_downsample_forward_backward": "passed",
                   "spconv_preserves_empty_batch": "passed",
                   "sparse_output_shape": list(out.shape)},
        "not_verified": ["full FutureDet imports and training", "nuScenes data chain",
                         "PillarMSF model", "APf accuracy", "AMP or multi-GPU"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("environment/validation.json"))
    args = parser.parse_args()
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "status": "failed"}
    try:
        report.update(probe())
        report["status"] = "passed"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
