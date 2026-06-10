param()
$ErrorActionPreference = "Stop"

Write-Host "`n[INFO] Stopping DeliveryForensics Docker Stack..." -ForegroundColor Blue

docker compose down

Write-Host "`n[SUCCESS] Stack stopped successfully." -ForegroundColor Green
