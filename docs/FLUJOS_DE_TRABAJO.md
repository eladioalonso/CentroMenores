# Flujos de trabajo

## 1. Finalidad

Este documento describe cómo se utilizará Gestión del Centro durante la actividad cotidiana. Los recorridos son una propuesta funcional inicial que deberá validarse con los profesionales del centro antes de implementar las pantallas y las reglas definitivas.

El documento especifica el comportamiento de la aplicación; no sustituye los protocolos educativos, sanitarios ni organizativos del centro. Los criterios de autorización, comunicación, actuación y conservación deberán ajustarse a los procedimientos aprobados por la dirección.

## 2. Principios comunes a todos los flujos

- Cada profesional inicia sesión con su propia cuenta.
- La aplicación identifica automáticamente al usuario y registra la fecha y hora de las operaciones relevantes.
- Antes de crear un menor nuevo, se buscará si ya existe una ficha para evitar duplicados.
- Los registros se vinculan a la ficha del menor y, cuando corresponda, a la estancia activa en el momento del hecho.
- Los formularios reutilizan los datos ya registrados; no solicitan volver a escribirlos sin necesidad.
- Los campos y acciones disponibles dependen de los permisos del usuario.
- La aplicación distingue entre guardar un borrador, registrar una anotación, cerrar un proceso y rectificar un registro.
- Una rectificación no debe borrar silenciosamente el contenido anterior: conservará autoría, fecha y motivo cuando proceda.
- Los avisos y paneles se calculan a partir de los registros originales.
- Las operaciones que afecten a varios registros se realizarán de forma coherente, evitando estados parciales.

## 3. Inicio de turno

### Objetivo

Que el profesional que comienza su turno pueda conocer los asuntos relevantes y pendientes sin tener que revisar manualmente todos los módulos.

### Recorrido propuesto

1. El educador abre la aplicación.
2. Introduce sus credenciales personales.
3. La aplicación valida la cuenta y carga sus permisos.
4. Se muestra el panel de inicio con información que ese usuario esté autorizado a consultar.
5. El panel presenta, según configuración:
   - Menores presentes en el centro.
   - Menores que figuran fuera y retornos pendientes.
   - Tareas asignadas o pendientes.
   - Incidencias abiertas que requieran seguimiento.
   - Actividades previstas.
   - Avisos y fechas relevantes.
   - Información de traspaso pendiente de revisar.
6. El profesional consulta los detalles necesarios y puede marcar como leído un traspaso si esa función se habilita.
7. La aplicación mantiene la sesión activa hasta el cierre manual, el cambio de usuario o el bloqueo por inactividad.

### Reglas

- El panel no mostrará datos para los que el usuario no tenga permiso.
- La confirmación de lectura de un traspaso no equivaldrá a confirmar que una tarea está realizada.
- La aplicación no marcará automáticamente como resuelto ningún asunto por el mero hecho de abrirlo.

## 4. Alta de un menor e inicio de estancia

### Objetivo

Registrar a un menor sin duplicar su identidad y abrir un nuevo periodo de estancia.

### Recorrido propuesto

1. El profesional autorizado accede a Menores.
2. Busca por los datos identificativos disponibles para comprobar si existe una ficha previa.
3. Si existe, abre la ficha existente. No crea otra ficha por tratarse de un reingreso.
4. Si no existe, crea una ficha con los datos mínimos necesarios y autorizados.
5. Accede a Estancias y registra un nuevo ingreso.
6. Introduce los datos propios de esa estancia, como fecha y hora de inicio y observaciones operativas previstas.
7. La aplicación valida los campos obligatorios y comprueba que no haya otra estancia incompatible abierta.
8. Se confirma el registro y la nueva estancia queda relacionada con la ficha personal.
9. Los módulos posteriores podrán asociar sus registros a esa estancia.

### Reglas

