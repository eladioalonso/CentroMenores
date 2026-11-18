# Gestión del Centro

Aplicación de escritorio local para la gestión interna de un centro de menores.

## Enfoque

- Windows, funcionamiento local y distribución portable.
- Un único ordenador de trabajo por turnos, con cuentas individuales.
- Python, PySide6, SQLite, SQLAlchemy y Alembic.
- Datos persistentes dentro de la carpeta portable.
- Desarrollo y pruebas exclusivamente con datos ficticios.

## Preparar el entorno de desarrollo

Requiere Python 3.11 o superior.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Ejecutar y probar

```powershell
gestion-centro
pytest
```

En desarrollo, la carpeta de datos se puede indicar con `CENTRO_DATOS_DIR`; por defecto se utiliza `.centro_datos/`, excluida de Git. En la distribución portable, los datos se ubicarán junto al ejecutable.

## Documentación

- [Planteamiento](docs/PLANTEAMIENTO.md)
- [Módulos](docs/MODULOS.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Usuarios y permisos](docs/USUARIOS_Y_PERMISOS.md)
- [Flujos de trabajo](docs/FLUJOS_DE_TRABAJO.md)
- [Modelo conceptual de datos](docs/MODELO_DATOS.md)
- [Decisiones consolidadas](docs/DECISIONES_CONSOLIDADAS.md)
- [Catálogos vacunales y trazabilidad documental](docs/VACUNACION_CATALOGOS.md)
- [Guía de prueba funcional en Windows](docs/PRUEBAS_MANUALES.md)
- [Seguridad y requisitos de despliegue](docs/SEGURIDAD_DESPLIEGUE.md)

## Funciones de la versión de desarrollo

- Navegación principal organizada en los cuatro módulos funcionales aprobados.
- Expediente principal con identidad única, estancias, seguimiento educativo, escolaridad, documentos, autorizaciones, visitas y salidas.
- Expediente sanitario permanente por menor, con medicación, administraciones, vacunas, revisiones y versiones trazables.
- Parte diario cronológico compartido, con anotaciones relacionadas con uno o varios menores y rectificaciones versionadas.
- Informes de incidencias con selección explícita de hechos del parte, borradores compartidos, emisión, rectificación e historial de versiones.
- Edición ordinaria compartida: cualquier educador activo puede modificar registros creados por otro educador; se conserva la autoría histórica.
- Copias ZIP verificables y restauración con copia previa, validación de integridad y reconciliación de auditoría.
- Ayuda integrada y modo de demostración aislado.

Modo de demostración: ejecutar `GestionCentro.exe --demo`. En desarrollo puede ejecutarse `python -m gestion_centro --demo`. Usa una carpeta independiente (`demo_data` junto al EXE portable o `.centro_demo` en desarrollo) y no abre la carpeta de datos normales.

La demostración precarga expedientes, estancias y anotaciones ficticias. Incluye una cuenta de prueba `EDUCADOR` (contraseña inicial de demostración: `012345678910`), sin permisos de administración. Cambia la contraseña de prueba si el flujo lo permite y no reutilices esa clave en ningún otro servicio. Los educadores activos pueden consultar y registrar información sanitaria; el campo histórico `health_access` ya no bloquea ese acceso. La carga es idempotente y no duplica ejemplos al volver a abrir la demo. No copies datos reales a esa carpeta.

El acceso móvil por Wi-Fi no está habilitado. No abrir puertos ni exponer el equipo a redes externas para intentar activarlo.

## Estado de desarrollo

Rama activa: `desarrollo/nucleo-aplicacion`. No fusionar ni desplegar desde `main`.

El repositorio contiene los cuatro módulos funcionales y un área técnica de administración reservada al administrador. Las herramientas de agenda, calendario, documentación, seguimiento educativo, escolaridad, autorizaciones y salidas están integradas en los módulos correspondientes; las tablas heredadas de comunicaciones e incidencias no constituyen módulos funcionales visibles.

La compilación portable y las pruebas automatizadas deben comprobarse siempre para el commit más reciente. La aplicación continúa en validación: falta la prueba funcional en el equipo Windows definitivo, la validación operativa de migraciones y restauración en ese entorno, la revisión institucional de seguridad y protección de datos y la aprobación de la organización responsable. No utilizar con datos reales.
