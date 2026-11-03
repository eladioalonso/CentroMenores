# Módulos funcionales

Este documento describe la responsabilidad de cada módulo y sus relaciones. Es una especificación inicial: los campos concretos, pantallas y flujos se detallarán con el usuario antes de implementarlos.

## 1. Menores y expedientes

Es el punto de entrada a la información individual.

- Ficha personal única con datos identificativos y datos de contacto relevantes para la actividad interna.
- Personas de referencia y contactos autorizados, según el procedimiento del centro.
- Situación actual y acceso al historial.
- Relaciones con estancias, diario, incidencias, salidas, PEI, escolaridad, actividades y documentos.

Los datos personales no se volverán a introducir en cada módulo. Se consultarán desde la ficha del menor mediante relaciones.

## 2. Estancias

Gestiona cada periodo de permanencia en el centro.

- Ingreso, reingreso y baja.
- Fechas y situación de la estancia.
- Observaciones y datos operativos propios de ese periodo.
- Historial de la estancia y registros asociados.

Un menor puede tener varias estancias. Una estancia cerrada se conserva y no se reutiliza para un ingreso posterior.

## 3. Área sanitaria

Módulo con control de acceso reforzado.

- Identificadores y cobertura sanitaria, incluido CIP cuando proceda.
- Tipo y vigencia de tarjeta sanitaria o documento especial de asistencia.
- Centro sanitario y profesionales de referencia.
- Caducidades, alertas e histórico de cambios.
- Documentos sanitarios relacionados.
- Información y seguimiento sanitario que el centro esté autorizado a registrar.

Los datos de identidad se consultan desde la ficha personal; no se crea una segunda ficha del menor. El acceso a este módulo y a sus documentos se limitará expresamente a usuarios autorizados.

### Vacunación individual

La vacunación forma parte de la ficha sanitaria del expediente principal de cada menor, con independencia de sus ingresos y estancias.

- Calendario oficial de Melilla vigente y sus versiones históricas, con referencia al calendario común del SNS.
- Vista individual por menor con vacuna, enfermedad prevenible, dosis, edad/fecha recomendada, estado y próximas actuaciones orientativas.
- Historial de administraciones con fecha real, número/identificación de dosis, profesional o centro sanitario, lote/fabricante cuando consten, documento justificativo y autor del asiento.
- Registro de vacunas recibidas antes del ingreso o fuera del centro, sin exigir estancia activa.
- Seguimiento diferenciado de calendario sistemático, campañas estacionales y recomendaciones para grupos de riesgo.
- Dosis pendientes o atrasadas señaladas como avisos para revisión sanitaria, nunca como prescripción automática.
- Historial y auditoría: no se borran administraciones; cualquier corrección queda vinculada al asiento original.
- Las reglas de calendario se versionan por vigencia y cohorte. Un cambio del calendario no altera retrospectivamente las pautas históricas.

## 4. Diario profesional

Registro cronológico de observaciones y acontecimientos cotidianos.

- Fecha y hora.
- Autor profesional.
- Menor y, cuando proceda, estancia relacionada.
- Categoría y contenido.
- Búsqueda por menor, estancia, autor, categoría y periodo.
- Rectificaciones o ampliaciones conservando la anotación original y su trazabilidad.

Se definirán criterios para diferenciar observaciones ordinarias, información sensible y anotaciones que deban registrarse como incidencia formal.

## 5. Incidencias

Registro y seguimiento de acontecimientos que requieren tratamiento específico.

- Tipo, fecha, hora, lugar y descripción.
- Gravedad o prioridad, según catálogo acordado.
- Uno o varios menores implicados.
- Profesionales intervinientes.
- Actuaciones realizadas, seguimiento y estado de resolución.
- Documentos asociados.
- Autoría, cambios y cierre.

La relación entre incidencias y menores será de muchos a muchos: una incidencia puede implicar a varios menores y un menor puede aparecer en numerosas incidencias.

## 6. Salidas, visitas y retornos

Control operativo de movimientos fuera del centro.

- Tipo de salida o visita.
- Menor o grupo de menores.
- Fecha y hora previstas y reales de salida y regreso.
- Destino, acompañantes y profesional responsable.
- Autorización y observaciones internas.
- Estado: prevista, en curso, finalizada, cancelada o con incidencia, según reglas que se acuerden.
- Avisos de retornos pendientes o retrasados.

Se deberá poder consultar rápidamente qué menores están fuera del centro.

