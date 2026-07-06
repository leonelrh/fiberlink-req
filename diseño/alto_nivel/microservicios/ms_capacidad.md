# Microservicio: ms-capacidad

## Descripción general
- **Dominio:** Disponibilidad (ARQ-01)
- **Requerimiento origen:** RF04 - Validar capacidad técnica (ARQ-03)
- **Nube / Runtime:** Azure Container Apps (80,000 validaciones/día, tráfico constante)
- **Exposición:** Azure API Management (`/v1/capacidad`), OAuth2 Entra ID
- **Base de datos:** Azure SQL (réplica de nodos/CTO/puertos sincronizada por eventos desde Inventario Oracle + tabla de reservas propias)

## Funcionalidades

### F1. Validar capacidad técnica (nodo, CTO, puerto)

**Contrato de entrada** — `POST /v1/capacidad/validaciones`
```json
{
  "nodoId": "NODO-4512",
  "ctoId": "CTO-8821",
  "planSolicitado": "300MB",
  "canal": "CRM|PORTAL|APP_MOVIL",
  "correlationId": "uuid"
}
```

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "capacidadDisponible": true,
  "puertoSugerido": "CTO-8821-P05",
  "puertosLibres": 3,
  "splitterOcupacion": 0.62,
  "fechaValidacion": "2026-07-05T10:00:00Z"
}
```

**Errores:** `400` datos inválidos, `401/403` no autorizado, `404` nodo/CTO inexistente, `503` réplica y origen no disponibles.

**Pseudocódigo**
```
funcion validarCapacidad(solicitud):
    correlationId = solicitud.correlationId ?? generarUUID()
    si no autorizado(token, "capacidad:validar"): registrarAuditoria(intento); retornar 401/403   # E04
    si faltan campos obligatorios: retornar 400 con detalle                                       # E02
    cto = repositorio.obtenerCTO(solicitud.nodoId, solicitud.ctoId)
    si repositorio no disponible:
        # degradación controlada: intenta consulta directa vía ms-conectores-core (ESC-09)
        respuesta = msConectoresCore.invocar("INVENTARIO", "consultarCapacidad", solicitud)
        si falla: registrarTraza(ERROR, "INVENTARIO", tiempo); retornar 503                       # E03
    puertosLibres = contarPuertos(cto, estado="LIBRE") - reservasVigentes(cto)
    resultado = { capacidadDisponible: puertosLibres > 0, puertoSugerido: primeroLibre(cto) }
    publicarTrazaIntegracion(correlationId, canal, "ms-capacidad", "OK", tiempoRespuesta)          # INT-08
    retornar 200 resultado
```

### F2. Reservar puerto (usada por ms-solicitudes y ms-programacion-instalacion)

**Contrato de entrada** — `POST /v1/capacidad/reservas`
```json
{ "ctoId": "CTO-8821", "puertoId": "CTO-8821-P05", "solicitudId": "SOL-991", "ttlHoras": 72, "correlationId": "uuid" }
```

**Contrato de salida** — `201 Created`
```json
{ "reservaId": "RES-1201", "estado": "RESERVADO", "expira": "2026-07-08T10:00:00Z", "correlationId": "uuid" }
```

**Errores:** `409` puerto ya reservado/ocupado (idempotencia por `solicitudId` — INT-06: si ya existe reserva para la misma solicitud, retorna la existente con `200`), `404`, `401/403`, `400`.

**Pseudocódigo**
```
funcion reservarPuerto(solicitud):
    si existe reserva vigente con solicitudId: retornar 200 reserva existente      # idempotente INT-06
    en transaccion:
        puerto = bloquearPuerto(ctoId, puertoId)
        si puerto.estado != LIBRE: retornar 409
        insertar reserva_puerto(estado=RESERVADO, expira=ahora+ttl)
    publicarEvento("CapacidadReservada", envolventeINT09)     # propaga a Inventario vía ms-conectores-core
    retornar 201
