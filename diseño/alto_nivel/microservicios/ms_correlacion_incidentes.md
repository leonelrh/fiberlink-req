# Microservicio: ms-correlacion-incidentes

## Descripción general
- **Dominio:** Operación / Observabilidad (ARQ-01)
- **Requerimiento origen:** RF12 - Correlación de incidentes de red con clientes afectados (ARQ-03); consume lo habilitado por RNOF04
- **Nube / Runtime:** GCP Cloud Run (procesamiento continuo de alarmas normalizadas desde Pub/Sub)
- **Integraciones:** ITSM/mesa de ayuda en Azure (vía ms-conectores-core), ms-notificaciones (avisos proactivos, IVR, portal), BigQuery/Power BI (KPIs)
- **Base de datos:** estado operativo de alarmas/incidentes en BigQuery (DDL abajo); topología provista por ms-ingesta-red

## Funcionalidades

### F1. Correlacionar alarmas y crear incidente maestro

Consume `red-alarmas-normalizadas`, deduplica, agrupa por topología, estima causa raíz, calcula clientes afectados (marcando empresariales con SLA) y crea el incidente maestro en el ITSM en menos de 5 minutos.

**Contrato de entrada:** evento `AlarmaRed` v1.0 (envolvente INT-09, ver ms-ingesta-red).

**Contrato de salida:** incidente maestro:
```json
{
  "incidenteId": "INC-2211",
  "estado": "ACTIVO",
  "causaRaizProbable": { "nodoId": "NODO-4512", "elemento": "FIBRA-TRONCAL-07", "confianza": 0.91 },
  "alarmasAgrupadas": 4812,
  "clientesAfectados": { "total": 12450, "empresariales": 320, "conSLA": 145 },
  "itsmTicketId": "ITSM-99120",
  "correlationId": "uuid"
}
```

**Pseudocódigo**
```
funcion alRecibirAlarma(evento):
    alarma = evento.payload
    existente = alarmas.buscarActiva(alarma.nodoId, alarma.tipoAlarma)
    si existente:                                                        # E06 deduplicación
        existente.ocurrencias++; actualizar ts; retornar                 # sin alarma ni incidente duplicado
    topo = topologia.obtener(alarma.nodoId)
    si topo nula o desactualizada:                                       # E05 inventario desactualizado
        alarma.estado = "PENDIENTE_CORRELACION_MANUAL"
        alertarNOC(inconsistenciaInventario); registrar discrepancia para saneamiento
        retornar   # no crea incidente maestro automáticamente
    grupo = agruparPorSubarbolTopologico(alarma, ventanaTemporal)
    causaRaiz = elementoComunMasProfundo(grupo, topo)
    afectados = topologia.clientesDependientes(causaRaiz)                # incluye empresariales + SLA
    si afectados.total < umbralMasivo:                                   # E08 umbral no alcanzado
        registrar alarma individual con clientes asociados (visible para soporte N1)
        retornar   # sin incidente maestro
    incidente = crearIncidenteMaestro(grupo, causaRaiz, afectados, estado=ACTIVO)   # E01: 1 incidente, no miles
    resultado = conectores.invocar("ITSM", "crearIncidente", incidente, reintentosExponenciales)
    si resultado falla:                                                  # E09 error técnico ITSM
        incidente.estado = "PENDIENTE_PUBLICACION"; encolar reproceso    # alarmas conservadas
        alertarNOC(falloIntegracion); registrarIncidentePlataforma
        retornar
    incidente.itsmTicketId = resultado.ticketId                          # trazabilidad alarma↔interno↔ITSM
    verificar (ts creación ITSM - ts primera alarma) < 5 min             # SLA E01, métrica OBS-03
```

### F2. Gestionar notificación proactiva y consulta de afectados

Al confirmar el operador del NOC el incidente, dispara avisos por app/mensajería (vía ms-notificaciones), actualiza IVR y publica aviso en el portal. Expone consulta para el sistema telefónico: si el número pertenece a un afectado, el IVR informa falla y ETA sin pasar por agente.

