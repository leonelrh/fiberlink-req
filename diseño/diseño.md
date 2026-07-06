# Decisiones de Diseño — FiberLink Andina Telecom

**Modelo LLM utilizado:** Claude Fable 5 (`claude-fable-5`, Anthropic)
**Fecha:** 5 de julio de 2026

Este documento resume los criterios de decisión principales del diseño de alto nivel (microservicios, diagramas de secuencia y diagrama de arquitectura multinube), con trazabilidad a los lineamientos por código (ARQ-10). Al final se declaran explícitamente los criterios aplicados que **no** están listados en la carpeta `lineamientos/`, según lo pedido en "Elementos adicionales" de `contexto/instrucciones.md`.

---

## D01. Distribución de responsabilidades por nube

**Decisión:** Azure concentra la exposición/gobierno de APIs y la capa de integración empresarial; GCP concentra el bus de eventos, la analítica, la trazabilidad y la observabilidad; AWS se limita a la huella existente del Portal de Clientes.

**Criterio:** Aprovechar lo que ya existe en cada nube (API Management y mesa de ayuda en Azure; Pub/Sub, BigQuery y modelo de churn en GCP; portal y PostgreSQL en AWS) en lugar de migrar. Es la propuesta de uso de los tres archivos de stack (`stack_tecnologico_azure.md`, `_gcp.md`, `_aws.md`) y reduce el impacto lateral (ARQ-07). La separación de dominios funcionales por nube cumple ARQ-01.

## D02. Plataforma de Integración Empresarial con conector único hacia los sistemas core

**Decisión:** `ms-conectores-core` es el único componente que habla con CRM, Inventario Oracle, OSS/OCS, Facturación, ERP, Field Service, GIS e ITSM. Expone una API canónica interna (`POST /v1/core/{sistema}/{operacion}`) que traduce el modelo canónico al protocolo de cada sistema (REST, SOAP, JDBC, archivos).

**Criterio:** Elimina las integraciones punto a punto (objetivo de la iniciativa 1) y garantiza INT-07 (los core no se integran directamente entre sí para nuevos flujos), ARQ-02 y ARQ-09 (la plataforma habilita las demás iniciativas). Cada invocación aplica timeout, reintentos controlados y circuit breaker por sistema (INT-03), valida formato antes de invocar (INT-10), registra evidencias de intercambio (INT-08) y llega on-premises solo por VPN/ExpressRoute (SEG-10, INT-12).

## D03. Selección de runtime por patrón de tráfico y volumetría

**Decisión:**

| Runtime | Microservicios | Justificación (volumetría) |
|---|---|---|
| Azure Container Apps (siempre activo) | ms-solicitudes, ms-cobertura, ms-capacidad, ms-estado-servicio, ms-programacion-instalacion, ms-activacion, ms-conectores-core | Tráfico constante y alto: 150K consultas de cobertura/día, 80K validaciones de capacidad/día, 40K solicitudes/día, 20K consultas de estado/día, pico 4x (≈25K consultas de cobertura/hora pico) |
| Azure Functions (intermitente / dirigido por eventos) | ms-eventos-negocio, ms-notificaciones, ms-conciliacion-datos | ~116K eventos/día (40% de transacciones, 2–5 KB c/u) en ráfagas; notificaciones disparadas por Service Bus; conciliación por timer |
| GCP Cloud Run (streaming continuo) | ms-trazabilidad, ms-ingesta-red, ms-correlacion-incidentes | Ingesta continua desde Pub/Sub; rol de GCP: observabilidad y analítica |

**Criterio:** ARQ-08 exige criterios explícitos para elegir entre microservicios, funciones y servicios administrados; ESC-01 exige diseñar sobre la volumetría; ESC-03 exige escalado horizontal (los tres runtimes escalan por réplicas/instancias). Es el mismo criterio Lambda-vs-Fargate del stack AWS, aplicado con los equivalentes de Azure y GCP.

## D04. Síncrono = APIs versionadas; asíncrono = eventos con esquema estándar

**Decisión:** Las consultas y comandos entran por Azure API Management como APIs `/v1` documentadas con contratos de entrada/salida/errores (INT-01, INT-04, INT-05). Los hechos de negocio se propagan como eventos con `eventId`, `eventType`, `version`, `correlationId`, `sourceSystem`, `timestamp`, `payload` (INT-09), publicados por `ms-eventos-negocio`.

**Criterio:** INT-02 y ESC-05 (lo diferible se ejecuta asíncrono). El `correlationId` se propaga extremo a extremo desde el canal hasta el sistema core y sus eventos derivados (OBS-02, OBS-06, OBS-08), lo que habilita la búsqueda por correlación en `ms-trazabilidad` (OBS-10).

