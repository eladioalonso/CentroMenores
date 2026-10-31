"""Ayuda integrada y guía operativa de la aplicación."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton


HELP_HTML = """
<h2>Gestión del Centro · Guía de uso</h2>
<p><b>Estado:</b> versión de desarrollo. No introducir datos reales hasta la validación
funcional, técnica, jurídica y de protección de datos por la entidad responsable.</p>
<h3>Primer inicio</h3>
<ol><li>Crear la cuenta administradora inicial.</li><li>El administrador crea cuentas individuales.</li>
<li>Asignar permisos y mantener las cuentas personales.</li><li>Crear el expediente y abrir una estancia antes de asociar actuaciones.</li></ol>
<h3>Diario e incidencias</h3>
<p>Registrar hechos objetivos, diferenciando la hora del hecho y la fecha de registro.
Seleccionar el turno correcto. Vincular únicamente las estancias implicadas.
El cierre bloquea nuevas anotaciones; las rectificaciones deben ser entradas nuevas,
con motivo y autor, nunca sobrescribir el original.</p>
<h3>Agenda y calendario</h3>
<p>Las tareas de equipo se comparten entre turnos. Revisar diariamente pendientes,
citas, actividades y estados. La vista anual muestra los elementos existentes; no crea
automáticamente calendarios oficiales ni sustituye su revisión.</p>
<h3>Sanidad y medicación</h3>
<p>La aplicación registra información aportada por profesionales autorizados.
No diagnostica ni prescribe. La medicación debe basarse en una prescripción válida.
Registrar administración, rechazo o falta de disponibilidad con sus observaciones.</p>
<h3>Comunicaciones</h3>
<p>Los borradores compartidos admiten aportaciones trazables. No modificar ni atribuirse
las aportaciones de otros profesionales. Cerrar solo cuando se haya revisado el contenido.</p>
<h3>Copias y restauración</h3>
<p>Crear copias manuales antes de operaciones importantes y conectar la unidad externa
para sincronizar las pendientes. Verificar las copias. La restauración sustituye datos
y adjuntos: exige confirmar, crea una copia previa y conserva la auditoría disponible.
No apagar el equipo durante el proceso.</p>
<h3>Seguridad y privacidad</h3>
<ul><li>Bloquear Windows al abandonar el puesto.</li><li>No compartir usuarios ni contraseñas.</li>
<li>No exportar expedientes completos salvo autorización y necesidad justificadas.</li>
<li>Custodiar físicamente las unidades USB; las copias no están cifradas.</li>
<li>Notificar incidentes de seguridad por el procedimiento del centro.</li></ul>
<h3>Preguntas frecuentes</h3>
<p><b>¿Puedo borrar una anotación cerrada?</b> No; debe rectificarse manteniendo el original.</p>
<p><b>¿Puedo abrir una nueva estancia para un menor que ya tiene ficha?</b>
Sí, al reingreso se reutiliza la ficha y se crea una estancia distinta.</p>
<p><b>¿Una copia válida garantiza que puedo restaurarla en cualquier versión?</b>
No. La restauración comprueba la versión del esquema y se cancela si no coincide.</p>
<p><b>¿Puedo usar la aplicación desde el móvil?</b> El acceso móvil todavía no está habilitado.
No expongas el equipo a la red ni abras puertos para intentar habilitarlo manualmente.</p>
<p><b>¿Qué hago ante un error?</b> Anota el momento y la acción realizada, conserva los registros
y solicita soporte. No manipules directamente la base de datos.</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda y preguntas frecuentes")
        self.resize(820, 680)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(HELP_HTML)
        browser.setOpenExternalLinks(False)
        layout.addWidget(browser)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
