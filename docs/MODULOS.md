# Organización funcional de la aplicación

La aplicación tendrá **dos apartados principales de trabajo**. La pantalla de Inicio puede mantenerse como entrada rápida y el área de Administración será exclusivamente técnica para el administrador; no son módulos de trabajo.

## 1. Información del menor

Una ficha única por menor, con tres pestañas sencillas:

### 1.1 Datos generales
- Nombre.
- Apellidos.
- Sexo.
- Fecha de nacimiento.
- Lugar de nacimiento.
- País de nacimiento.
- Nacionalidad.
- Dirección actual.
- Código postal.
- NIF/NIE.
- Email.
- Número de teléfono móvil.

La edad se calculará automáticamente a partir de la fecha de nacimiento, sin pedir que se introduzca manualmente.

### 1.2 Información sanitaria
- CIP.
- Fecha de emisión de la tarjeta sanitaria.
- Fecha de caducidad.
- Centro de salud asignado.
- Facultativo asignado.
- Enfermería asignada.
- Enfermedades y tratamientos.

La información sanitaria estará dentro de la ficha del menor, no en un módulo independiente. Se mantendrá el historial de cambios y, cuando proceda, el detalle de medicación, administraciones y vacunación asociado a ese menor. Los datos sanitarios no se duplicarán en el parte diario: allí solo se reflejarán las actuaciones o incidencias que deban constar cronológicamente.

### 1.3 Documentos escaneados
- Adjuntar y consultar documentos escaneados desde la propia ficha.
- Cada documento conservará su relación con el menor y su historial.

## 2. Parte diario / Calendario

Un único registro por fecha, organizado por turnos:

- Fecha.
- Personal de mañana.
- Personal de tarde.
- Personal de noche.
- Altas de menores.
- Bajas de menores.
- Actividades de mañana.
- Actividades de tarde.
- Actividades de noche.
- Conductas positivas.
- Conductas negativas.
- Observaciones.

Las anotaciones conservarán fecha, turno, autoría y rectificaciones. Los registros cerrados podrán corregirse mediante una nueva versión, conservando el original y el motivo.

El calendario se consultará desde este mismo apartado, sin constituir otro módulo independiente.

## Reglas comunes

- La ficha del menor será el punto único de consulta de sus datos generales, sanitarios y documentos.
- Los educadores activos podrán consultar y actualizar la información ordinaria, con trazabilidad de los cambios.
- La información se introducirá una sola vez y se reutilizará mediante vínculos.
- Las herramientas técnicas de usuarios, copias, restauración y diagnóstico permanecerán separadas y reservadas al administrador.
- Las funciones anteriores que ya no formen parte de estos dos apartados no deben aparecer como módulos ni botones de uso diario. Los datos históricos existentes se conservarán durante la simplificación; no se eliminarán automáticamente.
- La aplicación seguirá en validación y no se utilizará con datos reales hasta completar las pruebas y la aprobación institucional.
