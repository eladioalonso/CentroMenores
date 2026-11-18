"""Interfaz de informes de incidencias basados en anotaciones del parte diario."""
from datetime import datetime
from pathlib import Path

from docx import Document
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QVBoxLayout,
)
from sqlalchemy import select

from gestion_centro.domain.models import (
    DiaryDay, DiaryEntry, DiaryEntryStayLink, Minor, Stay,
)
from gestion_centro.domain.incident_reports_service import (
    get_incident_report, list_incident_reports, save_incident_report,
)
from gestion_centro.persistence.database import session_scope


CATEGORY_LABELS = {
    "activity": "Actividad", "positive": "Conducta positiva",
    "negative": "Conducta negativa", "observation": "Observación",
    "general": "General", "health": "Salud", "maintenance": "Mantenimiento",
    "other": "Otros",
}
STATUS_LABELS = {
    "draft": "Borrador", "issued": "Emitido", "rectified": "Rectificado",
}


def _local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.astimezone()
    return value.astimezone()


class IncidentReportsDialog(QDialog):
    """Selecciona hechos, guarda borradores y conserva versiones emitidas."""

    def __init__(self, factory, actor_id):
        super().__init__()
        self.factory, self.actor_id = factory, actor_id
        self.entries_by_id = {}
        self.current_report_id = None
        self.current_report_status = None
        self.rectifying = False
        self.setWindowTitle("Informes de incidencias")
        self.resize(1180, 800)
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Los informes se construyen a partir de anotaciones existentes del parte diario. "
            "Cada versión conserva los hechos originales seleccionados y la persona que la emite."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        saved = QHBoxLayout()
        self.saved_reports = QComboBox()
        self.saved_reports.currentIndexChanged.connect(self.open_selected_report)
        refresh_saved = QPushButton("Actualizar")
        refresh_saved.clicked.connect(self.refresh_saved_reports)
        saved.addWidget(QLabel("Informes guardados"))
        saved.addWidget(self.saved_reports, 1)
        saved.addWidget(refresh_saved)
        layout.addLayout(saved)

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
                .distinct().order_by(Minor.family_names, Minor.given_names)
            ).all()
            for minor in minors:
                self.minor.addItem(f"{minor.family_names}, {minor.given_names}", minor.id)
        filters.addRow("Desde", self.start)
        filters.addRow("Hasta", self.end)
        filters.addRow("Menor", self.minor)
        layout.addLayout(filters)

        refresh = QPushButton("Buscar anotaciones del parte")
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
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 2)

        details = QFormLayout()
        self.title = QLineEdit("Informe de incidencias")
        self.recipient = QLineEdit()
        self.recipient.setPlaceholderText("Dirección, Fiscalía, Consejería…")
        details.addRow("Título", self.title)
        details.addRow("Destinatario", self.recipient)
        layout.addLayout(details)

        layout.addWidget(QLabel("Contenido del informe · revisa el borrador antes de emitirlo"))
        self.preview = QTextEdit()
        self.preview.setPlaceholderText("Selecciona hechos y pulsa «Preparar borrador».")
        layout.addWidget(self.preview, 2)

        actions = QHBoxLayout()
        prepare = QPushButton("Preparar borrador")
        prepare.clicked.connect(self.prepare_draft)
        self.save_button = QPushButton("Guardar borrador")
        self.save_button.clicked.connect(self.save_draft)
        self.issue_button = QPushButton("Emitir versión")
        self.issue_button.clicked.connect(self.issue_report)
        self.rectify_button = QPushButton("Preparar rectificación")
        self.rectify_button.clicked.connect(self.prepare_rectification)
        self.history_button = QPushButton("Historial de versiones")
        self.history_button.clicked.connect(self.view_report_history)
        export = QPushButton("Exportar Word…")
        export.clicked.connect(self.export_docx)
        new = QPushButton("Nuevo informe")
        new.clicked.connect(self.new_report)
        for button in (new, prepare, self.save_button, self.issue_button,
                       self.rectify_button, self.history_button, export):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.load_entries()
        self.refresh_saved_reports()

    def _selected_entry_ids(self):
        result = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                entry_id = item.data(Qt.ItemDataRole.UserRole)
                if entry_id in self.entries_by_id:
                    result.append(entry_id)
        return result

    def load_entries(self):
        start, end = self.start.date().toPython(), self.end.date().toPython()
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
            # Si una anotación tiene rectificaciones, el informe usa solo la última
            # versión; la cadena de versiones permanece accesible en el historial.
            superseded_ids = {entry.correction_of_id for entry in entries if entry.correction_of_id}
            entries = [entry for entry in entries if entry.id not in superseded_ids]
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
                data = {
                    "id": entry.id, "happened_at": entry.happened_at,
                    "category": entry.category, "content": entry.content,
                    "author": entry.author_name_snapshot,
                    "minors": ", ".join(dict.fromkeys(names)) or "Sin menor vinculado",
                }
                self.entries_by_id[entry.id] = data
                rows.append(data)

        self.table.setRowCount(len(rows))
        for index, entry in enumerate(rows):
            include = QTableWidgetItem()
            include.setFlags(include.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            include.setCheckState(Qt.CheckState.Checked)
            include.setData(Qt.ItemDataRole.UserRole, entry["id"])
            happened = _local_datetime(entry["happened_at"])
            values = [
                include, QTableWidgetItem(happened.strftime("%d/%m/%Y %H:%M")),
                QTableWidgetItem(entry["minors"]),
                QTableWidgetItem(CATEGORY_LABELS.get(entry["category"], entry["category"])),
                QTableWidgetItem(entry["content"]), QTableWidgetItem(entry["author"]),
            ]
            for column, item in enumerate(values):
                self.table.setItem(index, column, item)

    def prepare_draft(self):
        selected = [self.entries_by_id[item] for item in self._selected_entry_ids()]
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
            "", "RELACIÓN CRONOLÓGICA DE LOS HECHOS", "",
        ]
        for entry in selected:
            happened = _local_datetime(entry["happened_at"])
            lines.extend([
                f"{happened.strftime('%d/%m/%Y %H:%M')} · {CATEGORY_LABELS.get(entry['category'], entry['category'])}",
                f"Menor(es): {entry['minors']}", entry["content"],
                f"Anotado originalmente por: {entry['author']}", "",
            ])
        self.preview.setPlainText("\n".join(lines))

    def save_draft(self):
        self._save(issue=False)

    def issue_report(self):
        self._save(issue=True)

    def _save(self, *, issue: bool):
        ids = self._selected_entry_ids()
        if not ids:
            QMessageBox.warning(self, "Sin hechos vinculados", "Marca las anotaciones que forman parte de esta versión.")
            return
        try:
            with session_scope(self.factory) as session:
                report = save_incident_report(
                    session, actor_account_id=self.actor_id,
                    title=self.title.text(), recipient=self.recipient.text(),
                    content=self.preview.toPlainText(), entry_ids=ids,
                    report_id=self.current_report_id, issue=issue,
                )
                self.current_report_id = report.id
                status = report.status
            self.current_report_status = status
            self.rectifying = False
            self.refresh_saved_reports(select_id=self.current_report_id)
            QMessageBox.information(
                self, "Informe emitido" if issue else "Borrador guardado",
                "Se ha guardado una nueva versión del informe. "
                + ("La versión emitida queda conservada y no se sobrescribirá." if issue
                   else "Puedes continuar editándola antes de emitirla.")
            )
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo guardar el informe", str(exc))

    def refresh_saved_reports(self, select_id=None):
        with session_scope(self.factory) as session:
            reports = list_incident_reports(session, actor_account_id=self.actor_id)
            items = [(f"{report.title} · {STATUS_LABELS.get(report.status, report.status)} · "
                      f"{report.updated_at.astimezone().strftime('%d/%m/%Y %H:%M')}", report.id)
                     for report in reports]
        self.saved_reports.blockSignals(True)
        self.saved_reports.clear()
        self.saved_reports.addItem("— Nuevo informe —", None)
        for label, report_id in items:
            self.saved_reports.addItem(label, report_id)
        if select_id:
            index = self.saved_reports.findData(select_id)
            if index >= 0:
                self.saved_reports.setCurrentIndex(index)
        self.saved_reports.blockSignals(False)

    def open_selected_report(self, _index):
        report_id = self.saved_reports.currentData()
        if not report_id:
            return
        try:
            with session_scope(self.factory) as session:
                report = get_incident_report(
                    session, actor_account_id=self.actor_id, report_id=report_id
                )
                version = report.versions[-1] if report.versions else None
                entry_ids = [item.entry_id for item in version.entries] if version else []
                linked_entries = session.scalars(
                    select(DiaryEntry).where(DiaryEntry.id.in_(entry_ids))
                ).all() if entry_ids else []
                linked_dates = [entry.diary_day.diary_date for entry in linked_entries]
                details = (report.title, report.recipient, report.status,
                           version.content if version else "", entry_ids,
                           min(linked_dates) if linked_dates else None,
                           max(linked_dates) if linked_dates else None)
            self.current_report_id = report_id
            self.current_report_status = details[2]
            self.minor.setCurrentIndex(0)
            if details[5] and details[6]:
                self.start.setDate(QDate(details[5].year, details[5].month, details[5].day))
                self.end.setDate(QDate(details[6].year, details[6].month, details[6].day))
                self.load_entries()
            self.title.setText(details[0])
            self.recipient.setText(details[1] or "")
            self.preview.setPlainText(details[3])
            selected = set(details[4])
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked if item.data(Qt.ItemDataRole.UserRole) in selected
                                       else Qt.CheckState.Unchecked)
            issued = details[2] in {"issued", "rectified"}
            self.save_button.setEnabled(not issued)
            self.issue_button.setText("Emitir rectificación" if issued else "Emitir versión")
            self.rectifying = False
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo abrir el informe", str(exc))

    def view_report_history(self):
        if not self.current_report_id:
            QMessageBox.information(self, "Selecciona un informe", "Guarda o abre un informe para consultar su historial.")
            return
        try:
            with session_scope(self.factory) as session:
                report = get_incident_report(
                    session, actor_account_id=self.actor_id, report_id=self.current_report_id
                )
                versions = list(report.versions)
                history = []
                for version in versions:
                    history.extend([
                        f"VERSIÓN {version.version_number} · {STATUS_LABELS.get(version.status, version.status)}",
                        f"Fecha: {version.created_at.astimezone().strftime('%d/%m/%Y %H:%M')}",
                        f"Realizada por: {version.created_by_name_snapshot}",
                        f"Hechos vinculados: {len(version.entries)}",
                        "", version.content, "", "—" * 50, "",
                    ])
            dialog = QDialog(self)
            dialog.setWindowTitle("Historial de versiones del informe")
            dialog.resize(900, 650)
            layout = QVBoxLayout(dialog)
            viewer = QTextEdit()
            viewer.setReadOnly(True)
            viewer.setPlainText("\\n".join(history) if history else "El informe todavía no tiene versiones.")
            layout.addWidget(viewer)
            close = QPushButton("Cerrar")
            close.clicked.connect(dialog.accept)
            layout.addWidget(close)
            dialog.exec()
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "No se pudo consultar el historial", str(exc))

    def prepare_rectification(self):
        if not self.current_report_id:
            QMessageBox.information(self, "Selecciona un informe", "Abre primero el informe que necesitas rectificar.")
            return
        self.rectifying = True
        self.save_button.setEnabled(False)
        self.issue_button.setText("Emitir rectificación")
        QMessageBox.information(
            self, "Rectificación",
            "Modifica el contenido y la selección de hechos. Al emitir, se creará una nueva versión "
            "rectificada y se conservarán todas las versiones anteriores."
        )

    def new_report(self):
        self.current_report_id = None
        self.current_report_status = None
        self.rectifying = False
        self.saved_reports.blockSignals(True)
        self.saved_reports.setCurrentIndex(0)
        self.saved_reports.blockSignals(False)
        self.title.setText("Informe de incidencias")
        self.recipient.clear()
        self.preview.clear()
        self.save_button.setEnabled(True)
        self.issue_button.setText("Emitir versión")
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def export_docx(self):
        content = self.preview.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Informe vacío", "Prepara o abre un informe antes de exportarlo.")
            return
        if not self.current_report_id or self.current_report_status not in {"issued", "rectified"}:
            QMessageBox.information(self, "Informe no emitido", "Emite el informe antes de exportar la versión oficial.")
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
            lines = content.splitlines()
            if lines:
                document.add_heading(lines[0], 0)
                for line in lines[1:]:
                    document.add_paragraph(line)
            document.save(Path(filename))
            QMessageBox.information(self, "Informe exportado", "El documento Word se ha guardado correctamente.")
        except OSError as exc:
            QMessageBox.critical(self, "No se pudo exportar", str(exc))
