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

La administración técnica no debe conceder automáticamente acceso al contenido sanitario. Ese acceso requiere una autorización específica. No obstante, al tratarse de una aplicación local, habrá que analizar las limitaciones de separación frente a quien tenga control administrativo del ordenador y de los archivos.

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

## 4. Protección reforzada del área sanitaria

- El acceso estará limitado a usuarios expresamente autorizados.
- Consultar, modificar, adjuntar, exportar e imprimir información sanitaria podrán ser permisos distintos.
- Los documentos sanitarios heredarán restricciones equivalentes o más estrictas.
- Los paneles, búsquedas e informes no mostrarán datos sanitarios a usuarios sin autorización.
- Los accesos y operaciones relevantes quedarán registrados.
- No se incluirán datos sanitarios en notificaciones generales, mensajes de error ni registros técnicos.

La asignación concreta de autorizaciones sanitarias queda pendiente de validación por el centro.

## 5. Identificación y sesión

- Cada profesional tendrá una cuenta individual.
- Las contraseñas se almacenarán mediante hash seguro, nunca en texto claro.
- Se contemplará el cambio y restablecimiento controlado de contraseña.
- La sesión se bloqueará tras un periodo configurable de inactividad.
- El usuario podrá cerrar sesión al terminar su turno.
- La aplicación ofrecerá un cambio de usuario que cierre la sesión anterior antes de iniciar otra.
- Los errores de autenticación no revelarán información innecesaria sobre las cuentas.

## 6. Auditoría

Se registrarán, según la política que se defina:

- Inicios y cierres de sesión y fallos de autenticación.
- Altas, modificaciones, rectificaciones, cierres y operaciones de eliminación.
- Consultas o exportaciones de información especialmente sensible, cuando sea viable y proporcionado.
- Cambios de permisos y configuración.
- Copias y restauraciones.

Cada evento incluirá como mínimo usuario, fecha/hora, tipo de operación y referencia al registro afectado cuando corresponda. Se evitará copiar el contenido sensible completo dentro del registro de auditoría.

La auditoría no deberá poder alterarse desde las pantallas ordinarias de trabajo. Se definirán permisos y plazos de conservación para estos registros.

## 7. Principios de administración

- Aplicar el principio de mínimo privilegio.
- Registrar los cambios de roles y permisos.
- Evitar permisos implícitos que no estén documentados.
- Revisar periódicamente las cuentas activas.
- Desactivar cuentas cuando una persona deje de necesitar acceso.
- No permitir que un educador ordinario se otorgue privilegios administrativos.
- Mantener separadas, en la medida técnicamente viable, las funciones de administración del sistema y el acceso a información especialmente sensible.

## 8. Decisiones pendientes

Antes de implementar el sistema se deberá confirmar:

1. Si existen otros perfiles profesionales que deban tener acceso a la aplicación, además de educadores y administrador del sistema.
2. Qué autorizaciones concretas tendrá cada educador sobre los distintos módulos y registros.
3. Qué personas estarán autorizadas para acceder al área sanitaria y con qué alcance.
4. Si el administrador del sistema podrá consultar información operativa o si sus permisos se limitarán a la administración técnica, salvo que también actúe como educador.
5. Quién puede consultar, modificar, exportar y cerrar cada tipo de registro.
6. Qué eventos se auditan y durante cuánto tiempo se conservan.
7. Cómo se gestionan las ausencias, sustituciones y bajas de usuarios.
