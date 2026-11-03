# Base documental del calendario vacunal de Melilla 2026

> Documento de análisis de fuentes oficiales para preparar el catálogo de vacunación de la aplicación. No constituye una pauta clínica ni habilita la generación automática de prescripciones.

## Fuentes oficiales y vigencia

1. **Ciudad Autónoma de Melilla, Orden n.º 3567, de 9 de diciembre de 2025**, publicada en BOME n.º 6335, de 12 de diciembre de 2025, artículo 1322. Incluye el calendario infantil a partir de 2026 y el calendario del adulto 2026.
   - Página oficial: https://www.melilla.es/melillaportal/contenedor.jsp?anuncio=1&contenido=38585&nivel=1400&seccion=s_fdoc_d4_v1.jsp&tipo=5
   - PDF del artículo y anexos: https://bomemelilla.es/bome/descargar/BOME-A-2025-1322.pdf
2. **Ministerio de Sanidad, Calendario común de vacunación e inmunización a lo largo de toda la vida, recomendado 2026**, aprobado por el CISNS el 12 de diciembre de 2025.
   - PDF: https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/docs/CalendarioVacunacion_Todalavida.pdf
   - Portal de calendarios 2026: https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/home.htm
3. **Portal de calendarios de vacunaciones de Melilla**, actualizado el 12 de diciembre de 2025. Publica además el calendario acelerado 2025 y los documentos de grupos de riesgo infantil y adulto.
   - https://www.melilla.es/melillaportal/contenedor.jsp?anuncio=1&codMenu=9&codMenuPN=601&contenido=32611&nivel=1400&seccion=s_fdes_d4_v1.jsp&tipo=6

## Calendario infantil Melilla a partir de 2026

Transcripción de las edades y dosis indicadas en el Anexo I del BOME 6335, páginas 4167-4168. Los códigos de dosis se conservan como referencia documental; no deben convertirse directamente en órdenes médicas.

| Edad | Vacunas / dosis que aparecen en el anexo |
|---|---|
| Prenatal | dTpa durante el embarazo entre semanas 28 y 36; gripe IM durante campaña, en cualquier momento de gestación |
| 0 meses | HB neonatal en el supuesto indicado en la nota (a) |
| 2 meses | VPI 1, DTPa 1, Hib 1, HB 1, MenB 1, neumococo 1, rotavirus 1 |
| 4 meses | VPI 2, DTPa 2, Hib 2, HB 2, MenACWY, MenB 2, neumococo 2, rotavirus 2 |
| 6 meses | Neumococo 3; rotavirus 3 solo si el preparado requiere pauta de tres dosis |
| 11 meses | VPI 3, DTPa 3, Hib 3, HB 3, neumococo 4 |
| 12 meses | Triple vírica, MenACWY, MenB 3 |
| 15 meses | Hepatitis A 1, varicela 1 |
| 24 meses | Hepatitis A 2 |
| 3 años | Tetravírica como segunda dosis frente a sarampión, rubéola, parotiditis y varicela |
| 6 años | VPI 4 y DTPa 4 |
| 12 años | MenACWY, VPH; varicela 2 dosis si susceptible según la nota (d) |
| 14 años | Td 5 |
| 6-24 meses | Gripe intramuscular según campaña |
| 24 meses-17 años | Gripe intranasal o intramuscular según campaña |

### Notas expresas del anexo oficial

- HB neonatal: para hijos de madres portadoras, la pauta indicada es 0, 1 y 6 meses (nota a); la indicación exacta y cualquier pauta especial requieren validación sanitaria.
- Rotavirus: la tercera dosis solo se contempla cuando el preparado utilizado es de tres dosis (nota b).
- Tetravírica: reúne sarampión, rubéola, parotiditis y varicela (nota c).
- Varicela a los 12 años: para personas que refieran no haber pasado la enfermedad ni haber sido vacunadas; pauta de dos dosis (nota d).
- Anticuerpo monoclonal frente a VRS: menores de 12 meses solo durante campaña, del 1 de octubre al 31 de marzo (nota e). Es inmunización pasiva y debe modelarse separadamente de vacunas.
- Gripe: IM de 6 a 24 meses e intranasal o IM de 24 meses a 17 años (nota f).

