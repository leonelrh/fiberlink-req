# Microservicio: ms-eventos-negocio

## Descripción general
- **Dominio:** Integración (ARQ-01)
- **Requerimiento origen:** RF06 - Publicar eventos de negocio (ARQ-03)
- **Nube / Runtime:** Azure Functions (carga dirigida por eventos, intermitente respecto del total de tráfico; ~116,000 eventos/día según volumetría: 40% de transacciones generan evento, 2–5 KB c/u)
- **Brokers:** Azure Service Bus (distribución interna a la capa de integración) y GCP Pub/Sub (bus de eventos de negocio para analítica, observabilidad y suscriptores)
- **Base de datos:** Azure SQL (catálogo de eventos, registro de publicación, fallidos)

## Funcionalidades

### F1. Publicar evento de negocio

Punto único de publicación: valida la envolvente INT-09 y el esquema del payload contra el catálogo, y publica en los tópicos correspondientes (Service Bus + Pub/Sub).

**Contrato de entrada** — `POST /v1/eventos`
```json
{
  "eventId": "uuid",
  "eventType": "ServicioActivado",
  "version": "1.0",
  "correlationId": "uuid",
  "sourceSystem": "ms-activacion",
  "timestamp": "2026-07-05T10:00:00Z",
  "payload": { "servicioId": "SRV-33421", "contrato": "CT-2026-7781", "plan": "300MB" }
}
```

**Contrato de salida** — `202 Accepted`
```json
{ "eventId": "uuid", "estado": "PUBLICADO", "topicos": ["sb://eventos-negocio", "pubsub://eventos-negocio"], "correlationId": "uuid" }
```

**Errores:** `400` envolvente incompleta o payload no cumple esquema (indica campos incumplidos), `401/403` publicador no autorizado, `409` eventId duplicado (idempotencia: retorna publicación original), `422` eventType/version no registrado en catálogo, `503` brokers no disponibles (persiste en `publicacion_fallida` para reproceso y responde error controlado).

**Pseudocódigo**
```
funcion publicarEvento(evento):
    si no autorizado(credencial, "eventos:publicar", evento.eventType): auditar; retornar 401/403   # E04
    faltantes = validarEnvolvente(evento)            # eventId..payload, INT-09
    si faltantes: retornar 400 con lista             # E02
    definicion = catalogo.obtener(evento.eventType, evento.version)
    si nula: retornar 422                            # INT-05: versiones explícitas
    si no validarEsquema(evento.payload, definicion.esquema): retornar 400
    si evento.payload contiene campos sensibles no permitidos: retornar 400     # SEG-09
    si registro_publicacion existe(eventId): retornar 409 con original          # INT-06
    resultado = publicar(serviceBus, pubSub, evento)
    si resultado falla:
        guardar publicacion_fallida(evento, motivo); alertar                    # E03, OBS-04
        retornar 503 error controlado
    guardar registro_publicacion(evento, topicos, OK)                           # INT-08, OBS-08
    retornar 202
```

### F2. Administrar catálogo de eventos

**Contrato de entrada** — `POST /v1/eventos/catalogo` / `GET /v1/eventos/catalogo/{eventType}`
```json
{ "eventType": "ServicioActivado", "version": "1.1", "esquemaPayload": { "...JSON Schema..." }, "compatibleCon": "1.0", "propietario": "ms-activacion" }
```

**Contrato de salida** — `201 Created` con la definición registrada. Cambios incompatibles exigen nueva `version` (INT-05); `409` si intenta sobrescribir una versión publicada.

**Pseudocódigo**
```
funcion registrarTipoEvento(definicion):
    si rol(usuario) != ARQUITECTO_INTEGRACION: retornar 403
    si existe(eventType, version): retornar 409
    si esCambioIncompatible(definicion, versionAnterior) y misma version: retornar 422 "requiere nueva versión"
    persistir catalogo_evento; auditar cambio                                    # SEG-06
    retornar 201
```

### F3. Reprocesar publicaciones fallidas

**Contrato de entrada** — `POST /v1/eventos/reprocesos` `{ "eventIds": ["..."], "usuario": "operador" }`
**Contrato de salida** — `202 Accepted` con resumen; cada evento reprocesado vuelve por F1 conservando su `eventId` original (idempotente).

**Pseudocódigo**
```
funcion reprocesarFallidos(peticion):
    si rol(usuario) not in [OPERADOR_INTEGRACION]: retornar 403; auditar
    para cada id: evento = publicacion_fallida.obtener(id)
        si nulo o ya publicado: marcar rechazado
        sino publicarEvento(evento) y actualizar estado
    retornar 202 resumen
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE catalogo_evento (
    catalogo_id     INT IDENTITY PRIMARY KEY,
    event_type      VARCHAR(60) NOT NULL,
    version         VARCHAR(10) NOT NULL,
    esquema_payload VARCHAR(MAX) NOT NULL,       -- JSON Schema
    compatible_con  VARCHAR(10) NULL,
    propietario     VARCHAR(50) NOT NULL,
    campos_sensibles_prohibidos VARCHAR(500) NULL,
    fecha_registro  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT uq_catalogo UNIQUE (event_type, version)
);

CREATE TABLE registro_publicacion (
    event_id        UNIQUEIDENTIFIER PRIMARY KEY,
    event_type      VARCHAR(60) NOT NULL,
    version         VARCHAR(10) NOT NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    source_system   VARCHAR(50) NOT NULL,
    topicos         VARCHAR(300) NOT NULL,
    resultado       VARCHAR(10) NOT NULL,
    tiempo_publicacion_ms INT NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_publicacion_correlation ON registro_publicacion (correlation_id);
CREATE INDEX ix_publicacion_tipo_fecha ON registro_publicacion (event_type, fecha);

CREATE TABLE publicacion_fallida (
    event_id        UNIQUEIDENTIFIER PRIMARY KEY,
    evento_json     VARCHAR(MAX) NOT NULL,
    motivo          VARCHAR(200) NOT NULL,
    intentos        INT NOT NULL DEFAULT 1,
    estado          VARCHAR(20) NOT NULL,        -- PENDIENTE | REPROCESADO_OK | DESCARTADO
    usuario_reproceso VARCHAR(50) NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF06-E01 | Ejecución exitosa: evento validado y publicado con traza por correlationId |
| RF06-E02 | Solicitud inválida: rechazo con campos/reglas incumplidas (envolvente o esquema) |
| RF06-E03 | Broker no disponible: error controlado, evento persistido para reproceso |
| RF06-E04 | Publicador no autorizado rechazado con auditoría |
| RF06-CA01..CA05 | Criterios de aceptación de RF06 |
| RNOF01 (mecanismos) | Propagación de eventos: todo cambio de datos maestros pasa por este punto |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-05 / ARQ-09 | Contratos de eventos explícitos y versionados; habilitador del bus multinube |
| INT-02 / INT-05 / INT-06 | Asincronía por eventos, versionado de cambios incompatibles, idempotencia por eventId |
| INT-08 / INT-09 / INT-10 / INT-11 | Registro de publicación, envolvente obligatoria, validación previa, reproceso controlado |
| ESC-05 / ESC-06 / ESC-07 | Publicación asíncrona, brokers administrados escalables, backpressure vía colas |
| OBS-01 / OBS-02 / OBS-04 / OBS-08 | Logs estructurados, correlación evento-transacción, alertas de fallo de publicación |
| SEG-03 / SEG-04 / SEG-06 / SEG-09 | Publicadores autenticados con mínimo privilegio por eventType; eventos sin datos sensibles innecesarios |
