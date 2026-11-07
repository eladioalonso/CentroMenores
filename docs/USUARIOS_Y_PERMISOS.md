# Usuarios, perfiles y permisos

## 1. Objetivo

El ordenador será compartido por varios educadores que trabajan por turnos. La aplicación debe identificar a cada persona y atribuirle sus operaciones, sin utilizar cuentas compartidas.

La estructura de perfiles confirmada inicialmente por el centro es sencilla: todos los educadores tienen las mismas funciones. Además, una persona (el responsable del sistema) tendrá permisos adicionales de administración técnica.

## 2. Perfiles confirmados

### Educador

Todos los educadores utilizarán el mismo perfil y dispondrán de las mismas funciones ordinarias, de acuerdo con las autorizaciones y reglas generales de protección de datos del centro.

Las funciones ordinarias previstas incluyen el trabajo con menores y estancias, diario profesional, incidencias, salidas y visitas, actividades, seguimiento educativo, escolaridad, tareas y traspasos, y consulta de la documentación necesaria para su trabajo.

No habrá categorías de educadores ni niveles diferentes de permisos entre ellos en esta primera definición.

### Administrador del sistema

El responsable del sistema tendrá su perfil ordinario de educador y, además, permisos adicionales para administrar técnicamente la aplicación.

Entre las funciones adicionales previstas:
- Crear, activar, bloquear y desactivar cuentas de usuario.
- Gestionar credenciales y restablecimientos de acceso.
- Administrar roles y permisos de la aplicación.
- Configurar catálogos y parámetros generales.
- Realizar tareas de mantenimiento.
- Gestionar copias de seguridad y restauraciones.
- Consultar los registros técnicos y de auditoría según la política que se establezca.

Los permisos de administración son aditivos: no sustituyen ni eliminan las funciones ordinarias de educador.

La administración técnica no concede automáticamente acceso al contenido sanitario. El administrador puede asignar o retirar expresamente el permiso sanitario a una cuenta; cada cambio queda auditado. Al tratarse de una aplicación local, habrá que analizar las limitaciones de separación frente a quien tenga control administrativo del ordenador y de los archivos.

## 3. Permisos por operación

Aunque todos los educadores compartan el mismo perfil, los permisos se definirán por tipo de operación cuando sea necesario, por ejemplo:

- Consultar.
- Crear.
- Modificar o rectificar.
- Cerrar o finalizar.
- Exportar o imprimir.
- Administrar usuarios y permisos.
- Gestionar copias y restauraciones.

La autorización se comprobará en los servicios de aplicación antes de ejecutar la operación y acceder a los datos protegidos. Las restricciones legales o de confidencialidad se aplicarán con independencia de que los educadores compartan perfil.

## 4. Diario profesional: autoría, consulta y rectificaciones

El diario profesional será visible para todos los educadores autorizados, pero la autoría de cada anotación debe quedar protegida.

- **Consulta:** todos los educadores pueden consultar las anotaciones del diario, respetando las restricciones de acceso que se definan para información especialmente sensible.
- **Anotación propia:** el autor podrá corregir sus propias anotaciones únicamente mientras permanezca abierto el turno completo al que pertenecen. El turno ordinario descrito por el centro comprende una tarde (15:00–22:00), la mañana siguiente (08:00–15:00) y la noche siguiente (22:00–08:00 del día posterior). Para permitir prolongaciones excepcionales por falta de sustitución, el cierre podrá realizarse manualmente al terminar realmente el servicio o, si no se realiza, se ejecutará automáticamente al cumplirse 48 horas desde el inicio del turno. Ese plazo es un límite absoluto. Las correcciones realizadas antes del cierre serán trazables y nunca sobrescribirán silenciosamente el contenido original.
- **Anotación ajena:** otro educador no podrá editar ni sustituir el texto original.
- **Matización:** cualquier educador autorizado podrá añadir una matización o comentario vinculado a una anotación ajena. La matización será un registro independiente, con su propio autor, fecha y hora; el texto original permanecerá intacto.
- **Rectificación posterior al cierre o de una anotación ajena:** si se detecta un error una vez finalizado el turno de 48 horas, el autor tampoco podrá modificar la anotación original. Deberá añadir una rectificación vinculada, indicando quién la realiza, cuándo y el motivo. La rectificación no borrará el texto original.
- **Historial:** la consulta de una anotación permitirá distinguir el texto original, sus correcciones por el autor y las matizaciones o rectificaciones añadidas por otros profesionales.
- **Trazabilidad:** todas las operaciones conservarán identidad del usuario, fecha/hora y relación con la anotación afectada. El sistema deberá asociar cada anotación al turno completo correspondiente. El turno podrá cerrarse mediante una acción expresa del educador responsable o de un administrador autorizado cuando el servicio haya terminado realmente; si nadie lo cierra, el sistema lo cerrará automáticamente al cumplirse 48 horas desde su inicio. El cierre manual podrá adelantar el bloqueo, pero nunca ampliar el límite absoluto.

La aplicación deberá distinguir claramente una matización (información complementaria) de una rectificación (señalar o corregir un dato erróneo). Los permisos para exportar o imprimir el diario se definirán por separado.

## 4 bis. Edición de registros propios y rectificaciones

Como regla general, el profesional que crea un registro podrá corregirlo directamente, sin esperar al administrador, mientras el registro esté en estado editable y no exista una restricción específica del módulo.

