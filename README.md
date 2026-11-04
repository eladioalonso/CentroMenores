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

## Funciones recientes de desarrollo

- Calendario con vistas diaria, semanal, mensual y anual sobre los elementos de agenda.
- Restauración integral con copia previa obligatoria, validación de integridad y versión del esquema, y reconciliación de la auditoría existente.
- Exportación de estadísticas agregadas a CSV, PDF y Word.
- Ayuda integrada con guía operativa y preguntas frecuentes.
- Modo de demostración aislado: ejecutar `GestionCentro.exe --demo`. En desarrollo puede ejecutarse `python -m gestion_centro --demo`. Usa una carpeta de demostración independiente (`demo_data` junto al EXE portable o `.centro_demo` en desarrollo); no abre la carpeta de datos normales.

El modo de demostración arranca con una base separada y solicita crear un administrador de prueba. No copiar datos reales a esa carpeta.

El acceso móvil por Wi-Fi no está habilitado todavía. No abrir puertos ni exponer el equipo a redes externas para intentar activarlo. Requiere terminar la autenticación móvil, TLS con certificado confiable, expiración de tokens, cola de revisión y pruebas de seguridad.

## Estado de desarrollo

Rama activa: `desarrollo/nucleo-aplicacion`. No fusionar ni desplegar desde `main`.

Incluye actualmente modelos, servicios y primeras interfaces para:
- Cuentas individuales, perfiles, bloqueo por inactividad y auditoría.
- Menores, estancias, acontecimientos, diario e incidencias.
- Agenda compartida y tareas.
- Comunicaciones internas con aportaciones trazables.
- Seguimiento educativo y escolaridad.
- Ficha sanitaria, pautas prescritas, administración de medicación y vacunas.
- Documentación personal con versiones y huella SHA-256.
- Autorizaciones y salidas.
- Copias ZIP verificables y sincronización externa pendiente.

La interfaz sigue en desarrollo y no todos los flujos están completos. Las ejecuciones de CI deben comprobarse para el commit más reciente antes de considerar válida una compilación. No utilizar con datos reales: faltan validación funcional integral, restauración integral probada, revisión de seguridad y protección de datos, y aprobación de la organización responsable.
