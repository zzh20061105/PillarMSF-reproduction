#!/usr/bin/env python3
"""Nonempty FP32 smoke checks of the native extension, without importing det3d.

These call native forward/backward kernels directly. They do not validate the
upstream Python autograd Functions or a complete PillarMSF model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import torch


def load_extension(build_dir: Path):
    spec = importlib.machinery.PathFinder.find_spec("pillar_cuda", [str(build_dir)])
    if spec is None or spec.loader is None or spec.origin is None:
        raise RuntimeError(f"pillar_cuda not found in {build_dir}; run build_pillar_ops.sh")
    origin = Path(spec.origin).resolve()
    if not origin.is_relative_to(build_dir):
        raise RuntimeError(f"Unexpected extension location: {origin}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, origin


def assert_equal(actual: torch.Tensor, expected: torch.Tensor) -> None:
    torch.cuda.synchronize(0)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)


def check_pillars(ops) -> None:
    # Relative xy coordinates; every point is valid, and batch segments are contiguous.
    xyz = torch.tensor(
        [[0.02, 0.03, 0.0], [0.04, 0.01, 0.5],
         [0.15, 0.28, -1.0], [0.28, 0.15, 1.0]],
        device="cuda:0", dtype=torch.float32,
    )
    batch_counts = torch.tensor([3, 1], device="cuda:0", dtype=torch.int32)
    mask = torch.zeros((2, 4, 4), device="cuda:0", dtype=torch.bool)
    assert xyz.shape[0] > 0  # Never launch the original N=0 kernel.
    ops.create_pillar_indices_stack_wrapper(0.125, xyz, batch_counts, mask)
    expected_mask = torch.zeros_like(mask)
    expected_mask[0, 0, 0] = True
    expected_mask[0, 2, 1] = True
    expected_mask[1, 1, 2] = True
    assert_equal(mask, expected_mask)

    locations = torch.cumsum(mask.flatten(), dim=0).to(torch.int32)
    num_pillars = int(locations[-1].item())
    assert num_pillars > 0
    bev_indices = (locations.view_as(mask) * mask.to(torch.int32) - 1).contiguous()
    pillars = torch.zeros((num_pillars, 3), device="cuda:0", dtype=torch.int32)
    ops.create_pillar_indices_wrapper(bev_indices, pillars)
    assert_equal(pillars, torch.tensor(
        [[0, 0, 0], [0, 2, 1], [1, 1, 2]], device="cuda:0", dtype=torch.int32,
    ))

    pairs = torch.full((xyz.shape[0], 1), -1, device="cuda:0", dtype=torch.int32)
    ops.create_pillar_indice_pairs_stack_wrapper(
        0.125, xyz, batch_counts, bev_indices, pairs,
    )
    assert_equal(pairs, torch.tensor(
        [[0], [0], [1], [2]], device="cuda:0", dtype=torch.int32,
    ))


def check_flatten(ops) -> None:
    pairs = torch.tensor(
        [[0, -1], [-1, 1], [1, 0]], device="cuda:0", dtype=torch.int32,
    )
    valid = pairs.flatten() >= 0
    prefix = torch.cumsum(valid, dim=0).to(torch.int32)
    length = int(prefix[-1].item())
    assert length > 0
    positions = (prefix * valid.to(torch.int32) - 1).contiguous()
    first = torch.zeros(length, device="cuda:0", dtype=torch.int32)
    second = torch.zeros_like(first)
    ops.flatten_indice_pairs_wrapper(pairs, positions, first, second)
    assert_equal(first, torch.tensor([0, 1, 2, 2], device="cuda:0", dtype=torch.int32))
    assert_equal(second, torch.tensor([0, 1, 1, 0], device="cuda:0", dtype=torch.int32))


def check_gather(ops) -> None:
    features = torch.tensor(
        [[1, 2], [3, 4], [5, 6]], device="cuda:0", dtype=torch.float32,
    )
    indices = torch.tensor([2, 0, 2], device="cuda:0", dtype=torch.int32)
    gathered = torch.zeros((3, 2), device="cuda:0", dtype=torch.float32)
    ops.gather_feature_wrapper(indices, features, gathered)
    assert_equal(gathered, features.index_select(0, indices.long()))

    grad_out = torch.tensor(
        [[1, 2], [3, 4], [5, 6]], device="cuda:0", dtype=torch.float32,
    )
    grad_features = torch.zeros_like(features)
    ops.gather_feature_grad_wrapper(indices, grad_out, grad_features)
    expected_grad = torch.zeros_like(features).index_add_(0, indices.long(), grad_out)
    assert_equal(grad_features, expected_grad)


def check_scatter(ops) -> None:
    # Positive inputs and unique maxima avoid the upstream zero-init/tie ambiguities.
    src = torch.tensor(
        [[1, 5, 2, 4], [3, 1, 6, 2]], device="cuda:0", dtype=torch.float32,
    )
    indices = torch.tensor([0, 0, 1, 1], device="cuda:0", dtype=torch.int32)
    arg = torch.full((2, 2), -1, device="cuda:0", dtype=torch.int32)
    pooled = torch.zeros((2, 2), device="cuda:0", dtype=torch.float32)
    ops.scatter_max_wrapper(indices, src, arg, pooled)

    # Independent PyTorch max/autograd reference.
    src_ref = src.clone().requires_grad_(True)
    pooled_ref = torch.stack(
        [src_ref[:, indices == group].max(dim=1).values for group in range(2)],
        dim=1,
    )
    assert_equal(pooled, pooled_ref.detach())
    assert_equal(arg, torch.tensor(
        [[1, 3], [4, 6]], device="cuda:0", dtype=torch.int32,
    ))

    grad_out = torch.tensor([[1, 2], [3, 4]], device="cuda:0", dtype=torch.float32)
    grad_src = torch.zeros_like(src)
    ops.scatter_max_grad_wrapper(arg, grad_out, grad_src)
    (pooled_ref * grad_out).sum().backward()
    assert_equal(grad_src, src_ref.grad)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=Path("/home/pillar/build/pillar_ops"))
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / "environment/pillar_ops_validation.json",
        help="Successful native smoke report as JSON (UTC timestamp included)",
    )
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; no native kernels were run")
    torch.cuda.set_device(0)
    ops, origin = load_extension(args.build_dir.resolve())
    passed = []
    # The original launchers use the default stream; this check intentionally uses it.
    with torch.cuda.stream(torch.cuda.default_stream(0)):
        for name, check in [
            ("pillar indices and point pairs", check_pillars),
            ("flatten valid pairs", check_flatten),
            ("gather forward and gradient kernel", check_gather),
            ("scatter max forward and gradient kernel", check_scatter),
        ]:
            check(ops)
            passed.append(name)
            print(f"[PASS] {name}")

    report = {
        "status": "passed",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "extension": str(origin),
        "scope": "nonempty FP32/int32 native kernels, CUDA device 0, default stream",
        "passed": passed,
        "not_tested": [
            "N=0 / no valid pillars: original kernels are not called",
            "upstream Python autograd Functions and end-to-end model",
            "negative scatter features, equal maxima, invalid indices",
            "ROI edges / 820 valid grid plus 832 storage shape",
            "AMP/FP16, non-default streams, multiple GPUs",
            "rotated NMS, DIoU, datasets, training, APf metrics",
        ],
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    print(f"Validation report: {output}")
    print("Native smoke checks passed. Untested boundaries remain unresolved.")


if __name__ == "__main__":
    main()
