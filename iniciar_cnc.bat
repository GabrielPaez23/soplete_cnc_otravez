@echo off
chcp 65001 >nul
title HMI CNC - Soplete

echo ==========================================================
echo        INICIANDO INTERFAZ DE CONTROL HMI CNC
echo ==========================================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se pudo encontrar Python en tu sistema.
        echo Por favor, asegúrate de instalar Python y marcar la opción 'Add Python to PATH'.
        pause
        exit /b
    )
    set PYTHON_CMD=py
)

cd /d "%~dp0"

echo [1/3] Verificando dependencias (Flask, Pandas, Openpyxl)...
%PYTHON_CMD% -c "import flask, pandas, openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias necesarias...
    %PYTHON_CMD% -m pip install --upgrade pip
    %PYTHON_CMD% -m pip install flask pandas openpyxl
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias.
        pause
        exit /b
    )
)

if not exist "%USERPROFILE%\Desktop\HMI CNC.lnk" (
    echo [2/3] ¿Deseas crear un acceso directo en tu Escritorio?
    set /p crear_acceso="Escribe S para Si, o cualquier otra tecla para omitir: "
    if /i "%crear_acceso%"=="S" (
        powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\HMI CNC.lnk'); $Shortcut.TargetPath = '%~dp0iniciar_cnc.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = 'shell32.dll,243'; $Shortcut.Save()"
    )
)

echo [3/3] Iniciando servidor y abriendo navegador...
start /b cmd /c "timeout /t 2 >nul && start http://127.0.0.1:5000"
%PYTHON_CMD% cnc_soplete.py
if errorlevel 1 (
    echo [ERROR] Ocurrió un fallo al ejecutar la aplicación.
    pause
)