**Contrato de entrada** — `POST /v1/incidentes/{incidenteId}/confirmaciones` `{ "operador": "noc.rgarcia", "mensajeCliente": "...", "etaReparacion": "...", "correlationId": "uuid" }`
**Contrato de salida** — `202 Accepted`; evento `IncidenteMaestroConfirmado` hacia ms-notificaciones con clientes, zonas IVR y aviso de portal; hora de envío por notificación registrada.

**Consulta IVR** — `GET /v1/incidentes/afectados?telefono=+51999888777` →
```json
{ "afectado": true, "incidenteId": "INC-2211", "mensaje": "Falla masiva en tu zona", "etaReparacion": "2026-07-05T18:00:00Z", "ofrecerActualizaciones": true }
```
Errores: `404` teléfono sin incidente activo asociado (`afectado:false` con `200`), `401/403` consumidor no autorizado.

**Pseudocódigo**
```
funcion confirmarIncidente(incidenteId, datos):
    si rol(operador) != NOC: retornar 403
    incidente = repositorio.obtener(incidenteId); si estado != ACTIVO: retornar 409
    publicarEvento("IncidenteMaestroConfirmado", { clientesAfectados, zonasIvr, mensaje, portal:true })
    retornar 202

funcion consultarAfectado(telefono):
    cliente = indiceAfectados.buscarPorTelefono(telefono)      # E03: cliente llama y el IVR lo reconoce
    si nulo: retornar 200 { afectado: false }
    retornar 200 { afectado: true, incidente, eta, ofrecerActualizaciones: true }
```

### F3. Cerrar incidente maestro con resolución en cascada

**Contrato de entrada** — `POST /v1/incidentes/{incidenteId}/resoluciones` `{ "operador": "noc.rgarcia", "verificacionTecnica": true, "correlationId": "uuid" }`
**Contrato de salida** — `200 OK`: tickets hijos cerrados automáticamente en el ITSM, notificación de restablecimiento enviada, duración total registrada para SLA, KPIs publicados a BigQuery → Power BI.

**Pseudocódigo**
```
funcion resolverIncidente(incidenteId, datos):
    si rol(operador) != NOC o no datos.verificacionTecnica: retornar 403/422
    incidente = repositorio.obtener(incidenteId)
    hijos = tickets.vinculados(incidenteId)
    para cada hijo: conectores.invocar("ITSM", "cerrarTicket", hijo, motivo=RESOLUCION_MAESTRO)   # E04 cascada
    incidente.estado = "RESUELTO"; incidente.duracion = ahora - incidente.inicio                  # SLA
    publicarEvento("IncidenteResuelto", { clientesAfectados })       # notificación de restablecimiento
    insertar kpi_incidente en BigQuery (duración, afectados, SLA)    # tablero Power BI
    retornar 200
```

## Estructura de base de datos (BigQuery — DDL SQL)