- La ficha personal y la estancia son entidades distintas.
- Un reingreso crea una nueva estancia; no reactiva ni sobrescribe una estancia histórica.
- Los datos personales se mantienen en la ficha única.
- Los datos que cambien con el tiempo deberán tener una política definida: dato vigente o historial de cambios, según su naturaleza.
- La aplicación no decidirá por sí sola cuestiones administrativas o de autorización que estén fuera de su alcance.

## 5. Consulta y actualización de la ficha personal

1. El profesional busca al menor mediante los filtros autorizados.
2. Abre la ficha única.
3. Consulta los datos que su perfil permite ver.
4. Si tiene permiso de modificación, actualiza el dato correspondiente.
5. La aplicación registra quién realizó el cambio y cuándo.
6. Si el dato requiere conservar versiones anteriores, se guarda el histórico en lugar de sobrescribirlo sin trazabilidad.

### Reglas

- No se crearán fichas duplicadas para corregir o actualizar información.
- La modificación de datos especialmente sensibles podrá requerir permisos específicos.
- Los cambios relevantes deberán poder revisarse en el historial de auditoría.

## 6. Diario profesional

### Objetivo

Disponer de un registro cronológico general y único de la actividad cotidiana del centro. No habrá un diario independiente por menor: las anotaciones se consultarán en una cronología común y podrán relacionarse con uno o varios menores cuando corresponda.

### Recorrido propuesto

1. El educador entra en Diario profesional.
2. La aplicación muestra la cronología general, ordenada por fecha y hora, con los registros que el usuario esté autorizado a consultar.
3. Para crear una anotación, el profesional selecciona si se trata de un registro general del centro o si está relacionado con uno o varios menores.
4. Si selecciona menores, la aplicación permite vincular todos los implicados en una única anotación y propone comprobar la estancia correspondiente de cada uno cuando proceda.
5. Selecciona una categoría o tipo de anotación de un catálogo configurable.
6. Introduce el contenido y los datos complementarios definidos por el centro.
7. Guarda la anotación.
8. La aplicación registra automáticamente el autor, la fecha y la hora de creación, y conserva la relación con los menores y las estancias que correspondan.
9. La anotación aparece una sola vez en la cronología general y también en las consultas o historiales autorizados de cada menor relacionado.

### Reglas

- El diario es un registro cronológico general del centro, no una colección de diarios individuales.
- Una anotación puede no estar relacionada con ningún menor, o estar relacionada con uno o varios.
- Si un mismo acontecimiento afecta a varios menores, se creará una única anotación con varias relaciones; no se duplicará el texto por cada menor.
- La fecha y hora del acontecimiento, si difieren de la fecha y hora de registro, deberán poder distinguirse.
- Las consultas podrán filtrarse, como mínimo, por intervalo de fechas, menor relacionado, profesional autor y categoría, siempre respetando los permisos.
- Una anotación no debe confundirse automáticamente con una incidencia.
- Si el contenido requiere abrir una incidencia formal, la aplicación podrá ofrecer iniciar ese flujo y mantener la relación entre ambos registros, evitando duplicar innecesariamente la información.
- Las anotaciones guardadas no se modificarán de forma silenciosa. Las rectificaciones conservarán trazabilidad de autoría, fecha, motivo y contenido anterior conforme a la política que apruebe el centro.
- Se definirán permisos diferenciados para consultar, crear, rectificar y exportar anotaciones.

## 7. Registro y seguimiento de una incidencia

### Objetivo

Documentar un acontecimiento, las personas implicadas y las actuaciones de seguimiento.

### Recorrido propuesto

1. El profesional autorizado abre Incidencias y selecciona Nuevo registro.
2. Introduce fecha, hora, lugar, tipo y descripción.
3. Selecciona uno o varios menores implicados.
4. Comprueba la estancia relacionada de cada menor cuando proceda.
5. Identifica a los profesionales intervinientes, según los permisos y datos disponibles.
6. Añade las actuaciones realizadas y la información complementaria que corresponda.
7. Adjunta documentos si está autorizado.
8. Guarda la incidencia.
9. La aplicación crea las relaciones con todos los menores y profesionales seleccionados.
10. Si procede, el usuario crea tareas de seguimiento relacionadas con la incidencia.
11. Los profesionales autorizados consultan su evolución.
12. La incidencia se cierra cuando se cumplen los criterios de cierre que establezca el centro.