```

### F3. Sincronizar capacidad desde Inventario

**Contrato de entrada:** evento `InventarioCapacidadActualizada` (envolvente INT-09) con nodos/CTO/puertos y estados.
**Contrato de salida:** ACK; upsert en réplica; inválidos a DLQ (INT-11).

**Pseudocódigo**
```
funcion alRecibirEventoCapacidad(evento):
    si no validarEnvolvente(evento): moverADLQ(evento); retornar
    upsert nodo/cto/puerto segun payload
    liberar reservas expiradas
    actualizar sincronizacion_control
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE nodo (
    nodo_id     VARCHAR(20) PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    region      VARCHAR(50)  NOT NULL,
    estado      VARCHAR(15)  NOT NULL DEFAULT 'ACTIVO',
    fecha_actualizacion DATETIME2 NOT NULL
);

CREATE TABLE cto (
    cto_id      VARCHAR(20) PRIMARY KEY,
    nodo_id     VARCHAR(20) NOT NULL REFERENCES nodo(nodo_id),
    capacidad_total INT     NOT NULL,
    splitter    VARCHAR(10) NOT NULL,
    estado      VARCHAR(15) NOT NULL DEFAULT 'ACTIVA',
    fecha_actualizacion DATETIME2 NOT NULL
);

CREATE TABLE puerto (
    puerto_id   VARCHAR(30) PRIMARY KEY,
    cto_id      VARCHAR(20) NOT NULL REFERENCES cto(cto_id),
    estado      VARCHAR(15) NOT NULL,      -- LIBRE | RESERVADO | OCUPADO | AVERIADO
    fecha_actualizacion DATETIME2 NOT NULL
);
CREATE INDEX ix_puerto_cto_estado ON puerto (cto_id, estado);

CREATE TABLE reserva_puerto (
    reserva_id   VARCHAR(20) PRIMARY KEY,
    puerto_id    VARCHAR(30) NOT NULL REFERENCES puerto(puerto_id),
    solicitud_id VARCHAR(20) NOT NULL,
    correlation_id UNIQUEIDENTIFIER NOT NULL,
    estado       VARCHAR(15) NOT NULL,     -- RESERVADO | CONFIRMADO | LIBERADO | EXPIRADO
    fecha_reserva DATETIME2  NOT NULL DEFAULT SYSUTCDATETIME(),
    fecha_expira DATETIME2   NOT NULL,
    CONSTRAINT uq_reserva_solicitud UNIQUE (solicitud_id)
);

CREATE TABLE validacion_capacidad_log (
    validacion_id  BIGINT IDENTITY PRIMARY KEY,
    correlation_id UNIQUEIDENTIFIER NOT NULL,
    canal          VARCHAR(20) NOT NULL,
    nodo_id        VARCHAR(20) NULL,
    cto_id         VARCHAR(20) NULL,
    resultado      VARCHAR(10) NOT NULL,
    codigo_error   VARCHAR(30) NULL,
    tiempo_respuesta_ms INT    NOT NULL,
    fecha          DATETIME2   NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_validacion_correlation ON validacion_capacidad_log (correlation_id);

CREATE TABLE sincronizacion_control (
    fuente      VARCHAR(30) PRIMARY KEY,
    ultima_sincronizacion DATETIME2 NOT NULL,
    estado      VARCHAR(15) NOT NULL
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF04-E01 | Ejecución exitosa de validación de capacidad con traza por correlationId |
| RF04-E02 | Solicitud inválida rechazada con detalle de campos |
| RF04-E03 | Sistema destino (Inventario) no disponible: error controlado y registro |
| RF04-E04 | Consumidor no autorizado rechazado con auditoría |
| RF04-CA01..CA05 | Criterios de aceptación de RF04 |
| RF08-E01 (apoyo) | Reserva de equipos/puerto durante programación de instalación |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-04 | Dominio disponibilidad, trazable a RF04, alta cohesión |
| INT-01 / INT-04 / INT-05 | API versionada con contratos completos |
| INT-02 / INT-09 / INT-11 | Sincronización por eventos con envolvente estándar y DLQ |
| INT-06 | Reserva idempotente por solicitudId |
| INT-08 | Evidencias de intercambio |
| INT-12 / ESC-09 | Degradación controlada ante indisponibilidad del Oracle on-premises |
| ESC-03 / ESC-06 / ESC-07 | Escala horizontal, réplica local, control de concurrencia con bloqueo de puerto |
| OBS-01 / OBS-02 / OBS-09 | Logs estructurados, correlationId, clasificación de fallas |
| SEG-01 / SEG-03 / SEG-04 / SEG-06 | TLS, OAuth2, mínimo privilegio, auditoría de operaciones críticas |