## Cambios explícitos de la actualización 2026

- La segunda dosis de triple vírica y la segunda dosis de varicela que antes figuraban por separado a los 3 años se agrupan en una administración tetravírica a los 3 años. Las primeras dosis siguen separadas: triple vírica a los 12 meses y varicela a los 15 meses.
- Desde 2026 la vacuna antigripal es intramuscular desde los 6 hasta los 24 meses; entre 24 meses y 17 años puede ser intranasal o intramuscular.
- El anexo también muestra VRS como anticuerpo monoclonal infantil en la ventana de campaña; no se debe presentar como vacuna convencional ni inferir indicación fuera de las condiciones oficiales.

## Calendario común SNS 2026: relación con Melilla

El calendario común del SNS sirve como marco estatal, pero el calendario publicado por Melilla contiene adaptaciones y detalles territoriales. La aplicación debe conservar ambos documentos como catálogos/versiones independientes y priorizar el calendario territorial aplicable, mostrando la referencia estatal como contexto, no fusionando filas automáticamente.

El portal del Ministerio incluye documentos específicos para grupos de riesgo infantil y adulto. Las indicaciones de riesgo no se deben inferir únicamente de edad o de diagnósticos escritos libremente: requieren condición documentada y validación por profesional sanitario.

## Reglas de implementación obligatorias

1. Cada registro de vacuna administrada pertenece al expediente permanente del menor (minor_id); la estancia es un contexto histórico opcional y nunca la clave principal.
2. El calendario es un catálogo versionado por jurisdicción, fecha de vigencia, edición, fuente y referencia oficial. Nunca sobrescribir ediciones anteriores.
3. La elegibilidad informativa debe considerar fecha de nacimiento, cohorte, fecha de vigencia del calendario, dosis documentadas y antecedentes conocidos. No aplicar mecánicamente el calendario 2026 a todas las cohortes.
4. Separar vacunas sistemáticas, recuperación/acelerado, grupos de riesgo, campañas estacionales e inmunización pasiva VRS. Cada modalidad debe conservar su fuente y versión.
5. Los calendarios acelerados y grupos de riesgo se mantienen como documentos separados. No generar automáticamente dosis de rescate, intervalos, contraindicaciones ni recomendaciones clínicas a partir de reglas simplificadas.
6. El sistema puede presentar una lista orientativa para revisión sanitaria: prevista, pendiente de verificar, administrada, aplazada, no administrada con motivo o no aplicable tras validación. El estado no sustituye el juicio clínico.
7. Toda administración es inmutable. Un error se corrige mediante rectificación vinculada, preservando el dato original, autor, fecha y motivo.
8. Las vacunas administradas antes del ingreso o fuera del centro se incorporan al expediente sin exigir estancia activa.
9. No mostrar como «pendiente» una dosis solo porque no exista registro en la aplicación: distinguir claramente «sin dato/documentación» de «pendiente confirmado por profesional».
10. La UI debe advertir que las fechas por edad son referencias del calendario y que el centro de salud/profesional sanitario confirma pauta, producto, intervalos y oportunidad.

## Pendiente de verificación antes de activar reglas en producción

- Revisar el PDF completo del calendario acelerado Melilla 2025 y sus notas de edades mínimas, intervalos y cohortes.
- Obtener y revisar las versiones vigentes de los documentos Melilla de grupos de riesgo infantil y adulto; no reutilizar documentos antiguos sin comprobar edición.
- Verificar las reglas de cohortes y transición entre ediciones con la autoridad sanitaria competente.
- Validar clínicamente el catálogo, los textos y cualquier cálculo de fechas antes de activarlo. Hasta entonces, la app solo debe mostrar los registros individuales y el contenido documental, sin calcular indicaciones automáticas.
