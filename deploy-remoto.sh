#!/bin/bash
# Script de ejemplo para desplegar en máquina remota

# Configuración
REMOTE_USER="usuario"
REMOTE_HOST="ip-servidor-remoto"
REMOTE_PATH="/opt/mysql-backup"

echo "================================================"
echo "Desplegando contenedor MySQL Backup en servidor remoto"
echo "================================================"
echo ""

# Crear directorio remoto
echo "1. Creando directorio remoto..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_PATH}"

# Copiar archivos necesarios
echo "2. Copiando archivos al servidor..."
scp Dockerfile ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp docker-compose.yml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp backup_mysql.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp crontab ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
scp entrypoint.sh ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

# Construir y ejecutar en el servidor remoto
echo "3. Construyendo y ejecutando contenedor..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
cd ${REMOTE_PATH}
docker-compose down
docker-compose build
docker-compose up -d
docker ps | grep mysql-backup
EOF

echo ""
echo "================================================"
echo "Despliegue completado!"
echo "================================================"
echo ""
echo "Para ver logs:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'docker logs mysql-backup'"
echo ""
echo "Para ejecutar backup manual:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'docker exec mysql-backup python /app/backup_mysql.py'"
echo ""