## 7. Seguimiento educativo y PEI

Organiza los objetivos y la evolución educativa individual.

- PEI y sus versiones.
- Áreas de intervención.
- Objetivos generales y específicos.
- Actuaciones y actividades relacionadas.
- Evaluaciones, revisiones y fechas.
- Profesionales responsables.
- Documentos asociados e histórico.

Las revisiones conservarán las versiones anteriores para poder reconstruir la evolución.

## 8. Escolaridad y formación

Registra la trayectoria formativa relevante para el seguimiento interno.

- Centro, curso, nivel y tutoría.
- Situación de matrícula.
- Asistencia y seguimiento, cuando se gestione en el centro.
- Evolución académica y observaciones autorizadas.
- Formación complementaria.

Se estudiará si los cambios de centro o curso deben tener historial propio en lugar de sobrescribir el dato vigente.

## 9. Actividades

Planifica y registra actividades educativas, recreativas y de otra naturaleza.

- Catálogo de actividades.
- Programación, fecha, horario, espacio y responsable.
- Participantes múltiples.
- Asistencia y observaciones.
- Relación opcional con objetivos del PEI.

La participación se guardará mediante relaciones estructuradas, no como una lista de nombres en un campo de texto.

## 10. Tareas, turnos y traspasos

Facilita la continuidad del trabajo entre equipos.

- Tareas con descripción, prioridad, responsable, estado y vencimiento.
- Asignación y seguimiento.
- Turnos y calendario, si se confirma que deben gestionarse en la aplicación.
- Traspasos entre profesionales o equipos.
- Asuntos pendientes y confirmación de lectura cuando proceda.

Debe quedar claro quién comunica, quién recibe y qué tareas siguen abiertas.

## 11. Documentación

Repositorio documental único dentro de la carpeta de datos de la aplicación.

- Categorías y metadatos del documento.
- Archivo, nombre, formato, tamaño y fechas relevantes.
- Autor o responsable de incorporación.
- Relaciones con menores, estancias, incidencias, PEI u otros registros.
- Control de acceso y, si se requiere, versiones.

El mismo archivo no se duplicará para asociarlo a varios registros: se almacenará una vez y se crearán las relaciones necesarias. Los documentos sanitarios tendrán restricciones reforzadas.

## 12. Panel de control

Vista resumida calculada a partir de los módulos.

- Menores presentes.
- Ingresos y bajas recientes.
- Salidas en curso y retornos pendientes.
- Incidencias abiertas.
- Tareas pendientes.
- Actividades previstas.
- Caducidades y avisos configurados.

El panel no será una fuente de datos independiente: cada indicador procederá de los registros originales y respetará los permisos del usuario.

## 13. Informes y estadísticas

- Informes individuales e informes por estancia.
- Listados de incidencias y actuaciones.
- Actividades y participación.
- Seguimiento educativo.
- Ocupación y movimientos.
- Filtros por fecha, categoría y otros criterios autorizados.
- Vista imprimible y exportación en formatos que se determinen.

Los informes deberán respetar los permisos y evitar mostrar datos sensibles a usuarios no autorizados.

## 14. Administración, usuarios y auditoría

- Alta, baja y bloqueo de cuentas.
- Roles y permisos por módulo y operación.
- Configuración de bloqueo por inactividad.
- Catálogos y parámetros.
- Registro de inicio y cierre de sesión y de operaciones relevantes.
- Copias de seguridad, restauración y comprobaciones.
- Herramientas de mantenimiento.

La eliminación lógica o física de registros, los plazos de conservación y las operaciones administrativas deberán definirse expresamente; no se habilitará un borrado indiscriminado como comportamiento predeterminado.

## 15. Relaciones transversales

- Un menor tiene una ficha y puede tener varias estancias.
- Los registros profesionales se relacionan con el menor y, cuando corresponda, con la estancia en la que sucedieron.
- Una incidencia puede involucrar a varios menores y profesionales.
- Una actividad puede tener varios participantes.
- Un documento se almacena una vez y puede relacionarse con varios registros.
- Una tarea puede originarse en una incidencia, un traspaso u otra necesidad.
- El panel y los informes consultan las relaciones existentes, sin duplicar la información.


> **Especificación vigente:** consultar [Decisiones consolidadas del diseño](DECISIONES_CONSOLIDADAS.md). Este documento reúne las decisiones aprobadas más recientes y prevalece sobre cualquier apartado anterior que las contradiga.
