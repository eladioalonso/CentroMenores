# Seguridad y despliegue

## Estado

La aplicación es una versión de desarrollo local para Windows. No debe utilizarse con expedientes reales hasta que la entidad responsable complete la validación funcional, jurídica, de protección de datos y de seguridad.

## Límites de seguridad conocidos

- La base SQLite y los archivos adjuntos se almacenan en la carpeta local de datos en formato legible por el sistema operativo.
- Los ZIP de copia de seguridad no tienen cifrado propio. La comprobación de integridad no equivale a cifrado.
- Una persona con permisos de administrador local o acceso físico al disco puede acceder a los archivos y potencialmente modificar la base de datos y los registros locales de auditoría.
- El registro de auditoría es de solo lectura desde la interfaz; no es un sistema externo inmutable ni una garantía frente a un administrador local malicioso.
- La aplicación está diseñada para uso local en un único equipo. No debe compartirse una base SQLite en una carpeta de red ni exponerse por Internet.
- El acceso móvil por Wi-Fi no está habilitado. No abrir puertos ni configurar redirecciones para intentar activarlo.

Estos límites impiden considerar la aplicación una plataforma de producción para datos especialmente protegidos sin controles adicionales.

## Requisitos mínimos antes de cargar datos reales

1. **Equipo institucional:** Windows actualizado, administrado por la entidad y con una cuenta de Windows individual para cada profesional cuando sea posible.
2. **Cifrado del dispositivo:** activar BitLocker para todo el volumen que contenga la aplicación, la base de datos y los adjuntos. La custodia de las claves de recuperación corresponde al área técnica autorizada.
3. **Cifrado de copias externas:** utilizar unidades USB o discos externos cifrados con BitLocker To Go u otro mecanismo institucional aprobado. No copiar ZIP de respaldo a soportes sin cifrar.
4. **Permisos NTFS:** limitar la carpeta de datos a las cuentas Windows autorizadas y al equipo técnico que deba mantenerla. No ubicarla en carpetas públicas ni sincronizadas automáticamente.
5. **Protección del puesto:** bloqueo automático de Windows, antivirus/EDR institucional, actualizaciones y prohibición de compartir credenciales.
6. **Copias:** establecer periodicidad, responsables, número de generaciones, ubicación externa cifrada y una prueba periódica de restauración.
7. **Auditoría:** definir responsables de consulta, conservación, revisión y exportación de los registros. Para requisitos de inmutabilidad o centralización se necesitará un sistema institucional externo.
8. **Gobernanza:** aprobar perfiles, autorizaciones sanitarias, conservación, exportaciones, respuesta a incidentes, encargados del tratamiento y evaluación de impacto cuando proceda.

## Uso de la versión de prueba

- Utilizar exclusivamente el modo demostración y datos inventados.
- Mantener la carpeta de demostración separada de cualquier carpeta que contenga datos reales.
- No importar expedientes, documentos, imágenes ni bases de datos del centro.
- No utilizar el equipo de pruebas como repositorio de información real.
- Informar de errores sin adjuntar información personal.

## Criterios de autorización de puesta en servicio

La puesta en servicio requiere, como mínimo:
- pruebas funcionales satisfactorias en el equipo Windows que vaya a utilizarse;
- validación de copias y restauración;
- configuración y verificación del cifrado de disco y soportes;
- revisión de permisos, auditoría y accesos sanitarios;
- aprobación de la dirección y de los responsables de protección de datos y seguridad de la entidad;
- plan de mantenimiento, actualización, soporte y recuperación ante incidentes.

La compilación portable y las pruebas automáticas satisfactorias no sustituyen estas autorizaciones.
