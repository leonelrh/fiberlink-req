# Microservicio: ms-conectores-core

## Descripción general
- **Dominio:** Integración (ARQ-01) — es el núcleo de la Plataforma de Integración Empresarial (ARQ-09)
- **Requerimiento origen:** RF02 - Integrar sistemas críticos (ARQ-03); habilita RNOF01 y RNOF02 (RG-03)
- **Nube / Runtime:** Azure Container Apps (tráfico constante 24/7: toda interacción con sistemas core pasa por aquí)
- **Sistemas conectados:** CRM (SaaS), Inventario Oracle (on-premises), OSS/OCS (on-premises), Facturación (Unix on-premises), ERP (on-premises), Field Service (SaaS), GIS, ITSM/mesa de ayuda (Azure)
- **Base de datos:** Azure SQL (catálogo de sistemas, evidencias de intercambio, suscripciones, reproceso)
- **Conectividad on-premises:** canal privado (VPN/ExpressRoute) — SEG-10

## Funcionalidades

### F1. Invocar operación en sistema core (mediación síncrona)

API interna canónica que traduce el modelo canónico al protocolo de cada sistema (REST, SOAP, JDBC, archivos), con timeout, reintentos controlados y circuit breaker por sistema.

**Contrato de entrada** — `POST /v1/core/{sistema}/{operacion}`
```json
{
  "correlationId": "uuid",
  "consumidor": "ms-solicitudes",
  "payload": { "...modelo canónico de la operación..." },
  "idempotencyKey": "uuid"
}
```

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "sistema": "CRM",
  "operacion": "crearCasoVenta",
  "resultado": "OK",
  "payload": { "...respuesta canónica..." },
  "tiempoRespuestaMs": 320
}
```

**Errores:** `400` payload no cumple esquema canónico (INT-10), `401/403` consumidor no autorizado (credencial individual por sistema — RG-03), `404` sistema/operación no catalogada, `504` timeout del sistema core, `503` circuit breaker abierto (degradación controlada ESC-09/INT-12). Toda falla se clasifica: VALIDACION | AUTENTICACION | TIMEOUT | INDISPONIBILIDAD | ERROR_FUNCIONAL | ERROR_TECNICO (OBS-09).

**Pseudocódigo**
```
funcion invocarSistemaCore(sistema, operacion, solicitud):
    si no autorizado(credencialConsumidor, sistema, operacion): auditar; retornar 401/403   # SEG-04, RG-03
    definicion = catalogo.obtener(sistema, operacion)
    si nula: retornar 404
    si no validarEsquema(solicitud.payload, definicion.esquemaEntrada): retornar 400        # INT-10
    si circuitBreaker(sistema).abierto: registrarIntercambio(FALLIDO, INDISPONIBILIDAD); retornar 503
    intento = 0
    mientras intento < definicion.maxReintentos:                                            # INT-03
        respuesta = adaptador(sistema).ejecutar(operacion, transformar(payload), timeout=definicion.timeoutMs)
        si respuesta.ok:
            registrarIntercambio(origen=consumidor, destino=sistema, OK, tiempo)            # INT-08
            retornar 200 transformarRespuesta(respuesta)
        si respuesta.errorTransitorio y operacion.idempotente: intento++; esperaExponencial()
        sino: romper
    circuitBreaker(sistema).registrarFallo()
    registrarIntercambio(FALLIDO, clasificarFalla(respuesta), codigo, tiempo)               # OBS-09
    retornar 503/504 error controlado con correlationId
```

### F2. Entregar eventos a sistemas suscritos (mediación asíncrona)

Consume tópicos de Azure Service Bus / GCP Pub/Sub y entrega cada evento a los sistemas core suscritos, garantizando que la propagación de datos maestros llegue a todas las plataformas (RNOF01).

**Contrato de entrada:** evento con envolvente INT-09 (`eventId`, `eventType`, `version`, `correlationId`, `sourceSystem`, `timestamp`, `payload`).

**Contrato de salida:** entrega confirmada por suscriptor registrada en `entrega_evento`; fallos → cola de reintentos con espera exponencial; agotados → DLQ + alerta (OBS-04).

**Pseudocódigo**
```
funcion alRecibirEvento(evento):
    si no validarEnvolvente(evento): moverADLQ(evento, "ESQUEMA_INVALIDO"); retornar
    suscriptores = suscripcion.buscar(evento.eventType, evento.version)
    para cada s en suscriptores:
        si entrega ya confirmada (eventId, s): continuar                     # idempotencia INT-06
        resultado = invocarSistemaCore(s.sistema, s.operacionDestino, evento.payload)
        registrar entrega_evento(eventId, s.sistema, resultado, tiempoPropagacion)
        si fallo transitorio: encolar reintento(esperaExponencial, maxIntentos)
        si agotado: moverADLQ + alertar operaciones                          # RNOF01 alertas
