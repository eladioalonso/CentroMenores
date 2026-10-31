# Arquitectura técnica propuesta

## 1. Objetivo técnico

Construir una aplicación de escritorio para Windows, de uso local y portable. Varios educadores utilizarán el mismo ordenador por turnos, cada uno con una cuenta individual.

No se requiere servidor central, servicio web ni acceso simultáneo desde varios ordenadores. La base de datos será local al equipo donde se ejecute la aplicación.

## 2. Tecnologías propuestas

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Lenguaje | Python | Lógica de aplicación |
| Interfaz | PySide6 | Ventanas, formularios, tablas y navegación |
| Base de datos | SQLite | Persistencia local |
| Acceso a datos | SQLAlchemy | Modelos y operaciones de persistencia |
| Migraciones | Alembic | Evolución controlada del esquema |
| Empaquetado | PyInstaller, modo onedir | Distribución autocontenida para Windows |
| Pruebas | Pytest | Pruebas unitarias e integración |

Las versiones concretas se fijarán en los archivos de dependencias y se validarán en el entorno de construcción. El usuario final no instalará Python, bibliotecas ni motores de base de datos.

## 3. Despliegue portable

La distribución tendrá una carpeta raíz, por ejemplo:

```text
GestionCentro/
├── GestionCentro.exe
├── _internal/             # Runtime y bibliotecas empaquetadas
├── data/
│   ├── centro.db          # Base de datos SQLite
│   ├── documentos/        # Archivos documentales
│   ├── imagenes/          # Imágenes y adjuntos
│   └── backups/           # Copias locales
├── config/
│   └── configuracion.json
├── logs/
└── LEEME.txt
```

La estructura definitiva se ajustará a las necesidades del empaquetado. El requisito esencial es que todos los datos persistentes y la configuración propia de la aplicación residan dentro de la carpeta raíz, sin depender de rutas específicas del usuario de Windows.

## 4. Resolución de rutas

- La aplicación localizará su carpeta de instalación de forma fiable tanto en ejecución normal como empaquetada.
- Las rutas de base de datos, documentos, configuración, copias y registros se construirán a partir de esa carpeta.
- No se guardarán datos persistentes en AppData, Documentos, Escritorio ni otras ubicaciones externas.
- No se utilizará una ruta absoluta ligada a un usuario o equipo concreto.
- La aplicación comprobará al inicio que puede escribir en las carpetas necesarias y mostrará un error comprensible si no tiene permisos.

La carpeta deberá ubicarse en una ruta local donde el usuario de Windows tenga permisos de lectura y escritura. No se recomienda ejecutar la base SQLite desde una carpeta de red o sincronizada por servicios de nube.

## 5. Base de datos local

SQLite es adecuada para el escenario definido: un único ordenador y uso por turnos, sin varios equipos modificando una base compartida.

Requisitos:

- Activar y verificar claves foráneas.
- Usar transacciones para operaciones que afecten a varios registros.
- Definir restricciones de integridad y campos obligatorios.
- Crear índices para búsquedas habituales.
- Gestionar correctamente conexiones y cierre de la base.
- Configurar un tiempo de espera razonable ante bloqueos.
- Evaluar WAL y su política de checkpoint mediante pruebas; no copiar una base activa ignorando sus archivos auxiliares.
- No permitir dos instancias de la aplicación trabajando simultáneamente sobre la misma carpeta. Implementar un mecanismo de instancia única o bloqueo de ejecución.
- Ejecutar comprobaciones de integridad y ofrecer mensajes claros ante errores.

La base de datos no se colocará en una carpeta compartida de red. Si en el futuro se necesita acceso simultáneo desde varios ordenadores, se revisará la arquitectura y se migrará a un servicio de base de datos centralizado.

## 6. Persistencia de documentos

Los archivos se almacenarán en subcarpetas privadas bajo data/. La base de datos conservará sus metadatos y relaciones, además de una ruta relativa dentro del repositorio documental.

- Evitar nombres de archivo que permitan salir de la carpeta raíz mediante rutas manipuladas.
- Generar identificadores internos únicos para los archivos.
- Validar tamaño, extensión y tipo de contenido según las políticas que se definan.
- Aplicar controles de acceso antes de abrir, exportar o eliminar un documento.
- No exponer documentos sanitarios a perfiles generales.
- Evitar duplicar el archivo al asociarlo a varios registros.
- Definir qué ocurre al eliminar o archivar un registro relacionado.