### Reglas

- Una incidencia puede implicar a varios menores.
- No se creará una incidencia independiente por cada menor si se trata del mismo acontecimiento.
- Las actuaciones posteriores se añadirán al historial de seguimiento.
- El cierre no eliminará la incidencia ni sus relaciones.
- Los datos sensibles se mostrarán únicamente a los perfiles autorizados.
- La aplicación no sustituye los canales de comunicación urgente establecidos por el centro.

## 8. Salida, visita y retorno

### Objetivo

Conocer qué salidas están previstas, cuáles están en curso y cuándo se ha producido el retorno.

### Recorrido propuesto

1. El profesional autorizado abre Salidas y visitas.
2. Selecciona el menor o grupo de menores.
3. Registra el tipo de movimiento y los datos necesarios: destino, fechas u horas previstas, acompañantes y responsable, según proceda.
4. Registra la autorización o referencia interna correspondiente, de acuerdo con el procedimiento del centro.
5. Guarda la salida prevista.
6. Cuando se produce la salida, registra la fecha y hora reales.
7. La aplicación refleja el movimiento como en curso.
8. Cuando se produce el retorno, el profesional registra fecha y hora reales.
9. Si hay una variación o acontecimiento relevante, añade la observación o inicia el flujo de incidencia correspondiente.
10. La salida queda finalizada y se conserva en el historial del menor.

### Reglas

- Deben distinguirse las horas previstas de las horas reales.
- Una salida no se considerará finalizada solo porque haya pasado la hora prevista.
- El panel mostrará los movimientos en curso y los retornos pendientes.
- La aplicación no sustituirá la comprobación directa de la presencia física del menor.
- Los estados y alertas se ajustarán al protocolo del centro.

## 9. Planificación y registro de actividades

1. El profesional autorizado abre Actividades.
2. Selecciona una actividad existente o crea una nueva si tiene permiso.
3. Registra fecha, horario, lugar, responsable y descripción.
4. Selecciona uno o varios participantes.
5. La aplicación registra las participaciones mediante relaciones individuales.
6. Tras la actividad, el profesional registra asistencia y observaciones.
7. Si procede, relaciona la actividad con objetivos educativos o actuaciones del PEI.
8. La actividad aparece en las consultas e informes autorizados.

### Reglas

- Una actividad puede tener múltiples participantes.
- La ausencia de un menor no debe confundirse con la cancelación de toda la actividad.
- Las observaciones individuales deberán poder asociarse al participante correspondiente.
- No se duplicarán datos personales de los participantes.

## 10. Seguimiento educativo y PEI

1. El profesional autorizado abre la ficha del menor y accede al seguimiento educativo.
2. Consulta el PEI vigente y sus objetivos.
3. Registra una actuación, observación o evaluación vinculada al área y objetivo correspondiente cuando proceda.
4. Identifica autor y fecha.
5. En una revisión, actualiza el estado de los objetivos y documenta la evaluación.
6. Cuando se aprueba una nueva versión del PEI, se conserva la anterior y se identifica la nueva vigencia.
7. Los documentos asociados quedan vinculados al expediente y al periodo correspondiente.

### Reglas

- El seguimiento cotidiano no debe sobrescribir el PEI.
- Las versiones anteriores deben seguir siendo consultables por usuarios autorizados.
- La aplicación facilitará la relación entre objetivos, actuaciones y evaluaciones, pero no determinará valoraciones educativas automáticamente.

## 11. Gestión escolar y formativa

1. El profesional autorizado accede al apartado Escolaridad y formación.
2. Consulta la situación vigente.
3. Registra o actualiza centro, curso, tutoría y demás datos que el centro decida gestionar.
4. Añade seguimientos, observaciones o documentos autorizados.
5. Cuando se produce un cambio de curso o centro, se conserva el periodo anterior si así se define en el modelo de datos.
6. La información queda disponible para el seguimiento y los informes autorizados.

