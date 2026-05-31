param(
    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Wait-JsonEndpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$Retries = 60
    )

    for ($i = 1; $i -le $Retries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5
            Write-Host "$Name OK"
            return $response
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "$Name did not become ready: $Url"
}

function Invoke-Docker {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $DockerExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: docker $($Arguments -join ' ')"
    }
}

function Invoke-DockerCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 45
    )

    $argumentText = ($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join " "

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $DockerExe
    $startInfo.Arguments = $argumentText
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $null = $process.Start()
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        $process.Kill()
        return @{
            ExitCode = 124
            Output = "Timed out after $TimeoutSeconds seconds."
        }
    }

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    return @{
        ExitCode = $process.ExitCode
        Output = (($stdout, $stderr) -join "`n").Trim()
    }
}

$DockerCommand = (Get-Command docker -ErrorAction SilentlyContinue)
if ($DockerCommand) {
    $DockerExe = $DockerCommand.Source
} else {
    $DefaultDockerExe = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $DefaultDockerExe) {
        $DockerExe = $DefaultDockerExe
    } else {
        $DockerExe = $null
    }
}

if (-not $DockerExe) {
    throw "Docker CLI is not available. Install/start Docker Desktop, then rerun this script."
}

$dockerInfo = Invoke-DockerCapture -Arguments @("version", "--format", "{{.Server.Version}}")
$serverVersionText = $dockerInfo.Output
if (
    $dockerInfo.ExitCode -ne 0 -or
    [string]::IsNullOrWhiteSpace($serverVersionText) -or
    $serverVersionText -eq '""' -or
    $serverVersionText -match "request returned|unable|Cannot connect|Docker Desktop is unable|daemon"
) {
    Write-Host @"
Docker Engine is not ready.

Docker CLI was found at: $DockerExe
docker version output:
$serverVersionText

Start Docker Desktop and wait until the engine is running, then rerun this script.
On Windows, if WSL/Virtual Machine Platform/Hyper-V was just enabled or Docker Desktop was just installed, restart Windows first.
"@
    exit 1
}
Write-Host "Docker Engine OK: $serverVersionText"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Invoke-Docker -Arguments @("compose", "up", "-d", "--build")
Invoke-Docker -Arguments @("compose", "ps")

$backendPort = "8000"
$frontendPort = "80"
foreach ($line in Get-Content ".env") {
    if ($line -match "^BACKEND_PORT=(.+)$") { $backendPort = $Matches[1].Trim() }
    if ($line -match "^FRONTEND_PORT=(.+)$") { $frontendPort = $Matches[1].Trim() }
}

Wait-JsonEndpoint -Url "http://127.0.0.1:$backendPort/api/health" -Name "Backend health"
Wait-JsonEndpoint -Url "http://127.0.0.1:$backendPort/api/llm/status" -Name "LLM status"

$frontendReady = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$frontendPort" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            Write-Host "Frontend OK"
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $frontendReady) {
    throw "Frontend did not become ready: http://127.0.0.1:$frontendPort"
}

python scripts/smoke_api.py "http://127.0.0.1:$backendPort/api"
if ($LASTEXITCODE -ne 0) {
    throw "API smoke test failed."
}

Write-Host "Docker Compose verification passed."

if ($Cleanup) {
    Invoke-Docker -Arguments @("compose", "down")
    Write-Host "Docker Compose services stopped."
}
