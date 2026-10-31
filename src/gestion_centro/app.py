"""Punto de entrada de la interfaz de escritorio."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gestión del Centro")
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)
        label = QLabel(
            "Base técnica inicial\n\n"
            "La aplicación todavía no está preparada para gestionar datos reales."
        )
        label.setStyleSheet("font-size: 16px; padding: 32px;")
        self.setCentralWidget(label)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gestión del Centro")
    window = MainWindow()
    window.show()
    return app.exec()
