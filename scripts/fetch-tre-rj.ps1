$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot '../data/validation'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($endpoint in @('locaisvotacao', 'zonas')) {
    $uri = "https://apps.tre-rj.jus.br/api-dados-abertos/$endpoint"
    $response = Invoke-WebRequest -Uri $uri -TimeoutSec 45
    $json = if ($response.Content -is [byte[]]) {
        [Text.Encoding]::UTF8.GetString($response.Content)
    } else { [string]$response.Content }
    $items = $json | ConvertFrom-Json
    if (-not ($items -is [array])) { throw "Resposta inesperada de $uri" }
    $json | Set-Content (Join-Path $destination "tre-rj-$endpoint.json") -Encoding utf8
    Write-Output "$endpoint : $($items.Count) registros"
}
