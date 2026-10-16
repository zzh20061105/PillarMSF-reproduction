# source this file from an interactive Bash shell
export PILLARMSF_PROJECT=/mnt/d/ai_study/PillarMSF
export CUDA_HOME=/usr/local/cuda-12.1
export PATH="$CUDA_HOME/bin:/usr/lib/wsl/lib:$PATH"
export TORCH_CUDA_ARCH_LIST=8.9
export MAX_JOBS=2
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/home/pillar/.cache/torch_extensions
source /home/pillar/venvs/pillarmsf/bin/activate
cd "$PILLARMSF_PROJECT"
