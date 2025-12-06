#!/usr/bin/env python3
"""
Script para respaldar bases de datos MySQL
Realiza backups de múltiples bases de datos y los guarda con fecha y hora
"""

import os
import subprocess
import datetime
import logging
import json
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_mysql.log'),
        logging.StreamHandler()
    ]
)

# Configuración de la base de datos
DB_HOST = '35.209.63.29'
DB_PORT = '9090'
DB_USER = 'root'
DB_PASSWORD = 'sasa'
DATABASES = ['db_springboot_cloud', 'gastos_db', 'ruleta_db', 'traking']

# Directorio para guardar los backups
BACKUP_DIR = Path('backups')
BACKUP_DIR.mkdir(exist_ok=True)

# Días de retención de backups (opcional)
RETENTION_DAYS = 30


def create_backup(database_name):
    """
    Crea un backup de una base de datos específica
    
    Args:
        database_name (str): Nombre de la base de datos a respaldar
        
    Returns:
        bool: True si el backup fue exitoso, False en caso contrario
    """
    try:
        # Generar nombre del archivo con fecha y hora
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{database_name}_{timestamp}.sql"
        backup_path = BACKUP_DIR / backup_filename
        
        logging.info(f"Iniciando backup de {database_name}...")
        
        # Comando mysqldump
        cmd = [
            'mysqldump',
            f'--host={DB_HOST}',
            f'--port={DB_PORT}',
            f'--user={DB_USER}',
            f'--password={DB_PASSWORD}',
            '--skip-ssl',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            database_name
        ]
        
        # Ejecutar el comando y guardar el resultado
        with open(backup_path, 'w', encoding='utf-8') as backup_file:
            result = subprocess.run(
                cmd,
                stdout=backup_file,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        # Verificar que el archivo se creó y tiene contenido
        if backup_path.exists() and backup_path.stat().st_size > 0:
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logging.info(f"✓ Backup completado: {backup_filename} ({size_mb:.2f} MB)")
            
            # Comprimir el archivo (opcional)
            compress_backup(backup_path)
            
            return True
        else:
            logging.error(f"✗ El archivo de backup está vacío: {backup_filename}")
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"✗ Error al crear backup de {database_name}: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"✗ Error inesperado al respaldar {database_name}: {str(e)}")
        return False


def compress_backup(backup_path):
    """
    Comprime el archivo de backup usando gzip
    
    Args:
        backup_path (Path): Ruta del archivo a comprimir
    """
    try:
        import gzip
        import shutil
        
        gz_path = Path(str(backup_path) + '.gz')
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Eliminar el archivo original sin comprimir
        backup_path.unlink()
        
        size_mb = gz_path.stat().st_size / (1024 * 1024)
        logging.info(f"  Archivo comprimido: {gz_path.name} ({size_mb:.2f} MB)")
        
    except Exception as e:
        logging.warning(f"  No se pudo comprimir el archivo: {str(e)}")


def cleanup_old_backups():
    """
    Elimina backups más antiguos que RETENTION_DAYS
    """
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=RETENTION_DAYS)
        deleted_count = 0
        
        for backup_file in BACKUP_DIR.glob('*.sql.gz'):
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                logging.info(f"Eliminado backup antiguo: {backup_file.name}")
        
        for backup_file in BACKUP_DIR.glob('*.sql'):
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                logging.info(f"Eliminado backup antiguo: {backup_file.name}")
        
        if deleted_count > 0:
            logging.info(f"Total de backups antiguos eliminados: {deleted_count}")
            
    except Exception as e:
        logging.warning(f"Error al limpiar backups antiguos: {str(e)}")


def main():
    """
    Función principal que ejecuta el proceso de backup
    """
    logging.info("="*60)
    logging.info("INICIO DEL PROCESO DE BACKUP")
    logging.info("="*60)
    
    success_count = 0
    failed_count = 0
    
    # Realizar backup de cada base de datos
    for database in DATABASES:
        if create_backup(database):
            success_count += 1
        else:
            failed_count += 1
    
    # Limpiar backups antiguos
    cleanup_old_backups()
    
    # Resumen
    logging.info("="*60)
    logging.info(f"RESUMEN: {success_count} exitosos, {failed_count} fallidos")
    logging.info("="*60)
    
    # Guardar estado en archivo JSON para monitoreo web
    status_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'success_count': success_count,
        'failed_count': failed_count,
        'total_databases': len(DATABASES),
        'status': 'success' if failed_count == 0 else 'error',
        'databases': DATABASES
    }
    
    try:
        with open('backup_status.json', 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        logging.warning(f"No se pudo guardar el archivo de estado: {str(e)}")
    
    # Retornar código de salida
    return 0 if failed_count == 0 else 1


if __name__ == '__main__':
    exit(main())
