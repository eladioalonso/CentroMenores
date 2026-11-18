# Modelo conceptual de datos

## 1. Finalidad

Este documento describe las entidades persistentes que sostienen los cuatro módulos funcionales. El modelo mantiene una identidad única del menor, separa las estancias de la trayectoria permanente y evita duplicar acontecimientos o documentos.

El esquema físico vigente se implementa mediante SQLAlchemy y migraciones Alembic. Para los requisitos funcionales prevalece [Decisiones consolidadas](DECISIONES_CONSOLIDADAS.md).

## 2. Identidad y estancias

### Menor

Representa la identidad única de cada menor. Incluye datos personales y de identificación. No se crea una ficha nueva por cada ingreso o reingreso.

### Estancia

Representa un periodo concreto de ingreso. Pertenece a un menor y tiene número de secuencia, fechas y estado. Un menor puede tener varias estancias. Cerrar una estancia no elimina la ficha ni sus registros históricos.

Las anotaciones, documentos y movimientos pueden relacionarse con una estancia cuando sea necesario conservar el contexto temporal. La información sanitaria permanente se relaciona directamente con el menor.

## 3. Módulo 1: expediente principal

### Datos personales e historial

Los datos identificativos se guardan una sola vez en la entidad Menor. Las modificaciones personales relevantes pueden conservar versiones con autor, fecha/hora y valores anteriores/nuevos.

### Educación y escolaridad

- Los objetivos educativos pertenecen al expediente/estancia correspondiente.
- Las actualizaciones de seguimiento se conservan como registros históricos versionables.
- Las escolarizaciones tienen periodos, centro, curso y registros asociados.
- Una rectificación no elimina la actualización original.

### Documentación

Los archivos se almacenan una sola vez en el repositorio local. Sus metadatos conservan categoría, título, nombre físico seguro, hash, versión, fechas y autoría. Se relacionan con el menor y/o la estancia según corresponda.

### Autorizaciones, visitas y salidas

Las autorizaciones conservan vigencia, estado, alcance y trazabilidad. Las salidas y retornos distinguen horas previstas y reales, destino, responsable, estado y vínculos con menores/estancias.

## 4. Módulo 2: expediente sanitario

### Perfil sanitario

La ficha sanitaria pertenece al menor, no a una estancia. Incluye CIP, centro de salud, facultativo, enfermería, vigencia de tarjeta, antecedentes, alergias, condiciones relevantes e instrucciones de emergencia. Los cambios se conservan en un historial versionado.

### Medicación

- La pauta prescrita se relaciona con el menor y puede conservar el vínculo a la estancia en la que se registró.
- Los horarios diarios son entidades relacionadas con la pauta.
- Las administraciones registran hora prevista, resultado, nota, autor y fecha de registro.
- Las rectificaciones de administraciones crean versiones que conservan los valores anteriores.

### Vacunación

- Los registros de administración se relacionan directamente con el menor.
- Cada registro puede vincularse a un elemento del catálogo documental y a un justificante.
- Se conservan vacuna, dosis, fecha, fabricante, producto, lote, centro/profesional y autoría cuando consten.
- Las revisiones individuales de dosis son registros separados y repetibles, con estado, fecha, profesional y fundamento.
- Los catálogos y ediciones son referencias documentales versionadas; no crean automáticamente administraciones ni dosis pendientes.

## 5. Módulo 3: parte diario

### Día y anotación

DiaryDay representa la fecha del parte. DiaryEntry representa una anotación cronológica con turno, categoría, contenido, fecha/hora del hecho, fecha/hora de registro y autor original.

Una anotación puede ser general o estar relacionada con uno o varios menores. DiaryEntryStayLink relaciona una anotación con la estancia correspondiente y conserva snapshots identificativos para consulta histórica.

### Rectificaciones

Una rectificación crea otra DiaryEntry vinculada a la versión anterior mediante la relación de corrección. La cadena conserva texto original, autoría, marcas temporales y motivo. La vista cotidiana muestra la última versión vigente, y el historial permite consultar las anteriores.

El cierre de un día limita la incorporación de nuevas anotaciones ordinarias, pero no impide rectificar anotaciones existentes por cualquier educador activo.

### Planificación

Agenda y calendario son vistas de los registros de planificación compartidos. No deben convertirse en fuentes paralelas que dupliquen las mismas tareas o actividades.

