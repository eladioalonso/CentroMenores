"""Interfaz de copias de seguridad para administración."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox,
    QFileDialog, QHBoxLayout,
)
from gestion_centro.persistence.backups import create_backup, verify_backup, sync_pending_backups, restore_backup
from gestion_centro.persistence.database import session_scope
from gestion_centro.auth.models import AccessAudit, UserAccount


class BackupDialog(QDialog):
    def __init__(self, paths, factory, actor_id):
        super().__init__()
        self.paths, self.factory, self.actor_id = paths, factory, actor_id
        self.setWindowTitle("Copias de seguridad")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Las copias incluyen la base de datos, documentos e imágenes."))
        actions = QHBoxLayout()
        create = QPushButton("Crear copia manual")
        create.clicked.connect(self.create_manual)
        verify = QPushButton("Verificar seleccionada")
        verify.clicked.connect(self.verify_selected)
        sync = QPushButton("Sincronizar pendientes con USB…")
        sync.clicked.connect(self.sync_usb)
        restore = QPushButton("Restaurar copia completa…")
        restore.clicked.connect(self.restore_selected)
        actions.addWidget(create)
        actions.addWidget(verify)
        actions.addWidget(sync)
        actions.addWidget(restore)
        layout.addLayout(actions)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.refresh()

    def refresh(self):
        self.list.clear()
        archives = sorted(self.paths.backups.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        for archive in archives:
            self.list.addItem(str(archive))

    @staticmethod
    def require_admin(session, actor_id):
        account = session.get(UserAccount, actor_id)
        if (account is None or not account.active or not account.professional.active
                or account.role != "admin"):
            raise PermissionError("Se requiere una cuenta administradora activa")
        return account

    def audit(self, event, details):
        with session_scope(self.factory) as session:
            account = self.require_admin(session, self.actor_id)
            session.add(AccessAudit(
                account_id=account.id, username_snapshot=account.username,
                event=event, details=details,
            ))

    def create_manual(self):
        try:
            with session_scope(self.factory) as session:
                self.require_admin(session, self.actor_id)
            archive = create_backup(self.paths, kind="manual")
            self.audit("backup_created", archive.name)
            QMessageBox.information(self, "Copia creada", "Copia verificada: " + archive.name)
            self.refresh()
        except (OSError, ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Error de copia", str(exc))

    def verify_selected(self):
        item = self.list.currentItem()
        if item is None:
            QMessageBox.information(self, "Selecciona", "Selecciona una copia.")
            return
        try:
            with session_scope(self.factory) as session:
                self.require_admin(session, self.actor_id)
            manifest = verify_backup(Path(item.text()))
            self.audit("backup_verified", Path(item.text()).name)
            QMessageBox.information(self, "Verificación correcta",
                "Integridad correcta. Archivos incluidos: " + str(len(manifest["files"])))
        except (OSError, ValueError, KeyError, PermissionError) as exc:
            QMessageBox.critical(self, "Copia no válida", str(exc))

    def restore_selected(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar copia completa", str(self.paths.backups), "Copias ZIP (*.zip)")
        if not filename:
            return
        answer = QMessageBox.warning(
            self, "Restauración integral",
            "Se sustituirán la base de datos, documentos e imágenes por el contenido de la copia. "
            "Antes se creará una copia previa automática. La auditoría actual se conservará. "
            "La versión del esquema debe coincidir. Cierra cualquier otra instancia. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            with session_scope(self.factory) as session:
                actor = session.get(UserAccount, self.actor_id)
                if actor is None or not actor.active or not actor.professional.active or actor.role != "admin":
                    raise PermissionError("Se requiere una cuenta administradora activa")
                actor_name = actor.username
            # Cierra conexiones en pool antes de sustituir el fichero SQLite en Windows.
            bind = getattr(self.factory, "kw", {}).get("bind")
            if bind is not None:
                bind.dispose()
            pre_restore = restore_backup(self.paths, Path(filename))
            with session_scope(self.factory) as session:
                actor = session.get(UserAccount, self.actor_id)
                session.add(AccessAudit(
                    account_id=actor.id if actor else None,
                    username_snapshot=actor.username if actor else actor_name,
                    event="backup_restored",
                    details=f"Archivo: {Path(filename).name}; copia previa: {pre_restore.name}",
                ))
            QMessageBox.information(self, "Restauración completada",
                "La restauración ha finalizado. La copia previa se conserva en la carpeta de backups. "
                "Reinicia la aplicación y comprueba los expedientes y documentos.")
            self.refresh()
        except (OSError, ValueError, PermissionError, KeyError) as exc:
            QMessageBox.critical(self, "Restauración cancelada", str(exc))

    def sync_usb(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta del USB")
        if not directory:
            return
        try:
            with session_scope(self.factory) as session:
                self.require_admin(session, self.actor_id)
            completed = sync_pending_backups(self.paths, Path(directory))
            self.audit("backup_external_sync", str(len(completed)))
            QMessageBox.information(self, "Sincronización",
                "Copias verificadas en el USB: " + str(len(completed)))
            self.refresh()
        except (OSError, ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Error de sincronización", str(exc))
