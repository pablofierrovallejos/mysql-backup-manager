# Script PowerShell para crear tarea programada
# Ejecutar como Administrador

Write-Host "Creando tarea programada para backup de MySQL..." -ForegroundColor Cyan
Write-Host ""

# Obtener la ruta del directorio actual
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "backup_mysql.py"

# Detectar Python
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonPath) {
    Write-Host "ERROR: Python no encontrado en el PATH" -ForegroundColor Red
    Write-Host "Por favor instale Python o agregue Python al PATH del sistema" -ForegroundColor Red
    Read-Host "Presione Enter para salir"
    exit 1
}

Write-Host "Python encontrado en: $PythonPath" -ForegroundColor Green
Write-Host "Script: $PythonScript" -ForegroundColor Green
Write-Host ""

try {
    # Crear acción
    $Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$PythonScript`"" -WorkingDirectory $ScriptDir
    
    # Crear trigger (diario a las 23:30)
    $Trigger = New-ScheduledTaskTrigger -Daily -At "23:30"
    
    # Configurar para ejecutar con los privilegios más altos
    $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType ServiceAccount -RunLevel Highest
    
    # Configuraciones adicionales
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Registrar la tarea
    Register-ScheduledTask -TaskName "Backup MySQL Diario" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Tarea programada creada exitosamente!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Nombre: Backup MySQL Diario"
    Write-Host "Horario: Todos los días a las 23:30"
    Write-Host ""
    Write-Host "Para verificar: Get-ScheduledTask -TaskName 'Backup MySQL Diario'"
    Write-Host "Para ejecutar manualmente: Start-ScheduledTask -TaskName 'Backup MySQL Diario'"
    Write-Host "Para eliminar: Unregister-ScheduledTask -TaskName 'Backup MySQL Diario' -Confirm:`$false"
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: No se pudo crear la tarea programada" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Asegúrese de ejecutar PowerShell como Administrador" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Presione Enter para salir"