## 7. Usuarios y sesiones

Aunque el ordenador sea compartido, cada profesional utilizará una cuenta individual.

- Contraseñas protegidas con un algoritmo de hash de contraseñas adecuado y parámetros actualizables.
- No almacenar contraseñas en texto claro.
- Bloqueo automático por inactividad.
- Cierre de sesión y cambio de usuario.
- Permisos comprobados en la capa de aplicación y en los servicios de acceso a datos.
- Registro de operaciones relevantes.
- No confiar únicamente en ocultar controles de la interfaz para proteger información.

La aplicación local no puede ofrecer la misma separación de seguridad que un servidor con controles independientes frente a una persona con privilegios de administrador sobre el propio Windows. Este riesgo deberá contemplarse en el análisis de seguridad del equipo y de la carpeta de datos.

## 8. Portabilidad y copias

Para trasladar la aplicación:

1. Cerrar sesión y salir completamente del programa.
2. Verificar que no queda ningún proceso de la aplicación abierto.
3. Realizar una copia íntegra de la carpeta.
4. Comprobar la copia y trasladarla a una ruta local del otro ordenador.
5. Ejecutar el archivo principal.

No se debe copiar una base de datos SQLite en uso mediante una copia ordinaria de archivos. Las copias de seguridad se realizarán mediante un mecanismo consistente de SQLite o con la aplicación cerrada.

Las copias internas se perderán si se elimina la carpeta completa. Por ello, se ofrecerá exportación de copias cifradas a una ubicación externa autorizada y se documentará cómo restaurarlas. Las copias externas deberán tener acceso restringido y una política de conservación.

## 9. Empaquetado y actualizaciones

Se propone PyInstaller en modo onedir. El resultado incluirá el ejecutable y sus bibliotecas de ejecución en la carpeta de distribución.

- El usuario final solo ejecutará el programa.
- Se probará en instalaciones limpias de Windows compatibles.
- No se implementará un sistema de actualización automática ni un apartado de actualizaciones en la aplicación. Cualquier sustitución manual futura deberá seguir un procedimiento controlado y disponer de copia verificada previa.
- Antes de actualizar se exigirá una copia de seguridad verificada.
- Las migraciones de base de datos se ejecutarán de forma controlada y con posibilidad de recuperación.
- La carpeta podrá trasladarse entre equipos Windows compatibles, respetando permisos, arquitectura y dependencias del sistema operativo.

## 10. Estructura lógica del código

Separar responsabilidades para evitar que las pantallas contengan reglas de negocio o consultas SQL dispersas. Estructura orientativa:

```text
src/
├── app/                   # Inicio, configuración y ciclo de vida
├── ui/                    # Ventanas, diálogos y componentes PySide6
├── domain/                # Entidades y reglas de negocio
├── services/              # Casos de uso y operaciones
├── repositories/          # Acceso a datos
├── persistence/           # SQLAlchemy, SQLite y migraciones
├── security/              # Autenticación, permisos y sesiones
├── documents/             # Almacenamiento y validación de archivos
└── reporting/             # Informes y exportaciones
```

La estructura es una propuesta de separación de responsabilidades; se concretará al revisar el código existente.

## 11. Pruebas técnicas mínimas

- Inicio, cierre de sesión y bloqueo por inactividad.
- Acceso autorizado y denegado por perfil.
- Aislamiento de información sanitaria.
- Integridad de relaciones y transacciones.
- Gestión de errores y bloqueo de base de datos.
- Prevención de dos instancias simultáneas.
- Copia y restauración verificadas.
- Migración de esquema con copia previa.
- Ejecución desde una carpeta con espacios y caracteres no ASCII en su ruta.
- Portabilidad a otro ordenador Windows limpio.
- Pruebas con un volumen de datos representativo.

## 12. Evolución futura

Si cambian las condiciones —por ejemplo, varios ordenadores trabajando simultáneamente con los mismos datos— no se compartirá el archivo SQLite por red. Se diseñará una arquitectura cliente-servidor con base de datos central, autenticación y permisos aplicados en el servidor. Esa ampliación queda fuera del alcance actual.


> **Especificación vigente:** consultar [Decisiones consolidadas del diseño](DECISIONES_CONSOLIDADAS.md). Este documento reúne las decisiones aprobadas más recientes y prevalece sobre cualquier apartado anterior que las contradiga.
