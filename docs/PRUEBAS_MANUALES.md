# Guía de prueba funcional en Windows

## Objetivo y límites

Esta guía sirve para probar la interfaz y los flujos con información inventada. La compilación portable es una versión de desarrollo: que se abra correctamente o que las pruebas automáticas pasen no la convierte en un sistema aprobado para datos reales.

**No introduzcas nombres, fechas de nacimiento, identificadores, fotografías, documentos, información sanitaria ni ningún otro dato real de menores.** Tampoco copies bases de datos del centro a la carpeta de demostración.

## Obtener la compilación

1. Abre la ejecución de [Build portable Windows](https://github.com/eladioalonso/CentroMenores/actions/workflows/build-portable.yml?query=branch%3Adesarrollo%2Fnucleo-aplicacion).
2. Entra en la ejecución más reciente que indique success y cuyo commit coincida con el encabezado de la rama desarrollo/nucleo-aplicacion.
3. En la sección **Artifacts**, descarga el artefacto GestionCentro-Windows-portable.
4. Extrae el ZIP completo en una carpeta local con permisos de escritura. No ejecutes el programa desde dentro del ZIP ni separes el EXE de los demás archivos.
5. Para una primera prueba, conserva esa carpeta separada de cualquier instalación o carpeta de trabajo existente.

El artefacto de GitHub Actions tiene caducidad. Si ya no aparece, utiliza la ejecución satisfactoria más reciente.

## Primera ejecución: modo demostración

1. Ejecuta GestionCentro.exe --demo.
2. La demostración utiliza una carpeta independiente: demo_data junto al EXE portable (o .centro_demo en desarrollo) y solicita crear un administrador de prueba.
3. Usa una contraseña de prueba robusta que no utilices en ningún otro servicio.
4. Crea una o dos cuentas ficticias adicionales para probar los perfiles.
5. En Administración de cuentas, concede expresamente el permiso sanitario solo a la cuenta ficticia que usarás para probar el módulo de salud. El permiso está desactivado por defecto, también para el administrador.
6. Mantén otra cuenta sin ese permiso para comprobar que no puede abrir la ficha ni los documentos sanitarios.
7. No cambies a la ejecución normal para probar con expedientes reales.

La carpeta de demostración y la carpeta normal son distintas. No copies datos entre ellas.

## Lista de comprobación

Marca cada punto como correcto, incorrecto o no probado. Anota el texto del error y los pasos que lo reproducen, pero no incluyas datos personales.

### Inicio y seguridad

- [ ] La aplicación abre con --demo y solicita crear el administrador inicial.
- [ ] Se puede crear una cuenta profesional y entrar con ella.
- [ ] Un usuario educador no ve las herramientas exclusivas de administración.
- [ ] Una cuenta sin permiso sanitario no puede abrir la ficha ni consultar documentos sanitarios.
- [ ] El administrador puede conceder y retirar el permiso sanitario, y la operación queda auditada.
- [ ] Cerrar sesión devuelve a la pantalla de acceso.
- [ ] El bloqueo por inactividad vuelve a pedir credenciales.
- [ ] Cinco intentos fallidos aplican el control de reintentos previsto.
- [ ] Cerrar y volver a abrir conserva la base de datos de demostración.

### Expedientes y estancias

- [ ] Crear un expediente con datos inventados.
- [ ] Buscarlo y abrirlo desde la lista.
- [ ] Editar datos y comprobar que el historial conserva los cambios.
- [ ] Abrir una estancia y comprobar que aparece como activa.
- [ ] Cerrar la estancia con motivo y fecha.
- [ ] Abrir un segundo ingreso sin duplicar el expediente.

### Diario, incidencias, agenda y comunicaciones

- [ ] Registrar una anotación ficticia vinculada al menor.
- [ ] Buscar por fecha y categoría.
- [ ] Registrar una incidencia y consultar su estado.
- [ ] Crear una tarea de equipo y verla desde calendario.
- [ ] Cambiar su estado y comprobar que la vista se actualiza.
- [ ] Crear una comunicación, añadir una aportación y comprobar su autoría.
- [ ] Cerrar y reabrir una comunicación según los permisos disponibles.

### Educación, documentos, autorizaciones y salidas

- [ ] Crear un objetivo educativo y añadir una actualización.
- [ ] Registrar un dato escolar y consultar el historial.
- [ ] Adjuntar un documento ficticio permitido y comprobar sus metadatos.
- [ ] Registrar una autorización con vigencia.
- [ ] Crear una salida de prueba, revisar las autorizaciones y cambiar su estado.
- [ ] Comprobar que los registros históricos siguen consultables al cerrar una estancia.

### Salud y vacunación

- [ ] Abrir la ficha sanitaria del expediente.
- [ ] Registrar una pauta ficticia y sus horarios.
- [ ] Registrar un resultado de administración de prueba.
- [ ] Consultar las ediciones documentales de calendarios.
- [ ] Registrar una administración vacunal ficticia.
- [ ] Introducir fabricante, producto, lote, centro y profesional si se dispone de esos datos de prueba.
- [ ] Vincular un documento sanitario ficticio del mismo expediente.
- [ ] Crear una revisión profesional ficticia y comprobar su orden histórico.
- [ ] Comprobar que no se generan dosis pendientes automáticamente.

No uses datos clínicos verdaderos ni tomes decisiones sanitarias a partir de la aplicación de prueba.

### Informes, copias y mantenimiento

- [ ] Generar estadísticas con un periodo de prueba.
- [ ] Exportar CSV, PDF y Word y comprobar que son legibles.
- [ ] Crear una copia ZIP manual.
- [ ] Verificar la copia.
- [ ] Restaurar únicamente una copia de demostración en una carpeta de demostración separada.
- [ ] Ejecutar el diagnóstico y revisar los avisos.
- [ ] Comprobar que los documentos y las imágenes de prueba se incluyen en la copia.

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
- Los flujos anteriores se revisan sin errores bloqueantes.
- La copia y restauración se prueban en entorno aislado.
- Se completa una revisión de seguridad, privacidad, control de acceso y protección de datos.
- La entidad responsable valida protocolos, permisos, conservación, tratamiento de datos y uso sanitario.

La aceptación funcional por parte de quien prueba la aplicación es una parte de la validación, no sustituye las revisiones institucionales y legales.
