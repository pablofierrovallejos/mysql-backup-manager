#!/bin/bash
set -e

echo "=========================================="
echo "Iniciando contenedor de Backup MySQL"
echo "=========================================="
echo "Fecha: $(date)"
echo "Zona horaria: $TZ"
echo ""

# Verificar dependencias
if ! command -v mysqldump &> /dev/null; then
    echo "ERROR: mysqldump no está instalado"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "ERROR: Python no está instalado"
    exit 1
fi

echo "✓ mysqldump: $(mysqldump --version | head -1)"
echo "✓ Python: $(python --version)"
echo ""

# Crear directorio de backups
mkdir -p /app/backups

echo "Configuración:"
echo "- Directorio de backups: /app/backups"
echo "- Programación: Todos los días a las 23:30"
echo "- Monitor Web: http://<host>:5000"
echo ""

# Iniciar Flask en background
echo "Iniciando monitor web Flask..."
python /app/web_monitor.py > /app/flask.log 2>&1 &

# Iniciar scheduler en foreground con logs
echo "Iniciando scheduler de backups..."
echo "=========================================="
python /app/scheduler.py
