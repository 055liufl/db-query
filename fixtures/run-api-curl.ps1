# 与 test.rest 对齐的后端 API 冒烟（需本机已启动 backend:8000）
# PowerShell: .\fixtures\run-api-curl.ps1
# 需 PostgreSQL 可连时，PUT / 元数据 / 查询 / 自然语言 才会成功

$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000/api/v1"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "=== GET /dbs ===" -ForegroundColor Cyan
curl.exe -sS -w "`nHTTP %{http_code}`n" "$base/dbs"

Write-Host "`n=== PUT invalid URL (expect 400) ===" -ForegroundColor Cyan
curl.exe -sS -w "`nHTTP %{http_code}`n" -X PUT "$base/dbs/test-bad" `
  -H "Content-Type: application/json" `
  --data-binary "@$root\fixtures\curl-body-bad-url.json"

Write-Host "`n=== GET missing connection (expect 404) ===" -ForegroundColor Cyan
curl.exe -sS -w "`nHTTP %{http_code}`n" "$base/dbs/no-such"

Write-Host "`n=== POST query missing connection (expect 404) ===" -ForegroundColor Cyan
curl.exe -sS -w "`nHTTP %{http_code}`n" -X POST "$base/dbs/missing/query" `
  -H "Content-Type: application/json" `
  --data-binary "@$root\fixtures\curl-body-query.json"

Write-Host "`n=== POST natural missing connection (expect 404) ===" -ForegroundColor Cyan
curl.exe -sS -w "`nHTTP %{http_code}`n" -X POST "$base/dbs/missing/query/natural" `
  -H "Content-Type: application/json" `
  --data-binary "@$root\fixtures\curl-body-natural.json"

Write-Host "`n=== PUT my-postgres (needs PostgreSQL on localhost:5432) ===" -ForegroundColor Yellow
curl.exe -sS -w "`nHTTP %{http_code}`n" -X PUT "$base/dbs/my-postgres" `
  -H "Content-Type: application/json" `
  --data-binary "@$root\fixtures\curl-body-put.json"

Write-Host "`nDone. If PUT returned 500 connection_failed, start PostgreSQL and re-run." -ForegroundColor Gray
