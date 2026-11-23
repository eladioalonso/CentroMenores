# Flujos de trabajo

## 1. Finalidad y organización

Este documento describe el uso cotidiano de Gestión del Centro. La navegación funcional se limita a cuatro módulos:

1. **Expediente principal del menor.**
2. **Expediente sanitario del menor.**
3. **Parte diario.**
4. **Informes de incidencias.**

Inicio es un panel de entrada. Administración es un área técnica reservada al administrador. Ninguno constituye un módulo funcional adicional.

El documento especifica el comportamiento de la aplicación; no sustituye los protocolos educativos, sanitarios ni organizativos del centro. La dirección y los responsables institucionales deben validar las reglas, la protección de datos y los procedimientos antes de cualquier uso con información real.

## 2. Principios comunes

- Cada profesional utiliza su propia cuenta.
- Todos los educadores activos tienen las mismas capacidades ordinarias de consulta, creación y modificación en los cuatro módulos.
- No se restringe la edición por autoría, turno, antigüedad del registro o cierre del parte.
- La aplicación identifica al usuario y registra la fecha y hora de las operaciones relevantes.
- Antes de crear un expediente se busca si el menor ya existe, para evitar duplicados.
- Los registros se vinculan al menor y, cuando corresponde, a la estancia en la que ocurrió el hecho.
- La información se introduce una sola vez y se reutiliza mediante relaciones entre módulos.
- Una rectificación conserva la versión anterior, la autoría, la fecha/hora y el motivo cuando corresponda.
- Los datos sanitarios detallados se mantienen en el expediente sanitario. El diario puede reflejar actuaciones necesarias para la cronología, pero no sustituye ni duplica la ficha sanitaria.
- Los informes de incidencias seleccionan hechos del parte diario; no crean una segunda fuente factual independiente.

## 3. Expediente principal del menor

### Abrir o crear un expediente

1. El educador entra en Expediente principal.
2. Busca al menor por los datos identificativos disponibles.
3. Si existe, abre la ficha única. Un reingreso no crea un expediente nuevo.
4. Si no existe, crea la ficha con los datos personales disponibles y autorizados.
5. La edad se calcula a partir de la fecha de nacimiento; no se almacena como dato independiente que pueda quedar desactualizado.
6. El sistema conserva los cambios relevantes en el historial.

### Gestionar estancias

1. Desde la ficha, el educador consulta las estancias anteriores.
2. Para un ingreso o reingreso, registra un nuevo periodo.
3. Para una baja, registra fecha y motivo de cierre.
4. El sistema mantiene la ficha personal y todos los periodos anteriores.
5. Los registros creados durante una estancia permanecen vinculados a ella cuando corresponda.

Una estancia cerrada no elimina el expediente ni su historial. El mismo menor puede tener varias estancias independientes.

### Seguimiento educativo, escolaridad y documentos

- El seguimiento educativo se registra en el expediente principal, con objetivos, actuaciones, evolución y rectificaciones versionadas.
- Los datos escolares y sus periodos se conservan para consulta histórica.
- Los documentos personales y administrativos se almacenan una vez y se vinculan al menor o a la estancia correspondiente.
- Las autorizaciones, consentimientos, visitas y restricciones se consultan desde el contexto del menor.
- Las salidas y retornos se registran con fechas previstas y reales, responsables, destino y estado.
- Cualquier educador activo puede consultar y modificar estos registros, conservando su historial.

## 4. Expediente sanitario del menor

### Consulta y actualización

1. El educador abre Expediente sanitario.
2. Selecciona al menor. La lista incluye residentes con estancia activa y menores inactivos o dados de baja.
3. Consulta la ficha sanitaria, historial, alergias, antecedentes e instrucciones de emergencia.
4. Actualiza los datos sanitarios ordinarios cuando corresponda.
5. La aplicación conserva versiones y registra quién realizó el cambio.

La ficha sanitaria pertenece al expediente permanente del menor, no a una estancia concreta. Los registros históricos siguen disponibles después de una baja o reingreso.

### Medicación y tratamientos

1. Se registra una pauta prescrita con su referencia, dosis, instrucciones, vigencia y horarios.
2. Los horarios se reflejan en la vista de administraciones del día y turno.
3. El educador registra el resultado de cada administración según la pauta y la actuación realizada.
4. Si se detecta un error, cualquier educador activo puede rectificar el registro.
5. La rectificación conserva el contenido previo, el nuevo contenido, el autor y la fecha.

La aplicación no prescribe medicamentos ni decide pautas. Se registran las indicaciones documentadas por el profesional competente.

### Vacunación

1. El educador consulta el historial de vacunas y las ediciones documentales de calendario disponibles.
2. Registra una administración solo cuando dispone de la información correspondiente.
3. Vincula los datos de vacuna, dosis, fecha, lote, producto, centro/profesional y justificante cuando consten.
4. Las revisiones individuales de dosis reflejan el criterio profesional documentado.
5. Las rectificaciones mantienen el historial.

Los calendarios son referencias documentales. La ausencia de un registro no demuestra por sí sola que una dosis esté pendiente. La aplicación no prescribe, no diagnostica y no determina automáticamente pautas de rescate o contraindicaciones.

## 5. Parte diario

### Registro cronológico

