"""Generación de informes de incidencias a partir del parte diario."""
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QVBoxLayout,
)
from sqlalchemy import select

from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import (
    DiaryDay, DiaryEntry, DiaryEntryStayLink, Minor, Stay,
)
from gestion_centro.persistence.database import session_scope


CATEGORY_LABELS = {
    "activity": "Actividad",
    "positive": "Conducta positiva",
    "negative": "Conducta negativa",
    "observation": "Observación",
    "general": "General",
    "health": "Salud",
    "maintenance": "Mantenimiento",
    "other": "Otros",
}


def _local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.astimezone()
    return value.astimezone()


class IncidentReportsDialog(QDialog):
    """Permite seleccionar hechos del diario, revisar el texto y exportar a Word."""

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.entries_by_id = {}
        self.setWindowTitle("Informes de incidencias")
        self.resize(1120, 760)
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Selecciona las anotaciones del parte diario que deben formar parte del informe. "
            "El texto generado se puede revisar y editar antes de exportarlo. "
            "Los registros originales no se modifican."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        filters = QFormLayout()
        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate().addMonths(-1))
        self.end = QDateEdit()
        self.end.setCalendarPopup(True)
        self.end.setDate(QDate.currentDate())
        self.minor = QComboBox()
        self.minor.addItem("Todos los menores", None)
        with session_scope(factory) as session:
            minors = session.scalars(
                select(Minor).join(Stay, Stay.minor_id == Minor.id)
                .where(Stay.status == "active")
                .distinct().order_by(Minor.family_names, Minor.given_names)
            ).all()
            for minor in minors:
                self.minor.addItem(
                    f"{minor.family_names}, {minor.given_names}", minor.id
                )
        filters.addRow("Desde", self.start)
        filters.addRow("Hasta", self.end)
        filters.addRow("Menor", self.minor)
        layout.addLayout(filters)

        refresh = QPushButton("Buscar anotaciones")
        refresh.clicked.connect(self.load_entries)
        layout.addWidget(refresh)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Incluir", "Fecha y hora", "Menor(es)", "Apartado", "Anotación del parte", "Educador"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.table, 2)

        details = QFormLayout()
        self.title = QLineEdit("Informe de incidencias")
        self.recipient = QLineEdit()
        self.recipient.setPlaceholderText("Dirección, Consejería de Bienestar Social…")
        details.addRow("Título", self.title)
        details.addRow("Destinatario", self.recipient)
        layout.addLayout(details)

        layout.addWidget(QLabel("Borrador del informe · puedes revisar y modificar el texto"))
        self.preview = QTextEdit()
        self.preview.setPlaceholderText(
            "Marca las anotaciones que quieras incluir y pulsa «Preparar borrador»."
        )
        layout.addWidget(self.preview, 2)

        actions = QHBoxLayout()
        prepare = QPushButton("Preparar borrador")
        prepare.clicked.connect(self.prepare_draft)
        export = QPushButton("Exportar informe Word…")
        export.clicked.connect(self.export_docx)
        actions.addWidget(prepare)
        actions.addStretch(1)
        actions.addWidget(export)
        layout.addLayout(actions)
        self.load_entries()

    def load_entries(self):
        start = self.start.date().toPython()
        end = self.end.date().toPython()
        if end < start:
            QMessageBox.warning(self, "Periodo no válido", "La fecha final no puede ser anterior a la inicial.")
            return
        self.entries_by_id = {}
        with session_scope(self.factory) as session:
            query = select(DiaryEntry).join(
                DiaryDay, DiaryDay.id == DiaryEntry.diary_day_id
            ).where(DiaryDay.diary_date >= start, DiaryDay.diary_date <= end)
            minor_id = self.minor.currentData()
            if minor_id:
                stay_ids = select(Stay.id).where(Stay.minor_id == minor_id)
                entry_ids = select(DiaryEntryStayLink.entry_id).where(
                    DiaryEntryStayLink.stay_id.in_(stay_ids)
                )
                query = query.where(DiaryEntry.id.in_(entry_ids))
            entries = session.scalars(
                query.order_by(DiaryEntry.happened_at, DiaryEntry.recorded_at)
            ).all()
            rows = []
            for entry in entries:
                links = session.scalars(select(DiaryEntryStayLink).where(
                    DiaryEntryStayLink.entry_id == entry.id
                )).all()
                names = []
                for link in links:
                    stay = session.get(Stay, link.stay_id)
                    if stay is not None:
                        names.append(f"{stay.minor.given_names} {stay.minor.family_names}")
                self.entries_by_id[entry.id] = {
                    "id": entry.id,
                    "happened_at": entry.happened_at,
                    "category": entry.category,
                    "content": entry.content,
                    "author": entry.author_name_snapshot,
                    "minors": ", ".join(dict.fromkeys(names)) or "Sin menor vinculado",
                }
                rows.append(self.entries_by_id[entry.id])

        self.table.setRowCount(len(rows))
        for index, entry in enumerate(rows):
            include = QTableWidgetItem()
            include.setFlags(
                include.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            include.setCheckState(Qt.CheckState.Checked)
            include.setData(Qt.ItemDataRole.UserRole, entry["id"])
            happened = _local_datetime(entry["happened_at"])
            values = [
                include,
                QTableWidgetItem(happened.strftime("%d/%m/%Y %H:%M")),
                QTableWidgetItem(entry["minors"]),
                QTableWidgetItem(CATEGORY_LABELS.get(entry["category"], entry["category"])),
                QTableWidgetItem(entry["content"]),
                QTableWidgetItem(entry["author"]),
            ]
            for column, item in enumerate(values):
                self.table.setItem(index, column, item)
        self.preview.clear()

    def prepare_draft(self):
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                entry_id = item.data(Qt.ItemDataRole.UserRole)
                if entry_id in self.entries_by_id:
                    selected.append(self.entries_by_id[entry_id])
        selected.sort(key=lambda item: item["happened_at"])
        if not selected:
            QMessageBox.information(self, "Sin anotaciones", "Selecciona al menos una anotación del parte diario.")
            return
        start = self.start.date().toPython().strftime("%d/%m/%Y")
        end = self.end.date().toPython().strftime("%d/%m/%Y")
        minors = list(dict.fromkeys(
            name for entry in selected for name in entry["minors"].split(", ")
            if name != "Sin menor vinculado"
        ))
        lines = [
            self.title.text().strip() or "Informe de incidencias",
            f"Destinatario: {self.recipient.text().strip() or 'No especificado'}",
            f"Periodo consultado: {start} - {end}",
            f"Menor(es): {', '.join(minors) if minors else 'No especificado'}",
            "",
            "RELACIÓN CRONOLÓGICA DE LOS HECHOS",
            "",
        ]
        for entry in selected:
            happened = _local_datetime(entry["happened_at"])
            lines.extend([
                f"{happened.strftime('%d/%m/%Y %H:%M')} · {CATEGORY_LABELS.get(entry['category'], entry['category'])}",
                f"Menor(es): {entry['minors']}",
                entry["content"],
                f"Anotado por: {entry['author']}",
                "",
            ])
        self.preview.setPlainText("\n".join(lines))

    def export_docx(self):
        content = self.preview.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Informe vacío", "Prepara y revisa el borrador antes de exportarlo.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe de incidencias",
            "informe_incidencias.docx", "Documento Word (*.docx)"
        )
        if not filename:
            return
        if not filename.lower().endswith(".docx"):
            filename += ".docx"
        try:
            document = Document()
            paragraphs = content.splitlines()
            if paragraphs:
                document.add_heading(paragraphs[0], 0)
                for line in paragraphs[1:]:
                    document.add_paragraph(line)
            document.save(Path(filename))
            with session_scope(self.factory) as session:
                actor = session.get(UserAccount, self.actor_id)
                if actor is None or not actor.active or not actor.professional.active:
                    raise PermissionError("La cuenta no está activa.")
                selected_ids = []
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, 0)
                    if item and item.checkState() == Qt.CheckState.Checked:
                        selected_ids.append(item.data(Qt.ItemDataRole.UserRole))
                session.add(AccessAudit(
                    account_id=actor.id, username_snapshot=actor.username,
                    event="incident_report_exported",
                    details=f"Archivo Word; anotaciones:{len(selected_ids)}; "
                    f"periodo:{self.start.date().toString('yyyy-MM-dd')}:{self.end.date().toString('yyyy-MM-dd')}",
                ))
            QMessageBox.information(self, "Informe generado", "El documento Word se ha guardado correctamente.")
        except (OSError, PermissionError) as exc:
            QMessageBox.critical(self, "No se pudo exportar", str(exc))
