# Decisiones consolidadas del diseño

**Estado:** especificación funcional consolidada para revisión.  
**Ámbito:** aplicación local de gestión interna de un centro de menores.  
**Rama documental:** `documentacion/planteamiento-inicial`.

Este documento reúne las decisiones aprobadas durante el diseño y prevalece sobre cualquier descripción anterior que las contradiga. No autoriza todavía el inicio de la programación. Las cuestiones marcadas como pendientes requieren validación antes de utilizar datos reales.

## 1. Alcance, despliegue y uso

- Aplicación de escritorio Windows, portable, de uso local y sin conexión a Internet obligatoria.
- Un único ordenador de trabajo en el centro; los educadores lo utilizan por turnos con cuentas individuales.
- Tecnologías propuestas: Python, PySide6, SQLite, SQLAlchemy, Alembic y PyInstaller en modo `onedir`.
- Toda la información persistente estará dentro de la carpeta de la aplicación: base de datos, documentos, fotografías, configuración, registros y copias locales. No dependerá de AppData ni de rutas personales.
- No se permitirá que dos instancias utilicen simultáneamente la misma carpeta/base de datos.
- SQLite no se utilizará desde una carpeta de red ni se compartirá para escrituras simultáneas entre equipos.
- La comunicación opcional con móviles se hará mediante navegador y Wi-Fi local, con QR/códigos temporales y controles de acceso; no requiere instalar una app móvil. La viabilidad concreta deberá probarse en la red del centro.
- No se desarrollará un módulo de Servicios Generales ni de mantenimiento del edificio.
- No se incluirá un sistema de actualización automática ni un apartado de actualización dentro de la aplicación. Una eventual sustitución manual futura requerirá copia previa y procedimiento controlado.
- La interfaz será sencilla, moderna y discreta, con tema claro/oscuro por usuario, menú lateral compacto, panel general común y ayuda contextual.

## 2. Perfiles, autenticación y sesiones

Solo existen dos perfiles: **Administrador** y **Educadores**. Todos los educadores tienen las mismas capacidades ordinarias; no hay jerarquías de educadores ni privilegios especiales por turno. El administrador tiene acceso completo a los módulos y funciones de administración, con todas sus acciones auditadas.

- Cada persona utiliza su propia cuenta. No se comparten credenciales.
- Las contraseñas se almacenan mediante hash seguro, nunca en texto claro. Esto no implica cifrar la base de datos.
- Tras **5 intentos consecutivos** de contraseña incorrecta se cerrará la sesión activa o el flujo de autenticación en curso; no se bloqueará la cuenta y se podrá volver a intentar.
- Tras **15 minutos de inactividad**, la sesión se bloqueará y exigirá de nuevo la contraseña.
- Al cerrar la aplicación se cerrará automáticamente la sesión.
- El administrador puede crear/desactivar usuarios y restablecer contraseñas; no puede consultar las contraseñas existentes.
- El panel principal tendrá la misma estructura para todos; los datos y acciones visibles dependerán de los permisos aplicables.
- Todos los educadores pueden consultar y aportar en los módulos ordinarios acordados. La ficha sanitaria está disponible para todos los educadores según el alcance funcional aprobado, y el administrador tiene acceso completo.

## 3. Administración y continuidad

La aplicación incluirá:
- Cambio de administrador desde la propia aplicación, manteniendo usuarios, permisos, auditoría e historial.
- Desactivación de la cuenta del administrador saliente sin borrar su autoría histórica.
- Procedimiento de recuperación administrativa si el administrador no está disponible, mediante una persona autorizada por la dirección.
- Continuidad de acceso a las copias y a la aplicación sin depender de la contraseña personal del administrador anterior.
- Registro auditado de designación, transferencia, recuperación y desactivación.

La custodia institucional de la carpeta y de los USB será responsabilidad del centro, no de una persona concreta.

## 4. Seguridad, privacidad y cifrado

Decisión funcional expresa: **no se incorporará cifrado adicional de la base de datos, documentos ni copias de seguridad**, ni contraseñas independientes para abrir las copias. Las copias USB podrán abrirse directamente desde otro ordenador y contendrán una copia completa portable.

