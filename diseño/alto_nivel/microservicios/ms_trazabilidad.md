# Microservicio: ms-trazabilidad

## Descripción general
- **Dominio:** Observabilidad (ARQ-01)
- **Requerimientos origen:** RF07 - Registrar trazabilidad de integración y RNOF03 - Auditabilidad de activación y facturación (ARQ-03)
- **Nube / Runtime:** GCP Cloud Run (rol de GCP: observabilidad y analítica; ingesta continua desde Pub/Sub)
- **Almacenamiento:** BigQuery (trazas y auditoría consultables, particionadas por fecha) + Cloud Storage con política de retención bloqueada (copia WORM inmutable del log de auditoría, 5 años — RNOF03)
- **Exposición:** API de consulta publicada a través de Azure API Management (gobierno central de APIs), backend en Cloud Run

## Funcionalidades

### F1. Registrar traza de integración (ingesta)

Consume el tópico Pub/Sub `trazabilidad-integracion` donde todos los microservicios publican sus evidencias de intercambio (INT-08).

**Contrato de entrada** — mensaje Pub/Sub:
```json
{
  "eventId": "uuid", "eventType": "TrazaIntegracion", "version": "1.0",
  "correlationId": "uuid", "sourceSystem": "ms-solicitudes", "timestamp": "...",
  "payload": {
    "sistemaOrigen": "CRM", "sistemaDestino": "ms-solicitudes", "canal": "CRM",
    "operacion": "crearCasoVenta", "resultado": "OK", "tipoFalla": null,
    "codigoError": null, "tiempoRespuestaMs": 320,
    "clienteId": "CLI-99213", "servicioId": "SRV-33421"
  }
}
```

**Contrato de salida:** ACK; inserción en `traza_integracion`; mensajes malformados → tópico DLQ (INT-11).

**Pseudocódigo**
```
funcion alRecibirTraza(mensaje):
    si no validarEnvolvente(mensaje): publicarDLQ(mensaje); retornar
    enmascarar campos sensibles del payload            # OBS-05
    insertar traza_integracion (streaming insert BigQuery)
    actualizar métricas por sistema/tipoFalla          # OBS-03, OBS-09
```

### F2. Consultar trazabilidad

**Contrato de entrada** — `GET /v1/trazas?correlationId=...&sistemaOrigen=...&sistemaDestino=...&clienteId=...&servicioId=...&desde=...&hasta=...&tipoFalla=...` (OBS-10)

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "total": 6,
  "trazas": [
    { "timestamp": "...", "sistemaOrigen": "PORTAL", "sistemaDestino": "ms-solicitudes", "operacion": "registrarSolicitud", "resultado": "OK", "tiempoRespuestaMs": 850 },
    { "timestamp": "...", "sistemaOrigen": "ms-solicitudes", "sistemaDestino": "CRM", "operacion": "crearCasoVenta", "resultado": "OK", "tiempoRespuestaMs": 320 }
  ]
}
```

**Errores:** `400` sin al menos un filtro y rango de fechas válido, `401/403` rol sin permiso de consulta, `404` sin resultados (lista vacía con `total: 0`, no error), `503` almacén no disponible.

**Pseudocódigo**
```
funcion consultarTrazas(filtros):
    si no autorizado(token, "trazas:consultar"): auditar; retornar 401/403      # E04
    si filtros vacíos o rango > 90 días: retornar 400                           # E02, protege rendimiento
    resultados = bigquery.consultar(traza_integracion, filtros, orden=timestamp)
    registrar consulta (usuario, filtros, fecha)                                # SEG-12
    retornar 200 resultados
```

### F3. Registrar evento de auditoría (RNOF03)

Consume el tópico `auditoria-negocio`. Cubre los 14 eventos auditables del ciclo instalación→activación→facturación.

**Contrato de entrada** — mensaje con envolvente INT-09; payload:
```json
{
  "ordenInstalacionId": "ORD-55012", "clienteId": "CLI-99213",
  "tipoEvento": "GENERACION_CONTRATO",
  "estadoAnterior": "EN_ACTIVACION", "estadoNuevo": "CONTRATO_GENERADO",
  "usuarioProceso": "tecnico.jperez", "resultado": "EXITOSO", "mensajeError": null,
  "datosEvento": { "contrato": "CT-2026-7781", "plan": "300MB", "monto": 89.90, "equipos": ["ONT-8912"], "tecnico": "jperez" }
}
```

**Contrato de salida:** ACK; inserción append-only en BigQuery + archivo WORM en Cloud Storage (bucket con retención bloqueada 5 años). No existe API de modificación ni borrado.

**Pseudocódigo**
```
funcion alRecibirEventoAuditoria(mensaje):
    si no validarEnvolvente(mensaje) o faltan datos mínimos: publicarDLQ + alerta; retornar
    registro = construirRegistroAuditoria(mensaje)      # incluye hash encadenado con registro anterior
    insertar auditoria_evento (append-only)
    escribir copia JSON en gs://auditoria-worm/{fecha}/{eventId}.json   # inmutable, retención 5 años
