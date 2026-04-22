$ErrorActionPreference = "Stop"

$ContainerName = "pm-mvp"
$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }

if ($existing) {
  docker rm -f $ContainerName | Out-Null
  Write-Output "PM MVP container stopped and removed."
} else {
  Write-Output "PM MVP container is not running."
}