Consecuencias que deben quedar visibles en la documentación y en la formación:
- Cualquier persona que obtenga una copia USB o acceso a la carpeta de datos podrá leer los datos contenidos en ella.
- El centro deberá controlar físicamente el ordenador y los USB, limitar el acceso a la carpeta de Windows y definir quién puede custodiar y transportar las copias.
- El control de acceso dentro de la aplicación no protege los archivos frente a una persona con acceso directo suficiente al sistema de archivos o privilegios administrativos de Windows.
- No se almacenarán contraseñas de usuario en texto claro; se utilizará hash seguro.
- No se incluirán datos reales de menores en el repositorio, pruebas, ejemplos ni informes técnicos de diagnóstico.
- Se evitarán datos personales o sanitarios en notificaciones generales, mensajes de error y logs técnicos.

No se debe describir la solución como cifrada ni como invulnerable frente a administradores del equipo. La protección se basa en cuentas individuales, permisos de aplicación, seguridad de Windows, control físico y procedimientos del centro.

## 5. Auditoría y alertas

El administrador podrá consultar una auditoría de accesos y actividad:
- Inicios y cierres de sesión, fallos de autenticación y cierres automáticos.
- Cambios y restablecimientos de contraseña (sin registrar la contraseña).
- Expedientes consultados, registros creados/modificados/rectificados, documentos abiertos/exportados, informes generados y operaciones de copia/restauración.
- Consultas de comunicaciones confidenciales y accesos de emergencia.
- Usuario, fecha/hora, tipo de acción, resultado y referencia al registro afectado, evitando duplicar innecesariamente contenido sensible.

La auditoría tendrá apartado propio, filtros por usuario, fechas, módulo, acción y expediente, y exportación PDF/Excel. Las consultas y exportaciones de auditoría también se registrarán. La aplicación no ofrecerá edición o borrado ordinario de eventos de auditoría.

- La auditoría tendrá copias de respaldo independientes de las copias generales.
- Una restauración general conservará la auditoría más reciente, incluidos los eventos posteriores a la copia restaurada.
- Se conservará el estado actual antes de restaurar y se registrará la operación.
- El administrador recibirá alertas persistentes hasta revisarlas y marcarlas como atendidas, conservando el historial.
- Umbral de alerta: más de **20 documentos o expedientes exportados en 10 minutos**.
- Umbral de alerta: consulta de más de **30 expedientes diferentes en 10 minutos**.
- Los umbrales generan avisos, no bloqueos automáticos ni una conclusión automática de conducta indebida.
- Los accesos de emergencia generan alerta y revisión administrativa obligatoria.

**Límite técnico:** en una aplicación local sin cifrado, una persona con control suficiente del equipo y de los archivos podría manipular datos fuera de la aplicación. La auditoría podrá diseñarse como registro de solo anexado, con controles de integridad y copias separadas, pero no debe prometerse inmutabilidad absoluta frente a quien controle el ordenador y todos sus soportes.

La conservación se ajustará a una política aprobada y a los plazos legales aplicables. No se establecerá conservación indefinida por defecto sin revisión normativa.

## 6. Acceso de emergencia

Todos los educadores podrán activar el procedimiento excepcional (*break glass*) sin depender de la presencia del administrador, exclusivamente ante una necesidad real y urgente.

- Motivo/justificación obligatoria.
- Aviso visible de que se está usando un permiso excepcional.
- Acceso limitado en alcance y duración, con caducidad automática.
- Consulta de información sanitaria necesaria (alergias graves, medicación activa, antecedentes relevantes, tratamientos especiales), teléfonos de familiares/tutores, autorizaciones y restricciones vigentes y documentación identificativa esencial (NIE, pasaporte, tarjeta sanitaria, etc.) cuando sea necesaria.
- No anula automáticamente prohibiciones ni restricciones legales de contacto o salida.
- Cada acceso registra usuario, fecha/hora, duración, expediente, datos consultados, motivo y actuaciones declaradas.
- El administrador recibe aviso y debe revisar y cerrar formalmente cada caso, marcándolo justificado o solicitando aclaraciones. Los casos que requieren aclaración permanecen abiertos.
- La revisión y cualquier actuación posterior también quedan auditadas.
- El acceso excepcional de consulta no concede por sí mismo permiso para alterar prescripciones, autorizaciones o registros.

## 7. Copias, restauración y migración

### Copias
- Copias automáticas diarias: conservar las últimas **30**.
- Copias manuales: sin límite de 30, con nombre/descripción y metadatos de autor, fecha, hora, tamaño, ubicación e integridad.
- Copia previa a cualquier operación manual de mantenimiento o sustitución de la aplicación que pueda afectar a datos.
- Copia local en otra carpeta del mismo PC y segunda ubicación externa configurable (USB).
- Si el USB no está conectado, se realiza la copia local y se marca la externa como pendiente; al detectar el dispositivo se completa y verifica sin duplicar una copia válida del mismo estado.
- Las copias USB son **sin cifrado**, directamente legibles y contienen la carpeta completa de datos necesaria para recuperar el centro.
- Las copias deben incluir base de datos, documentos, fotografías, auditoría y configuración/datos necesarios para la recuperación. No se copiará una base SQLite activa mediante una copia ordinaria de archivos ignorando WAL u otros auxiliares: se usará SQLite Backup API o se cerrará la aplicación correctamente.

