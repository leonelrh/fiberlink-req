# Microservicio: ms-ingesta-red

## Descripción general
- **Dominio:** Observabilidad / Operación de red (ARQ-01)
- **Requerimiento origen:** RNOF04 - Integración de fuentes de red al bus de eventos (ARQ-03)
- **Nube / Runtime:** GCP Cloud Run (ingesta continua desde Pub/Sub; rol de GCP: eventos y analítica) + Cloud Scheduler para sincronización de inventario
- **Fuentes:** NMS regionales, logs de red, inventario de red Oracle (on-premises)
- **Almacenamiento:** BigQuery (eventos normalizados, rechazados, métricas de fuentes) y tabla de topología para el motor de correlación
- **Bus:** GCP Pub/Sub — tópicos `red-ingesta-cruda`, `red-alarmas-normalizadas`, `red-rechazados` (DLQ)

## Funcionalidades

### F1. Registrar fuente e ingerir eventos de red

Solo fuentes registradas y con credencial individual (cuenta de servicio dedicada por NMS — RNOF02-RG03) pueden publicar. Eventos de fuentes no autorizadas se rechazan, se registran en bitácora de seguridad y generan alerta.

**Contrato de entrada (registro)** — `POST /v1/fuentes-red`
```json
{ "fuenteId": "NMS-NORTE", "region": "LIMA-NORTE", "tipo": "NMS|LOGS|INVENTARIO", "esquemaMapeoId": "MAP-NMS-V2", "cuentaServicio": "nms-norte@fiberlink.iam", "correlationId": "uuid" }
```
**Contrato de salida** — `201 Created` `{ "fuenteId": "NMS-NORTE", "estado": "INTEGRADA", "topico": "red-ingesta-cruda" }`; el indicador de cobertura de integración se actualiza.

**Contrato de entrada (ingesta)** — mensaje Pub/Sub crudo con atributos `fuenteId`, `region`, firma de la cuenta de servicio.

**Pseudocódigo**
```
funcion alRecibirEventoCrudo(mensaje):
    fuente = registro.obtener(mensaje.atributos.fuenteId)
    si fuente nula o credencial no corresponde:                          # E05 fuente no autorizada
        registrar bitacora_seguridad(intento, origen); alertar equipoSeguridad
        descartar sin entregar a normalización; retornar
    encolar a normalizacion(mensaje, fuente)

funcion monitorIngesta():   # tarea continua
    para cada fuente INTEGRADA:
        si sinEventos(fuente) > umbral:                                  # E07 pérdida de conectividad
            fuente.estado = "SIN_SEÑAL"; alertarNOC(region)
            registrar ventana_perdida(fuente, inicio) para auditoría
        si fuente recupera flujo: recuperar pendientes (replay del NMS); cerrar ventana; estado=INTEGRADA
```

### F2. Normalizar eventos al esquema canónico de alarma

**Contrato de entrada:** evento crudo heterogéneo. **Contrato de salida:** evento canónico publicado en `red-alarmas-normalizadas` (envolvente INT-09):
```json
{
  "eventId": "uuid", "eventType": "AlarmaRed", "version": "1.0",
  "correlationId": "uuid", "sourceSystem": "NMS-NORTE", "timestamp": "...",
  "payload": {
    "idOriginalFuente": "TRAP-7781", "region": "LIMA-NORTE",
    "nodoId": "NODO-4512", "elemento": "OLT-12/P4", "severidad": "CRITICA",
    "tipoAlarma": "LOS", "descripcion": "Loss of signal"
  }
}
```
Eventos con esquema inválido o campos obligatorios ausentes → `red-rechazados` con motivo, fuente y campo, incrementando el indicador de calidad de datos de la fuente (E06).

**Pseudocódigo**
```
funcion normalizar(mensajeCrudo, fuente):
    mapeo = esquema_mapeo.obtener(fuente.esquemaMapeoId)
    canonico = transformar(mensajeCrudo, mapeo)          # conserva idOriginalFuente
    faltantes = validarCampos(canonico, obligatorios)
    si faltantes:
        publicar red-rechazados { evento, motivo, fuente, campos: faltantes }     # E06
        incrementar indicador_calidad(fuente); retornar
    registrar fuente/region/timestamp; publicar red-alarmas-normalizadas(canonico)
    # formatos distintos de operadores adquiridos: cada uno con su mapeo, ninguno se descarta (E02)
```

### F3. Sincronizar inventario/topología desde Oracle

Cloud Scheduler dispara la tarea según frecuencia definida. La topología (nodos, puertos, clientes) alimenta al motor de correlación (ms-correlacion-incidentes).

**Contrato de entrada** — trigger programado o `POST /v1/topologia/sincronizaciones`.
**Contrato de salida** — `202`; al finalizar: topología actualizada, fecha de última sincronización, validación de integridad referencial nodo↔cliente, indicador de frescura publicado al tablero.

**Pseudocódigo**
```
funcion sincronizarInventario():
    intentar:
        datos = conectores.invocar("INVENTARIO", "extraerTopologia")     # vía plataforma integración
        si datos parciales o error: lanzar FalloSincronizacion
        validar integridad referencial (nodos ↔ puertos ↔ clientes)
        reemplazar topologia (versionado, transaccional)
        actualizar control_sincronizacion(fecha=ahora, estado=OK)
        publicar indicador_frescura al tablero                            # E03
    capturar FalloSincronizacion:                                         # E08
        NO actualizar topología con datos parciales; conservar última versión válida
        si antiguedad > umbralFrescura: marcar inventario "DESACTUALIZADO"
        alertar equipoDatos
```

