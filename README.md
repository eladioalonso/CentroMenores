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

## Estado

Esta rama incorpora el núcleo técnico inicial. Todavía no implementa autenticación, expedientes ni operaciones con datos de menores. No utilizar con datos reales.
