$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$ImageName = "pm-mvp"
$ContainerName = "pm-mvp"
$VolumeName = "pm-mvp-data"

docker build --tag $ImageName $RootDir

$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }
if ($existing) {
  docker rm -f $ContainerName | Out-Null
}

docker volume create $VolumeName | Out-Null

docker run `
  --detach `
  --name $ContainerName `
  --publish 8000:8000 `
  --volume "${VolumeName}:/data" `
  --env "DB_PATH=/data/pm.db" `
  $ImageName | Out-Null

Write-Output "PM MVP started: http://localhost:8000"