```sql
CREATE TABLE noc.alarma (
    alarma_id       STRING NOT NULL,
    event_id_origen STRING NOT NULL,
    nodo_id         STRING,
    tipo_alarma     STRING NOT NULL,
    severidad       STRING NOT NULL,
    estado          STRING NOT NULL,      -- ACTIVA | AGRUPADA | PENDIENTE_CORRELACION_MANUAL | CERRADA
    ocurrencias     INT64 NOT NULL,
    incidente_id    STRING,
    correlation_id  STRING NOT NULL,
    ts_primera      TIMESTAMP NOT NULL,
    ts_ultima       TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts_primera)
CLUSTER BY nodo_id, estado;

CREATE TABLE noc.incidente_maestro (
    incidente_id    STRING NOT NULL,
    estado          STRING NOT NULL,      -- ACTIVO | CONFIRMADO | PENDIENTE_PUBLICACION | RESUELTO
    causa_raiz_nodo STRING,
    causa_raiz_elemento STRING,
    confianza       FLOAT64,
    alarmas_agrupadas INT64 NOT NULL,
    total_afectados INT64 NOT NULL,
    afectados_empresariales INT64 NOT NULL,
    afectados_con_sla INT64 NOT NULL,
    itsm_ticket_id  STRING,
    eta_reparacion  TIMESTAMP,
    ts_inicio       TIMESTAMP NOT NULL,
    ts_creacion_itsm TIMESTAMP,
    ts_resolucion   TIMESTAMP,
    duracion_min    INT64,
    correlation_id  STRING NOT NULL
) PARTITION BY DATE(ts_inicio);

CREATE TABLE noc.incidente_cliente_afectado (
    incidente_id    STRING NOT NULL,
    cliente_id      STRING NOT NULL,
    telefono        STRING,
    segmento        STRING NOT NULL,      -- RESIDENCIAL | EMPRESARIAL
    tiene_sla       BOOL NOT NULL,
    notificado      BOOL NOT NULL,
    ts_notificacion TIMESTAMP
) PARTITION BY DATE(_PARTITIONTIME);

CREATE TABLE noc.ticket_vinculado (
    incidente_id    STRING NOT NULL,
    ticket_hijo_id  STRING NOT NULL,
    origen          STRING NOT NULL,      -- CALL_CENTER | PORTAL | APP
    estado          STRING NOT NULL,      -- ABIERTO | CERRADO_CASCADA
    ts_vinculo      TIMESTAMP NOT NULL
);

CREATE TABLE noc.kpi_incidente (
    incidente_id    STRING NOT NULL,
    duracion_min    INT64,
    total_afectados INT64,
    cumplimiento_sla BOOL,
    ts              TIMESTAMP NOT NULL
) PARTITION BY DATE(ts);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF12-E01 | Falla masiva agrupada en un solo incidente con causa raíz, lista de afectados (empresariales/SLA), ITSM < 5 min, estado "Activo" |
| RF12-E02 | Notificación proactiva por app/mensajería, IVR actualizado, aviso en portal, hora de envío registrada (con ms-notificaciones) |
| RF12-E03 | Cliente que llama es reconocido por el IVR: información de falla y ETA sin agente |
| RF12-E04 | Cierre en cascada: tickets hijos cerrados, notificación de restablecimiento, duración para SLA, KPIs a Power BI |
| RF12-E05 | Alarma sin correlación por inventario desactualizado: sin incidente automático, "Pendiente de correlación manual", alerta e inconsistencia registrada |
| RF12-E06 | Deduplicación: sin alarmas duplicadas, contador de ocurrencias, sin incidente nuevo |
| RF12-E07 | Falla de canal de notificación: registro por canal, reintentos, alerta al NOC, no marcados como notificados (con ms-notificaciones) |
| RF12-E08 | Umbral no alcanzado: alarma individual con clientes asociados, visible para soporte N1 |
| RF12-E09 | Error técnico en ITSM: incidente no marcado como creado, alarmas en cola de reproceso, alertas registradas |
| RNOF04-E04 | Publicación de incidentes correlacionados hacia el ITSM con acuse y trazabilidad alarma↔interno↔ITSM |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-04 | Dominio operación; trazable a RF12; alta cohesión (solo correlación) |
| INT-02 / INT-03 / INT-06 / INT-09 / INT-11 | Consumo por eventos, reintentos exponenciales al ITSM, idempotencia por eventId, envolvente estándar, cola de reproceso |
| INT-07 | El ITSM se invoca vía ms-conectores-core, nunca directo desde la red |
| ESC-03 / ESC-05 / ESC-06 / ESC-07 | Escala horizontal ante tormentas de alarmas; procesamiento asíncrono con control de flujo |
| OBS-02 / OBS-03 / OBS-04 / OBS-07 / OBS-08 | Correlación end-to-end, métrica del SLA de 5 min, alertas, tableros NOC/Power BI, correlación evento-incidente |
| SEG-04 / SEG-06 / SEG-09 | Acciones de NOC por rol con auditoría; eventos de notificación sin datos sensibles innecesarios |
