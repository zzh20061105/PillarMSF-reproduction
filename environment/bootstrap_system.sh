#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then echo 'Run in the new PillarMSF distro as root'; exit 1; fi
. /etc/os-release
if [ "$ID" != ubuntu ] || [ "$VERSION_ID" != 22.04 ]; then echo 'Expected Ubuntu 22.04'; exit 1; fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg git build-essential python3.10-venv python3.10-dev python3-pip cmake ninja-build pkg-config unzip
if ! id pillar >/dev/null 2>&1; then useradd --create-home --shell /bin/bash pillar; fi
cat > /etc/wsl.conf <<'EOF'
[user]
default=pillar
[interop]
appendWindowsPath=false
EOF
install -d -o pillar -g pillar /home/pillar/venvs /home/pillar/data /home/pillar/build /home/pillar/.cache /home/pillar/.cache/pip /home/pillar/.cache/torch_extensions
curl -fL --retry 3 --connect-timeout 20 https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb -o /tmp/pillarmsf-cuda-keyring.deb
dpkg -i /tmp/pillarmsf-cuda-keyring.deb
apt-get update
apt-get install -y --no-install-recommends cuda-toolkit-12-1
runuser -u pillar -- python3.10 -m venv /home/pillar/venvs/pillarmsf
printf '%s\n' 'Independent system dependencies installed.'
