# Revisión de navegación y carga de trabajo cotidiana

**Estado:** la navegación principal está organizada en los cuatro módulos aprobados. Esta revisión sirve para comprobar que los flujos internos siguen siendo sencillos y que no reaparecen módulos funcionales paralelos.

## Criterio de organización

La aplicación se utiliza en un único ordenador compartido por educadores de distintos turnos. Debe ser fácil localizar la información, evitar duplicidades y permitir que cualquier educador continúe el trabajo de otro sin depender de la persona que creó el registro.

La navegación funcional tiene exactamente cuatro módulos:

1. Expediente principal del menor.
2. Expediente sanitario del menor.
3. Parte diario.
4. Informes de incidencias.

Inicio es un panel de entrada, no un módulo funcional adicional. Administración es un área técnica reservada al administrador, no un módulo de trabajo para educadores.

## 1. Expediente principal del menor

Debe ser el punto de referencia para consultar la trayectoria personal y educativa.

Contiene o integra:
- Datos identificativos y personales.
- Estancias, ingresos, reingresos y bajas.
- Acontecimientos e historial del menor.
- Seguimiento educativo, objetivos y escolaridad.
- Documentación personal y administrativa.
- Salidas, retornos, autorizaciones, visitas y restricciones.

La ficha principal debe facilitar el acceso a los apartados especializados con el menor ya seleccionado. La información sanitaria detallada se mantiene en el expediente sanitario y no se duplica en el principal.

## 2. Expediente sanitario del menor

Debe estar vinculado a la ficha única del menor y permitir consultar la historia sanitaria aunque no exista una estancia activa.

Contiene:
- Ficha sanitaria y datos de contacto sanitario.
- Antecedentes, alergias e instrucciones de emergencia.
- Consultas, urgencias y actuaciones registradas.
- Medicación, pautas, horarios y administraciones.
- Vacunas, dosis, justificantes y revisiones profesionales.
- Historial de cambios.

Todos los educadores activos tienen las mismas capacidades ordinarias de consulta y edición. Las operaciones sanitarias relevantes quedan trazadas. La interfaz debe dejar claro cuándo se está consultando información histórica de un menor sin estancia activa.

Los calendarios vacunales son referencias documentales; no prescriben ni determinan por sí solos dosis pendientes.

## 3. Parte diario

Es la fuente cronológica única de los hechos y de la actividad cotidiana del centro.

Debe facilitar:
- Consulta por fecha, categoría y menor.
- Registro de actividades realizadas en el día, comportamientos positivos, comportamientos negativos y observaciones.
- Las altas y bajas se reflejan desde el historial de estancias del expediente; no se duplican como categorías manuales del parte.
- Anotaciones generales o relacionadas con varios menores.
- Rectificaciones vinculadas a la anotación original.
- Acceso a agenda y calendario como vistas de planificación relacionadas, sin crear una segunda fuente de datos.

El cierre de un día organiza el registro e impide añadir nuevas anotaciones ordinarias, pero no bloquea la corrección de hechos existentes. Cualquier educador activo puede rectificar anotaciones de otro educador; la aplicación conserva original, versión, autor y motivo.

## 4. Informes de incidencias

Los informes se elaboran a partir de anotaciones ya existentes en el parte diario.

El flujo debe ser:
1. Buscar por periodo y, cuando proceda, por menor.
2. Seleccionar expresamente los hechos que se incluirán.
3. Preparar el borrador cronológico.
4. Guardar el borrador para continuarlo desde otra sesión de educador.
5. Revisar y emitir la versión oficial.
6. Exportar a Word.
7. Si hay que corregirla, crear una nueva versión rectificada sin sobrescribir la emitida.

Por seguridad, ninguna anotación debe estar seleccionada automáticamente al iniciar un informe. Así se evita incorporar accidentalmente hechos o menores ajenos al documento.

## Administración técnica

Solo el administrador accede a cuentas, configuración, copias de seguridad, restauración, mantenimiento y diagnóstico. Estas funciones no deben convertirse en un quinto módulo de trabajo.

## Principios para reducir carga de datos

- Capturar cada dato una sola vez y reutilizarlo mediante relaciones.
- Mostrar primero la información y las acciones relevantes para la tarea actual.
- No exigir campos complementarios que no sean necesarios para guardar un registro.
- Usar valores predeterminados seguros y editables; nunca inferir hechos sensibles.
- Mantener formularios claros y breves, agrupando datos relacionados en pestañas.
- Evitar botones grandes o repetidos; priorizar textos legibles y acciones claras.
- Mantener trazabilidad, autoría, fecha/hora, controles de permisos y validaciones.
- Evitar alertas redundantes y mostrar avisos accionables.

## Pendiente de validación funcional

La prueba en el equipo de trabajo debe confirmar:
- Que las tareas habituales se pueden realizar en pocos pasos.
- Que la tipografía se lee cómodamente en el monitor de oficina.
- Que los expedientes se entienden sin formación informática avanzada.
- Que los educadores pueden corregir registros compartidos sin sobrescribir versiones.
- Que la búsqueda de hechos para informes no facilita incluir datos ajenos por error.
- Que la navegación no presenta opciones duplicadas ni módulos heredados.

La revisión funcional debe realizarse con datos ficticios. La aprobación de uso con datos reales requiere, además, las validaciones institucionales y de protección de datos descritas en la documentación de seguridad.
