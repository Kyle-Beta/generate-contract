@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo Build Windows package
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found in PATH.
  pause
  exit /b 1
)

if not exist ".venv_build\Scripts\activate.bat" (
  echo [INFO] Create venv .venv_build
  python -m venv .venv_build
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
)

call .venv_build\Scripts\activate.bat
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  pause
  exit /b 1
)

echo [INFO] Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo [ERROR] Failed to install dependencies.
  pause
  exit /b 1
)

if exist "build" rd /s /q "build" 2>nul
if exist "dist" rd /s /q "dist" 2>nul

echo [INFO] Run PyInstaller
python -m PyInstaller generate_contracts.spec --noconfirm
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed.
  pause
  exit /b 1
)

if not exist "dist" (
  echo [ERROR] dist folder not found.
  pause
  exit /b 1
)

set APP_EXE=
for /r "dist" %%F in (*.exe) do (
  if /I not "%%~nxF"=="contract-generator-setup.exe" (
    set APP_EXE=%%F
    goto :found_exe
  )
)

:found_exe
if "%APP_EXE%"=="" (
  echo [ERROR] App exe not found in dist.
  pause
  exit /b 1
)

for %%F in ("%APP_EXE%") do (
  set SIZE=%%~zF
)
set /a SIZE_KB=!SIZE!/1024
set /a SIZE_MB=!SIZE_KB!/1024

echo.
echo [OK] Build finished
echo App: %APP_EXE%
echo Size: !SIZE_KB! KB (!SIZE_MB! MB)
echo.

call .venv_build\Scripts\deactivate.bat >nul 2>nul
pause
