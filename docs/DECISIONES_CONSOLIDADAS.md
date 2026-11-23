# Decisiones consolidadas del diseño

**Estado:** especificación funcional aprobada y en implementación.  
**Ámbito:** aplicación local de gestión interna de un centro de menores.  
**Rama de implementación:** `desarrollo/nucleo-aplicacion`.

Este documento reúne las decisiones aprobadas durante el diseño y prevalece sobre cualquier descripción anterior que las contradiga. La programación ha sido autorizada por el usuario en la rama de implementación. Las cuestiones marcadas como pendientes requieren validación antes de utilizar datos reales.

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

## 9. Organización funcional simplificada

La aplicación tendrá **dos apartados principales de trabajo**:

1. **Información del menor.** Una ficha única con tres secciones: datos generales (nombre, apellidos, sexo, fecha y lugar de nacimiento, país de nacimiento, nacionalidad, dirección actual, código postal, NIF/NIE, email y teléfono móvil); información sanitaria (CIP, fecha de emisión y caducidad de tarjeta, centro de salud, facultativo, enfermería, enfermedades y tratamientos); y documentos escaneados.
2. **Parte diario / Calendario.** Registro cronológico único por fecha, organizado en cuatro apartados: actividades realizadas en el día, comportamientos positivos, comportamientos negativos y observaciones. Cada anotación conserva fecha/hora, autoría y, cuando corresponda, vínculos con uno o varios menores. No se solicita personal ni se separan actividades por turnos en el formulario diario. Las altas y bajas se consultan desde el historial de estancias del expediente. El calendario queda integrado en este apartado.

El inicio/panel general puede mantenerse como pantalla de entrada, pero no es un módulo funcional adicional. Administración, usuarios, permisos, copias, restauración, mantenimiento y configuración son herramientas técnicas reservadas al administrador.

La información sanitaria deja de mostrarse como módulo independiente y se integra en la ficha del menor. Se conservarán los datos sanitarios existentes, el historial de versiones, y el detalle clínico o de medicación que ya esté registrado, sin duplicarlo en el parte diario.

Las funciones anteriores que no aparecen en esta estructura dejarán de ocupar la navegación o las pantallas de uso cotidiano. Los registros históricos se conservarán durante la simplificación y no se eliminarán automáticamente.

Reglas comunes:
- La ficha del menor será el punto único de consulta de sus datos generales, sanitarios y documentos.
- El parte diario será la fuente cronológica de actividad, hechos y continuidad entre turnos.
- Todos los educadores activos podrán consultar y actualizar la información ordinaria, con autoría, auditoría e historial de rectificaciones.
- Los registros cerrados podrán corregirse mediante una nueva versión, conservando el original y el motivo.
- La información se introducirá una sola vez y se reutilizará mediante vínculos, evitando duplicidades.

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

## 13. Fases de implementación

La implementación continúa en `desarrollo/nucleo-aplicacion`. Estado de las fases:

1. **Completada:** navegación de cuatro módulos y permisos ordinarios compartidos.
2. **Completada en el núcleo funcional:** edición y trazabilidad de expedientes principales y sanitarios; continúa la revisión integral de casos límite.
3. **Completada en el núcleo funcional:** parte diario como fuente cronológica, rectificaciones vinculadas e integración de incidencias históricas sin duplicación deliberada.
4. **Completada en el núcleo funcional:** borradores persistentes, emisión, rectificación, historial de versiones y exportación de informes desde el parte diario.
5. **Completada en la navegación:** agenda, documentación, seguimiento educativo, escolaridad, salidas, visitas y autorizaciones quedan integrados en los módulos principales.
6. **En validación:** migraciones, integridad de datos, copias, restauración y comprobaciones de la compilación Windows. Las pruebas automatizadas de migración y copia/restauración deben complementarse con validación operativa en Windows.
7. **En validación:** la batería automatizada alcanza 135 pruebas superadas y existe una compilación portable generada; queda la prueba funcional del usuario con datos ficticios y la revisión final antes de declarar una versión candidata.

Los cambios se realizan de forma incremental, sin borrar información histórica ni modificar datos de usuario de forma destructiva. Una compilación de desarrollo no se considerará definitiva hasta superar las pruebas, la validación funcional y la revisión de seguridad.


## 14. Decisiones técnicas aprobadas en la revisión

Estas decisiones complementan las decisiones funcionales anteriores y guían la implementación incremental autorizada.

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


## Vacunación individual y calendario oficial

- El historial vacunal pertenece al expediente sanitario permanente de cada menor y se relaciona directamente con su identificador de expediente (`minor_id`). No pertenece a una estancia concreta; la estancia, si se conoce, se conserva únicamente como contexto histórico opcional.
- Cada menor tendrá su propio seguimiento de vacunas y dosis: previstas/recomendadas, pendientes, administradas, aplazadas, contraindicadas o no administradas, con motivo y trazabilidad.
- El calendario de referencia principal será el oficial de la Ciudad Autónoma de Melilla. Se conservará también la referencia al calendario común del Sistema Nacional de Salud para contextualizar equivalencias y cambios.
- La configuración del calendario será versionada por fecha de vigencia y fuente oficial. No se sobrescribirán reglas antiguas: el calendario aplicable dependerá de la cohorte/fecha de nacimiento y de la pauta individual documentada.
- Las recomendaciones por grupos de riesgo o situaciones especiales se mostrarán separadas del calendario sistemático y no se activarán automáticamente por inferencia. Requerirán condición documentada y validación sanitaria.
- La aplicación podrá calcular edades/fechas orientativas y señalar dosis pendientes, pero no prescribirá ni decidirá por sí misma vacunas, productos, intervalos clínicos, contraindicaciones o pautas de rescate. Toda pauta individual debe contrastarse con el profesional sanitario y el documento oficial vigente.
- Cada administración registrada será un evento inmutable con vacuna, dosis, fecha, profesional/centro sanitario si consta, lote y fabricante si se dispone, fuente documental y autor del registro en la aplicación. Las correcciones se harán mediante rectificación vinculada, sin borrar el evento original.
- Las vacunas administradas fuera del centro o antes del ingreso podrán incorporarse al expediente con su fecha real y procedencia documental; no se exigirá estancia activa.
- Se mantendrá la separación entre calendario recomendado, pauta individual del menor y administración efectivamente realizada.