### Restauración
- Restauración siempre integral, nunca por módulos.
- Asistente desde la interfaz: selección, verificación de integridad/compatibilidad, copia preventiva del estado actual, restauración controlada y verificación de base de datos, relaciones y archivos.
- Antes de restaurar se identificarán los registros/documentos posteriores a la fecha de la copia. Se conservará la auditoría más reciente y se evitará perder trabajo posterior mediante un procedimiento de reconciliación revisado; no se mezclarán automáticamente datos incompatibles.
- Si no puede garantizarse una reconciliación segura, la aplicación detendrá la restauración y solicitará intervención autorizada.
- Registrar quién, cuándo, origen, resultado y verificaciones.

### Migración
- La carpeta portable podrá trasladarse a otro ordenador Windows compatible, con la aplicación cerrada.
- Asistente para restaurar en otro equipo desde USB, conservando usuarios, hash de contraseñas, permisos, expedientes, documentos, fotografías, auditoría y configuración.
- Comprobación automática de usuarios, permisos, expedientes, relaciones, documentos, fotografías, auditoría, base de datos y funcionamiento.
- La migración no se marcará finalizada mientras haya errores sin resolver.
- Comprobar espacio disponible y permisos de escritura antes de operar.

## 8. Mantenimiento y diagnóstico

- Comprobación de espacio al iniciar y vigilancia durante el uso; avisos ante espacio insuficiente para trabajar, adjuntar archivos o crear copias.
- Apartado de mantenimiento para consultar el espacio ocupado por base de datos, documentos, fotografías y copias, localizar archivos grandes y revisar la evolución.
- Limpieza de temporales, restos de operaciones interrumpidas y archivos auxiliares no necesarios. Nunca eliminar automáticamente expedientes, documentos, fotografías, registros históricos ni auditoría.
- Diagnóstico automático y completo manual por el administrador: base de datos, relaciones, carpetas, permisos, adjuntos, copias, espacio y estado general.
- Los informes técnicos no contendrán datos identificativos, sanitarios ni contenido de menores. Si se necesitara soporte con datos reales, deberá autorizarse y minimizarse separadamente.

## 9. Módulos funcionales acordados

La aplicación incluye:
1. Panel general.
2. Usuarios, permisos, sesiones y administración.
3. Menores, ficha única, expedientes y estancias independientes.
4. Familiares, contactos y restricciones.
5. Diario profesional único por fecha, dividido en mañana/tarde/noche.
6. Comunicaciones internas, incluidas comunicaciones confidenciales.
7. Borradores compartidos y recuperación de formularios interrumpidos.
8. Seguimiento educativo, objetivos, logros e informes.
9. Área sanitaria, episodios, medicación, vacunación, citas e informes.
10. Escolaridad y reuniones/seguimiento escolar.
11. Actividades grupales e individuales.
12. Agenda única, tareas y avisos.
13. Salidas, visitas, contactos y retornos.
14. Documentación y autorizaciones.
15. Informes oficiales y solicitudes externas, con verificación de autorización.
16. Estadísticas y memorias para administrador.
17. Recepción y consulta de archivos desde móviles por navegador y Wi-Fi local.
18. Auditoría, alertas y acceso de emergencia.
19. Copias, restauración, migración, mantenimiento y diagnóstico.
20. Ayuda integrada y modo de demostración con datos ficticios y restablecimiento independiente.

No se incluye módulo de Servicios Generales/mantenimiento del edificio. El libro de mantenimiento del centro queda fuera de la aplicación.

