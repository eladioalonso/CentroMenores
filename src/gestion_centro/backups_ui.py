"""Interfaz de copias de seguridad para administración."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox,
    QFileDialog, QHBoxLayout,
)
from gestion_centro.persistence.backups import create_backup, verify_backup, sync_pending_backups


class BackupDialog(QDialog):
    def __init__(self, paths):
        super().__init__()
        self.paths = paths
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
        actions.addWidget(create)
        actions.addWidget(verify)
        actions.addWidget(sync)
        layout.addLayout(actions)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.refresh()

    def refresh(self):
        self.list.clear()
        archives = sorted(self.paths.backups.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        for archive in archives:
            self.list.addItem(str(archive))

    def create_manual(self):
        try:
            archive = create_backup(self.paths, kind="manual")
            QMessageBox.information(self, "Copia creada", "Copia verificada: " + archive.name)
            self.refresh()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error de copia", str(exc))

    def verify_selected(self):
        item = self.list.currentItem()
        if item is None:
            QMessageBox.information(self, "Selecciona", "Selecciona una copia.")
            return
        try:
            manifest = verify_backup(Path(item.text()))
            QMessageBox.information(self, "Verificación correcta",
                "Integridad correcta. Archivos incluidos: " + str(len(manifest["files"])))
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(self, "Copia no válida", str(exc))

    def sync_usb(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta del USB")
        if not directory:
            return
        try:
            completed = sync_pending_backups(self.paths, Path(directory))
            QMessageBox.information(self, "Sincronización",
                "Copias verificadas en el USB: " + str(len(completed)))
            self.refresh()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error de sincronización", str(exc))
