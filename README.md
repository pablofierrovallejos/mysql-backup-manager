# Backup Automático de Bases de Datos MySQL con Docker

Solución containerizada en Docker para realizar backups automáticos de bases de datos MySQL con programación mediante cron interno.

## 📋 Características

- ✅ Backup de múltiples bases de datos MySQL
- ✅ Compresión automática de archivos con gzip
- ✅ Nombres de archivo con fecha y hora
- ✅ Logging detallado de operaciones
- ✅ Limpieza automática de backups antiguos (30 días)
- ✅ **Programación automática mediante cron interno del contenedor**
- ✅ **Ejecución diaria a las 23:30 horas**
- ✅ **Contenedor portable para despliegue en cualquier máquina remota**
- ✅ **Persistencia de backups mediante volúmenes Docker**

## 🔧 Requisitos Previos

**Solo necesitas Docker:**

1. **Docker Desktop** (Windows/Mac) o **Docker Engine** (Linux)
   - Descargar desde: https://www.docker.com/products/docker-desktop/
   - Verificar instalación: `docker --version`

2. **Docker Compose** (incluido en Docker Desktop)
   - Verificar instalación: `docker-compose --version`

## 📦 Instalación y Despliegue

### Opción 1: Usando Docker Compose (Recomendado)

1. Clonar o copiar este proyecto en tu máquina (local o remota)

2. Ajustar configuración en `docker-compose.yml` si es necesario:
   ```yaml
   environment:
     - TZ=America/Mexico_City  # Zona horaria
     - DB_HOST=35.209.63.29
     - DB_PORT=9090
     # ... otros parámetros
   ```

3. Construir y ejecutar el contenedor:
   ```bash
   docker-compose up -d
   ```

### Opción 2: Usando Docker directamente

1. Construir la imagen:
   ```bash
   docker build -t mysql-backup:latest .
   ```

2. Ejecutar el contenedor:
   ```bash
   docker run -d \
     --name mysql-backup \
     --restart unless-stopped \
     -v ./backups:/app/backups \
     -v ./backup_mysql.log:/app/backup_mysql.log \
     -e TZ=America/Mexico_City \
     mysql-backup:latest
   ```

## ⚙️ Configuración

### Bases de Datos

El script está configurado para respaldar las siguientes bases de datos:
- `db_springboot_cloud`
- `gastos_db`
- `ruleta_db`
- `traking`

**Servidor MySQL:**
- Host: `35.209.63.29`
- Puerto: `9090`
- Usuario: `root`
- Contraseña: `sasa`

### Modificar Configuración

**Opción 1: Variables de entorno en `docker-compose.yml`**
```yaml
environment:
  - DB_HOST=35.209.63.29
  - DB_PORT=9090
  - DB_USER=root
  - DB_PASSWORD=sasa
  - RETENTION_DAYS=30
```

**Opción 2: Editar directamente `backup_mysql.py`**
```python
DB_HOST = '35.209.63.29'
DB_PORT = '9090'
DB_USER = 'root'
DB_PASSWORD = 'sasa'
DATABASES = ['db_springboot_cloud', 'gastos_db', 'ruleta_db', 'traking']
RETENTION_DAYS = 30
```

### Cambiar Horario de Ejecución

Edita el archivo `crontab` antes de construir la imagen:
```
# Formato: minuto hora día mes día_semana
30 23 * * *    # 23:30 todos los días
0 2 * * *      # 02:00 todos los días
*/6 * * * *    # Cada 6 horas
```

## 🚀 Uso

### Verificar Estado del Contenedor

```bash
# Ver si el contenedor está corriendo
docker ps | grep mysql-backup

# Ver logs del contenedor
docker logs mysql-backup

# Ver logs en tiempo real
docker logs -f mysql-backup
```

### Ejecución Manual del Backup

```bash
# Ejecutar backup inmediatamente (sin esperar a las 23:30)
docker exec mysql-backup python /app/backup_mysql.py

# Ver logs del último backup
docker exec mysql-backup cat /app/backup_mysql.log

# Ver logs de cron
docker exec mysql-backup tail -f /var/log/cron.log
```

### Gestión del Contenedor

```bash
# Detener el contenedor
docker-compose down

# Iniciar el contenedor
docker-compose up -d

# Reiniciar el contenedor
docker-compose restart

# Ver estadísticas de recursos
docker stats mysql-backup
```

Los backups se guardarán en la carpeta `backups/` del host con el formato:
```
nombre_base_datos_YYYYMMDD_HHMMSS.sql.gz
```

## 📊 Logs

El script genera un archivo de log `backup_mysql.log` que contiene:
- Fecha y hora de cada ejecución
- Estado de cada backup (exitoso/fallido)
- Tamaño de los archivos generados
- Errores y advertencias

## 🛠️ Comandos Útiles

### Ver logs y estado
```bash
# Logs del contenedor
docker logs mysql-backup

# Logs en tiempo real
docker logs -f mysql-backup

# Logs del script de backup
docker exec mysql-backup cat /app/backup_mysql.log

# Logs de cron
docker exec mysql-backup cat /var/log/cron.log

# Entrar al contenedor (debug)
docker exec -it mysql-backup /bin/bash
```