### Reglas transversales
### Autoría, edición y rectificación de registros
- Como regla general, el profesional que crea un registro podrá corregir y modificar sus propios registros directamente, sin necesitar la intervención del administrador, mientras el registro permanezca editable y no exista una restricción específica.
- La autoría no se transfiere por el hecho de que otro profesional consulte el registro. Otro educador no podrá sobrescribir el contenido original de un registro ajeno; podrá añadir una aportación, matización o rectificación vinculada cuando el módulo lo permita.
- Toda modificación conservará trazabilidad: usuario que la realiza, fecha y hora, registro afectado y diferencias o versión anterior suficiente para reconstruir qué se modificó. Nunca se sobrescribirá silenciosamente información ya registrada.
- Cuando un registro esté cerrado, validado, firmado, enviado oficialmente o sujeto a una regla específica de inalterabilidad, no se reabrirá para editarlo ordinariamente. Se añadirá una rectificación vinculada, con motivo obligatorio cuando corresponda, conservando íntegro el original.
- El administrador no será intermediario obligatorio para las correcciones ordinarias de los autores. Sus facultades de supervisión y administración no sustituyen la autoría ni eliminan la trazabilidad.
- Cada módulo deberá definir sus estados editables, los límites temporales y los procedimientos de rectificación. Se mantienen las reglas especiales ya acordadas para el diario profesional (autoría propia y ventana de corrección limitada al cierre del turno, con máximo absoluto de 48 horas).
- Antes de habilitar la edición de un tipo de registro se comprobarán conflictos de edición, permisos, historial de versiones, auditoría y recuperación ante fallos.

- Ficha única por menor; cada reingreso crea nueva estancia.
- No duplicar información: el módulo de origen es el registro principal; otros módulos enlazan o muestran resúmenes.
- Diferenciar fecha/hora del hecho y fecha/hora de registro.
- Correcciones, matizaciones y rectificaciones conservan el original y su trazabilidad.
- No registrar como definitivo un borrador ni una recuperación temporal sin confirmación expresa.
- El diario es un libro único compartido por fecha y tres turnos; cierre manual o automático a las 48 horas desde el inicio del turno, límite absoluto.
- Los borradores compartidos no se asignan a una persona; cualquier educador puede continuar y cerrar/reabrir con trazabilidad. Papelera: 2 meses. Recuperaciones temporales: 7 días.
- El ciclo del educador sigue el patrón de turnos acordado; turno actual se detecta por calendario/horario con corrección manual trazable.
- Los informes se generan solo con información necesaria, autorizada y revisada antes de entregar.
- No se automatizan diagnósticos, prescripciones ni valoraciones educativas.

## 10. Ayuda y formación

- Manual integrado con explicaciones sencillas por módulo, procedimientos paso a paso, ejemplos ficticios, solución de problemas y búsqueda contextual.
- Guía rápida para nuevos educadores.
- Modo de demostración completamente separado de los datos reales, con menores y registros ficticios.
- Botón para restablecer todos los datos de demostración al estado inicial sin afectar a la base real.

## 11. Política de conservación provisional

Criterios funcionales acordados, sujetos a validación normativa:
- Expedientes y documentación: según plazos legales e instrucciones de la Administración competente.
- Auditoría: sin borrado automático mientras no exista política de conservación/eliminación autorizada y revisada.
- Borradores en papelera: máximo 2 meses.
- Recuperaciones temporales: máximo 7 días.
- Copias automáticas diarias: últimas 30; copias manuales y previas a cambios, según política aprobada.
- Las copias de respaldo no sustituyen la política legal de conservación del expediente.

## 12. Pendientes antes de usar datos reales

1. Revisar RGPD, LOPDGDD, normativa española y autonómica aplicable al centro, instrucciones de la Administración competente, plazos de conservación y necesidad de evaluación de impacto.
2. Validar con dirección y delegado de protección de datos la decisión de mantener copias USB sin cifrado, su custodia física y los permisos Windows. La decisión funcional de no cifrar se mantiene, pero sus riesgos deben quedar aceptados institucionalmente.
3. Definir el procedimiento institucional y las personas autorizadas para la recuperación administrativa.
4. Probar el flujo de acceso de emergencia, la caducidad, el alcance de consulta y revisión posterior.
5. Definir umbrales/criterios complementarios de alertas y cómo se evitarán falsos positivos.
6. Diseñar y probar reconciliación de datos posteriores a una copia restaurada; nunca prometer una fusión automática universal.
7. Confirmar las condiciones de red Wi-Fi, firewall y dispositivos para el portal móvil local.
8. Definir los campos concretos de fichas, catálogos, informes y permisos por operación.
9. Validar la estructura final de la carpeta portable y pruebas de restauración/migración en Windows limpio.
10. Establecer política institucional de custodia del ordenador, carpeta portable y USB.

## 13. Fases propuestas de desarrollo (no iniciadas)

1. Base técnica, cuentas, permisos, auditoría, sesiones, configuración y copias.
2. Panel, turnos, diario, comunicaciones y borradores.
3. Fichas, estancias, familiares, restricciones, documentos y autorizaciones.
4. Sanidad, medicación, vacunación y episodios.
5. Seguimiento educativo, escolaridad y actividades.
6. Agenda, tareas, salidas y contactos.
7. Informes, estadísticas y memorias.
8. Móvil local, ayuda, demostración y validación integral.

