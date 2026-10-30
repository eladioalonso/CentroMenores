# Planteamiento del proyecto

## 1. Finalidad

Gestión del Centro será una aplicación de escritorio para organizar la actividad interna de un centro de menores. Su finalidad es reunir en un único sistema la información operativa y profesional necesaria para el trabajo cotidiano, evitando duplicidades y conservando un historial fiable.

La aplicación se utilizará localmente en un ordenador Windows compartido por varios educadores que trabajan por turnos. Cada profesional accederá con su propia cuenta.

## 2. Alcance

### Incluido

- Fichas personales únicas de los menores.
- Registro de ingresos, reingresos, estancias y bajas del centro.
- Área sanitaria con acceso especialmente restringido.
- Diario profesional.
- Incidencias y seguimiento de actuaciones.
- Salidas, visitas, autorizaciones internas y retornos.
- Seguimiento educativo y Proyecto Educativo Individual (PEI).
- Escolaridad y formación.
- Planificación y registro de actividades.
- Tareas, turnos y traspasos de información entre equipos.
- Archivo documental centralizado.
- Panel de situación, informes y estadísticas.
- Administración de usuarios, permisos, configuración, auditoría y copias de seguridad.

### Fuera del alcance inicial

La aplicación se limitará a la actividad interna del centro. No gestionará los procedimientos administrativos externos de protección de menores ni pretende sustituir los sistemas oficiales de organismos públicos. Si en el futuro se desea incorporar alguna función de ese tipo, deberá aprobarse y especificarse como una ampliación independiente.

## 3. Principios funcionales

1. **Ficha única:** cada menor tendrá una única identidad dentro de la aplicación.
2. **Estancias independientes:** un menor podrá tener varias estancias a lo largo del tiempo. Cada ingreso o reingreso tendrá sus propias fechas y su propio historial.
3. **Histórico preservado:** cerrar una estancia no borrará sus registros ni alterará los datos históricos.
4. **Dato único:** la información personal se mantendrá en su módulo de origen y los demás módulos la consultarán mediante relaciones.
5. **Relaciones explícitas:** una incidencia, actividad o documento podrá relacionarse con varios menores cuando corresponda, sin recurrir a listas de nombres en campos de texto.
6. **Trazabilidad:** las operaciones relevantes identificarán al usuario y la fecha/hora; las rectificaciones no ocultarán el registro original.
7. **Permisos por función:** cada usuario accederá únicamente a las funciones y datos autorizados.
8. **Protección reforzada:** la información sanitaria tendrá permisos más restrictivos que el resto de la información.
9. **Información coherente:** paneles e informes se calcularán a partir de los registros originales, sin mantener copias manuales de los mismos datos.
10. **Uso sencillo:** la interfaz estará pensada para profesionales que no necesitan conocimientos técnicos.

## 4. Usuarios y forma de trabajo

El mismo ordenador podrá ser utilizado por varios educadores en distintos turnos. Cada uno deberá iniciar sesión con su propia cuenta; no se compartirán credenciales. La aplicación deberá bloquear la sesión tras un periodo configurable de inactividad y permitir un cambio de usuario claro y rápido.

El diseño inicial contempla un único proceso de aplicación y una única base de datos local. No se considera que varios ordenadores vayan a modificar simultáneamente una base de datos compartida por red.

## 5. Módulos funcionales

La descripción detallada de cada módulo está en [MODULOS.md](MODULOS.md). Los módulos principales son:

- Menores y expedientes.
- Estancias.
- Área sanitaria.
- Diario profesional.
- Incidencias.
- Salidas, visitas y retornos.
- Seguimiento educativo y PEI.
- Escolaridad y formación.
- Actividades.
- Tareas, turnos y traspasos.
- Documentación.
- Panel de control.
- Informes y estadísticas.
- Administración, usuarios, permisos y auditoría.

## 6. Criterios de aceptación generales

Antes de considerar lista una versión funcional, deberá comprobarse que:

- Los datos personales de un menor se mantienen en una sola ficha.
- Se pueden registrar varios ingresos del mismo menor sin perder los anteriores.
- Los registros relacionados aparecen en los historiales y consultas correspondientes.
- Los permisos se aplican también al intentar acceder a datos desde operaciones internas, no solo ocultando botones.
- La información sanitaria no queda accesible a perfiles no autorizados.
- Las operaciones importantes quedan registradas.
- Las copias se pueden restaurar y se comprueba su integridad.
- La aplicación puede ejecutarse desde una carpeta portable en otro equipo Windows compatible.
- El programa no necesita que los educadores instalen Python ni bibliotecas.
- La aplicación funciona sin conexión a Internet.

## 7. Desarrollo por fases

1. Confirmación del alcance, flujos de trabajo y reglas del centro.
2. Diseño del modelo de datos y de los permisos.
3. Base de la aplicación: inicio de sesión, configuración local, auditoría y copias.
4. Menores y estancias.
5. Área sanitaria y documentación.
6. Diario profesional e incidencias.
7. Salidas, visitas y retornos.
8. Seguimiento educativo, PEI y escolaridad.
9. Actividades, tareas, turnos y traspasos.
10. Panel, informes, pruebas, empaquetado y documentación de uso.

Las fases podrán ajustarse después de revisar el programa existente y validar los procedimientos reales del centro.

## 8. Protección de datos

Se aplicarán desde el diseño los principios de minimización, limitación de finalidad, confidencialidad, integridad, disponibilidad y responsabilidad proactiva. Antes de utilizar datos reales deberán revisarse las obligaciones aplicables, los perfiles de acceso, los plazos de conservación, las copias de seguridad y la necesidad de una evaluación de impacto.

El desarrollo y las pruebas utilizarán exclusivamente datos ficticios. No se subirán al repositorio expedientes reales, documentos identificativos, información sanitaria, credenciales ni bases de datos del centro.
