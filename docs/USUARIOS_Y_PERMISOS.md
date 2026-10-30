# Usuarios, perfiles y permisos

## 1. Objetivo

El ordenador será compartido por varios profesionales que trabajan por turnos. La aplicación debe identificar a cada persona y atribuirle sus operaciones, sin utilizar cuentas compartidas.

Los perfiles descritos aquí son una propuesta inicial. Los permisos definitivos deberán validarse con la dirección del centro y ajustarse a las funciones reales de cada puesto.

## 2. Perfiles iniciales

| Perfil | Finalidad |
|---|---|
| Dirección | Supervisión general y autorización de funciones administrativas |
| Coordinación | Organización y seguimiento operativo |
| Educador | Trabajo cotidiano, anotaciones, actividades y seguimiento educativo |
| Personal sanitario autorizado | Acceso limitado a la información sanitaria cuando corresponda |
| Consulta | Lectura de información expresamente autorizada |
| Administrador técnico | Mantenimiento técnico y configuración de la aplicación |

Una misma persona podrá tener más de una función si la organización lo autoriza, pero se evitarán privilegios innecesarios.

## 3. Permisos por operación

Los permisos no se limitarán a permitir u ocultar módulos. Se definirán acciones independientes, por ejemplo:

- Consultar.
- Crear.
- Modificar.
- Cerrar o finalizar.
- Exportar o imprimir.
- Administrar usuarios y permisos.
- Gestionar copias y restauraciones.

La autorización se comprobará en los servicios de aplicación antes de ejecutar la operación y acceder a los datos protegidos.

## 4. Protección reforzada del área sanitaria

- El acceso estará limitado a usuarios expresamente autorizados.
- Consultar, modificar, adjuntar, exportar e imprimir información sanitaria podrán ser permisos distintos.
- Los documentos sanitarios heredarán restricciones equivalentes o más estrictas.
- Los paneles, búsquedas e informes no mostrarán datos sanitarios a usuarios sin autorización.
- Los accesos y operaciones relevantes quedarán registrados.
- No se incluirán datos sanitarios en notificaciones generales, mensajes de error ni registros técnicos.

## 5. Identificación y sesión

- Cada profesional tendrá una cuenta individual.
- Las contraseñas se almacenarán mediante hash seguro, nunca en texto claro.
- Se contemplará el cambio y restablecimiento controlado de contraseña.
- La sesión se bloqueará tras un periodo configurable de inactividad.
- El usuario podrá cerrar sesión al terminar su turno.
- La aplicación ofrecerá un cambio de usuario que cierre la sesión anterior antes de iniciar otra.
- Los errores de autenticación no revelarán si una cuenta existe o está bloqueada más allá de lo necesario para orientar al usuario.

## 6. Auditoría

Se registrarán, según la política que se defina:

- Inicios y cierres de sesión y fallos de autenticación.
- Altas, modificaciones, cierres y operaciones de eliminación.
- Consultas o exportaciones de información especialmente sensible, cuando sea viable y proporcionado.
- Cambios de permisos y configuración.
- Copias y restauraciones.

Cada evento incluirá como mínimo usuario, fecha/hora, tipo de operación y referencia al registro afectado cuando corresponda. Se evitará copiar el contenido sensible completo dentro del registro de auditoría.

La auditoría no deberá poder alterarse desde las pantallas ordinarias de trabajo. Se definirán permisos y plazos de conservación para estos registros.

## 7. Matriz inicial orientativa

La siguiente matriz no concede automáticamente permisos: sirve como punto de partida para el análisis con el centro.

| Área | Dirección | Coordinación | Educador | Sanitario autorizado | Consulta |
|---|---|---|---|---|---|
| Ficha personal | Según autorización | Trabajo operativo | Trabajo operativo | Datos necesarios | Lectura autorizada |
| Estancias | Supervisión | Gestión | Consulta/registro autorizado | Datos necesarios | Lectura autorizada |
| Diario profesional | Supervisión autorizada | Gestión autorizada | Crear y consultar según asignación | Solo si procede | No por defecto |
| Incidencias | Supervisión | Seguimiento | Registrar y consultar según función | Solo si procede | No por defecto |
| Salidas y visitas | Supervisión | Gestión | Gestión operativa autorizada | No por defecto | Lectura autorizada |
| PEI y seguimiento | Supervisión autorizada | Coordinación | Intervención autorizada | No por defecto | No por defecto |
| Escolaridad | Supervisión autorizada | Gestión autorizada | Seguimiento autorizado | No por defecto | Lectura autorizada |
| Actividades | Supervisión | Planificación | Gestión operativa | No por defecto | Lectura autorizada |
| Área sanitaria | Solo si tiene autorización expresa | No por defecto | No por defecto | Según autorización | No |
| Usuarios y permisos | Administración autorizada | No por defecto | No | No | No |
| Auditoría | Según autorización | Consulta limitada si procede | No | No | No |

El administrador técnico no tendrá acceso automático al contenido sanitario por el mero hecho de mantener la aplicación. La separación real de ese acceso en un programa local deberá analizarse teniendo en cuenta que quien controla el equipo y sus archivos puede tener capacidades técnicas superiores a las de un usuario ordinario.

## 8. Administración de permisos

- Aplicar el principio de mínimo privilegio.
- Permitir retirar permisos cuando cambien las funciones de una persona.
- Registrar los cambios de roles y permisos.
- Evitar permisos implícitos por pertenecer a un grupo amplio.
- Revisar periódicamente las cuentas activas.
- Desactivar cuentas cuando una persona deje de necesitar acceso.
- No permitir que un usuario ordinario se otorgue privilegios a sí mismo.

## 9. Decisiones pendientes

Antes de implementar el sistema se deberá confirmar:

1. Qué puestos y funciones existen realmente en el centro.
2. Qué personas pueden acceder a cada módulo y a cada menor.
3. Quién puede consultar, modificar, exportar y cerrar registros.
4. Qué perfiles están autorizados para el área sanitaria y con qué alcance.
5. Quién puede crear usuarios, bloquearlos y restablecer contraseñas.
6. Qué eventos se auditan y durante cuánto tiempo se conservan.
7. Cómo se gestionan las ausencias, sustituciones y cambios de puesto.