## 6. Módulo 4: informes de incidencias

### Informe

IncidentReport representa el documento lógico, con título, destinatario, estado, creador, fechas y datos de emisión.

### Versión

IncidentReportVersion conserva cada versión del contenido, número secuencial, título, destinatario, estado, autor y fecha/hora. Las versiones emitidas no se sobrescriben; una rectificación genera una nueva versión.

### Hechos vinculados

IncidentReportEntry enlaza una versión de informe con una o varias anotaciones DiaryEntry. Un mismo hecho puede utilizarse en más de un informe. El vínculo conserva la referencia exacta a la versión de anotación que se seleccionó al emitir ese informe.

El informe es una composición documental de hechos del parte diario, no una segunda fuente de acontecimientos. Las modificaciones posteriores del diario no alteran los informes ya emitidos.

## 7. Usuarios, auditoría y permisos

### Profesional y cuenta

Professional representa la identidad de la persona. UserAccount contiene credenciales, rol y estado de acceso. Desactivar una cuenta no elimina la autoría histórica de sus registros.

### Auditoría

AccessAudit registra operaciones relevantes, con cuenta, nombre de usuario, evento, fecha/hora y detalle acotado. No debe duplicar innecesariamente contenido personal o sanitario dentro de la auditoría.

### Permisos

- Todos los educadores activos pueden consultar, crear y modificar información ordinaria de los cuatro módulos.
- La edición no depende de quién creó el registro, del turno o del cierre del día.
- Las herramientas técnicas de cuentas, configuración, copias, restauración y mantenimiento se reservan al administrador.
- Las consultas sanitarias y operaciones relevantes quedan auditadas conforme a la política vigente.

## 8. Relaciones principales

| Relación | Cardinalidad | Regla |
|---|---|---|
| Menor – Estancia | 1 a muchos | Cada ingreso/reingreso crea una estancia nueva |
| Menor – Perfil sanitario | 1 a 1 | Perfil sanitario permanente del menor |
| Menor – Pauta de medicación | 1 a muchos | Historial de pautas |
| Pauta – Horario | 1 a muchos | Horarios estructurados de la pauta |
| Pauta – Administración | 1 a muchos | Resultados de administraciones |
| Menor – Vacuna administrada | 1 a muchos | Historial vacunal permanente |
| Menor – Revisión de dosis | 1 a muchos | Revisiones profesionales repetibles |
| Menor – Anotación | muchos a muchos | Una anotación puede afectar a varios menores |
| Anotación – Estancia | mediante relación | Conserva el contexto de la estancia |
| Menor – Documento | 1 a muchos o relación compartida | El archivo se almacena una sola vez |
| Informe – Versión | 1 a muchos | Historial completo de borradores y emisiones |
| Versión de informe – Anotación | muchos a muchos | Un informe selecciona hechos; un hecho puede reutilizarse |
| Profesional – Cuenta | 1 a 1 | Identidad profesional separada de credenciales |
| Cuenta – Auditoría | 1 a muchos | Trazabilidad de operaciones |

## 9. Reglas de integridad

1. No duplicar la identidad del menor.
2. No reutilizar una estancia cerrada para representar un reingreso.
3. No duplicar una anotación porque afecte a varios menores.
4. No duplicar archivos por relacionarlos con varios registros.
5. Mantener relaciones históricas aunque una estancia finalice o una cuenta se desactive.
6. No eliminar físicamente registros históricos mediante operaciones ordinarias.
7. Conservar versiones anteriores al rectificar.
8. No modificar retroactivamente una versión de informe emitida.
9. Mantener vínculos entre cada informe y las anotaciones que lo sustentan.
10. Aplicar permisos también a búsquedas, documentos, consultas y exportaciones.
11. Utilizar identificadores internos estables, no nombres como claves de relación.
12. No generar automáticamente decisiones clínicas ni dosis pendientes a partir de la ausencia de datos.

## 10. Tablas heredadas

El esquema puede conservar tablas y columnas de versiones anteriores por compatibilidad, trazabilidad o migración histórica. Su existencia física no implica que sigan siendo módulos funcionales visibles. Las migraciones deben preservar los registros y evitar que los datos históricos se pierdan o se dupliquen en las nuevas vistas.

La evolución del esquema se realizará mediante migraciones Alembic versionadas y probadas con bases de datos representativas de versiones anteriores.
