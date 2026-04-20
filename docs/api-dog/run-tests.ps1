param(
    [string]$CollectionPath = "docs/api-dog/wasel-api-testing.postman_collection.json",
    [string]$EnvironmentPath = "docs/api-dog/wasel-local.postman_environment.json",
    [string]$OutputDir = "docs/api-dog/evidence"
)

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$jsonOutput = Join-Path $OutputDir "newman-run-$timestamp.json"

newman run $CollectionPath `
    -e $EnvironmentPath `
    -r "cli,json" `
    --reporter-json-export $jsonOutput

if ($LASTEXITCODE -eq 0) {
    Write-Host "Run complete. JSON report saved to: $jsonOutput"
} else {
    Write-Error "Newman run failed. Exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