## 12. Área sanitaria

1. El usuario con permiso sanitario accede al módulo específico.
2. Busca al menor y consulta su información sanitaria autorizada.
3. Registra o actualiza cobertura, CIP, tipo de documento, vigencia y referencias sanitarias según los campos aprobados.
4. Añade un centro o profesional sanitario al catálogo reutilizable si tiene permiso.
5. Adjunta documentación sanitaria en el repositorio protegido.
6. La aplicación registra autoría y fecha de la operación.
7. Los avisos de caducidad se muestran exclusivamente a los usuarios autorizados.

### Reglas

- La identidad del menor se consulta desde su ficha única.
- La información sanitaria no se replica en módulos generales.
- Las notificaciones generales no incluirán detalles sanitarios.
- El acceso a documentos sanitarios estará protegido igual o más estrictamente que el acceso a sus metadatos.
- El alcance exacto de los datos que se registrarán deberá validarse con el centro.

## 13. Documentación

1. El usuario autorizado selecciona Incorporar documento.
2. Elige el archivo y su categoría.
3. Introduce los metadatos requeridos: título, fecha documental, fecha de incorporación y observaciones, según proceda.
4. Selecciona los registros con los que debe relacionarse.
5. La aplicación valida el archivo y lo almacena en el repositorio interno.
6. Guarda sus metadatos y relaciones.
7. Los usuarios autorizados pueden localizarlo desde el módulo documental o desde los registros relacionados.

### Reglas

- El archivo se almacena una sola vez.
- La relación con varios menores o registros no genera copias adicionales.
- Los permisos se aplican tanto a la ficha documental como al archivo físico.
- La eliminación y sustitución de documentos tendrá un procedimiento controlado y auditable.

## 14. Tareas y traspaso entre turnos

### Crear y gestionar una tarea

1. El profesional crea una tarea desde el módulo de tareas o desde un registro relacionado.
2. Introduce descripción, prioridad, responsable y fecha límite, según los campos configurados.
3. La tarea queda vinculada al asunto que la origina cuando corresponda.
4. El responsable actualiza su estado.
5. Al completarla, registra el resultado y la fecha de finalización.

### Realizar un traspaso

1. El profesional que finaliza el turno prepara la información pendiente de comunicar.
2. Selecciona tareas, incidencias u otros asuntos relevantes que deban aparecer en el traspaso.
3. Añade un resumen operativo, evitando repetir datos que ya están registrados.
4. Guarda el traspaso con autor y fecha/hora.
5. El profesional del siguiente turno consulta el traspaso.
6. Puede confirmar su lectura si esa función está habilitada.
7. Las tareas continúan en su propio módulo y conservan su responsable y estado.

### Reglas

- Un traspaso no sustituye al registro original de una incidencia, tarea o anotación.
- Confirmar lectura no significa aceptar, resolver ni completar el asunto.
- Debe poder consultarse quién creó el traspaso y quién confirmó su lectura.
- La información sanitaria o especialmente sensible solo se incluirá cuando sea necesario y el destinatario esté autorizado.

## 15. Cierre de estancia y baja

1. El usuario autorizado localiza al menor y la estancia que debe finalizar.
2. Comprueba que está seleccionando la estancia correcta.
3. Registra fecha y hora de finalización y los datos operativos que el centro haya definido.
4. La aplicación comprueba si hay procesos abiertos relacionados y presenta avisos, sin eliminar ni cerrar automáticamente registros.
5. El usuario confirma el cierre.
6. La estancia queda marcada como finalizada.
7. La ficha personal permanece disponible y conserva todas sus estancias anteriores.
8. Los historiales, incidencias, anotaciones, documentos y actividades siguen relacionados con la estancia original.

### Reglas

