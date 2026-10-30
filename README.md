# Gestión del Centro

Aplicación de escritorio para la gestión interna de un centro de menores.

## Objetivo

Centralizar la actividad cotidiana del centro en una aplicación Windows de uso local, con fichas únicas de menores, estancias e historial, seguimiento educativo, diario profesional, incidencias, salidas, actividades, documentación, tareas e informes.

La aplicación está concebida para que varios educadores utilicen **el mismo ordenador por turnos**, cada uno con su propia cuenta y permisos.

## Enfoque de despliegue

- Aplicación de escritorio para Windows.
- Funcionamiento local, sin necesidad de conexión a Internet.
- Distribución portable: el programa y sus datos estarán contenidos en una carpeta.
- No será necesario instalar Python ni bibliotecas en los equipos de los educadores.
- La carpeta podrá copiarse a otro ordenador Windows compatible, con la aplicación cerrada.
- La eliminación de la carpeta eliminará también los datos que estén dentro de ella. Las copias externas de seguridad deberán gestionarse por separado.

## Tecnologías propuestas

- Python: lenguaje principal.
- PySide6: interfaz gráfica.
- SQLite: base de datos local.
- SQLAlchemy: acceso y mapeo de datos.
- Alembic: migraciones del esquema.
- PyInstaller, modo onedir: empaquetado de la aplicación para Windows.

Estas tecnologías constituyen la propuesta inicial y podrán revisarse durante el diseño técnico antes de comenzar la implementación.

## Documentación

- [Planteamiento del proyecto](docs/PLANTEAMIENTO.md)
- [Módulos funcionales](docs/MODULOS.md)
- [Arquitectura técnica](docs/ARQUITECTURA.md)
- [Usuarios y permisos](docs/USUARIOS_Y_PERMISOS.md)
- [Flujos de trabajo](docs/FLUJOS_DE_TRABAJO.md)
- [Modelo conceptual de datos](docs/MODELO_DATOS.md)

## Alcance y protección de datos

La aplicación gestionará exclusivamente la actividad interna del centro. No pretende sustituir ni gestionar los procedimientos administrativos externos de protección de menores.

Durante el desarrollo se utilizarán datos ficticios. No se deben incorporar al repositorio datos personales reales, expedientes, informes sanitarios, documentos identificativos, credenciales ni copias de bases de datos reales.

La aplicación deberá diseñarse conforme a los principios de protección de datos, minimización, control de acceso, trazabilidad y conservación segura.
