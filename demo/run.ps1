<#
.SYNOPSIS
Starts or stops the Windows Multivisor demo.

.DESCRIPTION
The example deliberately uses two virtual environments:
  * .venv-rpc: Python 3.12 Supervisor/RPC hosts (required by supervisor-win).
  * .venv: Python 3.14 central Multivisor web server.

Start mode prepares these environments when needed, starts the three
Supervisor hosts and central web server in the background, waits for a real
HTTP response, then returns control to the shell. It writes only ignored,
runtime-generated config and state files. Stop mode terminates precisely the
process trees recorded by the last successful launcher run; it never guesses
at or stops a user-owned Supervisor service.

.PARAMETER Stop
Stops the web server and three Supervisor instances started by this launcher.

.PARAMETER SkipSetup
Fails instead of creating/synchronizing missing virtual environments. Useful
when checking that a prepared demo has no hidden setup step.

.PARAMETER WebPort
Local port for the central web server. Defaults to 22000. Supply another free
port when a user-owned Multivisor instance already uses the default.
#>
[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$SkipSetup,
    [ValidateRange(1, 65535)]
    [int]$WebPort = 22000
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'This PowerShell launcher is for Windows. Use the documented Unix commands on other platforms.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exampleRoot = $PSScriptRoot
$rpcVenv = Join-Path $repoRoot '.venv-rpc'
$rpcScripts = Join-Path $rpcVenv 'Scripts'
$rpcPython = Join-Path $rpcScripts 'python.exe'
$supervisord = Join-Path $rpcScripts 'supervisord.exe'
$configs = @(
    (Join-Path $exampleRoot 'supervisord_lid001.conf'),
    (Join-Path $exampleRoot 'supervisord_lid002.conf'),
    (Join-Path $exampleRoot 'supervisord_baslid001.conf')
)
$runtimeConfigs = @($configs | ForEach-Object { "$_.windows.runtime.conf" })
$stateFile = Join-Path $exampleRoot '.multivisor-demo-launcher.json'
$webExecutable = Join-Path $repoRoot '.venv\Scripts\multivisor.exe'
$requiredPorts = @(9011, 9012, 9021, 9022, 9031, 9032, $WebPort)
$supervisorProcesses = @()

function Test-TcpPort {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $connection.AsyncWaitHandle.WaitOne(250)) {
            return $false
        }
        $client.EndConnect($connection)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Stop-Example {
    if (-not (Test-Path -LiteralPath $stateFile)) {
        throw "No launcher state file exists at $stateFile. Refusing to guess which processes to stop."
    }

    $state = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
    $processIds = @($state.WebProcessId) + @($state.SupervisorProcessIds)
    foreach ($processId in $processIds | Where-Object { $_ }) {
        # /T removes only the recorded launcher process and its descendants.
        & taskkill.exe /PID $processId /T /F *> $null
    }

    foreach ($runtimeConfig in @($state.RuntimeConfigs)) {
        Remove-Item -LiteralPath $runtimeConfig -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $stateFile -Force
    Write-Host 'Stopped the demo web server and Supervisor process trees.'
}

if ($Stop) {
    Stop-Example
    return
}

if (Test-Path -LiteralPath $stateFile) {
    throw "A previous launcher run is still recorded. Run .\demo\run.ps1 -Stop first."
}

$rpcHostReady = $false
if ((Test-Path -LiteralPath $rpcPython) -and (Test-Path -LiteralPath $supervisord)) {
    try {
        $rpcVersion = (& $rpcPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
        $rpcHostReady = ($LASTEXITCODE -eq 0 -and $rpcVersion -eq '3.12')
    }
    catch {
        $rpcHostReady = $false
    }
}

if (-not $rpcHostReady) {
    if ($SkipSetup) {
        throw "Missing a Python 3.12 Supervisor host at $rpcVenv. Run without -SkipSetup to create it."
    }

    Push-Location $repoRoot
    try {
        & uv venv --clear --python 3.12 .venv-rpc
        $previousVenv = $env:VIRTUAL_ENV
        $previousPath = $env:PATH
        try {
            $env:VIRTUAL_ENV = $rpcVenv
            $env:PATH = "$rpcScripts;$previousPath"
            & uv sync --active --python 3.12 --frozen --extra rpc --no-default-groups --group rpc-test
        }
        finally {
            $env:VIRTUAL_ENV = $previousVenv
            $env:PATH = $previousPath
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $rpcPython) -or -not (Test-Path -LiteralPath $supervisord)) {
    throw 'RPC-host setup did not create its Python 3.12 executable and supervisord.'
}

Push-Location $repoRoot
try {
    if (-not $SkipSetup) {
        & uv sync --frozen --extra web
    }
    if (-not (Test-Path -LiteralPath $webExecutable)) {
        throw "Missing $webExecutable. Run without -SkipSetup to synchronize the central web environment."
    }

    $occupiedPorts = @($requiredPorts | Where-Object { Test-TcpPort $_ })
    if ($occupiedPorts.Count -gt 0) {
        throw "Ports already in use: $($occupiedPorts -join ', '). Stop the previous demo or choose a different -WebPort."
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $exampleRoot 'log') | Out-Null

    # supervisor-win cannot reliably resolve a bare `python`. Its command
    # parser also treats Windows backslashes as escapes, so the copy expands
    # %(here)s to forward-slash absolute paths before Supervisor reads it.
    $forwardRpcPython = $rpcPython -replace '\\', '/'
    $forwardExampleRoot = $exampleRoot -replace '\\', '/'
    for ($index = 0; $index -lt $configs.Count; $index++) {
        $content = Get-Content -LiteralPath $configs[$index] -Raw
        $content = $content.Replace('%(here)s', $forwardExampleRoot)
        $content = $content -replace '(?m)^command=python(?=\s)', "command=`"$forwardRpcPython`""
        Set-Content -LiteralPath $runtimeConfigs[$index] -Value $content -NoNewline
    }

    foreach ($runtimeConfig in $runtimeConfigs) {
        $process = Start-Process -FilePath $supervisord -ArgumentList @('-c', $runtimeConfig) `
            -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
        $supervisorProcesses += $process
    }

    foreach ($port in @(9012, 9022, 9032)) {
        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            if (Test-TcpPort $port) {
                $ready = $true
                break
            }
            Start-Sleep -Seconds 1
        }
        if (-not $ready) {
            throw "RPC endpoint 127.0.0.1:$port did not become ready. Inspect demo\log."
        }
    }

    $webLog = Join-Path $exampleRoot 'log\multivisor-web.log'
    $webErrorLog = Join-Path $exampleRoot 'log\multivisor-web.err.log'
    $webProcess = Start-Process -FilePath $webExecutable `
        -ArgumentList @('--bind', "127.0.0.1:$WebPort", '-c', (Join-Path $exampleRoot 'multivisor.conf')) `
        -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput $webLog `
        -RedirectStandardError $webErrorLog -PassThru

    $state = [ordered]@{
        WebPort = $WebPort
        WebProcessId = $webProcess.Id
        SupervisorProcessIds = @($supervisorProcesses.Id)
        RuntimeConfigs = @($runtimeConfigs)
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $stateFile

    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $response = Invoke-WebRequest "http://127.0.0.1:$WebPort/" -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "The web server did not answer on http://127.0.0.1:$WebPort/. Inspect $webLog and run -Stop."
    }

    Write-Host "Demo is running at http://127.0.0.1:$WebPort (web PID $($webProcess.Id))."
    Write-Host 'Stop it later with .\demo\run.ps1 -Stop.'
}
catch {
    if (Test-Path -LiteralPath $stateFile) {
        Stop-Example
    }
    else {
        foreach ($process in $supervisorProcesses) {
            if ($process) {
                & taskkill.exe /PID $process.Id /T /F *> $null
            }
        }
        foreach ($runtimeConfig in $runtimeConfigs) {
            Remove-Item -LiteralPath $runtimeConfig -Force -ErrorAction SilentlyContinue
        }
    }
    throw
}
finally {
    Pop-Location
}