1. El educador abre Parte diario.
2. Selecciona la fecha.
3. Consulta la cronología de anotaciones de ese día.
4. Selecciona uno de los cuatro apartados: actividades realizadas en el día, comportamientos positivos, comportamientos negativos u observaciones.
5. Introduce el contenido y, cuando proceda, vincula uno o varios menores. Los hechos generales pueden quedar sin vincular.
6. Indica la fecha/hora en que ocurrió el hecho; la aplicación registra por separado el momento de registro y la autoría.
7. Guarda la anotación. La aplicación conserva autoría, relaciones y marcas de tiempo.

Las altas, reingresos y bajas se consultan y gestionan desde el historial de estancias del expediente, evitando duplicarlas como categorías manuales del parte diario. La cronología no solicita un parte de personal ni divide las actividades por turnos.

### Consulta y rectificación

- La cronología puede consultarse por fecha, periodo, categoría y menor.
- Una anotación puede relacionarse con varios menores sin duplicar el texto.
- Cualquier educador activo puede rectificar cualquier anotación, aunque la haya creado otra persona o pertenezca a un día cerrado.
- La rectificación crea una nueva versión vinculada a la anterior y conserva el contenido original.
- El cierre del parte impide añadir nuevas anotaciones ordinarias a esa fecha, pero no bloquea la rectificación de las existentes.
- Agenda y calendario son vistas de planificación relacionadas; no deben mantener fuentes de datos independientes.

## 6. Informes de incidencias

### Elaboración de un informe

1. El educador abre Informes de incidencias.
2. Selecciona un intervalo de fechas y, si lo necesita, filtra por un menor.
3. La aplicación muestra las anotaciones vigentes del parte diario, es decir, la última versión de cada hecho.
4. **Ninguna anotación aparece seleccionada automáticamente.** El educador marca expresamente solo los hechos que deben incorporarse.
5. Prepara el borrador cronológico y revisa título, destinatario y contenido.
6. Guarda el borrador. Queda disponible para que otro educador lo continúe.
7. Antes de emitirlo, comprueba que los hechos, menores, fechas y destinatario son los correctos.
8. Emite una versión oficial y la exporta a Word cuando sea necesario.

### Rectificación e historial

- Los borradores pueden ser editados por cualquier educador activo.
- Cada versión conserva texto, título, destinatario, autor, fecha/hora y vínculos con las anotaciones seleccionadas.
- Una versión emitida no se sobrescribe.
- Para corregirla se crea una nueva versión rectificada, manteniendo las anteriores.
- La autoría del hecho y la autoría de elaboración/emisión del informe se conservan por separado.
- Una modificación posterior del parte diario no cambia retroactivamente un informe ya emitido.
- El mismo hecho puede incluirse en varios informes, manteniendo siempre su vínculo con la anotación de origen.

La aplicación no incorpora automáticamente el contenido completo del expediente sanitario a un informe. Si un hecho sanitario debe constar en la cronología, se utiliza la información autorizada y registrada en el parte diario.

## 7. Edición compartida y auditoría

- Cualquier educador activo puede consultar, crear y modificar registros de los cuatro módulos.
- El autor original permanece identificado en su versión.
- Cada nueva versión identifica a quien realizó el cambio y cuándo.
- Los motivos de rectificación se registran cuando corresponda.
- Las consultas sanitarias y operaciones relevantes quedan auditadas conforme a la política configurada.
- La administración técnica —cuentas, permisos técnicos, configuración, copias, restauración y diagnóstico— permanece reservada al administrador.
- El administrador no será intermediario obligatorio para las modificaciones ordinarias.

## 8. Inicio de sesión, cambio de turno y fin de sesión

1. Cada educador inicia sesión con sus propias credenciales.
2. Consulta el panel de Inicio para orientarse sobre la actividad del centro.
3. Realiza las operaciones en los cuatro módulos según sus necesidades.
4. El traspaso de información entre turnos se apoya en la cronología del parte diario y en la agenda común; no crea una segunda copia de los hechos.
5. Antes de dejar el ordenador, guarda los cambios y cierra su sesión.
6. El siguiente educador inicia sesión con su propia cuenta.
7. El cierre de sesión no elimina, cierra ni bloquea registros del turno anterior.
8. El cierre de un parte organiza la fecha y limita la incorporación de nuevas anotaciones ordinarias, pero no impide rectificaciones posteriores por cualquier educador activo.

Los horarios habituales comunicados para los turnos son mañana (08:00–15:00), tarde (15:00–22:00) y noche (22:00–08:00 del día siguiente). La aplicación debe reflejar el turno real registrado y no utilizar un cierre automático para impedir rectificaciones.

## 9. Administración técnica

Solo el administrador accede a:
- Alta, activación y desactivación de cuentas.
- Configuración técnica.
- Copias de seguridad y restauración.
- Mantenimiento, diagnóstico y consulta de auditoría.

La restauración requiere autorización específica, verificación de la copia y conservación de una copia preventiva del estado actual. No se deben prometer fusiones automáticas de datos posteriores incompatibles.

## 10. Validación pendiente antes de datos reales

La prueba funcional debe realizarse exclusivamente con datos ficticios y comprobar:
- Los cuatro módulos y sus relaciones.
- Edición cruzada entre educadores y conservación de versiones.
- Consulta sanitaria de menores con y sin estancia activa.
- Selección explícita de hechos en informes.
- Recuperación y continuación de borradores por otro educador.
- Emisión, rectificación y exportación de informes.
- Integridad de migraciones, copias y restauración en Windows.

La puesta en servicio requiere además aprobación institucional, revisión de protección de datos, seguridad del equipo y soportes, permisos, conservación y protocolos sanitarios.