## D05. Doble broker: Azure Service Bus + GCP Pub/Sub

**Decisión:** `ms-eventos-negocio` publica en Service Bus (distribución interna: notificaciones, proyección de estado 360, sincronización de réplicas) y en Pub/Sub (bus de eventos para trazabilidad, analítica, churn y futuros suscriptores).

**Criterio:** Cada broker sirve al rol de su nube (D01). Separar el tráfico transaccional interno del consumo analítico evita que la analítica se convierta en cuello de botella del flujo operativo (ESC-06, ESC-10). Ambos caminos tienen DLQ y reproceso controlado (INT-11).

## D06. Réplicas de lectura locales en lugar de consultar Oracle on-premises en línea

**Decisión:** `ms-cobertura`, `ms-capacidad` y `ms-estado-servicio` responden desde réplicas materializadas en Azure SQL, sincronizadas por eventos desde Inventario Oracle, GIS y los sistemas core; no consultan Oracle en cada petición.

**Criterio:** 150K + 80K + 20K consultas/día con pico 4x golpearían directamente un Oracle on-premises heredado (ESC-06); la réplica implementa caché de lecturas frecuentes (ESC-04), aísla los picos comerciales de los procesos críticos de activación/facturación (ESC-10) y tolera indisponibilidad parcial del on-premises con degradación controlada (INT-12, ESC-09). Las escrituras que exigen verdad fuerte (reserva de puerto) sí se validan contra la fuente vía `ms-conectores-core`.

## D07. Saga con compensación para los procesos multi-sistema (activación y programación)

**Decisión:** `ms-activacion` y `ms-programacion-instalacion` orquestan sus pasos entre OSS, CRM, Facturación, Inventario, ERP y Field Service como una saga con estado persistido en Azure SQL y acciones de compensación (`compensarTodo`) si un paso falla; `ms-solicitudes` compensa la reserva de puerto si el CRM falla.

**Criterio:** No existen transacciones distribuidas entre un OSS on-premises, un CRM SaaS y una facturación Unix heredada; la saga garantiza el resultado de negocio atómico que exige RNOF01 (activación y facturación consistentes) con degradación controlada (ESC-09). Toda operación de escritura acepta `idempotencyKey` para tolerar reintentos y duplicados (INT-06). Ver "Criterios adicionales" abajo.

## D08. Trazabilidad y auditoría centralizadas con copia inmutable

**Decisión:** `ms-trazabilidad` consolida trazas de integración y registros de auditoría en BigQuery (particionado por fecha, consultable por `correlationId`, sistema, cliente, servicio y rango de fechas) y mantiene copia WORM en Cloud Storage con retención bloqueada de 5 años.

**Criterio:** RF07 + RNOF03 (auditabilidad de activación/facturación), INT-08 (evidencias de intercambio), OBS-10 (búsqueda), SEG-06 (auditoría de operaciones críticas) y SEG-12. La consulta se publica a través de API Management para mantener el gobierno central de APIs (INT-01). Las fallas se clasifican por tipo según OBS-09.

## D09. Observabilidad técnica por nube con dashboards unificados

**Decisión:** Application Insights + Azure Monitor/Log Analytics para los microservicios en Azure; Cloud Logging/Monitoring para los de GCP; CloudWatch para el portal en AWS. KPIs de negocio y operación en BigQuery → Power BI.

**Criterio:** OBS-01 (logs estructurados), OBS-03 (métricas técnicas y de negocio), OBS-04 (alertas de disponibilidad/latencia/saturación/fallos de publicación), OBS-07 (dashboards para soporte, NOC, operación y arquitectura). Se usa el servicio nativo de cada nube en lugar de una herramienta única para no crear un punto de acoplamiento adicional; la unificación se logra en la capa de datos (BigQuery/Power BI) y por `correlationId` (OBS-02).

## D10. Seguridad transversal

**Decisión:** Autenticación centralizada OAuth2 con Microsoft Entra ID y scopes por consumidor/operación; Application Gateway + WAF y rate limiting en API Management para todo lo expuesto a canales; secretos en Key Vault (Azure) y Secret Manager (GCP) con Managed Identity y rotación; TLS 1.2+ en todas las comunicaciones; eventos sin datos personales innecesarios; accesos administrativos y operaciones críticas auditadas vía `ms-trazabilidad`.

**Criterio:** SEG-01, SEG-02, SEG-03, SEG-04, SEG-05, SEG-07, SEG-09, SEG-10, SEG-11, SEG-12 y RNOF02. Las reglas de negocio no residen en los canales (ARQ-06), por lo que la autorización fina se aplica en APIM + microservicio, no en el portal ni la app.

## D11. AWS se conserva como está, integrado por APIs

