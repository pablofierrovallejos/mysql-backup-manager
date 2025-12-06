FROM python:3.11-slim

# Información del mantenedor
LABEL maintainer="backup-admin"
LABEL description="Contenedor para backup automático de bases de datos MySQL"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir flask schedule

# Configurar zona horaria (ajustar según necesidad)
ENV TZ=America/Mexico_City
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de la aplicación
COPY backup_mysql.py /app/
COPY web_monitor.py /app/
COPY scheduler.py /app/
COPY restore_targets.json /app/
COPY entrypoint.sh /entrypoint.sh

# Crear directorio para backups
RUN mkdir -p /app/backups

# Crear directorio para logs y backups
RUN mkdir -p /app/backups && \
    touch /app/backup_mysql.log && \
    touch /app/scheduler.log && \
    touch /app/flask.log

# Dar permisos a los archivos
RUN chmod +x /entrypoint.sh && \
    chmod 666 /app/backup_mysql.log && \
    chmod 666 /app/scheduler.log && \
    chmod 666 /app/flask.log

# Volumen para persistir los backups
VOLUME ["/app/backups"]

# Exponer puerto para Flask
EXPOSE 5000

# Script de entrada
COPY entrypoint-simple.sh /entrypoint-simple.sh
RUN chmod +x /entrypoint-simple.sh
ENTRYPOINT ["/entrypoint-simple.sh"]
