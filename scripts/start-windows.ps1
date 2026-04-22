$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$ImageName = "pm-mvp"
$ContainerName = "pm-mvp"
$VolumeName = "pm-mvp-data"
$EnvFile = Join-Path $RootDir ".env"

docker build --tag $ImageName $RootDir

$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }
if ($existing) {
  docker rm -f $ContainerName | Out-Null
}

docker volume create $VolumeName | Out-Null

$dockerArgs = @(
  "--detach"
  "--name", $ContainerName
  "--publish", "8000:8000"
  "--volume", "${VolumeName}:/data"
  "--env", "DB_PATH=/data/pm.db"
)

if (Test-Path $EnvFile) {
  $dockerArgs += @("--env-file", $EnvFile)
}

docker run @dockerArgs $ImageName | Out-Null

Write-Output "PM MVP started: http://localhost:8000"