```

### F3. Reprocesar intercambios y eventos fallidos (INT-11)

**Contrato de entrada** — `POST /v1/core/reprocesos`
```json
{ "tipo": "EVENTO|INTERCAMBIO", "ids": ["evt-1", "evt-2"], "usuario": "operador.noc", "correlationId": "uuid" }
```

**Contrato de salida** — `202 Accepted` con resumen `{ "aceptados": 2, "rechazados": 0 }`; resultado por elemento consultable en `/v1/core/reprocesos/{id}`.

**Errores:** `403` rol sin permiso de reproceso, `404` id inexistente, `409` elemento ya reprocesado con éxito.

**Pseudocódigo**
```
funcion reprocesar(peticion):
    si rol(usuario) not in [OPERADOR_INTEGRACION]: retornar 403; auditar     # SEG-12
    para cada id en peticion.ids:
        item = dlq.obtener(id)
        si item nulo: marcar rechazado(404)
        si item.estado == REPROCESADO_OK: marcar rechazado(409)
        encolar item con marca de reproceso manual y usuario                 # auditoría SEG-06
    retornar 202 resumen
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE sistema_core (
    sistema_id      VARCHAR(20) PRIMARY KEY,      -- CRM | INVENTARIO | OSS | FACTURACION | ERP | FIELD_SERVICE | GIS | ITSM
    nombre          VARCHAR(100) NOT NULL,
    tipo_conector   VARCHAR(20)  NOT NULL,        -- REST | SOAP | JDBC | ARCHIVO
    ubicacion       VARCHAR(20)  NOT NULL,        -- SAAS | ONPREM | AWS | AZURE | GCP
    timeout_ms      INT          NOT NULL DEFAULT 5000,
    max_reintentos  INT          NOT NULL DEFAULT 2,
    umbral_circuit_breaker DECIMAL(4,2) NOT NULL DEFAULT 0.50,
    estado          VARCHAR(15)  NOT NULL DEFAULT 'ACTIVO'
);

CREATE TABLE operacion_core (
    operacion_id    VARCHAR(40) PRIMARY KEY,
    sistema_id      VARCHAR(20) NOT NULL REFERENCES sistema_core(sistema_id),
    nombre          VARCHAR(80) NOT NULL,
    version         VARCHAR(10) NOT NULL,
    esquema_entrada VARCHAR(MAX) NOT NULL,        -- JSON Schema
    esquema_salida  VARCHAR(MAX) NOT NULL,
    idempotente     BIT          NOT NULL DEFAULT 0,
    CONSTRAINT uq_operacion UNIQUE (sistema_id, nombre, version)
);

CREATE TABLE intercambio (
    intercambio_id  BIGINT IDENTITY PRIMARY KEY,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    sistema_origen  VARCHAR(30) NOT NULL,
    sistema_destino VARCHAR(30) NOT NULL,
    operacion       VARCHAR(80) NOT NULL,
    canal           VARCHAR(20) NOT NULL,
    resultado       VARCHAR(10) NOT NULL,         -- OK | FALLIDO
    tipo_falla      VARCHAR(20) NULL,             -- OBS-09
    codigo_error    VARCHAR(30) NULL,
    tiempo_respuesta_ms INT     NOT NULL,
    fecha           DATETIME2   NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_intercambio_correlation ON intercambio (correlation_id);
CREATE INDEX ix_intercambio_fecha ON intercambio (fecha, sistema_destino);

CREATE TABLE suscripcion_evento (
    suscripcion_id  INT IDENTITY PRIMARY KEY,
    event_type      VARCHAR(60) NOT NULL,
    version         VARCHAR(10) NOT NULL,
    sistema_id      VARCHAR(20) NOT NULL REFERENCES sistema_core(sistema_id),
    operacion_destino VARCHAR(80) NOT NULL,
    activa          BIT NOT NULL DEFAULT 1
);

CREATE TABLE entrega_evento (
    entrega_id      BIGINT IDENTITY PRIMARY KEY,
    event_id        UNIQUEIDENTIFIER NOT NULL,
    event_type      VARCHAR(60) NOT NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    sistema_destino VARCHAR(20) NOT NULL,
    estado          VARCHAR(20) NOT NULL,     -- ENTREGADO | REINTENTO | DLQ | REPROCESADO_OK
    intentos        INT NOT NULL DEFAULT 1,
    usuario_reproceso VARCHAR(50) NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT uq_entrega UNIQUE (event_id, sistema_destino)
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF02-E01 | Ejecución exitosa de integración con respuesta por contrato y traza |
| RF02-E02 | Solicitud inválida rechazada con detalle (validación de esquema canónico) |
| RF02-E03 | Sistema destino no disponible: error controlado, circuit breaker, registro de sistema/código/tiempo |
| RF02-E04 | Consumidor no autorizado rechazado con auditoría |
| RF02-CA01..CA05 | Criterios de aceptación de RF02 |
| RNOF01 (mecanismos) | Propagación de eventos a todas las plataformas suscritas dentro de los tiempos máximos |
| RNOF02-RG03 | Credenciales individuales por sistema, mínimo privilegio, registro de sistema origen |
| RNOF04-E05 (apoyo) | Publicación de incidentes al ITSM con reintentos y acuse |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-02 / INT-07 | Los sistemas core no se integran punto a punto; toda mediación pasa por este servicio |
| ARQ-05 / ARQ-09 | Contratos explícitos; componente habilitador del roadmap |
| INT-01 / INT-02 / INT-04 / INT-05 | APIs versionadas síncronas y entrega asíncrona por eventos |
| INT-03 | Timeouts, reintentos con espera exponencial y circuit breaker |
| INT-06 | Idempotencia por eventId/idempotencyKey en entregas y operaciones |
| INT-08 / INT-09 / INT-10 / INT-11 / INT-12 | Evidencias, envolvente estándar, validación previa, reproceso controlado, tolerancia a on-premises |
| ESC-05 / ESC-06 / ESC-07 / ESC-09 | Asincronía, protección de sistemas legados con cuotas y backpressure, degradación controlada |
| OBS-01 / OBS-02 / OBS-04 / OBS-08 / OBS-09 | Logs, correlación, alertas de fallos de entrega, clasificación de fallas |
| SEG-01 / SEG-04 / SEG-05 / SEG-10 / SEG-11 / SEG-12 | TLS, mínimo privilegio, secretos en Key Vault con rotación 90 días, canal seguro on-premises, auditoría de accesos administrativos |
