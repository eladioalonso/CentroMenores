# Modelo conceptual de datos

## 1. Finalidad

Este documento describe las principales entidades de información y sus relaciones. Es un modelo conceptual inicial, previo al diseño físico de tablas y a la implementación. Debe validarse con los profesionales del centro y ajustarse a las obligaciones de protección de datos y conservación documental.

El modelo evita duplicidades, conserva el histórico y permite que un mismo acontecimiento o documento esté relacionado con varios registros sin almacenar copias innecesarias.

## 2. Entidades principales

### 2.1. Menor

Representa la identidad única de cada menor atendido por el centro.

- Tiene una ficha única.
- No se crea una ficha nueva por cada ingreso o reingreso.
- Se relaciona con sus estancias, anotaciones, incidencias, actividades, seguimientos, documentos y demás registros autorizados.
- Los datos identificativos se limitarán a los necesarios y su acceso dependerá de permisos.

### 2.2. Estancia

Representa un periodo concreto de ingreso o atención residencial.

- Pertenece a un único menor.
- Un menor puede tener varias estancias a lo largo del tiempo.
- Cada reingreso genera una nueva estancia.
- Los registros vinculados a una estancia conservan esa relación aunque la estancia finalice.
- La estancia no sustituye ni duplica la ficha personal.

### 2.3. Profesional y cuenta de usuario

Conviene distinguir la identidad profesional de las credenciales de acceso.

- El profesional representa a la persona que trabaja en el centro.
- La cuenta permite iniciar sesión y se asocia a un profesional.
- Una cuenta puede estar activa, bloqueada o deshabilitada sin borrar la autoría histórica de sus registros.
- Los permisos se asignan a través de roles y, cuando sea necesario, permisos específicos.

### 2.4. Anotación del diario profesional

Representa una entrada única de la cronología general del centro.

- Tiene fecha y hora de creación, autor y contenido.
- Puede tener fecha y hora del acontecimiento, que no tienen por qué coincidir con las de creación.
- Puede ser general del centro, sin menores relacionados.
- Puede relacionarse con uno o varios menores.
- Puede relacionarse con la estancia correspondiente de cada menor cuando proceda.
- Tiene una categoría configurable.
- Se muestra una sola vez en la cronología general, aunque esté relacionada con varios menores.
- Sus rectificaciones deben mantener trazabilidad; no se debe sobrescribir silenciosamente el contenido histórico.

La relación entre anotaciones y menores es de muchos a muchos: una anotación puede relacionarse con varios menores y cada menor puede tener muchas anotaciones.

### 2.5. Incidencia

Representa un acontecimiento que requiere registro y seguimiento específico.

- Puede implicar a uno o varios menores.
- Puede relacionarse con uno o varios profesionales.
- Puede tener actuaciones, documentos y tareas de seguimiento.
- Conserva fecha, hora, lugar, clasificación, descripción, estado y autoría.
- Puede estar relacionada con una anotación del diario que haya originado su apertura, sin duplicar innecesariamente el relato.

### 2.6. Actividad y participación

La actividad representa una acción planificada o realizada por el centro.

- Una actividad puede tener varios participantes.
- Cada participación se registra de forma individual para distinguir asistencia, ausencia y observaciones propias.
- La participación enlaza una actividad con un menor y, cuando proceda, con su estancia.

### 2.7. Seguimiento educativo y PEI

Se separan los documentos o planes vigentes de los registros de seguimiento.

- El PEI dispone de versiones con fechas de vigencia y estado.
- Los objetivos pertenecen a una versión concreta del plan.
- Las actuaciones y evaluaciones se registran como elementos históricos.
- Una nueva versión no elimina las anteriores.

### 2.8. Salida, visita y retorno

Representa un movimiento o ausencia temporal.

- Se relaciona con uno o varios menores según el caso.
- Distingue datos previstos de datos reales.
- Conserva responsable, tipo, estado y horas de salida y retorno.
- No se cierra automáticamente por el mero transcurso de la hora prevista.

### 2.9. Documento

Representa un archivo almacenado una sola vez y sus metadatos.

- El archivo físico se conserva en el repositorio documental interno.
- Los metadatos describen categoría, título, fechas, autoría y clasificación.
- Un documento puede relacionarse con varios menores y con otros registros.
- Las relaciones no generan copias del archivo.
- Los permisos deben proteger tanto los metadatos como el contenido del archivo.

### 2.10. Tarea y traspaso

La tarea representa una acción pendiente o asignada.