```

### F4. Consultar auditoría (rol Auditor)

**Contrato de entrada** — `GET /v1/auditoria?ordenId=...&clienteId=...&contrato=...&desde=...&hasta=...&tipoEvento=...`

**Contrato de salida** — `200 OK`: línea de tiempo completa de la orden (programación → instalación → activación → contrato → facturación → cierre) en una sola vista, incluyendo verificación de consistencia:
```json
{
  "ordenInstalacionId": "ORD-55012",
  "eventos": [ { "tipoEvento": "PROGRAMACION", "...": "..." } ],
  "verificacionConsistencia": {
    "contratoActivacionVsFacturacion": "CONSISTENTE",
    "planActivadoVsFacturado": "CONSISTENTE",
    "fechaFacturacionPosteriorActivacion": true,
    "clienteConsistente": true,
    "equiposVinculadosAContrato": true
  }
}
```

**Errores:** `401/403` rol distinto de AUDITOR/ADMIN_SISTEMAS, `400` filtros insuficientes.

**Pseudocódigo**
```
funcion consultarAuditoria(filtros, usuario):
    si rol(usuario) not in [AUDITOR, ADMIN_SISTEMAS]: auditar intento; retornar 403
    eventos = bigquery.consultar(auditoria_evento, filtros, orden=timestamp)
    verificacion = compararActivacionVsFacturacion(eventos)     # contrato, plan, fechas, cliente, equipos
    si discrepancia: registrar evento INCONSISTENCIA en auditoria_evento
    retornar 200 { eventos, verificacion }
```

## Estructura de base de datos (BigQuery — DDL SQL)

```sql
CREATE TABLE integracion.traza_integracion (
    event_id        STRING NOT NULL,
    correlation_id  STRING NOT NULL,
    ts              TIMESTAMP NOT NULL,
    sistema_origen  STRING NOT NULL,
    sistema_destino STRING NOT NULL,
    canal           STRING,
    operacion       STRING,
    resultado       STRING NOT NULL,          -- OK | FALLIDO
    tipo_falla      STRING,                   -- VALIDACION|AUTENTICACION|TIMEOUT|INDISPONIBILIDAD|ERROR_FUNCIONAL|ERROR_TECNICO
    codigo_error    STRING,
    tiempo_respuesta_ms INT64,
    cliente_id      STRING,
    servicio_id     STRING
)
PARTITION BY DATE(ts)
CLUSTER BY correlation_id, sistema_destino;

CREATE TABLE integracion.auditoria_evento (
    event_id            STRING NOT NULL,
    correlation_id      STRING NOT NULL,
    ts                  TIMESTAMP NOT NULL,   -- con zona horaria
    orden_instalacion_id STRING,
    cliente_id          STRING NOT NULL,
    tipo_evento         STRING NOT NULL,      -- 14 tipos auditables RNOF03
    estado_anterior     STRING,
    estado_nuevo        STRING,
    usuario_proceso     STRING NOT NULL,
    resultado           STRING NOT NULL,      -- EXITOSO | FALLIDO
    mensaje_error       STRING,
    contrato_numero     STRING,
    plan_contratado     STRING,
    monto_facturacion   NUMERIC,
    equipos             STRING,               -- JSON
    tecnico_asignado    STRING,
    hash_encadenado     STRING NOT NULL       -- hash(registro anterior + actual): evidencia de no alteración
)
PARTITION BY DATE(ts)
CLUSTER BY orden_instalacion_id, cliente_id;

CREATE TABLE integracion.consulta_auditoria_log (
    consulta_id     STRING NOT NULL,
    usuario         STRING NOT NULL,
    rol             STRING NOT NULL,
    filtros         STRING NOT NULL,
    ts              TIMESTAMP NOT NULL
) PARTITION BY DATE(ts);
```

> Inmutabilidad (RNOF03): la tabla `auditoria_evento` es append-only (sin UPDATE/DELETE permitidos por IAM); la copia primaria legal reside en Cloud Storage con **bucket retention policy bloqueada por 5 años**, inalterable incluso por administradores. Las consultas corren sobre BigQuery, separadas de los sistemas operativos (no impactan su rendimiento).

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF07-E01 | Ejecución exitosa: traza registrada/consultada conforme al contrato |
| RF07-E02 | Solicitud inválida rechazada con detalle |
| RF07-E03 | Almacén no disponible: error controlado y registro |
| RF07-E04 | Consumidor no autorizado rechazado con auditoría |
| RF07-CA01..CA05 | Criterios de aceptación de RF07 (búsqueda por correlationId) |
| RNOF03-EV01..EV14 | Los 14 eventos auditables del ciclo instalación→activación→facturación |
| RNOF03-CA | Consulta en una sola vista, verificación de consistencia activación/facturación, inmutabilidad, retención 5 años, sin impacto en operación |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-10 | Dominio observabilidad; trazable a RF07/RNOF03; sustenta trazabilidad global del diseño |
| INT-02 / INT-08 / INT-09 / INT-11 | Ingesta asíncrona de evidencias con envolvente estándar y DLQ |
| OBS-01 / OBS-02 / OBS-05 / OBS-06 / OBS-08 / OBS-09 / OBS-10 | Logs estructurados, rastreo por correlationId end-to-end, sin datos sensibles, correlación evento-transacción, clasificación de fallas, búsqueda multifiltro |
| ESC-05 / ESC-06 | Ingesta asíncrona; BigQuery separa consulta analítica de la operación |
| SEG-02 / SEG-04 / SEG-06 / SEG-12 | Cifrado en reposo, acceso por rol (Auditor), registro de auditoría de operaciones críticas y de las propias consultas |
