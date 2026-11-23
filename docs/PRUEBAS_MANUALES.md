# Guía de prueba funcional en Windows

## Objetivo y límites

Esta guía sirve para probar la interfaz y los flujos con información inventada. La compilación portable es una versión de desarrollo: que se abra correctamente o que las pruebas automáticas pasen no la convierte en un sistema aprobado para datos reales.

**No introduzcas nombres, fechas de nacimiento, identificadores, fotografías, documentos, información sanitaria ni ningún otro dato real de menores.** Tampoco copies bases de datos del centro a la carpeta de demostración.

## Obtener la compilación

1. Abre la ejecución de [Build portable Windows](https://github.com/eladioalonso/CentroMenores/actions/workflows/build-portable.yml?query=branch%3Adesarrollo%2Fnucleo-aplicacion).
2. Entra en la ejecución más reciente que indique success y cuyo commit coincida con el encabezado de la rama `desarrollo/nucleo-aplicacion`.
3. En **Artifacts**, descarga `GestionCentro-Windows-portable`.
4. Extrae el ZIP completo en una carpeta local con permisos de escritura. No ejecutes el programa desde dentro del ZIP ni separes el EXE de los demás archivos.
5. Conserva esa carpeta separada de cualquier instalación o carpeta de trabajo existente.

## Primera ejecución: modo demostración

1. Ejecuta `GestionCentro.exe --demo`.
2. Comprueba que aparecen 30 expedientes ficticios, con estancias activas y ficha sanitaria de prueba, y que el parte diario contiene 20 anotaciones de ejemplo vinculadas a distintos menores.
3. La demostración utiliza una carpeta independiente `demo_data` junto al EXE portable (o `.centro_demo` en desarrollo) y solicita crear un administrador de prueba.
4. Usa una contraseña robusta que no utilices en ningún otro servicio.
5. Crea dos cuentas ficticias de educador para comprobar la edición compartida.
6. Mantén separadas la carpeta de demostración y la carpeta normal. No copies datos entre ellas.

## Lista de comprobación

Marca cada punto como correcto, incorrecto o no probado. Anota los errores y los pasos para reproducirlos, sin incluir datos personales.

### Inicio y seguridad

- [ ] La aplicación abre con `--demo` y solicita crear el administrador inicial.
- [ ] Se puede crear una cuenta profesional y entrar con ella.
- [ ] Un educador no ve las herramientas técnicas de administración.
- [ ] Los educadores pueden consultar, crear y modificar información ordinaria.
- [ ] Un educador puede modificar un registro creado por otro educador y queda registrada la nueva autoría.
- [ ] Cerrar y volver a abrir conserva la base de datos de demostración.
- [ ] Cerrar sesión devuelve a la pantalla de acceso.
- [ ] El bloqueo por inactividad vuelve a pedir credenciales.

### 1. Información del menor

- [ ] Crear un expediente ficticio desde la ficha.
- [ ] Comprobar los campos: nombre, apellidos, sexo, fecha de nacimiento, lugar y país de nacimiento, nacionalidad, dirección, código postal, NIF/NIE, email y móvil.
- [ ] Comprobar el cálculo automático de edad.
- [ ] Comprobar CIP, fecha de emisión y caducidad de tarjeta, centro de salud, facultativo, enfermería y enfermedades/tratamientos.
- [ ] Comprobar que la información sanitaria queda vinculada al perfil clínico del menor y que se conserva el historial de cambios.
- [ ] Modificar datos generales y sanitarios y comprobar la trazabilidad.
- [ ] Consultar y gestionar ingresos/reingresos desde la pestaña de estancias; modificar y cerrar una estancia ficticia.
- [ ] Añadir un acontecimiento y comprobar que queda vinculado al menor.
- [ ] Rectificar un acontecimiento y consultar su historial de versiones.
- [ ] Abrir la sección de medicación, administraciones y vacunas desde la pestaña sanitaria y comprobar que el menor ya aparece seleccionado, incluso si no tiene estancia activa.
- [ ] Registrar una pauta ficticia y sus horarios.
- [ ] Registrar y rectificar una administración de prueba, comprobando que conserva versiones.
- [ ] Consultar calendarios vacunales documentales y registrar una vacuna ficticia.
- [ ] Añadir y consultar documentos escaneados ficticios desde la pestaña Documentos.
- [ ] Comprobar que la ficha permite consultar menores inactivos o sin estancia vigente.

Los calendarios vacunales son referencias documentales. No uses datos clínicos verdaderos ni tomes decisiones sanitarias a partir de la aplicación de prueba.

### 2. Parte diario / Calendario

- [ ] Seleccionar una fecha.
- [ ] Seleccionar una fecha y comprobar que se muestran las anotaciones de ese día.
- [ ] Registrar actividades realizadas en el día.
- [ ] Registrar comportamientos positivos y negativos en categorías separadas.
- [ ] Registrar observaciones generales.
- [ ] Vincular anotaciones a uno o varios menores cuando corresponda; dejar sin vincular los hechos generales.
- [ ] Comprobar que cada anotación muestra fecha/hora, categoría, autoría y contenido.
- [ ] Cambiar de fecha y volver a la original para comprobar que los registros se conservan.
- [ ] Cerrar el parte y comprobar que no admite nuevas anotaciones ordinarias.
- [ ] Rectificar una anotación con otra cuenta de educador y comprobar que se conserva el original, la nueva autoría y el motivo.
- [ ] Consultar el calendario desde el mismo apartado.

### Copias, restauración y mantenimiento

- [ ] Crear una copia ZIP manual.
- [ ] Verificar la copia.
- [ ] Comprobar que incluye base de datos y documentos ficticios.
- [ ] Restaurar únicamente una copia de demostración en una carpeta aislada.
- [ ] Ejecutar el diagnóstico y revisar los avisos.
- [ ] Comprobar que las herramientas técnicas de administración no están disponibles para educadores.

## Cómo comunicar un fallo

Para cada error apunta:
- Versión/commit de la compilación.
- Apartado y pantalla.
- Acción inmediatamente anterior.
- Resultado esperado y resultado obtenido.
- Texto exacto del mensaje.

No adjuntes capturas que contengan datos reales. Para un error visual, usa solo expedientes y documentos inventados.

## Criterios para dar por terminada la versión de prueba

- Todas las pruebas automáticas pasan en el commit actual.
- La compilación portable se completa y verifica sus recursos.
- La aplicación abre en Windows limpio y funciona en modo demostración.
- Se prueban los dos apartados principales sin errores bloqueantes.
- La copia y restauración se prueban en entorno aislado.
- Se completa una revisión de seguridad, privacidad, control de acceso y protección de datos.
- La entidad responsable valida protocolos, permisos, conservación, tratamiento de datos y uso sanitario.

La aceptación funcional no sustituye las revisiones institucionales y legales.