- Puede tener responsable individual o colectivo, según se defina.
- Puede estar relacionada con una incidencia, anotación, actividad u otro registro.
- Conserva prioridad, estado, fechas y resultado.

El traspaso representa información operativa comunicada entre turnos.

- Tiene autor, fecha y hora.
- Puede referenciar tareas, incidencias y otros registros existentes.
- La confirmación de lectura no equivale a completar ni resolver los asuntos referenciados.

### 2.11. Información sanitaria

La información sanitaria se modelará separada de los datos generales.

- Se relaciona con el menor correspondiente.
- Puede incluir referencias a centros y profesionales sanitarios, datos de cobertura y documentos, únicamente en el alcance que autorice el centro.
- Tendrá permisos reforzados.
- No se replicará en anotaciones generales, paneles o notificaciones sin necesidad y autorización.

### 2.12. Auditoría

Registra las operaciones relevantes realizadas en la aplicación.

- Usuario o profesional que realiza la operación.
- Fecha y hora.
- Tipo de operación.
- Registro afectado.
- Resultado y motivo cuando proceda.

La auditoría debe permitir reconstruir cambios relevantes sin convertirse en una vía para conceder acceso indiscriminado al contenido sensible.

## 3. Relaciones principales

| Relación | Cardinalidad conceptual | Regla |
|---|---|---|
| Menor – Estancia | 1 a muchos | Un menor puede tener varias estancias históricas |
| Menor – Anotación | muchos a muchos | Una anotación puede afectar a varios menores |
| Anotación – Estancia | mediante relación | Se conserva la estancia de cada menor cuando corresponda |
| Menor – Incidencia | muchos a muchos | Una incidencia puede implicar a varios menores |
| Incidencia – Profesional | muchos a muchos | Se registran los profesionales intervinientes |
| Actividad – Menor | muchos a muchos | La participación se registra individualmente |
| Menor – Documento | muchos a muchos | El archivo se almacena una sola vez |
| Registro – Documento | muchos a muchos | Un documento puede respaldar varios registros |
| Incidencia – Tarea | uno a muchos | Una incidencia puede generar tareas de seguimiento |
| Profesional – Anotación | uno a muchos | Cada anotación tiene un autor |
| Profesional – Cuenta | uno a uno o uno a ninguno | La identidad profesional no depende de que la cuenta siga activa |

Las cardinalidades definitivas y las excepciones deberán concretarse durante el diseño técnico.

## 4. Reglas de integridad

1. No duplicar la ficha de un menor.
2. No reutilizar una estancia finalizada para representar un reingreso.
3. No duplicar una anotación porque afecte a varios menores.
4. No duplicar archivos por relacionarlos con varios expedientes o registros.
5. Mantener las relaciones históricas aunque un registro cambie de estado.
6. No eliminar físicamente registros históricos mediante operaciones ordinarias.
7. Aplicar permisos en las consultas, pantallas, búsquedas, documentos y exportaciones.
8. Conservar autoría y marcas temporales de las operaciones relevantes.
9. Utilizar identificadores internos estables; no utilizar nombres como claves de relación.
10. Definir qué datos admiten corrección, versionado o cierre, y quién puede realizar esas operaciones.

## 5. Decisiones pendientes antes del modelo físico

- Determinar los campos mínimos de la ficha del menor.
- Definir los datos propios de cada estancia.
- Confirmar si una anotación puede vincularse a menores sin estancia activa y cómo se representa esa situación.
- Definir las categorías del diario y los criterios para abrir una incidencia.
- Concretar los datos de profesionales, cuentas, roles y permisos.
- Determinar qué módulos necesitan versionado completo.
- Definir metadatos, formatos y límites de los documentos.
- Establecer la política de conservación, rectificación, bloqueo y eliminación.
- Validar el tratamiento separado de información sanitaria.
- Confirmar los requisitos de informes y exportaciones.

## 6. Protección de datos durante el diseño

Este modelo no autoriza por sí mismo la recogida de todos los campos mencionados. El centro deberá justificar la finalidad y necesidad de cada dato, limitar el acceso y establecer plazos de conservación. Se utilizarán exclusivamente datos ficticios en el desarrollo y las pruebas. La revisión jurídica y de protección de datos deberá realizarse antes de utilizar información real.


> **Especificación vigente:** consultar [Decisiones consolidadas del diseño](DECISIONES_CONSOLIDADAS.md). Este documento reúne las decisiones aprobadas más recientes y prevalece sobre cualquier apartado anterior que las contradiga.
