@echo off
REM Script para crear tarea programada en Windows Task Scheduler
REM Ejecutar como Administrador

echo Creando tarea programada para backup de MySQL...
echo.

REM Obtener la ruta del directorio actual
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%backup_mysql.py"

REM Detectar ruta de Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python no encontrado en el PATH
    echo Por favor instale Python o agregue Python al PATH del sistema
    pause
    exit /b 1
)

REM Obtener ruta completa de Python
for /f "delims=" %%i in ('where python') do set "PYTHON_PATH=%%i"

echo Python encontrado en: %PYTHON_PATH%
echo Script: %PYTHON_SCRIPT%
echo.

REM Crear la tarea programada
schtasks /Create /TN "Backup MySQL Diario" /TR "\"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"" /SC DAILY /ST 23:30 /F /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo Tarea programada creada exitosamente!
    echo ============================================
    echo.
    echo Nombre: Backup MySQL Diario
    echo Horario: Todos los dias a las 23:30
    echo.
    echo Para verificar: schtasks /Query /TN "Backup MySQL Diario" /V /FO LIST
    echo Para ejecutar manualmente: schtasks /Run /TN "Backup MySQL Diario"
    echo Para eliminar: schtasks /Delete /TN "Backup MySQL Diario" /F
    echo.
) else (
    echo.
    echo ERROR: No se pudo crear la tarea programada
    echo Asegurese de ejecutar este archivo como Administrador
    echo.
)

pause
