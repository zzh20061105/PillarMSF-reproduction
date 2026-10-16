#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -un)" != pillar ]; then echo 'Run as pillar in PillarMSF-Ubuntu22'; exit 1; fi
. /etc/os-release
[ "$VERSION_ID" = 22.04 ]
PROJECT=/mnt/d/ai_study/PillarMSF
# NTFS source directories are owned by the WSL mount user. Trust only these roots.
for repo in "$PROJECT" "$PROJECT/references/FutureDet" "$PROJECT/references/PillarNet" "$PROJECT/references/nuscenes-forecast"; do
    if ! git config --global --get-all safe.directory | grep -Fxq "$repo"; then
        git config --global --add safe.directory "$repo"
    fi
done
PYTHON=/home/pillar/venvs/pillarmsf/bin/python
"$PYTHON" -m pip install --upgrade pip==24.3.1
"$PYTHON" -m pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121 --constraint "$PROJECT/environment/constraints-torch.txt"
"$PYTHON" -m pip install --no-cache-dir -r "$PROJECT/environment/requirements-core.txt"
"$PYTHON" -m pip install --no-build-isolation --no-deps -e "$PROJECT"
"$PYTHON" -m pip check
"$PYTHON" -m pip freeze > "$PROJECT/environment/requirements-resolved.txt"
