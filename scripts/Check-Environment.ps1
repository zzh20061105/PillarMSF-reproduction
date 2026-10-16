$ErrorActionPreference = 'Stop'
& "$env:WINDIR\System32\wsl.exe" -d PillarMSF-Ubuntu22 -u pillar -- bash -lc 'source /mnt/d/ai_study/PillarMSF/scripts/activate.sh && python scripts/check_environment.py --output environment/validation.json'
exit $LASTEXITCODE
