# Catálogos vacunales y trazabilidad documental

## Principios

Los calendarios se almacenan como ediciones documentales independientes. Una edición conserva su jurisdicción, código, título, vigencia declarada, fuente y referencia de página. No se sobrescriben ediciones anteriores.

El catálogo no genera automáticamente dosis pendientes ni determina indicaciones, contraindicaciones, productos, intervalos clínicos o pautas individuales. La ausencia de un registro de administración no demuestra que una dosis esté pendiente. Las valoraciones individuales deben ser realizadas y fundamentadas por profesionales sanitarios.

Los estados de las ediciones cargadas son documentales. La transcripción técnica y las pruebas de migración no equivalen a validación clínica o autorización institucional.

## Ediciones incorporadas

| Jurisdicción | Edición | Fuente | Uso |
|---|---|---|---|
| Melilla | Infantil 2026 | Orden 3567/2025, BOME 6335, Anexo I, p. 4167 | Referencia infantil local |
| Melilla | Adulto 2026 | Orden 3567/2025, BOME 6335, Anexo II, p. 4168 | Referencia adulta local |
| Melilla | Acelerado 2025 | Calendario acelerado MELILLA 2025, tablas 1-4 | Referencia histórica por tramos de edad |
| SNS | Riesgo infantil 2026 | CISNS, calendario recomendado 2026, 4 páginas | Referencia nacional para condiciones de riesgo |
| SNS | Riesgo adultos 2026 | CISNS, calendario recomendado 2026, 5 páginas | Referencia nacional para condiciones de riesgo |

Fuentes oficiales:

- Melilla, Orden 3567/2025: https://bomemelilla.es/bome/descargar/BOME-A-2025-1322.pdf
- Melilla, calendario acelerado 2025: https://melilla.es/melillaPortal/RecursosWeb/DOCUMENTOS/1/4_30756_1.pdf
- SNS, riesgo infantil 2026: https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/docs/CalendarioVacunacion_GRinfantil.pdf
- SNS, riesgo adultos 2026: https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/docs/CalendarioVacunacion_GRadultos.pdf

## Diferencias de jurisdicción y vigencia

- Los calendarios infantil y adulto de Melilla 2026 proceden de la orden local publicada en BOME.
- Las dos ediciones de grupos de riesgo están identificadas como SNS, no como calendarios propios de Melilla. El portal de Melilla consultado enlaza documentos de grupos de riesgo de 2024; no se han etiquetado como ediciones 2026 locales.
- El calendario acelerado incorporado corresponde expresamente a 2025 y se conserva como edición histórica. No debe presentarse como pauta acelerada vigente sin comprobar una actualización posterior y la validación sanitaria correspondiente.

## Tipos de entrada

- `dose`: referencia documental de una dosis individual del calendario.
- `schedule`: secuencia completa de visitas/dosis de un calendario acelerado. No se ofrece como una dosis individual al registrar revisiones de dosis.

Las administraciones pueden vincularse a una referencia `dose`. Una revisión que enlaza una administración debe conservar la misma referencia. Las secuencias completas de rescate no pueden vincularse como si fueran una dosis individual.

## Datos de trazabilidad de una administración

Cada administración puede conservar, además de la vacuna, fecha y referencia de dosis:
- Fabricante.
- Nombre comercial o producto.
- Número de lote.
- Centro sanitario.
- Profesional que administró.
- Documento justificativo sanitario del mismo expediente.

Estos campos son opcionales porque puede que un antecedente histórico no disponga de todos los datos. La aplicación no debe inventar ni completar datos ausentes. El justificante se vincula a un documento sanitario ya incorporado al expediente y no se duplica como archivo independiente.

## Pendientes de validación antes del uso operativo

1. Revisión de transcripción, notas, edades, intervalos y vigencias por profesional sanitario designado.
2. Confirmación de que las ediciones SNS 2026 son las referencias adecuadas para las situaciones de riesgo atendidas en Melilla y de si existe documentación local complementaria más reciente.
3. Revisión de la edición acelerada de Melilla y búsqueda periódica de una versión posterior.
4. Validación de la captura de trazabilidad de cada administración (producto comercial, lote, fabricante, centro y profesional, documento sanitario de origen), incluidos los criterios de obligatoriedad y los casos en que el dato no consta.
5. Pruebas funcionales en una instalación Windows limpia y con datos ficticios.

Hasta completar estos puntos, los catálogos son material de consulta documental y no deben utilizarse para decidir tratamientos ni para gestionar automáticamente calendarios individuales.
