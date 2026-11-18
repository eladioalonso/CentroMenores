# Guía de prueba funcional en Windows

## Objetivo y límites

Esta guía sirve para probar la interfaz y los flujos con información inventada. La compilación portable es una versión de desarrollo: que se abra correctamente o que las pruebas automáticas pasen no la convierte en un sistema aprobado para datos reales.

**No introduzcas nombres, fechas de nacimiento, identificadores, fotografías, documentos, información sanitaria ni ningún otro dato real de menores.** Tampoco copies bases de datos del centro a la carpeta de demostración.

## Obtener la compilación

1. Abre la ejecución de [Build portable Windows](https://github.com/eladioalonso/CentroMenores/actions/workflows/build-portable.yml?query=branch%3Adesarrollo%2Fnucleo-aplicacion).
2. Entra en la ejecución más reciente que indique success y cuyo commit coincida con el encabezado de la rama `desarrollo/nucleo-aplicacion`.
3. En la sección **Artifacts**, descarga `GestionCentro-Windows-portable`.
4. Extrae el ZIP completo en una carpeta local con permisos de escritura. No ejecutes el programa desde dentro del ZIP ni separes el EXE de los demás archivos.
5. Para una primera prueba, conserva esa carpeta separada de cualquier instalación o carpeta de trabajo existente.

El artefacto de GitHub Actions tiene caducidad. Si ya no aparece, utiliza la ejecución satisfactoria más reciente.

## Primera ejecución: modo demostración

1. Ejecuta `GestionCentro.exe --demo`.
2. La demostración utiliza una carpeta independiente `demo_data` junto al EXE portable (o `.centro_demo` en desarrollo) y solicita crear un administrador de prueba.
3. Usa una contraseña de prueba robusta que no utilices en ningún otro servicio.
4. Crea dos cuentas ficticias de educador para comprobar la edición compartida.
5. Mantén separadas la carpeta de demostración y la carpeta normal. No copies datos entre ellas.

## Lista de comprobación

Marca cada punto como correcto, incorrecto o no probado. Anota el texto del error y los pasos que lo reproducen, pero no incluyas datos personales.

### Inicio y seguridad

- [ ] La aplicación abre con `--demo` y solicita crear el administrador inicial.
- [ ] Se puede crear una cuenta profesional y entrar con ella.
- [ ] Un educador no ve las herramientas exclusivas de administración.
- [ ] Los educadores pueden consultar, crear y modificar información ordinaria de los cuatro módulos.
- [ ] Un educador puede modificar un registro creado por otro educador y queda registrada la nueva autoría.
- [ ] Cerrar y volver a abrir conserva la base de datos de demostración.
- [ ] Cambiar la contraseña propia exige la contraseña actual.
- [ ] Cerrar sesión devuelve a la pantalla de acceso.
- [ ] El bloqueo por inactividad vuelve a pedir credenciales.
- [ ] Cinco intentos fallidos aplican el control de reintentos previsto.

### 1. Expediente principal del menor

- [ ] Crear un expediente con datos inventados.
- [ ] Comprobar el cálculo automático de edad a partir de la fecha de nacimiento.
- [ ] Buscarlo y abrirlo desde la lista.
- [ ] Modificar datos personales y comprobar el historial de cambios.
- [ ] Abrir una estancia, cerrarla con fecha y motivo y comprobar el historial.
- [ ] Abrir un segundo ingreso sin duplicar el expediente.
- [ ] Consultar y modificar el seguimiento educativo y escolar.
- [ ] Incorporar un documento ficticio y comprobar sus metadatos.
- [ ] Registrar una autorización y comprobar su vigencia.
- [ ] Registrar una salida y un retorno, comprobando sus estados.
- [ ] Consultar las restricciones de visitas y contactos del expediente.

### 2. Expediente sanitario del menor

- [ ] Abrir la ficha sanitaria desde el módulo sanitario.
- [ ] Comprobar que aparecen tanto menores con estancia activa como menores inactivos.
- [ ] Guardar CIP, centro de salud, facultativo, enfermería y antecedentes ficticios.
- [ ] Registrar una pauta ficticia y sus horarios.
- [ ] Registrar un resultado de administración de prueba.
- [ ] Rectificar una administración y comprobar que conserva la versión anterior.
- [ ] Consultar los catálogos documentales de vacunación.
- [ ] Registrar una administración vacunal ficticia con sus datos de trazabilidad.
- [ ] Vincular un documento sanitario ficticio del mismo expediente.
- [ ] Añadir una revisión profesional ficticia y consultar su historial.
- [ ] Comprobar que la ausencia de un registro no genera automáticamente una dosis pendiente.
- [ ] Comprobar que otro educador puede consultar y modificar la información sanitaria, conservando la trazabilidad.

Los catálogos de vacunación son referencias documentales. No uses datos clínicos verdaderos ni tomes decisiones sanitarias a partir de la aplicación de prueba.

### 3. Parte diario

- [ ] Registrar anotaciones ficticias de mañana, tarde y noche.
- [ ] Vincular una anotación a uno o varios menores.
- [ ] Registrar una anotación general sin menor vinculado.
- [ ] Consultar el diario por fecha, categoría y menor.
- [ ] Comprobar que el autor y las fechas del hecho y del registro se muestran correctamente.
- [ ] Cerrar el parte del día y comprobar que no permite añadir anotaciones ordinarias nuevas.
- [ ] Rectificar una anotación existente después del cierre con otra cuenta de educador.
- [ ] Comprobar que se conserva el texto original, el motivo y la autoría de la rectificación.
- [ ] Consultar agenda y calendario y verificar que muestran los mismos datos de planificación.

### 4. Informes de incidencias

- [ ] Buscar anotaciones del parte por periodo.
- [ ] Comprobar que ninguna anotación aparece seleccionada automáticamente.
- [ ] Seleccionar expresamente solo los hechos que deban formar parte del informe.
- [ ] Preparar y guardar un borrador.
- [ ] Cerrar el diálogo, abrirlo de nuevo y recuperar el borrador.
- [ ] Continuar el borrador con otra cuenta de educador.
- [ ] Comprobar que la selección de hechos se conserva.
- [ ] Emitir una versión oficial y exportarla a Word.
- [ ] Rectificar la versión emitida y comprobar que se conservan ambas versiones.
- [ ] Comprobar que la rectificación no modifica las anotaciones originales del parte.
- [ ] Seleccionar «Nuevo informe» después de abrir un borrador y comprobar que no se modifica accidentalmente el borrador anterior.

### Copias, restauración y mantenimiento

- [ ] Crear una copia ZIP manual.
- [ ] Verificar la copia.
- [ ] Comprobar que incluye base de datos, documentos e imágenes de prueba.
- [ ] Restaurar únicamente una copia de demostración en una carpeta aislada.
- [ ] Comprobar que los registros de auditoría posteriores a la copia se conservan según las reglas de restauración.
- [ ] Ejecutar el diagnóstico y revisar los avisos.
- [ ] Comprobar que las herramientas de administración no están disponibles para educadores.

## Cómo comunicar un fallo

Para cada error apunta:
- Versión/commit de la compilación.
- Módulo y pantalla.
- Acción inmediatamente anterior.
- Resultado esperado y resultado obtenido.
- Texto exacto del mensaje, si aparece.

No adjuntes capturas que contengan datos reales. Para un error visual, usa solo expedientes y documentos inventados.

## Criterios para dar por terminada la versión de prueba

- Todas las pruebas automáticas pasan en el commit actual.
- La compilación portable se completa y verifica sus recursos.
- La aplicación abre en Windows limpio y funciona en modo demostración.
- Los flujos de los cuatro módulos se revisan sin errores bloqueantes.
- La copia y restauración se prueban en entorno aislado.
- Se completa una revisión de seguridad, privacidad, control de acceso y protección de datos.
- La entidad responsable valida protocolos, permisos, conservación, tratamiento de datos y uso sanitario.

La aceptación funcional por parte de quien prueba la aplicación es una parte de la validación, no sustituye las revisiones institucionales y legales.
