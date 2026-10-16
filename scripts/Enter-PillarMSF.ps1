# Open the dedicated environment; no changes to the Windows execution policy.
$ErrorActionPreference = 'Stop'
& "$env:WINDIR\System32\wsl.exe" -d PillarMSF-Ubuntu22 -u pillar -- bash --rcfile /mnt/d/ai_study/PillarMSF/scripts/interactive.bashrc -i
exit $LASTEXITCODE
