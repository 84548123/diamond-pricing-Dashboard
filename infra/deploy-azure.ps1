param(
    [string]$Location = "centralindia",
    [string]$ResourceGroup = "diamond-pricing-rg",
    [string]$EnvironmentName = "diamond-pricing-env",
    [string]$AppName = "diamond-pricing-api",
    [string]$StorageAccount = "",
    [string]$AdminKey = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required. Install it from https://aka.ms/installazurecliwindows, reopen PowerShell, then rerun this script."
}

az account show 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    az login
}

if (-not $StorageAccount) {
    # Storage account names must be globally unique, lower case, and 3-24 characters.
    $StorageAccount = "diamonddata" + (Get-Random -Minimum 100000 -Maximum 999999)
}
if (-not $AdminKey) {
    $secureKey = Read-Host "Administrator API key" -AsSecureString
    $AdminKey = [System.Net.NetworkCredential]::new('', $secureKey).Password
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"

az extension add --name containerapp --upgrade --yes
az group create --name $ResourceGroup --location $Location
az storage account create --name $StorageAccount --resource-group $ResourceGroup --location $Location --sku Standard_LRS --kind StorageV2 --access-tier Hot
az storage container create --name dashboard-data --account-name $StorageAccount --auth-mode login
$storageKey = az storage account keys list --resource-group $ResourceGroup --account-name $StorageAccount --query "[0].value" -o tsv
$storageConnection = "DefaultEndpointsProtocol=https;AccountName=$StorageAccount;AccountKey=$storageKey;EndpointSuffix=core.windows.net"

# `containerapp up` builds the backend from Dockerfile and creates the managed environment.
# The API scales to zero when idle. 8 GiB safely processes the multi-million-row
# VDB export and mirrors processed snapshots to Blob Storage before it scales down.
az containerapp up `
  --name $AppName `
  --resource-group $ResourceGroup `
  --location $Location `
  --environment $EnvironmentName `
  --source $backendPath `
  --ingress external `
  --target-port 8000 `
  --min-replicas 0 `
  --max-replicas 1 `
  --cpu 2.0 `
  --memory 8.0Gi `
  --env-vars "CORS_ORIGINS=https://diamond-pricing-dashboard.vercel.app" "AZURE_STORAGE_CONTAINER=dashboard-data" "PORT=8000"

az containerapp secret set --name $AppName --resource-group $ResourceGroup --secrets "admin-api-key=$AdminKey" "storage-connection=$storageConnection"
az containerapp update --name $AppName --resource-group $ResourceGroup --set-env-vars "ADMIN_API_KEY=secretref:admin-api-key" "AZURE_STORAGE_CONNECTION_STRING=secretref:storage-connection"

$url = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv
Write-Host "Deployment complete. Set VITE_API_URL=https://$url in Vercel, then redeploy the frontend." -ForegroundColor Green
Write-Host "Storage account: $StorageAccount (Hot LRS). Apply a lifecycle rule to delete raw uploads after 30 days." -ForegroundColor Yellow
