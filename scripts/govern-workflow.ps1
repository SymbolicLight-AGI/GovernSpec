param(
    [string]$Workdir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$GovernFile = "govern.yaml",
    [string]$PromptOut = "task.prompt.md",
    [string]$OpenAIJsonOut = "task.openai.json",
    [string]$McpPlanOut = "task.mcp-plan.json",
    [string]$OutputFile = "ai_output.md",
    [switch]$Init,
    [switch]$SkipTest
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Workdir)) {
    New-Item -ItemType Directory -Path $Workdir -Force | Out-Null
}

$resolvedWorkdir = (Resolve-Path $Workdir).Path

function Invoke-GovernSpecStep {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host ">> governspec $($Arguments -join ' ')"
    & governspec @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "GovernSpec command failed with exit code ${LASTEXITCODE}: governspec $($Arguments -join ' ')"
    }
}

Push-Location $resolvedWorkdir
try {
    if ($Init) {
        if (Test-Path -LiteralPath $GovernFile) {
            Write-Host ">> using existing GovernSpec file: $GovernFile"
        }
        else {
            Invoke-GovernSpecStep -Arguments @("init", "--file", $GovernFile)
        }
    }

    if (-not (Test-Path -LiteralPath $GovernFile)) {
        throw "GovernSpec file not found: $GovernFile. Run the script with -Init or create the file first."
    }

    Invoke-GovernSpecStep -Arguments @("validate", $GovernFile)
    Invoke-GovernSpecStep -Arguments @("compile", $GovernFile, "--target", "prompt", "--out", $PromptOut)
    Invoke-GovernSpecStep -Arguments @("compile", $GovernFile, "--target", "openai-json", "--out", $OpenAIJsonOut)
    Invoke-GovernSpecStep -Arguments @("compile", $GovernFile, "--target", "mcp-plan", "--out", $McpPlanOut)

    if ($SkipTest) {
        Write-Host ">> skipping final governspec test because -SkipTest was provided"
        exit 0
    }

    if (-not (Test-Path -LiteralPath $OutputFile)) {
        throw "Output file not found: $OutputFile. Generate model output first or rerun with -SkipTest."
    }

    Invoke-GovernSpecStep -Arguments @("test", $GovernFile, "--output", $OutputFile)
}
finally {
    Pop-Location
}
