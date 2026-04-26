Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [string]$ArtifactsDir = ".\dist",
    [string]$ExeName = "contract-generator.exe",
    [string]$ZipName = "contract-generator-windows.zip",
    [string]$SetupName = "contract-generator-setup.exe",
    [int]$LaunchWaitSeconds = 8,
    [switch]$SkipLaunchTest
)

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-File {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label 不存在: $Path"
    }
}

function Print-Hash {
    param([string]$Path, [string]$Label)
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $Path
    Write-Host ("{0} SHA256: {1}" -f $Label, $hash.Hash)
}

function Test-ZipContent {
    param([string]$ZipPath)

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("contract-smoke-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tmp | Out-Null
    try {
        Expand-Archive -LiteralPath $ZipPath -DestinationPath $tmp -Force
        $required = @(
            "合同批量生成器.exe",
            "README_windows.md",
            "sample_data.xlsx",
            "contract_template.docx"
        )
        foreach ($name in $required) {
            $found = Get-ChildItem -LiteralPath $tmp -Recurse -File | Where-Object { $_.Name -eq $name } | Select-Object -First 1
            if (-not $found) {
                throw "ZIP 内容缺失: $name"
            }
        }
        Write-Host "ZIP 内容检查通过。"
    }
    finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Recurse -Force
        }
    }
}

function Test-ExeLaunch {
    param([string]$ExePath, [int]$WaitSeconds)

    $proc = Start-Process -FilePath $ExePath -PassThru
    Start-Sleep -Seconds $WaitSeconds

    if ($proc.HasExited) {
        throw ("EXE 启动后立即退出，ExitCode={0}" -f $proc.ExitCode)
    }

    Write-Host ("EXE 启动检查通过，PID={0}" -f $proc.Id)
    Stop-Process -Id $proc.Id -Force
}

try {
    Write-Step "定位产物目录"
    $root = (Resolve-Path -LiteralPath $ArtifactsDir).Path
    Write-Host "ArtifactsDir: $root"

    $exePath = Join-Path $root $ExeName
    $zipPath = Join-Path $root $ZipName
    $setupPath = Join-Path $root $SetupName

    Write-Step "检查文件存在"
    Assert-File -Path $exePath -Label "EXE"
    Assert-File -Path $zipPath -Label "ZIP"
    Assert-File -Path $setupPath -Label "SETUP"
    Write-Host "文件存在检查通过。"

    Write-Step "输出文件大小"
    foreach ($file in @($exePath, $zipPath, $setupPath)) {
        $item = Get-Item -LiteralPath $file
        Write-Host ("{0} : {1:N2} MB" -f $item.Name, ($item.Length / 1MB))
    }

    Write-Step "输出 SHA256"
    Print-Hash -Path $exePath -Label "EXE"
    Print-Hash -Path $zipPath -Label "ZIP"
    Print-Hash -Path $setupPath -Label "SETUP"

    Write-Step "检查 ZIP 内容"
    Test-ZipContent -ZipPath $zipPath

    if (-not $SkipLaunchTest) {
        Write-Step "检查 EXE 可启动性"
        Test-ExeLaunch -ExePath $exePath -WaitSeconds $LaunchWaitSeconds
    }
    else {
        Write-Host "已跳过 EXE 启动检查。"
    }

    Write-Step "结果"
    Write-Host "Windows 构建冒烟检查通过。" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host ""
    Write-Host ("[FAIL] {0}" -f $_.Exception.Message) -ForegroundColor Red
    exit 1
}
