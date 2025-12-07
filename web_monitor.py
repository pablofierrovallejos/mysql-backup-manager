#!/usr/bin/env python3
"""
Aplicación Flask para monitorear el estado de los backups de MySQL
"""

from flask import Flask, render_template_string, jsonify, request
import os
import json
from pathlib import Path
from datetime import datetime
import subprocess
import gzip

app = Flask(__name__)

BACKUP_DIR = Path('/app/backups')
LOG_FILE = Path('/app/backup_mysql.log')
STATUS_FILE = Path('/app/backup_status.json')

# Template HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estado de Backups MySQL</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card.success .value { color: #28a745; }
        .stat-card.error .value { color: #dc3545; }
        .stat-card.warning .value { color: #ffc107; }
        .backups-list {
            padding: 30px;
        }
        .backups-list h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        th, td {
            padding: 15px;
            text-align: left;
        }
        tbody tr:nth-child(even) {
            background: #f8f9fa;
        }
        tbody tr:hover {
            background: #e9ecef;
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        .btn-delete {
            background: none;
            border: none;
            color: #dc3545;
            cursor: pointer;
            font-size: 1.3em;
            padding: 5px 10px;
            transition: transform 0.2s, color 0.2s;
            border-radius: 5px;
        }
        .btn-delete:hover {
            transform: scale(1.2);
            color: #c82333;
            background: #f8d7da;
        }
        .btn-delete:active {
            transform: scale(0.95);
        }
        .btn-restore {
            background: none;
            border: none;
            color: #17a2b8;
            cursor: pointer;
            font-size: 1.3em;
            padding: 5px 10px;
            transition: transform 0.2s, color 0.2s;
            border-radius: 5px;
            margin-left: 5px;
        }
        .btn-restore:hover {
            transform: scale(1.2);
            color: #138496;
            background: #d1ecf1;
        }
        .btn-restore:active {
            transform: scale(0.95);
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }
        .modal.show {
            display: block;
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 0;
            border-radius: 15px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            animation: slideDown 0.3s;
        }
        .modal-header {
            background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
        }
        .modal-header h2 {
            margin: 0;
            font-size: 1.5em;
        }
        .modal-body {
            padding: 30px;
        }
        .modal-footer {
            padding: 20px;
            text-align: right;
            border-top: 1px solid #dee2e6;
        }
        .close {
            color: white;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            line-height: 20px;
        }
        .close:hover {
            opacity: 0.7;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        .form-group select,
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 8px;
            font-size: 1em;
            box-sizing: border-box;
        }
        .form-group select:focus,
        .form-group input:focus {
            outline: none;
            border-color: #17a2b8;
            box-shadow: 0 0 0 0.2rem rgba(23,162,184,0.25);
        }
        .btn-modal {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            margin-left: 10px;
        }
        .btn-modal-primary {
            background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
            color: white;
        }
        .btn-modal-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(23,162,184,0.4);
        }
        .btn-modal-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-modal-secondary:hover {
            background: #5a6268;
        }
        .target-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideDown {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .action-buttons {
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .bulk-actions {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .bulk-actions.show {
            display: block;
        }
        .btn-bulk-delete {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
            border: none;
            padding: 10px 25px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-bulk-delete:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(220,53,69,0.4);
        }
        .btn-bulk-delete:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .checkbox-cell {
            text-align: center;
            width: 50px;
        }
        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s, opacity 0.3s;
            min-width: 200px;
        }
        .btn:hover {
            transform: scale(1.05);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        .btn-warning {
            background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            display: none;
        }
        .notification.show {
            display: block;
        }
        .notification.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .notification.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .notification.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .last-update {
            text-align: center;
            padding: 20px;
            color: #666;
            font-style: italic;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }
    </style>
    <script>
        function refreshPage() {
            location.reload();
        }
        
        function showNotification(message, type) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = 'notification ' + type + ' show';
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 5000);
        }
        
        function runBackupNow() {
            const btn = document.getElementById('backupBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Ejecutando...';
            
            showNotification('Iniciando backup manual...', 'info');
            
            fetch('/api/run-backup', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification('✅ Backup completado exitosamente', 'success');
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        showNotification('❌ Error: ' + data.message, 'error');
                        btn.disabled = false;
                        btn.textContent = '🔄 Ejecutar Backup';
                    }
                })
                .catch(error => {
                    showNotification('❌ Error de conexión: ' + error, 'error');
                    btn.disabled = false;
                    btn.textContent = '🔄 Ejecutar Backup';
                });
        }
        
        function deleteBackup(filename) {
            if (!confirm('¿Está seguro de eliminar el backup:\\n\\n' + filename + '\\n\\nEsta acción no se puede deshacer.')) {
                return;
            }
            
            showNotification('Eliminando backup...', 'info');
            
            fetch('/api/delete-backup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename: filename })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification('✅ Backup eliminado correctamente', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification('❌ Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('❌ Error de conexión: ' + error, 'error');
            });
        }
        
        let currentBackupFile = '';
        let currentDatabase = '';
        let restoreTargets = [];
        
        function openRestoreModal(filename, database) {
            currentBackupFile = filename;
            currentDatabase = database;
            
            document.getElementById('backupFilename').textContent = filename;
            document.getElementById('originalDatabase').textContent = database;
            
            // Cargar destinos de restauración
            fetch('/api/restore-targets')
                .then(response => response.json())
                .then(data => {
                    restoreTargets = data.targets;
                    const select = document.getElementById('targetServer');
                    select.innerHTML = '<option value="">Seleccione un servidor...</option>';
                    
                    data.targets.forEach((target, index) => {
                        const option = document.createElement('option');
                        option.value = index;
                        option.textContent = target.name + ' - ' + target.host;
                        select.appendChild(option);
                    });
                    
                    document.getElementById('restoreModal').classList.add('show');
                })
                .catch(error => {
                    showNotification('❌ Error al cargar destinos: ' + error, 'error');
                });
        }
        
        function closeRestoreModal() {
            document.getElementById('restoreModal').classList.remove('show');
        }
        
        function updateTargetInfo() {
            const select = document.getElementById('targetServer');
            const targetIndex = select.value;
            const targetInfo = document.getElementById('targetInfo');
            
            if (targetIndex !== '') {
                const target = restoreTargets[targetIndex];
                targetInfo.innerHTML = `
                    <strong>📍 Destino seleccionado:</strong><br>
                    <strong>Host:</strong> ${target.host}:${target.port}<br>
                    <strong>Usuario:</strong> ${target.user}<br>
                    <strong>Descripción:</strong> ${target.description}
                `;
                targetInfo.style.display = 'block';
            } else {
                targetInfo.style.display = 'none';
            }
        }
        
        function executeRestore() {
            const targetSelect = document.getElementById('targetServer');
            const targetIndex = targetSelect.value;
            const dbName = document.getElementById('targetDatabase').value.trim();
            
            if (targetIndex === '') {
                showNotification('⚠️ Debe seleccionar un servidor destino', 'error');
                return;
            }
            
            if (!dbName) {
                showNotification('⚠️ Debe ingresar el nombre de la base de datos', 'error');
                return;
            }
            
            const target = restoreTargets[targetIndex];
            
            if (!confirm(`¿Está seguro de restaurar el backup en:\\n\\nServidor: ${target.name}\\nBase de datos: ${dbName}\\n\\nEsta acción sobrescribirá los datos existentes.`)) {
                return;
            }
            
            closeRestoreModal();
            showNotification('🔄 Iniciando restauración...', 'info');
            
            fetch('/api/restore-backup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: currentBackupFile,
                    target_index: parseInt(targetIndex),
                    database_name: dbName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification('✅ Restauración completada exitosamente', 'success');
                } else {
                    showNotification('❌ Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('❌ Error de conexión: ' + error, 'error');
            });
        }
        
        // Cerrar modal al hacer clic fuera
        window.onclick = function(event) {
            const modal = document.getElementById('restoreModal');
            if (event.target == modal) {
                closeRestoreModal();
            }
        }
        
        // Funciones para selección múltiple
        function toggleSelectAll() {
            const selectAll = document.getElementById('selectAll');
            const checkboxes = document.querySelectorAll('.backup-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
            
            updateBulkActions();
        }
        
        function updateBulkActions() {
            const checkboxes = document.querySelectorAll('.backup-checkbox:checked');
            const bulkActions = document.getElementById('bulkActions');
            const selectedCount = document.getElementById('selectedCount');
            
            if (checkboxes.length > 0) {
                bulkActions.classList.add('show');
                selectedCount.textContent = checkboxes.length;
            } else {
                bulkActions.classList.remove('show');
                document.getElementById('selectAll').checked = false;
            }
        }
        
        function deleteSelectedBackups() {
            const checkboxes = document.querySelectorAll('.backup-checkbox:checked');
            const filenames = Array.from(checkboxes).map(cb => cb.value);
            
            if (filenames.length === 0) {
                showNotification('⚠️ No hay backups seleccionados', 'error');
                return;
            }
            
            if (!confirm(`¿Está seguro de eliminar ${filenames.length} backup(s) seleccionado(s)?\n\nEsta acción no se puede deshacer.`)) {
                return;
            }
            
            showNotification(`Eliminando ${filenames.length} backup(s)...`, 'info');
            
            fetch('/api/delete-multiple-backups', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filenames: filenames })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification(`✅ ${data.deleted} backup(s) eliminado(s) correctamente`, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification('❌ Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('❌ Error de conexión: ' + error, 'error');
            });
        }
        
        // Auto refresh cada 60 segundos
        setTimeout(function() {
            location.reload();
        }, 60000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Monitor de Backups MySQL</h1>
            <p>Estado en tiempo real de los respaldos de bases de datos</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total de Backups</h3>
                <div class="value">{{ stats.total }}</div>
            </div>
            <div class="stat-card success">
                <h3>Último Backup</h3>
                <div class="value" style="font-size: 1.2em;">{{ stats.last_backup }}</div>
            </div>
            <div class="stat-card warning">
                <h3>Espacio Usado</h3>
                <div class="value">{{ stats.total_size }}</div>
            </div>
            <div class="stat-card {{ 'success' if stats.last_status == 'success' else 'error' }}">
                <h3>Estado Último</h3>
                <div class="value" style="font-size: 1.5em;">{{ '✓' if stats.last_status == 'success' else '✗' }}</div>
            </div>
        </div>
        
        <div class="backups-list">
            <h2>📁 Archivos de Backup Recientes</h2>
            
            <div id="bulkActions" class="bulk-actions">
                <span><strong><span id="selectedCount">0</span> backup(s) seleccionado(s)</strong></span>
                <button class="btn-bulk-delete" onclick="deleteSelectedBackups()">
                    🗑️ Eliminar seleccionados
                </button>
            </div>
            
            {% if backups %}
            <table>
                <thead>
                    <tr>
                        <th class="checkbox-cell">
                            <input type="checkbox" id="selectAll" onchange="toggleSelectAll()" title="Seleccionar todos">
                        </th>
                        <th style="text-align: center;">#</th>
                        <th>Fecha/Hora</th>
                        <th>Base de Datos</th>
                        <th>Tamaño</th>
                        <th>Estado</th>
                        <th style="text-align: center;">Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for backup in backups %}
                    <tr>
                        <td class="checkbox-cell">
                            <input type="checkbox" class="backup-checkbox" value="{{ backup.filename }}" onchange="updateBulkActions()">
                        </td>
                        <td style="text-align: center;"><strong>{{ loop.index }}</strong></td>
                        <td>{{ backup.datetime }}</td>
                        <td><strong>{{ backup.database }}</strong></td>
                        <td>{{ backup.size }}</td>
                        <td><span class="status-badge status-success">Completo</span></td>
                        <td style="text-align: center;">
                            <button class="btn-restore" onclick="openRestoreModal('{{ backup.filename }}', '{{ backup.database }}')" title="Restaurar backup">
                                ♻️
                            </button>
                            <button class="btn-delete" onclick="deleteBackup('{{ backup.filename }}')" title="Eliminar backup">
                                🗑️
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="no-data">
                <p>No hay backups disponibles</p>
            </div>
            {% endif %}
        </div>
        
        <div class="last-update">
            Última actualización: {{ current_time }}
        </div>
    </div>
    
    <div id="notification" class="notification"></div>
    
    <!-- Modal de Restauración -->
    <div id="restoreModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="close" onclick="closeRestoreModal()">&times;</span>
                <h2>♻️ Restaurar Backup</h2>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>📁 Archivo de backup:</label>
                    <div style="padding: 10px; background: #f8f9fa; border-radius: 5px; font-family: monospace;">
                        <span id="backupFilename"></span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>💾 Base de datos original:</label>
                    <div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <span id="originalDatabase"></span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>🖥️ Servidor destino:</label>
                    <select id="targetServer" onchange="updateTargetInfo()">
                        <option value="">Cargando...</option>
                    </select>
                </div>
                
                <div id="targetInfo" class="target-info" style="display: none;"></div>
                
                <div class="form-group">
                    <label>🗄️ Nombre de la base de datos destino:</label>
                    <input type="text" id="targetDatabase" placeholder="Nombre de la base de datos" />
                    <small style="color: #666; display: block; margin-top: 5px;">
                        ⚠️ Si la base de datos existe, será eliminada y recreada
                    </small>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-modal btn-modal-secondary" onclick="closeRestoreModal()">Cancelar</button>
                <button class="btn-modal btn-modal-primary" onclick="executeRestore()">Restaurar</button>
            </div>
        </div>
    </div>
    
    <div class="action-buttons">
        <button id="backupBtn" class="btn btn-success" onclick="runBackupNow()">🔄 Ejecutar Backup</button>
        <button class="btn" onclick="refreshPage()">♻️ Actualizar</button>
    </div>
</body>
</html>
"""

def get_backup_stats():
    """Obtener estadísticas de los backups"""
    stats = {
        'total': 0,
        'last_backup': 'N/A',
        'total_size': '0 MB',
        'last_status': 'unknown'
    }
    
    if BACKUP_DIR.exists():
        backup_files = sorted(BACKUP_DIR.glob('*.sql.gz'), key=os.path.getmtime, reverse=True)
        stats['total'] = len(backup_files)
        
        if backup_files:
            last_file = backup_files[0]
            last_time = datetime.fromtimestamp(last_file.stat().st_mtime)
            stats['last_backup'] = last_time.strftime('%d/%m/%Y %H:%M')
            
            # Calcular tamaño total
            total_bytes = sum(f.stat().st_size for f in backup_files)
            total_mb = total_bytes / (1024 * 1024)
            if total_mb > 1024:
                stats['total_size'] = f"{total_mb/1024:.1f} GB"
            else:
                stats['total_size'] = f"{total_mb:.1f} MB"
    
    # Leer último estado del archivo de estado
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, 'r') as f:
                status_data = json.load(f)
                stats['last_status'] = status_data.get('status', 'unknown')
        except:
            pass
    
    return stats

def get_recent_backups(limit=20):
    """Obtener lista de backups recientes"""
    backups = []
    
    if BACKUP_DIR.exists():
        backup_files = sorted(BACKUP_DIR.glob('*.sql.gz'), key=os.path.getmtime, reverse=True)[:limit]
        
        for backup_file in backup_files:
            # Parsear nombre del archivo
            filename = backup_file.stem.replace('.sql', '')
            parts = filename.rsplit('_', 2)
            
            if len(parts) >= 3:
                db_name = '_'.join(parts[:-2])
                date_str = parts[-2]
                time_str = parts[-1]
                
                # Formatear fecha y hora
                try:
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    formatted_datetime = dt.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    formatted_datetime = f"{date_str} {time_str}"
                
                # Calcular tamaño
                size_bytes = backup_file.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                formatted_size = f"{size_mb:.2f} MB"
                
                backups.append({
                    'database': db_name,
                    'datetime': formatted_datetime,
                    'size': formatted_size,
                    'path': str(backup_file),
                    'filename': backup_file.name
                })
    
    return backups

@app.route('/')
def index():
    """Página principal"""
    stats = get_backup_stats()
    backups = get_recent_backups()
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        backups=backups,
        current_time=current_time
    )

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas"""
    return jsonify(get_backup_stats())

@app.route('/api/backups')
def api_backups():
    """API para obtener lista de backups"""
    return jsonify(get_recent_backups())

@app.route('/api/logs')
def api_logs():
    """API para obtener últimas líneas del log"""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            return jsonify({'logs': lines[-50:]})  # Últimas 50 líneas
    return jsonify({'logs': []})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/run-backup', methods=['POST'])
def run_backup():
    """Ejecuta un backup manual"""
    import logging
    
    try:
        logging.info("Ejecutando backup manual desde interfaz web...")
        
        # Ejecutar el script de backup
        result = subprocess.run(
            ['python', '/app/backup_mysql.py'],
            capture_output=True,
            text=True,
            timeout=300  # Timeout de 5 minutos
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Backup completado exitosamente',
                'output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Error al ejecutar backup',
                'error': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Timeout: El backup tardó más de 5 minutos'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/delete-backup', methods=['POST'])
def delete_backup():
    """Elimina un archivo de backup"""
    import logging
    
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({
                'status': 'error',
                'message': 'Nombre de archivo no proporcionado'
            }), 400
        
        # Validar que el archivo existe y está en el directorio de backups
        backup_path = BACKUP_DIR / filename
        
        if not backup_path.exists():
            return jsonify({
                'status': 'error',
                'message': 'Archivo no encontrado'
            }), 404
        
        # Validar que es un archivo de backup válido (seguridad)
        if not backup_path.suffix == '.gz' or not backup_path.parent == BACKUP_DIR:
            return jsonify({
                'status': 'error',
                'message': 'Archivo inválido'
            }), 400
        
        # Eliminar el archivo
        backup_path.unlink()
        
        logging.info(f"Backup eliminado: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': f'Backup {filename} eliminado correctamente'
        })
        
    except Exception as e:
        logging.error(f"Error al eliminar backup: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/delete-multiple-backups', methods=['POST'])
def delete_multiple_backups():
    """Elimina múltiples archivos de backup"""
    import logging
    
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        
        if not filenames or not isinstance(filenames, list):
            return jsonify({
                'status': 'error',
                'message': 'Lista de archivos no proporcionada'
            }), 400
        
        deleted_count = 0
        errors = []
        
        for filename in filenames:
            try:
                backup_path = BACKUP_DIR / filename
                
                # Validar que el archivo existe
                if not backup_path.exists():
                    errors.append(f'{filename}: No encontrado')
                    continue
                
                # Validar que es un archivo de backup válido (seguridad)
                if not backup_path.suffix == '.gz' or not backup_path.parent == BACKUP_DIR:
                    errors.append(f'{filename}: Archivo inválido')
                    continue
                
                # Eliminar el archivo
                backup_path.unlink()
                deleted_count += 1
                logging.info(f"Backup eliminado: {filename}")
                
            except Exception as e:
                errors.append(f'{filename}: {str(e)}')
                logging.error(f"Error al eliminar {filename}: {str(e)}")
        
        if deleted_count > 0:
            message = f'{deleted_count} backup(s) eliminado(s)'
            if errors:
                message += f'. Errores: {len(errors)}'
            
            return jsonify({
                'status': 'success',
                'message': message,
                'deleted': deleted_count,
                'errors': errors
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No se pudo eliminar ningún backup',
                'errors': errors
            }), 500
        
    except Exception as e:
        logging.error(f"Error al eliminar backups múltiples: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/restore-targets', methods=['GET'])
def get_restore_targets():
    """Obtiene la lista de servidores destino para restauración"""
    try:
        targets_file = Path('/app/restore_targets.json')
        
        if not targets_file.exists():
            return jsonify({
                'status': 'error',
                'message': 'Archivo de configuración de destinos no encontrado'
            }), 404
        
        with open(targets_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return jsonify({
            'status': 'success',
            'targets': config.get('databases', [])
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/restore-backup', methods=['POST'])
def restore_backup():
    """Restaura un backup en un servidor destino"""
    import logging
    import traceback
    
    # Configurar logging detallado
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logging.info("=== INICIO DE PROCESO DE RESTAURACIÓN ===")
        
        data = request.get_json()
        logging.debug(f"Datos recibidos: {data}")
        
        filename = data.get('filename')
        target_index = data.get('target_index')
        database_name = data.get('database_name')
        
        logging.info(f"Parámetros - Archivo: {filename}, Target Index: {target_index}, DB: {database_name}")
        
        if not filename or target_index is None or not database_name:
            logging.error(f"Parámetros incompletos - filename: {filename}, target_index: {target_index}, database_name: {database_name}")
            return jsonify({
                'status': 'error',
                'message': 'Parámetros incompletos'
            }), 400
        
        # Validar que el archivo de backup existe
        backup_path = BACKUP_DIR / filename
        logging.info(f"Verificando existencia del archivo: {backup_path}")
        
        if not backup_path.exists():
            logging.error(f"Archivo no encontrado: {backup_path}")
            return jsonify({
                'status': 'error',
                'message': f'Archivo de backup no encontrado: {backup_path}'
            }), 404
        
        logging.info(f"Archivo encontrado. Tamaño: {backup_path.stat().st_size} bytes")
        
        # Cargar configuración de destinos
        targets_file = Path('/app/restore_targets.json')
        logging.info(f"Cargando configuración de destinos desde: {targets_file}")
        
        if not targets_file.exists():
            logging.error(f"Archivo de configuración no encontrado: {targets_file}")
            return jsonify({
                'status': 'error',
                'message': 'Archivo de configuración de destinos no encontrado'
            }), 404
        
        with open(targets_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logging.debug(f"Configuración cargada: {config}")
        
        targets = config.get('databases', [])
        logging.info(f"Total de targets disponibles: {len(targets)}")
        
        if target_index < 0 or target_index >= len(targets):
            logging.error(f"Índice de destino inválido: {target_index} (debe estar entre 0 y {len(targets)-1})")
            return jsonify({
                'status': 'error',
                'message': f'Índice de destino inválido: {target_index}'
            }), 400
        
        target = targets[target_index]
        logging.info(f"Target seleccionado: {target['name']} - {target['host']}:{target['port']}")
        
        # Limpiar (eliminar y recrear) la base de datos destino
        drop_cmd = [
            'mysql',
            f'--host={target["host"]}',
            f'--port={target["port"]}',
            f'--user={target["user"]}',
            f'--password={target["password"]}',
            '--skip-ssl',
            '-e',
            f'DROP DATABASE IF EXISTS `{database_name}`; CREATE DATABASE `{database_name}`;'
        ]
        
        logging.info(f"Ejecutando comando DROP/CREATE DATABASE...")
        logging.debug(f"Comando (sin password): mysql --host={target['host']} --port={target['port']} --user={target['user']} --skip-ssl -e 'DROP DATABASE IF EXISTS `{database_name}`; CREATE DATABASE `{database_name}`;'")
        
        result = subprocess.run(drop_cmd, capture_output=True, text=True, timeout=30)
        
        logging.debug(f"Return code DROP/CREATE: {result.returncode}")
        logging.debug(f"STDOUT: {result.stdout}")
        logging.debug(f"STDERR: {result.stderr}")
        
        if result.returncode != 0:
            logging.error(f"Error al preparar base de datos: {result.stderr}")
            return jsonify({
                'status': 'error',
                'message': f'Error al preparar base de datos: {result.stderr}'
            }), 500
        
        logging.info(f"Base de datos {database_name} preparada correctamente")
        
        # Restaurar el backup usando gunzip y pipe a mysql
        gunzip_cmd = ['gunzip', '-c', str(backup_path)]
        
        restore_cmd = [
            'mysql',
            f'--host={target["host"]}',
            f'--port={target["port"]}',
            f'--user={target["user"]}',
            f'--password={target["password"]}',
            '--skip-ssl',
            '--force',              # Continuar si hay errores no críticos
            '--comments',           # Preservar comentarios SQL
            '--binary-mode=0'       # Modo texto para manejar procedimientos
        ]
        
        logging.info("Iniciando proceso de restauración...")
        logging.debug(f"Comando gunzip: {' '.join(gunzip_cmd)}")
        logging.debug(f"Comando mysql (sin password): mysql --host={target['host']} --port={target['port']} --user={target['user']} --skip-ssl --force --comments --binary-mode=0")
        
        # Ejecutar gunzip
        logging.info("Ejecutando gunzip...")
        gunzip_process = subprocess.Popen(
            gunzip_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logging.info("Ejecutando mysql restore...")
        result = subprocess.run(
            restore_cmd,
            stdin=gunzip_process.stdout,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos timeout
        )
        
        gunzip_process.stdout.close()
        gunzip_stderr = gunzip_process.communicate()[1]
        gunzip_returncode = gunzip_process.wait()
        
        logging.debug(f"Gunzip return code: {gunzip_returncode}")
        if gunzip_stderr:
            logging.debug(f"Gunzip STDERR: {gunzip_stderr.decode('utf-8', errors='replace')}")
        
        logging.debug(f"MySQL return code: {result.returncode}")
        logging.debug(f"MySQL STDOUT: {result.stdout}")
        logging.debug(f"MySQL STDERR: {result.stderr}")
        
        if result.returncode != 0:
            error_msg = f"Error al restaurar backup. Return code: {result.returncode}, STDERR: {result.stderr}"
            logging.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500
        
        logging.info(f"✅ Backup {filename} restaurado exitosamente en {target['name']} como {database_name}")
        logging.info("=== FIN DE PROCESO DE RESTAURACIÓN ===")
        
        return jsonify({
            'status': 'success',
            'message': f'Backup restaurado correctamente en {target["name"]}'
        })
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Timeout durante la restauración: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500
    except Exception as e:
        error_msg = f"Excepción durante restauración: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
