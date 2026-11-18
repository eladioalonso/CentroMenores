# Usuarios, perfiles y permisos

## 1. Objetivo

El ordenador será compartido por varios educadores que trabajan por turnos. La aplicación debe identificar a cada persona y atribuirle sus operaciones, sin utilizar cuentas compartidas.

La estructura de perfiles confirmada inicialmente por el centro es sencilla: todos los educadores tienen las mismas funciones. Además, una persona (el responsable del sistema) tendrá permisos adicionales de administración técnica.

## 2. Perfiles confirmados

### Educador

Todos los educadores utilizarán el mismo perfil y dispondrán de las mismas funciones ordinarias, de acuerdo con las autorizaciones y reglas generales de protección de datos del centro.

Las funciones ordinarias se organizan exclusivamente en cuatro módulos: expediente principal del menor, expediente sanitario del menor, parte diario e informes de incidencias generados desde el parte. Las herramientas de agenda, documentación, salidas, visitas, seguimiento educativo y escolaridad se integran dentro del expediente o del trabajo diario, sin constituir módulos adicionales.

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

La ficha sanitaria está disponible para todos los educadores activos, de acuerdo con la decisión funcional vigente. El administrador conserva además sus funciones técnicas. Al tratarse de una aplicación local, habrá que analizar las limitaciones de separación frente a quien tenga control administrativo del ordenador y de los archivos.

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

## 4. Parte diario: edición compartida y trazabilidad

Todos los educadores activos pueden consultar, crear y modificar cualquier anotación del parte diario, con independencia de quién la haya registrado y de que el día esté cerrado.

- La autoría original de cada versión se conserva como dato histórico.
- Una modificación crea una nueva versión vinculada a la anotación anterior; nunca sobrescribe silenciosamente el contenido previo.
- Cada modificación registra el educador que la realiza, fecha y hora, registro afectado y motivo indicado por el usuario.
- El cierre del día impide añadir nuevas anotaciones ordinarias a esa fecha, pero no impide revisar o corregir anotaciones ya existentes.
- Las rectificaciones posteriores se conservan vinculadas al original y pueden ser realizadas por cualquier educador activo.
- La consulta debe permitir distinguir el contenido original y sus versiones posteriores, identificando quién realizó cada cambio.
- Las incidencias y los informes generados desde el parte diario seguirán las mismas reglas de edición compartida, con conservación de versiones emitidas oficialmente.

El cierre de un parte diario es una regla de organización del registro, no una restricción de autoría ni un bloqueo de corrección. El administrador no será intermediario obligatorio para modificar información.

## 4 bis. Edición compartida en los cuatro módulos

Todos los educadores activos tienen las mismas capacidades ordinarias en los cuatro módulos funcionales:

1. Expediente principal del menor.
2. Expediente sanitario del menor.
3. Parte diario.
4. Informes de incidencias.

Pueden consultar, crear y modificar información de cualquiera de esos módulos, incluidos registros creados por otros educadores. La aplicación conservará la autoría de cada versión y la trazabilidad de las modificaciones.

Las excepciones se limitan a funciones técnicas de administración y a la conservación de documentos oficialmente emitidos: un informe ya remitido no se altera retroactivamente; se genera una versión rectificada que mantiene la anterior.

## 5. Acceso al área sanitaria: implementación vigente

La decisión funcional más reciente permite que todos los educadores activos consulten la información sanitaria y registren las actuaciones que corresponden a su trabajo. No se exige una autorización sanitaria individual ni que el administrador habilite previamente a cada educador.

- La ficha sanitaria, la medicación y la vacunación están vinculadas al expediente del menor.
- Las operaciones sanitarias relevantes y las consultas protegidas quedan registradas en auditoría.
- Los datos sanitarios no deben duplicarse en el diario; este puede mostrar un resumen de tratamientos activos procedente de la ficha sanitaria.
- El antiguo campo técnico `health_access` permanece en la base de datos por compatibilidad con versiones anteriores, pero no bloquea el acceso de los educadores activos.
- El perfil Educador no obtiene por ello funciones de administración técnica, copias o restauración.
- La autorización institucional, la minimización de datos, la revisión de roles y la aprobación de protección de datos siguen siendo requisitos previos a cualquier uso con información real.

La interfaz y los servicios aplicarán las mismas capacidades ordinarias a todos los educadores activos. No se restringirá la edición por autoría, turno o cierre del parte. Las operaciones técnicas de administración, copias y restauración permanecen reservadas al administrador.
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

## 9. Validaciones institucionales pendientes

Las decisiones funcionales sobre perfiles ya están aprobadas: Educadores y Administrador. Todos los educadores activos tienen las mismas capacidades ordinarias en los cuatro módulos, incluida la consulta y edición del expediente sanitario. No está pendiente decidir si los educadores pueden acceder a salud ni si pueden corregir registros de otros autores.

Antes de usar datos reales, la entidad responsable debe validar:
1. Qué profesionales, además de educadores y administrador técnico, deben tener cuenta.
2. Qué protocolos institucionales regulan el acceso a información personal y sanitaria.
3. Qué operaciones requieren autorización institucional específica, por ejemplo exportaciones, impresiones o recuperación de copias.
4. Qué eventos se auditan, quién puede consultar la auditoría y durante cuánto tiempo se conserva.
5. Cómo se gestionan altas, bajas, sustituciones y revisiones periódicas de cuentas.
6. Quién custodia el equipo, la carpeta de datos y los soportes de copia.
7. La adecuación de perfiles y permisos a la normativa y a las instrucciones de la Administración competente.

Estas validaciones no deben reintroducir restricciones de edición por autor, turno o cierre del parte, salvo que exista una nueva decisión expresa y documentada del centro.
 
> **Especificación vigente:** consultar [Decisiones consolidadas del diseño](DECISIONES_CONSOLIDADAS.md). Este documento reúne las decisiones aprobadas más recientes y prevalece sobre cualquier apartado anterior que las contradiga.


## Aplicación uniforme de permisos en los módulos

Los servicios de aplicación deben comprobar que la cuenta y el profesional estén activos, pero no deben limitar la consulta o edición ordinaria según el autor del registro, el turno o el cierre del día. Esta regla se aplica a expedientes principales, expedientes sanitarios, parte diario e informes de incidencias.

La administración técnica (usuarios, configuración, copias y restauraciones) continúa reservada al administrador. Los permisos administrativos no son necesarios para que un educador consulte o modifique información ordinaria de los cuatro módulos.

Toda modificación debe generar una nueva versión o una rectificación vinculada y registrar usuario, fecha/hora, registro afectado y motivo cuando corresponda. Las consultas sanitarias protegidas y las exportaciones seguirán registrándose en auditoría.