### Gestión de backups
```bash
# Ver backups generados
ls -lh backups/

# Espacio usado por backups
du -sh backups/

# Copiar backups a otra ubicación
docker cp mysql-backup:/app/backups /ruta/destino/
```

### Actualizar configuración
```bash
# Si modificas backup_mysql.py o crontab, reconstruir:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
respalda-basedatos/
├── Dockerfile                   # Definición del contenedor
├── docker-compose.yml           # Orquestación del contenedor
├── backup_mysql.py              # Script principal de backup
├── crontab                      # Programación de tareas (23:30 diario)
├── entrypoint.sh                # Script de inicialización del contenedor
├── requirements.txt             # Dependencias Python (usa módulos estándar)
├── README.md                    # Este archivo
├── .env.example                 # Ejemplo de variables de entorno
├── backups/                     # Carpeta donde se guardan los backups (volumen)
│   └── *.sql.gz                 # Archivos de backup comprimidos
└── backup_mysql.log             # Archivo de log (volumen)
```

## 🚢 Despliegue en Máquina Remota

### Transferir el proyecto

**Opción 1: Copiar archivos**
```bash
# Copiar todo el directorio a la máquina remota
scp -r respalda-basedatos usuario@maquina-remota:/ruta/destino/

# O usar rsync
rsync -avz respalda-basedatos/ usuario@maquina-remota:/ruta/destino/
```

**Opción 2: Usar Git**
```bash
# En la máquina remota
git clone <tu-repositorio>
cd respalda-basedatos
```

**Opción 3: Exportar/Importar imagen Docker**
```bash
# En la máquina local
docker build -t mysql-backup:latest .
docker save mysql-backup:latest | gzip > mysql-backup.tar.gz

# Transferir el archivo
scp mysql-backup.tar.gz usuario@maquina-remota:/tmp/

# En la máquina remota
docker load < /tmp/mysql-backup.tar.gz
docker-compose up -d
```

### Ejecutar en la máquina remota

```bash
# SSH a la máquina remota
ssh usuario@maquina-remota

# Navegar al directorio
cd /ruta/destino/respalda-basedatos

# Iniciar el contenedor
docker-compose up -d

# Verificar que está corriendo
docker ps | grep mysql-backup
```

## ⚠️ Seguridad

**Importante:** Este script contiene credenciales de base de datos en texto plano. Considera:

1. **Proteger el archivo:**
   ```powershell
   # Restringir permisos del archivo
   icacls backup_mysql.py /inheritance:r /grant:r "$env:USERNAME:F"
   ```

2. **Usar variables de entorno:**
   ```python
   import os
   DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'default_password')
   ```

3. **Proteger los backups:**
   - La carpeta `backups/` contiene datos sensibles
   - Considera encriptar los archivos de backup
   - Restringir acceso a usuarios autorizados

## 🔍 Solución de Problemas

### El contenedor no inicia
```bash
# Ver logs de error
docker logs mysql-backup

# Verificar que Docker está corriendo
docker ps

# Reconstruir sin caché
docker-compose build --no-cache
docker-compose up -d
```

### Los backups no se generan
```bash
# Verificar logs de cron
docker exec mysql-backup cat /var/log/cron.log

# Ejecutar backup manualmente para ver errores
docker exec mysql-backup python /app/backup_mysql.py

# Verificar que cron está corriendo
docker exec mysql-backup ps aux | grep cron
```

### Error: "Access denied" al conectar a MySQL
- Verificar las credenciales en `docker-compose.yml` o `backup_mysql.py`
- Comprobar que el usuario tenga permisos de backup
- Verificar conectividad: 
  ```bash
  docker exec mysql-backup mysqldump --host=35.209.63.29 --port=9090 --user=root --password=sasa --version
  ```

### No se crean los archivos en la carpeta backups/
- Verificar que el volumen está montado correctamente:
  ```bash
  docker inspect mysql-backup | grep Mounts -A 10
  ```
- Verificar permisos de la carpeta `backups/` en el host
- Revisar logs: `docker exec mysql-backup cat /app/backup_mysql.log`

### El horario no coincide (23:30)
- Verificar la zona horaria del contenedor:
  ```bash
  docker exec mysql-backup date
  ```
- Ajustar `TZ` en `docker-compose.yml`:
  ```yaml
  environment:
    - TZ=America/Mexico_City  # o tu zona horaria
  ```

### Probar cron manualmente
```bash
# Ejecutar el comando de cron directamente
docker exec mysql-backup /bin/bash -c "cd /app && /usr/local/bin/python /app/backup_mysql.py"

# Ver el contenido del crontab
docker exec mysql-backup crontab -l
```

## 📝 Licencia

Este proyecto es de uso libre.

## 👤 Autor

Script creado para automatizar backups de bases de datos MySQL.

---

**Fecha de creación:** Noviembre 2025
