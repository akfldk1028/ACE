# NotebookLM 로그인 헬퍼 스크립트
# 사용법: PowerShell에서 직접 실행
#   D:\Data\25_ACE\docs\portfolio\nlm_login.ps1

$ErrorActionPreference = "Stop"
$NLM = "C:\Users\SOGANG1\AppData\Roaming\Python\Python313\Scripts\nlm.exe"

Write-Host "=== NotebookLM CLI Login ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. 기존 invalid profile 삭제 + Chrome 열기..." -ForegroundColor Yellow
& $NLM login --clear

Write-Host ""
Write-Host "=== 로그인 결과 확인 ===" -ForegroundColor Cyan
& $NLM login --check

Write-Host ""
Write-Host "Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
