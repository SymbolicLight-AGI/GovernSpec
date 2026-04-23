param(
    [string]$Workdir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$IntentFile = "intent.yaml",
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

function Invoke-IntentStep {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Host ">> intent $($Arguments -join ' ')"
    & intent @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Intent command failed with exit code ${LASTEXITCODE}: intent $($Arguments -join ' ')"
    }
}

Push-Location $resolvedWorkdir
try {
    if ($Init) {
        if (Test-Path -LiteralPath $IntentFile) {
            Write-Host ">> using existing intent file: $IntentFile"
        }
        else {
            Invoke-IntentStep -Arguments @("init", "--file", $IntentFile)
        }
    }

    if (-not (Test-Path -LiteralPath $IntentFile)) {
        throw "Intent file not found: $IntentFile. Run the script with -Init or create the file first."
    }

    Invoke-IntentStep -Arguments @("validate", $IntentFile)
    Invoke-IntentStep -Arguments @("compile", $IntentFile, "--target", "prompt", "--out", $PromptOut)
    Invoke-IntentStep -Arguments @("compile", $IntentFile, "--target", "openai-json", "--out", $OpenAIJsonOut)
    Invoke-IntentStep -Arguments @("compile", $IntentFile, "--target", "mcp-plan", "--out", $McpPlanOut)

    if ($SkipTest) {
        Write-Host ">> skipping final intent test because -SkipTest was provided"
        exit 0
    }

    if (-not (Test-Path -LiteralPath $OutputFile)) {
        throw "Output file not found: $OutputFile. Generate model output first or rerun with -SkipTest."
    }

    Invoke-IntentStep -Arguments @("test", $IntentFile, "--output", $OutputFile)
}
finally {
    Pop-Location
}
