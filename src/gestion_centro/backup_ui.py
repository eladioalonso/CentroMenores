"""Interfaz de copias de seguridad."""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel,
)
from gestion_centro.persistence.backups import create_backup, verify_backup, sync_pending_backups


class BackupDialog(QDialog):
    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.setWindowTitle("Copias de seguridad")
        self.resize(520, 240)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Las copias incluyen la base de datos, documentos e imágenes. "
            "Comprueba y custodia la unidad externa por separado."
        ))
        create = QPushButton("Crear copia manual")
        create.clicked.connect(self.create)
        layout.addWidget(create)
        verify = QPushButton("Verificar una copia")
        verify.clicked.connect(self.verify)
        layout.addWidget(verify)
        sync = QPushButton("Sincronizar copias pendientes con USB")
        sync.clicked.connect(self.sync)
        layout.addWidget(sync)

    def create(self):
        try:
            archive = create_backup(self.paths, kind="manual")
            QMessageBox.information(self, "Copia creada", f"Copia local creada y verificada:\n{archive.name}\n\nQueda pendiente su copia en la unidad externa.")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error al crear la copia", str(exc))

    def verify(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar copia", str(self.paths.backups), "Copias ZIP (*.zip)")
        if not filename:
            return
        try:
            manifest = verify_backup(Path(filename))
            QMessageBox.information(self, "Copia válida",
                f"Integridad comprobada. Tipo: {manifest.get('kind')}\nFecha: {manifest.get('created_at')}\nArchivos: {len(manifest.get('files', {}))}")
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(self, "Copia no válida", str(exc))

    def sync(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de la unidad externa")
        if not folder:
            return
        try:
            completed = sync_pending_backups(self.paths, Path(folder))
            QMessageBox.information(self, "Sincronización",
                f"Copias externas verificadas: {len(completed)}")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Error de sincronización", str(exc))
