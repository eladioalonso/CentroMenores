# Planteamiento del proyecto

## 1. Finalidad

Gestión del Centro es una aplicación de escritorio local para organizar la actividad interna de un centro de protección de menores. Reúne la información necesaria para el trabajo cotidiano de los educadores, evita duplicidades y conserva un historial trazable.

La aplicación se utilizará en un ordenador Windows compartido por educadores que trabajan por turnos. Cada profesional accede con su propia cuenta. No se requiere servidor central ni escritura simultánea desde varios ordenadores.

## 2. Alcance funcional aprobado

La aplicación tendrá exactamente cuatro módulos de trabajo:

1. **Expediente principal del menor:** identidad, datos personales, estancias e ingresos/reingresos, seguimiento educativo, escolaridad, documentos, autorizaciones, visitas, restricciones, salidas y retornos.
2. **Expediente sanitario del menor:** ficha sanitaria, antecedentes, consultas y urgencias, tratamientos, medicación, administraciones, vacunación, revisiones y documentación sanitaria. Está vinculado a la ficha única del menor.
3. **Parte diario:** cronología compartida por fecha y turnos, educadores, altas/bajas, actividades, observaciones, conductas positivas y negativas y hechos relevantes.
4. **Informes de incidencias:** selección de anotaciones del parte diario, elaboración de borradores, revisión, emisión, rectificación e historial de versiones.

Inicio es un panel de entrada y resumen, no un módulo adicional. Administración es un área técnica reservada al administrador, no un módulo de trabajo para educadores.

No se incorporarán como módulos funcionales independientes comunicaciones, registro duplicado de incidencias, informes externos genéricos ni áreas paralelas de actividades o documentación. Las funciones necesarias se integran en los cuatro módulos aprobados.

## 3. Principios funcionales

1. **Ficha única:** cada menor tiene una identidad única dentro de la aplicación.
2. **Estancias independientes:** cada ingreso o reingreso crea un nuevo periodo, sin duplicar ni sobrescribir la ficha.
3. **Histórico preservado:** cerrar una estancia no elimina sus registros.
4. **Dato único:** la información se registra en su módulo de origen y se reutiliza mediante relaciones.
5. **Parte diario como fuente factual:** un acontecimiento se registra una vez en la cronología; un informe selecciona y enlaza los hechos, sin crear un segundo registro independiente del mismo acontecimiento.
6. **Edición compartida:** todos los educadores activos pueden consultar, crear y modificar la información ordinaria de los cuatro módulos, aunque el registro lo haya creado otro educador.
7. **Trazabilidad:** las rectificaciones conservan versiones anteriores, autoría, fecha/hora y motivo cuando corresponda.
8. **Acceso sanitario para educadores:** todos los educadores activos pueden consultar y actualizar la información sanitaria ordinaria conforme a los protocolos institucionales. Las operaciones relevantes quedan auditadas.
9. **Sencillez:** la interfaz debe ser comprensible para profesionales sin conocimientos técnicos avanzados.
10. **Protección de datos:** las decisiones sobre acceso, conservación, exportación y custodia deben validarse institucionalmente antes de usar datos reales.

## 4. Usuarios y forma de trabajo

Hay dos perfiles:
- **Educadores:** mismas capacidades ordinarias de consulta, creación y modificación en los cuatro módulos.
- **Administrador:** capacidades ordinarias de educador y, además, administración técnica de cuentas, configuración, copias, restauración, mantenimiento y auditoría.

Cada profesional utiliza una cuenta individual. No se comparten credenciales. La aplicación permite cerrar sesión y cambiar de usuario, y bloquea la sesión tras un periodo de inactividad configurable.

## 5. Plataforma y despliegue

- Aplicación de escritorio para Windows.
- Distribución portable autocontenida; el usuario final no instala Python ni bibliotecas.
- Base de datos SQLite local.
- Documentos y adjuntos dentro de la carpeta de la aplicación/datos.
- Funcionamiento sin conexión a Internet.
- Una sola instancia por carpeta de datos.
- No compartir la base SQLite por red.
- Copias verificables y restauración controlada.

La estructura y los límites de seguridad se detallan en [Arquitectura](ARQUITECTURA.md) y [Seguridad y despliegue](SEGURIDAD_DESPLIEGUE.md).

## 6. Criterios de aceptación funcional

- La identidad del menor se mantiene en una ficha única.
- Se pueden registrar varios ingresos sin perder los anteriores.
- La información sanitaria permanece vinculada al menor aunque no tenga estancia activa.
- Los educadores pueden consultar y modificar registros de otros educadores, conservando versiones.
- El parte diario mantiene una cronología única y permite rectificaciones posteriores.
- Los informes se generan desde anotaciones seleccionadas expresamente y conservan las versiones emitidas.
- Los documentos y relaciones se conservan al cerrar una estancia.
- La aplicación funciona desde una carpeta portable en Windows sin instalar dependencias.
- Las copias se verifican y pueden restaurarse en un entorno aislado.
- Las pruebas funcionales se realizan exclusivamente con datos ficticios.

## 7. Protección de datos y límites

El desarrollo y las pruebas utilizan datos ficticios. No se suben al repositorio expedientes reales, documentos identificativos, información sanitaria, credenciales ni bases de datos del centro.

Antes de usar datos reales, la entidad responsable debe revisar normativa aplicable, finalidad y base jurídica, perfiles de acceso, plazos de conservación, custodia del equipo y soportes, copias, auditoría y necesidad de evaluación de impacto. La aplicación no sustituye los sistemas oficiales ni los protocolos administrativos, educativos o sanitarios del centro.

## 8. Documentación vigente

- [Decisiones consolidadas](DECISIONES_CONSOLIDADAS.md): fuente de requisitos aprobados.
- [Módulos](MODULOS.md): alcance de cada módulo.
- [Flujos de trabajo](FLUJOS_DE_TRABAJO.md): recorridos operativos.
- [Usuarios y permisos](USUARIOS_Y_PERMISOS.md): perfiles y edición compartida.
- [Pruebas manuales](PRUEBAS_MANUALES.md): validación en Windows con datos ficticios.
- [Seguridad y despliegue](SEGURIDAD_DESPLIEGUE.md): límites y requisitos previos a producción.
