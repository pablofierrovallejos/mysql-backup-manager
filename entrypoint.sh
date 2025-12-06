#!/bin/bash
set -e

echo "=========================================="
echo "Iniciando contenedor de Backup MySQL"
echo "=========================================="
echo "Fecha: $(date)"
echo "Zona horaria: $TZ"
echo ""

# Verificar que mysqldump está disponible
if ! command -v mysqldump &> /dev/null; then
    echo "ERROR: mysqldump no está instalado"
    exit 1
fi

echo "✓ mysqldump encontrado: $(mysqldump --version)"

# Verificar que Python está disponible
if ! command -v python &> /dev/null; then
    echo "ERROR: Python no está instalado"
    exit 1
fi

echo "✓ Python encontrado: $(python --version)"

# Crear directorio de backups si no existe
mkdir -p /app/backups

# Crear archivos de log si no existen
touch /app/backup_mysql.log
touch /var/log/cron.log

echo ""
echo "Configuración de backup:"
echo "- Directorio de backups: /app/backups"
echo "- Log de backup: /app/backup_mysql.log"
echo "- Log de cron: /var/log/cron.log"
echo "- Programación: Todos los días a las 23:30"
echo ""

# Verificar que el archivo de script existe
if [ ! -f /app/backup_mysql.py ]; then
    echo "ERROR: Script backup_mysql.py no encontrado"
    exit 1
fi

echo "✓ Script de backup encontrado"

# Dar permisos al crontab y aplicarlo
chmod 0644 /etc/cron.d/backup-cron
crontab /etc/cron.d/backup-cron

# Verificar que el crontab está configurado
echo "✓ Tareas cron configuradas:"
crontab -l
echo ""

echo "=========================================="
echo "Ejecutando backup inicial..."
echo "=========================================="
python /app/backup_mysql.py
echo ""

echo "=========================================="
echo "Contenedor iniciado correctamente"
echo "=========================================="
echo ""
echo "Monitor Web disponible en: http://<host>:5000"
echo ""
echo "Para ejecutar backup manualmente:"
echo "  docker exec mysql-backup python /app/backup_mysql.py"
echo ""
echo "Para ver logs de cron:"
echo "  docker exec mysql-backup tail -f /var/log/cron.log"
echo ""
echo "Para ver logs de backup:"
echo "  docker exec mysql-backup tail -f /app/backup_mysql.log"
echo ""

# Iniciar Flask en background
echo "Iniciando servidor web Flask..."
python /app/web_monitor.py > /var/log/flask.log 2>&1 &

# Iniciar cron y seguir los logs
echo "Iniciando servicio cron..."
cron && tail -f /var/log/cron.log /app/backup_mysql.log