**No iniciar programación ni modificar código hasta recibir aprobación expresa del usuario después de revisar esta documentación y el plan técnico.**


## 14. Decisiones técnicas aprobadas en la revisión

Estas decisiones complementan las decisiones funcionales anteriores y quedan aprobadas para la fase de diseño técnico. No autorizan por sí solas el inicio de la programación.

### SQLite y acceso concurrente

- Usar SQLite inicialmente en modo de diario **DELETE**; no activar WAL en la configuración inicial.
- Configurar `synchronous=FULL`, `foreign_keys=ON` en cada conexión y un `busy_timeout` razonable y configurable.
- Utilizar transacciones para operaciones relacionadas. Las operaciones de escritura deben ser breves; no mantener transacciones abiertas mientras una persona rellena un formulario.
- Mantener una única instancia de la aplicación por carpeta/base de datos y centralizar el mecanismo de escritura.
- Detectar conflictos cuando dos usuarios intenten modificar el mismo registro y evitar sobrescrituras silenciosas.
- No compartir la base SQLite por red ni permitir escrituras desde varios equipos.

### Guardado y recuperación de formularios

- Guardado automático progresivo en almacenamiento temporal, separado del registro definitivo.
- La incorporación definitiva de información requiere que el usuario pulse Guardar o confirme expresamente la operación.
- Los datos temporales se asocian al usuario y formulario, se pueden revisar antes de recuperar y caducan a los 7 días.
- Un borrador o formulario recuperado nunca se convierte automáticamente en un registro oficial.
- La aplicación comprobará al iniciar si hubo un cierre inesperado, verificará la base de datos y los adjuntos, detectará operaciones interrumpidas y ofrecerá recuperación controlada.
- No se harán reparaciones destructivas ni se eliminarán datos dudosos silenciosamente.

### Copias completas y consistentes

- Las copias completas podrán ejecutarse con la aplicación abierta mediante un procedimiento coordinado y consistente, incluyendo base de datos, documentos, fotografías, auditoría y configuración necesaria.
- Para SQLite se utilizará el mecanismo de copia consistente (SQLite Backup API o equivalente probado); nunca se copiará una base activa ignorando archivos auxiliares.
- Cada copia se verificará antes de marcarse como válida. Los fallos quedarán registrados y no se presentarán como copias correctas.
- La base de datos y sus archivos adjuntos deben representar un mismo estado lógico. El procedimiento deberá coordinar escrituras y adjuntos durante la copia.
- La auditoría tendrá respaldo independiente y una restauración general no hará retroceder ni perder los eventos de auditoría más recientes.

### Documentos y fotografías

- Los documentos y fotografías se guardarán como archivos independientes de SQLite, dentro de la carpeta portable.
- Se utilizarán identificadores internos únicos y rutas relativas; los nombres físicos no incluirán nombres de menores.
- Se comprobará la integridad mediante hash.
- La incorporación seguirá un procedimiento seguro: escritura temporal, verificación y vinculación definitiva; se detectarán restos y archivos huérfanos sin borrarlos automáticamente cuando exista duda.

### Auditoría

- Los eventos de auditoría registrarán, como mínimo, usuario, fecha/hora, operación, resultado y referencia al registro afectado; se añadirá motivo cuando proceda.
- La auditoría se mantendrá separada de los datos operativos, con controles de integridad y copias propias.
- No habrá edición ni borrado ordinario de eventos.
- Se mantiene expresamente la limitación: sin cifrado y con control administrativo del ordenador y sus archivos, no puede garantizarse inmutabilidad absoluta.

### Ubicación y despliegue

- La carpeta activa se ubicará en una ruta local independiente y escribible, por ejemplo `C:\\CentroMenores`.
- No se utilizarán como ubicación activa `Program Files`, carpetas de red ni carpetas sincronizadas por OneDrive, Dropbox u otros servicios.
- La carpeta portable podrá trasladarse a otro ordenador con la aplicación cerrada y tras verificar la copia.

### Pruebas obligatorias antes de producción

Ninguna versión se considerará preparada para producción hasta superar pruebas con datos ficticios, incluyendo cierres forzados durante escrituras, apagados simulados, recuperación de formularios, restauración integral, migración a otro equipo, adjuntos ausentes/dañados/duplicados, conflictos de edición, fallos durante copias, permisos, auditoría y volúmenes representativos de información.
