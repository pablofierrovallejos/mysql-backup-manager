#!/bin/bash
# Script para solucionar el error de ContainerConfig y redesplegar

echo "🔄 Deteniendo y eliminando contenedor existente..."
docker-compose down

echo "🧹 Eliminando contenedor y volúmenes huérfanos..."
docker container prune -f

echo "📥 Descargando última imagen..."
docker-compose pull

echo "🚀 Iniciando contenedor con imagen actualizada..."
docker-compose up -d

echo "✅ Desplegue completado"
echo ""
echo "📊 Estado del contenedor:"
docker-compose ps

echo ""
echo "📝 Logs recientes:"
docker-compose logs --tail=20