- La edición de un registro propio no cambia su autoría original.
- Cada modificación registrará usuario, fecha/hora, registro afectado y versión o diferencias necesarias para reconstruir el contenido anterior.
- Otro educador no podrá sobrescribir el contenido original de un registro ajeno. Podrá incorporar una aportación, matización o rectificación vinculada, según las funciones del módulo.
- Los registros cerrados, validados, firmados o enviados oficialmente se corregirán mediante una rectificación vinculada, con el motivo requerido y conservación íntegra del original.
- El administrador no tendrá que autorizar ni ejecutar las correcciones ordinarias del autor. La administración y supervisión se mantendrán separadas de la autoría.
- Cada módulo concretará sus estados editables y excepciones. Para el diario se mantiene la regla específica: el autor corrige durante el periodo de apertura del turno, hasta un máximo absoluto de 48 horas; después se incorpora una rectificación vinculada.

## 5. Protección reforzada del área sanitaria

- El acceso estará limitado a usuarios expresamente autorizados mediante el permiso independiente «Acceso sanitario» de cada cuenta. El permiso está desactivado por defecto, también para administradores técnicos.
- En esta versión, el permiso sanitario habilita conjuntamente la ficha sanitaria y la gestión de documentos sanitarios. La separación de consulta, modificación, adjuntos, exportación e impresión en permisos distintos queda pendiente.
- Los documentos sanitarios heredarán restricciones equivalentes o más estrictas.
- Los paneles, búsquedas e informes no mostrarán datos sanitarios a usuarios sin autorización.
- La ficha del expediente ocultará los campos sanitarios (CIP, centro de salud, facultativos, caducidad e historial clínico), su edición y el acceso a ficha sanitaria y medicación cuando falte el permiso.
- En el diario se filtrarán las anotaciones de categoría sanitaria y las incidencias de salud; su alta, rectificación y gestión también exigirán autorización.
- Las citas de vacunación quedarán ocultas en agenda y calendario y no podrán crearse ni modificarse sin permiso sanitario.
- Las autorizaciones médicas y las salidas sanitarias se filtrarán en las consultas y exigirán permiso para su gestión.
- Los accesos y operaciones relevantes quedarán registrados.
- No se incluirán datos sanitarios en notificaciones generales, mensajes de error ni registros técnicos.

La función técnica de concesión y retirada del permiso está implementada y auditada. La designación de las cuentas autorizadas y la validación de su alcance corresponde al centro y sigue pendiente de aprobación institucional.

## 6. Identificación y sesión

- Cada profesional tendrá una cuenta individual.
- Las contraseñas se almacenarán mediante hash seguro, nunca en texto claro.
- Cada profesional puede cambiar su propia contraseña verificando la actual; el administrador puede realizar un restablecimiento controlado.
- La sesión se bloqueará tras un periodo configurable de inactividad.
- El usuario podrá cerrar sesión al terminar su turno.
- La aplicación ofrecerá un cambio de usuario que cierre la sesión anterior antes de iniciar otra.
- Los errores de autenticación no revelarán información innecesaria sobre las cuentas.

## 7. Auditoría

Se registrarán, según la política que se defina:

- Inicios y cierres de sesión y fallos de autenticación.
- Altas, modificaciones, rectificaciones, cierres y operaciones de eliminación.
- Consultas o exportaciones de información especialmente sensible, cuando sea viable y proporcionado.
- Cambios de permisos y configuración.
- Copias y restauraciones.

Cada evento incluirá como mínimo usuario, fecha/hora, tipo de operación y referencia al registro afectado cuando corresponda. Se evitará copiar el contenido sensible completo dentro del registro de auditoría.

La consulta de auditoría está disponible solo para administradores, con filtro por fechas; cada consulta también queda registrada. La interfaz es de solo lectura. Se definirán los permisos institucionales y plazos de conservación definitivos.

## 8. Principios de administración

- Aplicar el principio de mínimo privilegio.
- Registrar los cambios de roles y permisos.
- Evitar permisos implícitos que no estén documentados.
- Revisar periódicamente las cuentas activas.
- Desactivar cuentas cuando una persona deje de necesitar acceso.
- No permitir que un educador ordinario se otorgue privilegios administrativos.
- Mantener separadas, en la medida técnicamente viable, las funciones de administración del sistema y el acceso a información especialmente sensible.

## 9. Decisiones pendientes

Antes de implementar el sistema se deberá confirmar:

1. Si existen otros perfiles profesionales que deban tener acceso a la aplicación, además de educadores y administrador del sistema.
2. Qué autorizaciones concretas tendrá cada educador sobre los distintos módulos y registros.
3. Qué personas estarán autorizadas para acceder al área sanitaria y con qué alcance.
4. Si el administrador del sistema podrá consultar información operativa o si sus permisos se limitarán a la administración técnica, salvo que también actúe como educador.
5. Quién puede consultar, modificar, exportar y cerrar cada tipo de registro, incluida la autorización para cerrar manualmente un turno.
6. Qué eventos se auditan y durante cuánto tiempo se conservan.
7. Cómo se gestionan las ausencias, sustituciones y bajas de usuarios.


> **Especificación vigente:** consultar [Decisiones consolidadas del diseño](DECISIONES_CONSOLIDADAS.md). Este documento reúne las decisiones aprobadas más recientes y prevalece sobre cualquier apartado anterior que las contradiga.


## Acceso de lectura a módulos compartidos

Las consultas de agenda, comunicaciones, aportaciones, objetivos educativos, historial escolar y registros escolares requieren una cuenta activa desde sus servicios de dominio. Las lecturas quedan registradas en la auditoría de acceso. La consulta del historial educativo admite estancias cerradas para preservar el acceso autorizado a antecedentes; las operaciones de alta siguen exigiendo estancia activa cuando corresponde.

Las consultas de expedientes, diario, autorizaciones, salidas y calendario aplican además el permiso sanitario cuando el contenido corresponde a información de salud. Las lecturas sanitarias autorizadas quedan registradas; las lecturas generales filtran anotaciones de salud, autorizaciones médicas, salidas sanitarias y citas de vacunación.