**Decisión:** El Portal de Clientes permanece en AWS (CloudFront + WAF, ECS Fargate, Aurora PostgreSQL, ElastiCache Redis) y consume los nuevos flujos exclusivamente a través de API Management.

**Criterio:** Stack AWS: Fargate por tráfico constante 24/7, preferencia de ECS sobre EKS, Aurora PostgreSQL como base existente del portal, ElastiCache para lecturas frecuentes (ESC-04). Evitar migraciones sin valor de negocio (ARQ-07) y evitar que el portal se integre directo a sistemas core (INT-07, ARQ-06).

---

## Criterios adicionales aplicados (no listados en `lineamientos/`)

Según "Elementos adicionales" de `contexto/instrucciones.md`, se declaran los patrones usados que no tienen código de lineamiento, con el criterio que justificó incluirlos:

1. **Patrón Saga con compensación** (`ms-activacion`, `ms-programacion-instalacion`, `ms-solicitudes`). Criterio: lograr atomicidad de negocio entre sistemas heterogéneos (SaaS, on-premises, Unix heredado) donde las transacciones distribuidas no son viables; soporta RNOF01 y ESC-09 pero el patrón en sí no está prescrito en los lineamientos.
2. **Réplica de lectura materializada por eventos (CQRS ligero)** (`ms-cobertura`, `ms-capacidad`, `ms-estado-servicio`). Criterio: proteger el Oracle on-premises del volumen de consultas comerciales (150K/día, pico 4x) y dar al cliente la misma vista que registran los core; materializa ESC-04/ESC-06/ESC-10 con un patrón concreto no listado.
3. **Almacenamiento WORM con retención bloqueada** (`ms-trazabilidad`). Criterio: RNOF03 exige auditoría confiable de activación/facturación por 5 años; la inmutabilidad (no-repudio) es el mecanismo elegido, no prescrito por los lineamientos.
4. **`idempotencyKey` a nivel de contrato HTTP** (todas las APIs de escritura). Criterio: INT-06 exige idempotencia en integraciones críticas; se extendió el requisito al contrato de las APIs de negocio expuestas a canales, devolviendo la respuesta original ante claves repetidas (HTTP 409/200 según el caso).

---

## Trazabilidad requerimiento → microservicio → diagramas (ARQ-03, ARQ-10)

| Requerimiento | Microservicio responsable | Diagrama de secuencia |
|---|---|---|
| RF01 Registrar solicitud de servicio | ms-solicitudes | `diagramas_secuencia/RF01_registrar_solicitud_servicio.md` |
| RF02 Integrar sistemas críticos | ms-conectores-core | `diagramas_secuencia/RF02_integrar_sistemas_criticos.md` |
| RF03 Consultar cobertura | ms-cobertura | `diagramas_secuencia/RF03_consultar_cobertura.md` |
| RF04 Validar capacidad | ms-capacidad | `diagramas_secuencia/RF04_validar_capacidad.md` |
| RF05 Consultar estado de servicio | ms-estado-servicio | `diagramas_secuencia/RF05_consultar_estado_servicio.md` |
| RF06 Publicar eventos de negocio | ms-eventos-negocio | `diagramas_secuencia/RF06_publicar_eventos_negocio.md` |
| RF07 Trazabilidad de integración | ms-trazabilidad | `diagramas_secuencia/RF07_trazabilidad_integracion.md` |
| RF08 Programar instalación | ms-programacion-instalacion | `diagramas_secuencia/RF08_programar_instalacion_servicio_internet.md` |
| RF09 Notificar programación | ms-notificaciones | `diagramas_secuencia/RF09_notificar_programacion_instalacion.md` |
| RF10 Reprogramar instalación | ms-programacion-instalacion | `diagramas_secuencia/RF10_reprogramar_instalacion_servicio_internet.md` |
| RF11 Activar servicio | ms-activacion | `diagramas_secuencia/RF11_activar_servicio_internet.md` |
| RF12 Correlación incidente–cliente | ms-correlacion-incidentes | `diagramas_secuencia/RF12_correlacion_incidente_red_cliente.md` |
| RNOF01 Integridad de datos | ms-conciliacion-datos (+ sagas de D07) | — (transversal) |
| RNOF02 Seguridad de plataformas | Transversal: APIM, Entra ID, Key Vault, WAF (D10) | — (transversal) |
| RNOF03 Auditabilidad activación/facturación | ms-trazabilidad (WORM) | — (transversal) |
| RNOF04 Operación e integración de red | ms-ingesta-red | — (transversal) |

Arquitectura completa: `diagrama_arquitectura.md`. Detalle por microservicio (contratos, SQL, pseudocódigo, Gherkin y lineamientos por código): `microservicios/`.