- Finalizar una estancia no elimina la ficha personal.
- No se borran los registros históricos.
- Una nueva entrada se registra como una nueva estancia.
- La aplicación no decide por sí sola qué documentos deben conservarse o eliminarse; se aplicará la política de conservación aprobada.

## 16. Informes y consultas

1. El usuario abre Informes.
2. Selecciona el tipo de informe y los filtros disponibles.
3. La aplicación comprueba los permisos antes de consultar los datos.
4. Presenta una vista previa.
5. El usuario autorizado imprime o exporta el resultado.
6. La exportación queda registrada cuando la política de auditoría lo requiera.

Los informes deben indicar el periodo y los criterios utilizados. No incluirán campos sensibles por defecto si el usuario no tiene autorización o si no son necesarios para la finalidad del informe.

## 17. Copias de seguridad y restauración

### Crear una copia

1. El usuario con permiso accede a Copias de seguridad.
2. La aplicación comprueba que no haya operaciones incompatibles en curso.
3. Crea una copia consistente de la base de datos y de los documentos asociados.
4. Verifica que los archivos de la copia existen y que la base de datos supera las comprobaciones previstas.
5. Registra fecha, resultado y ubicación.
6. Ofrece exportar una copia cifrada a un dispositivo o ubicación externa autorizada.

### Restaurar una copia

1. Se exige autorización específica.
2. Se identifica la copia y se comprueba su integridad.
3. La aplicación informa de que la restauración sustituirá el estado actual.
4. Se crea una copia preventiva del estado actual cuando sea posible.
5. Se realiza la restauración con la aplicación en estado controlado.
6. Se comprueba la integridad de la base de datos y la disponibilidad de los documentos.
7. Se registra el resultado.

La restauración deberá probarse periódicamente; una copia no se considerará válida solo por haberse creado.

## 18. Cierre de sesión y fin de turno

1. El profesional guarda y finaliza las operaciones pendientes.
2. Consulta los asuntos que deben comunicarse al siguiente turno.
3. Registra el traspaso si procede.
4. Cierra su sesión.
5. La aplicación vuelve a la pantalla de acceso.
6. Si otro educador utiliza el equipo, inicia sesión con sus propias credenciales.

El cierre de sesión no debe cerrar ni finalizar automáticamente tareas, incidencias o salidas.

## 19. Estados y catálogos configurables

Los siguientes elementos no deben quedar fijados arbitrariamente en el código:

- Tipos y categorías de anotación.
- Tipos y niveles de incidencia.
- Estados y prioridades de tareas.
- Tipos y estados de salidas y visitas.
- Categorías documentales.
- Áreas y estados de objetivos del PEI.
- Tipos de actividad.
- Plazos de bloqueo por inactividad.
- Avisos y criterios de vencimiento.

Los catálogos se administrarán mediante permisos específicos. Los cambios en un catálogo no deben alterar el significado de registros históricos ya guardados.

## 20. Puntos que debe validar el centro

Antes de convertir estos flujos en requisitos definitivos, se necesita confirmar:

1. Qué datos mínimos se registran al ingreso y quién está autorizado para hacerlo.
2. Qué categorías de diario se utilizan y cuáles deben convertirse en incidencias.
3. Qué tipos, niveles y estados de incidencia existen en el centro.
4. Qué datos y estados se requieren para salidas, visitas y retornos.
5. Cómo se preparan y reciben actualmente los traspasos de turno.
6. Qué tareas deben asignarse a una persona y cuáles a un equipo o turno.
7. Qué estructura y periodicidad tiene el PEI y quién puede revisarlo o aprobarlo.
8. Qué información escolar se registra realmente.
9. Qué perfiles pueden consultar, registrar y exportar datos sanitarios.
10. Qué documentos se incorporan, quién puede verlos y qué política de conservación se aplica.
11. Qué informes se necesitan habitualmente y quién puede generarlos.
12. Qué avisos son imprescindibles en el panel de inicio.

Las respuestas se incorporarán a este documento antes de cerrar el diseño funcional.
