param()

Set-Location -Path $PSScriptRoot\..
$ErrorActionPreference = "Stop"

Write-Host "`n[INFO] Starting DeliveryForensics Docker Stack..." -ForegroundColor Blue

# Create directories
New-Item -ItemType Directory -Force -Path "data\clickhouse", "data\metabase", "logs" | Out-Null

# Handle .env and Fernet Key
if (!(Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
    } else {
        New-Item -ItemType File -Path .env | Out-Null
    }
}

if (!(Select-String -Path .env -Pattern "FERNET_KEY" -Quiet)) {
    $keyBytes = New-Object byte[] 32
    [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($keyBytes)
    $fernetKey = [Convert]::ToBase64String($keyBytes)
    Add-Content .env "FERNET_KEY=$fernetKey"
}

if (!(Select-String -Path .env -Pattern "AIRFLOW_UID" -Quiet)) {
    Add-Content .env "AIRFLOW_UID=50000"
}

# Start Stack
docker compose up -d --build

Write-Host "`n[INFO] Waiting for ClickHouse to be healthy..." -ForegroundColor Blue
do {
    $status = docker compose ps clickhouse --format "{{.Health}}"
    if ($status -eq "healthy") { break }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
} while ($true)

Write-Host "`nClickHouse is UP." -ForegroundColor Green

Write-Host "`n[INFO] Waiting for Metabase to initialize..." -ForegroundColor Blue
do {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) { break }
    } catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 5
} while ($true)

Write-Host "`nMetabase is UP." -ForegroundColor Green

# Provisioning
Write-Host "`n[INFO] Restoring ClickHouse Data & Provisioning Metabase..." -ForegroundColor Blue
docker exec -e PYTHONPATH=/opt/airflow/plugins --user airflow project-airflow-scheduler-1 python3 /opt/airflow/scripts/restore_db.py
docker exec -e PYTHONPATH=/opt/airflow/plugins --user airflow project-airflow-scheduler-1 python3 /opt/airflow/scripts/provision_metabase.py

Write-Host "`n[SUCCESS] DeliveryForensics system is running!" -ForegroundColor Green
Write-Host "--------------------------------------------------------"
Write-Host " Airflow Webserver:  http://localhost:8080 (User: airflow, Pass: airflow)"
Write-Host " Metabase Dashboard: http://localhost:3000 (User: admin@dustinia.com, Pass: DustiniaMaster2026!)"
Write-Host " ClickHouse HTTP:    http://localhost:8123"
Write-Host "--------------------------------------------------------"

