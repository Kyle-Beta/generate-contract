@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ============================================
echo  合同批量生成器 Windows 打包脚本
echo  生成当前 Flet 桌面版精简目录包，目标机器无需安装 Python
echo ============================================
echo.

:: ── 检查 Python（仅构建机需要）────────────────
where python > nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 python，构建机需要安装 Python 3.7+
    echo        下载：https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] 构建环境：%PY_VER%

:: ── 创建虚拟环境 ──────────────────────────────
if not exist ".venv_build\Scripts\activate.bat" (
    echo [INFO] 创建虚拟环境 .venv_build ...
    python -m venv .venv_build
    if errorlevel 1 ( echo [错误] 创建虚拟环境失败 & pause & exit /b 1 )
)
call .venv_build\Scripts\activate.bat

:: ── 安装依赖 ──────────────────────────────────
echo [INFO] 安装依赖（首次较慢）...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt pyinstaller
if errorlevel 1 ( echo [错误] 依赖安装失败 & pause & exit /b 1 )

:: ── 下载 UPX（可选，用于压缩体积）───────────────
set UPX_DIR=
if not exist "tools\upx.exe" (
    echo [INFO] 正在下载 UPX 压缩工具...
    if not exist "tools" mkdir tools
    :: 用 PowerShell 下载
    powershell -NoProfile -Command ^
      "try { Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-win64.zip' -OutFile 'tools\upx.zip' -UseBasicParsing; Expand-Archive -Path 'tools\upx.zip' -DestinationPath 'tools\upx_tmp' -Force; Copy-Item 'tools\upx_tmp\upx-4.2.4-win64\upx.exe' 'tools\upx.exe'; Remove-Item 'tools\upx.zip','tools\upx_tmp' -Recurse -Force; Write-Host 'UPX OK' } catch { Write-Host 'UPX SKIP' }"
)
if exist "tools\upx.exe" (
    echo [OK] UPX 可用，将启用压缩
    set UPX_DIR=--upx-dir tools
) else (
    echo [WARN] UPX 不可用，跳过压缩（体积约大 30%%）
)

:: ── 清理上次构建 ──────────────────────────────
if exist "dist\合同批量生成器" rd /s /q "dist\合同批量生成器" 2>nul
if exist "build" rd /s /q build 2>nul

:: ── 运行 PyInstaller ──────────────────────────
echo.
echo [INFO] 开始打包（约需 1-2 分钟）...
pyinstaller generate_contracts.spec --noconfirm %UPX_DIR%
if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方日志
    pause & exit /b 1
)

:: ── 检查结果并显示大小 ────────────────────────
if not exist "dist\合同批量生成器\合同批量生成器.exe" (
    echo [错误] 未找到输出文件 & pause & exit /b 1
)
for %%f in ("dist\合同批量生成器\合同批量生成器.exe") do set SIZE=%%~zf
set /a SIZE_KB=!SIZE! / 1024
set /a SIZE_MB=!SIZE_KB! / 1024

echo.
echo ============================================
echo  打包完成！
echo  文件：dist\合同批量生成器\合同批量生成器.exe
echo  主程序大小：!SIZE_KB! KB (!SIZE_MB! MB)
echo  说明：发布时建议压缩整个 dist\合同批量生成器 目录
echo ============================================
echo.
echo 程序说明：
echo   1. 双击打开 dist\合同批量生成器\合同批量生成器.exe
echo   2. 选择 Excel 数据源、Word 模板和输出目录
echo   3. 选择或确认“文件名字段”后点击开始生成
echo   4. 如需自定义图标，请在项目根目录放置 app.ico 后重新打包
echo.

deactivate
pause