**Control de saturación (E09):** suscripciones Pub/Sub con flow control y backpressure; eventos de severidad CRITICA en tópico prioritario; alertas de saturación al equipo de plataforma y métricas del pico registradas para ajuste de capacidad (ESC-07, OBS-04).

## Estructura de base de datos (BigQuery — DDL SQL)

```sql
CREATE TABLE red.fuente_red (
    fuente_id       STRING NOT NULL,
    region          STRING NOT NULL,
    tipo            STRING NOT NULL,          -- NMS | LOGS | INVENTARIO
    esquema_mapeo_id STRING NOT NULL,
    cuenta_servicio STRING NOT NULL,          -- credencial individual RG-03
    estado          STRING NOT NULL,          -- INTEGRADA | SIN_SEÑAL | SUSPENDIDA
    indicador_calidad FLOAT64,
    ultima_recepcion TIMESTAMP,
    fecha_registro  TIMESTAMP NOT NULL
);

CREATE TABLE red.evento_normalizado (
    event_id        STRING NOT NULL,
    id_original_fuente STRING,
    fuente_id       STRING NOT NULL,
    region          STRING NOT NULL,
    nodo_id         STRING,
    elemento        STRING,
    severidad       STRING NOT NULL,
    tipo_alarma     STRING NOT NULL,
    correlation_id  STRING NOT NULL,
    ts_fuente       TIMESTAMP NOT NULL,
    ts_ingesta      TIMESTAMP NOT NULL
)
PARTITION BY DATE(ts_ingesta)
CLUSTER BY nodo_id, severidad;

CREATE TABLE red.evento_rechazado (
    event_id        STRING,
    fuente_id       STRING NOT NULL,
    motivo          STRING NOT NULL,
    campos_faltantes STRING,
    payload_crudo   STRING,
    ts              TIMESTAMP NOT NULL
) PARTITION BY DATE(ts);

CREATE TABLE red.topologia_nodo (
    nodo_id         STRING NOT NULL,
    region          STRING NOT NULL,
    tipo_elemento   STRING NOT NULL,          -- OLT | SPLITTER | CTO | RUTA
    padre_nodo_id   STRING,
    clientes        STRING,                   -- JSON: clientes dependientes con segmento (residencial/empresarial+SLA)
    version_sync    INT64 NOT NULL,
    ts_sync         TIMESTAMP NOT NULL
);

CREATE TABLE red.control_sincronizacion (
    fuente          STRING NOT NULL,          -- INVENTARIO_ORACLE
    ultima_sync_ok  TIMESTAMP,
    estado          STRING NOT NULL,          -- OK | DESACTUALIZADO
    ventanas_perdida STRING                   -- JSON de ventanas para auditoría
);

CREATE TABLE red.bitacora_seguridad (
    intento_id      STRING NOT NULL,
    origen          STRING NOT NULL,
    detalle         STRING NOT NULL,
    ts              TIMESTAMP NOT NULL
) PARTITION BY DATE(ts);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RNOF04-E01 | Integración exitosa de un NMS regional: ingesta, normalización, fuente "Integrada", indicador de cobertura |
| RNOF04-E02 | Normalización de formatos heterogéneos conservando id original, sin descartes por formato |
| RNOF04-E03 | Sincronización de inventario: topología actualizada, integridad referencial, indicador de frescura |
| RNOF04-E04 (apoyo) | Entrega de alarmas normalizadas al motor de correlación que publica al ITSM |
| RNOF04-E05 | Rechazo de fuentes no autorizadas con bitácora de seguridad y alerta |
| RNOF04-E06 | Eventos con esquema inválido a cola de rechazados con motivo e indicador de calidad |
| RNOF04-E07 | Pérdida de conectividad: estado "Sin señal", alerta al NOC, ventana registrada, recuperación posterior |
| RNOF04-E08 | Falla de sincronización: sin datos parciales, última versión válida, "Desactualizado", alerta |
| RNOF04-E09 | Saturación del bus: control de flujo sin pérdida, priorización de críticos, alertas y métricas |
| RF12-E05 (apoyo) | Alarma con nodo inexistente detectable por frescura/integridad de topología |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 | Dominio observabilidad/operación; trazable a RNOF04 |
| INT-02 / INT-09 / INT-10 / INT-11 / INT-12 | Ingesta por eventos, envolvente estándar, validación previa, DLQ con reproceso, tolerancia a on-premises |
| ESC-03 / ESC-05 / ESC-06 / ESC-07 | Cloud Run escala horizontal, ingesta asíncrona, protección del bus, flow control y backpressure |
| OBS-01 / OBS-02 / OBS-03 / OBS-04 / OBS-09 | Logs, correlación, métricas de fuentes/calidad/frescura, alertas de ausencia de señal y saturación |
| SEG-03 / SEG-04 / SEG-06 / SEG-10 / SEG-11 | Cuentas de servicio individuales por fuente, mínimo privilegio, bitácora de seguridad, canal seguro con Oracle, rotación de credenciales |
| RNOF02-RG03 | Elimina credenciales compartidas de operadores adquiridos: una credencial por fuente con scope propio |
