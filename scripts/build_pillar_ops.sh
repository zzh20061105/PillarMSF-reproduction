#!/usr/bin/env bash
# Build only PillarNet's pillar_cuda extension; never edit references/.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
REFERENCE_ROOT="$PROJECT_ROOT/references/PillarNet"
SOURCE_DIR="$REFERENCE_ROOT/det3d/ops/pillar_ops"
BUILD_DIR="/home/pillar/build/pillar_ops"
EXPECTED_REF="0634209fb889c24104d758eae153b9ff4aa0240a"
PYTHON="${PYTHON:-/home/pillar/venvs/pillarmsf/bin/python}"

export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-12.1}"
export PATH="$CUDA_HOME/bin:$PATH"
export CC="${CC:-gcc-11}"
export CXX="${CXX:-g++-11}"
export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}"
export MAX_JOBS="${MAX_JOBS:-2}"

fail() { printf '%s\n' "ERROR: $*" >&2; exit 1; }
[[ -x "$PYTHON" ]] || fail "Python not found: $PYTHON"
[[ -f "$SOURCE_DIR/setup.py" ]] || fail "Missing reference source: $SOURCE_DIR"
[[ -x "$CUDA_HOME/bin/nvcc" ]] || fail "CUDA Toolkit nvcc not found under $CUDA_HOME"
command -v "$CC" >/dev/null || fail "Compiler not found: $CC"
command -v "$CXX" >/dev/null || fail "Compiler not found: $CXX"

ACTUAL_REF="$(git -C "$REFERENCE_ROOT" rev-parse HEAD)"
[[ "$ACTUAL_REF" == "$EXPECTED_REF" ]] || fail "PillarNet HEAD differs from the pinned reference"
git -C "$REFERENCE_ROOT" diff --quiet -- det3d/ops/pillar_ops LICENSE ||
    fail "Reference pillar_ops/LICENSE has tracked changes"
git -C "$REFERENCE_ROOT" diff --cached --quiet -- det3d/ops/pillar_ops LICENSE ||
    fail "Reference pillar_ops/LICENSE has staged changes"

# Refuse symlink redirection or an unrelated populated directory. No deletion.
[[ "$(realpath -m "$BUILD_DIR")" == "$BUILD_DIR" ]] ||
    fail "Build directory resolves outside the expected path"
if [[ -d "$BUILD_DIR" && -n "$(find "$BUILD_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    [[ -f "$BUILD_DIR/.pillarmsf-source-ref" ]] ||
        fail "Existing build directory is unmarked; inspect it before reuse"
    [[ "$(cat "$BUILD_DIR/.pillarmsf-source-ref")" == "$EXPECTED_REF" ]] ||
        fail "Existing build directory belongs to another source revision"
fi

"$PYTHON" - "$CUDA_HOME/bin/nvcc" <<'PY'
import subprocess
import sys
import torch

if torch.__version__.split("+")[0] != "2.5.1" or torch.version.cuda != "12.1":
    raise SystemExit("Expected PyTorch 2.5.1 with CUDA 12.1; found "
                     f"{torch.__version__}, CUDA {torch.version.cuda}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA is unavailable; check the Windows driver and WSL GPU access")
nvcc = subprocess.check_output([sys.argv[1], "--version"], text=True)
if "release 12.1," not in nvcc:
    raise SystemExit("Expected CUDA Toolkit 12.1 nvcc; found:\n" + nvcc)
print(f"Python: {sys.executable}")
print(f"PyTorch: {torch.__version__}, CUDA runtime: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(nvcc.strip())
PY

mkdir -p -- "$BUILD_DIR"
cp -a -- "$SOURCE_DIR/." "$BUILD_DIR/"
cp -- "$REFERENCE_ROOT/LICENSE" "$BUILD_DIR/LICENSE.PillarNet"
printf '%s\n' "$EXPECTED_REF" > "$BUILD_DIR/.pillarmsf-source-ref"

# Change only the copied header: THC include removal + modern CUDA predicate.
"$PYTHON" - "$SOURCE_DIR" "$BUILD_DIR" "$EXPECTED_REF" <<'PY'
import hashlib
import json
import pathlib
import sys

source, build = map(pathlib.Path, sys.argv[1:3])
header = build / "src/cuda_utils.h"
text = header.read_text(encoding="utf-8")
old_include = "#include <THC/THC.h>"
old_check = "x.type().is_cuda()"
if text.count(old_include) != 1 or text.count(old_check) != 1:
    raise SystemExit("Unexpected cuda_utils.h; compatibility patch was not applied")
for path in (source / "src").iterdir():
    if path.is_file() and path.suffix in {".h", ".cuh", ".cpp", ".cu"}:
        residual = path.read_text(encoding="utf-8").replace(old_include, "")
        if "THC" in residual:
            raise SystemExit(f"Unexpected THC usage in {path}; review before patching")
patched = text.replace(old_include + "\n", "").replace(old_check, "x.is_cuda()")
header.write_text(patched, encoding="utf-8", newline="\n")
hashes = {
    str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in source.rglob("*") if path.is_file()
}
record = {
    "repository": "VISION-SJTU/PillarNet",
    "ref": sys.argv[3],
    "source": str(source),
    "build": str(build),
    "patches": ["remove unused THC/THC.h include", "CHECK_CUDA uses x.is_cuda()"],
    "reference_sha256": hashes,
}
(build / ".pillarmsf-build.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
)
print(f"Prepared copied sources: {build}")
PY

# Force rebuild in place to avoid accepting a stale binary. Keep existing artifacts.
(
    cd -- "$BUILD_DIR"
    "$PYTHON" setup.py build_ext --inplace --force
)

"$PYTHON" - "$SOURCE_DIR" "$BUILD_DIR" <<'PY'
import hashlib
import json
import pathlib
import sys

source, build = map(pathlib.Path, sys.argv[1:3])
record = json.loads((build / ".pillarmsf-build.json").read_text(encoding="utf-8"))
current = {
    str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in source.rglob("*") if path.is_file()
}
if current != record["reference_sha256"]:
    raise SystemExit("Reference source changed during the build; investigate")
print("Reference pillar_ops file hashes unchanged.")
PY

# Only the extension build directory is added; do not expose references/det3d.
PYTHONPATH="$BUILD_DIR" "$PYTHON" "$SCRIPT_DIR/check_pillar_ops.py" --build-dir "$BUILD_DIR"
