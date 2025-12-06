#!/usr/bin/env python3
"""
Scheduler para ejecutar backups de MySQL usando Python schedule
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_backup():
    """Ejecutar el script de backup"""
    logging.info("=" * 60)
    logging.info("Iniciando backup programado")
    logging.info("=" * 60)
    
    try:
        result = subprocess.run(
            ['python', '/app/backup_mysql.py'],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("Backup completado exitosamente")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar backup: {e.stderr}")

def main():
    logging.info("=" * 60)
    logging.info("Scheduler iniciado")
    logging.info(f"Zona horaria: {time.tzname}")
    logging.info(f"Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("Programación: Todos los días a las 23:30")
    logging.info("=" * 60)
    
    # Ejecutar backup inicial
    logging.info("Ejecutando backup inicial...")
    run_backup()
    
    # Programar ejecución diaria a las 23:30
    schedule.every().day.at("23:30").do(run_backup)
    
    # Mantener el scheduler corriendo
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto

if __name__ == '__main__':
    main()
