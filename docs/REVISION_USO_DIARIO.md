# Revisión de navegación y carga de trabajo cotidiana

**Estado:** propuesta de organización de interfaz aplicada al menú principal; los flujos internos siguen en revisión.

## Criterio

La aplicación debe separar las tareas frecuentes del turno de las funciones de consulta, gestión especializada y administración. Reducir opciones visibles no significa eliminar datos ni controles necesarios.

## Navegación principal

### Día a día
Accesos prioritarios:
1. Expedientes y estancias.
2. Diario e incidencias.
3. Agenda común y tareas.
4. Comunicaciones internas.

Son los puntos de entrada previsibles para registrar hechos, consultar la situación de los menores y realizar el traspaso entre turnos.

### Gestión y consultas
Funciones disponibles sin ocupar el primer nivel del trabajo diario:
- Calendario.
- Documentación personal.
- Autorizaciones.
- Salidas.
- Seguimiento educativo y escolaridad.
- Ficha sanitaria y medicación.
- Informes externos.

### Administración
Pestaña exclusiva del perfil administrador:
- Administración de cuentas.
- Copias de seguridad.
- Mantenimiento y diagnóstico.
- Estadísticas y memoria.

## Solapamientos que deben resolverse en siguientes iteraciones

- **Agenda y calendario:** la agenda debe ser el lugar para crear y actualizar tareas, citas y eventos. El calendario debe ser una vista temporal de esa misma información, no una segunda fuente de datos. Antes de unificar pantallas hay que comprobar que ambas consultan los mismos registros y no mantienen calendarios paralelos.
- **Expediente y documentación:** la ficha del menor debe ser el punto de acceso contextual a documentos, autorizaciones, salidas, escolaridad, salud e historial. Los módulos especializados pueden seguir existiendo, pero deben abrirse con el menor/estancia ya seleccionados cuando se llegue desde un expediente.
- **Diario e incidencias:** mantenerlos como acceso cotidiano conjunto, pero distinguir claramente una anotación ordinaria de una incidencia formal. No duplicar un mismo hecho en ambos registros por defecto.
- **Informes externos y estadísticas:** separar los informes individualizados destinados a organismos externos de las estadísticas internas. Evitar que un mismo dato tenga que registrarse otra vez para generar un informe.
- **Salidas y autorizaciones:** la autorización debe consultarse desde el flujo de salida. No exigir navegar a otro módulo para comprobar una autorización, sin dejar de registrar la comprobación.
- **Escolaridad y seguimiento educativo:** mantener un único contexto educativo por estancia y evitar repetir datos escolares básicos en varias pantallas.

## Principios para reducir carga de datos

- Capturar cada dato una sola vez y reutilizarlo mediante relaciones.
- Mostrar primero los datos y acciones relevantes para la tarea actual.
- No exigir campos que no sean necesarios para guardar el registro; distinguir obligatorios legales/operativos de información complementaria.
- Usar valores predeterminados seguros y editables, nunca inferir hechos sensibles.
- Mantener formularios breves por pasos cuando haya tareas complejas.
- Mostrar campos avanzados solo cuando la elección anterior los haga necesarios.
- No convertir cada módulo funcional en una pantalla o botón de primer nivel.
- No eliminar trazabilidad, autoría, fecha/hora, controles de permisos ni validaciones para acortar formularios.
- Evitar alertas redundantes; agrupar avisos por prioridad y mostrar pendientes accionables.

## Pendiente de validar con usuarios del centro

Antes de cerrar el diseño de los formularios y panel:
- Qué cuatro o cinco tareas se realizan realmente en cada turno.
- Qué datos son obligatorios en cada tipo de anotación/incidencia.
- Qué información debe verse de inmediato al abrir un expediente.
- Qué campos se repiten entre diario, incidencias, comunicaciones y seguimiento educativo.
- Qué informes se utilizan de verdad y con qué periodicidad.

La navegación agrupada ya está implementada en el menú principal. La consolidación de datos y pantallas descrita en los solapamientos requiere revisar los servicios y modelos antes de modificar la estructura persistente.
