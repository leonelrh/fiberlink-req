# Microservicio: ms-solicitudes

## Descripción general
- **Dominio:** Provisión / Captación (ARQ-01)
- **Requerimiento origen:** RF01 - Registrar solicitud de servicio (ARQ-03)
- **Nube / Runtime:** Azure Container Apps (40,000 solicitudes/día, tráfico constante en horario comercial)
- **Exposición:** Azure API Management (`/v1/solicitudes`), OAuth2 Entra ID
- **Base de datos:** Azure SQL

## Funcionalidades

### F1. Registrar solicitud de servicio

Valida cobertura (ms-cobertura) y capacidad (ms-capacidad) antes de registrar; registra la solicitud en el CRM vía ms-conectores-core y publica el evento de negocio. La venta solo procede si es técnicamente viable.

**Contrato de entrada** — `POST /v1/solicitudes`
```json
{
  "cliente": { "tipoDocumento": "DNI", "numeroDocumento": "45781234", "nombre": "...", "telefono": "...", "email": "..." },
  "direccionInstalacion": "Av. Los Álamos 123, Lima",
  "coordenadas": { "lat": -12.0464, "lon": -77.0428 },
  "planSolicitado": "300MB",
  "canal": "CRM|PORTAL|APP_MOVIL|TABLET_CAMPO",
  "correlationId": "uuid",
  "idempotencyKey": "uuid"
}
```

**Contrato de salida** — `201 Created`
```json
{
  "solicitudId": "SOL-000991",
  "estado": "REGISTRADA",
  "cobertura": { "nodoId": "NODO-4512", "ctoId": "CTO-8821" },
  "reservaPuerto": "RES-1201",
  "crmCasoId": "CRM-88121",
  "correlationId": "uuid"
}
```

**Errores:** `400` datos inválidos, `401/403` no autorizado, `409` idempotencyKey repetida (retorna solicitud original), `422` sin cobertura o sin capacidad (respuesta funcional controlada con motivo), `503` sistema core no disponible.

**Pseudocódigo**
```
funcion registrarSolicitud(solicitud):
    correlationId = solicitud.correlationId ?? generarUUID()
    si no autorizado(token, "solicitudes:crear"): registrarAuditoria(intento); retornar 401/403      # E04
    si no validarDatos(solicitud): retornar 400 con campos incumplidos                                # E02, INT-10
    si existe solicitud con idempotencyKey: retornar 200 solicitud existente                          # INT-06

    cobertura = msCobertura.consultar(direccion, coordenadas, correlationId)
    si no cobertura.cobertura: retornar 422 "SIN_COBERTURA"
    capacidad = msCapacidad.validar(cobertura.nodoId, cobertura.ctoId, plan, correlationId)
    si no capacidad.capacidadDisponible: retornar 422 "SIN_CAPACIDAD"

    reserva = msCapacidad.reservarPuerto(cobertura.ctoId, capacidad.puertoSugerido, solicitudId, correlationId)
    resultadoCRM = msConectoresCore.invocar("CRM", "crearCasoVenta", datosSolicitud, correlationId)   # timeout+retry INT-03
    si resultadoCRM falla:
        msCapacidad.liberarReserva(reserva.reservaId)                                                 # compensación
        registrarTraza(correlationId, "ms-solicitudes", "CRM", "ERROR", codigo, tiempo)               # E03
        retornar 503 error controlado
    persistir solicitud_servicio(estado=REGISTRADA)
    msEventosNegocio.publicar("SolicitudServicioRegistrada", payloadSinDatosSensibles, correlationId) # RF06, SEG-09
    retornar 201
```

### F2. Consultar solicitud de servicio

**Contrato de entrada** — `GET /v1/solicitudes/{solicitudId}`

**Contrato de salida** — `200 OK`
```json
{ "solicitudId": "SOL-000991", "estado": "REGISTRADA", "plan": "300MB", "historial": [ { "estado": "REGISTRADA", "fecha": "..." } ], "correlationId": "uuid" }
```

**Errores:** `404` no existe, `401/403` no autorizado.

**Pseudocódigo**
```
funcion consultarSolicitud(solicitudId):
    si no autorizado: retornar 401/403
    solicitud = repositorio.obtener(solicitudId)
    si nula: retornar 404
    retornar 200 solicitud con historial
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE solicitud_servicio (
    solicitud_id     VARCHAR(20) PRIMARY KEY,
    idempotency_key  UNIQUEIDENTIFIER NOT NULL UNIQUE,
    correlation_id   UNIQUEIDENTIFIER NOT NULL,
    tipo_documento   VARCHAR(10)  NOT NULL,
    numero_documento VARCHAR(20)  NOT NULL,
    nombre_cliente   VARCHAR(150) NOT NULL,
    telefono         VARCHAR(20)  NULL,
    email            VARCHAR(150) NULL,
    direccion        VARCHAR(300) NOT NULL,
    lat              DECIMAL(10,7) NULL,
    lon              DECIMAL(10,7) NULL,
    plan_solicitado  VARCHAR(20)  NOT NULL,
    nodo_id          VARCHAR(20)  NULL,
    cto_id           VARCHAR(20)  NULL,
    reserva_id       VARCHAR(20)  NULL,
    crm_caso_id      VARCHAR(30)  NULL,
    canal            VARCHAR(20)  NOT NULL,
    estado           VARCHAR(20)  NOT NULL,   -- REGISTRADA | RECHAZADA | EN_INSTALACION | CERRADA
    fecha_registro   DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_solicitud_documento ON solicitud_servicio (numero_documento);
CREATE INDEX ix_solicitud_correlation ON solicitud_servicio (correlation_id);

CREATE TABLE solicitud_historial (
    historial_id   BIGINT IDENTITY PRIMARY KEY,
    solicitud_id   VARCHAR(20) NOT NULL REFERENCES solicitud_servicio(solicitud_id),
    estado_anterior VARCHAR(20) NULL,
    estado_nuevo   VARCHAR(20) NOT NULL,
    usuario_proceso VARCHAR(50) NOT NULL,
    correlation_id UNIQUEIDENTIFIER NOT NULL,
    fecha          DATETIME2   NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE solicitud_intercambio_log (
    intercambio_id BIGINT IDENTITY PRIMARY KEY,
    solicitud_id   VARCHAR(20) NULL,
    correlation_id UNIQUEIDENTIFIER NOT NULL,
    sistema_origen VARCHAR(30) NOT NULL,
    sistema_destino VARCHAR(30) NOT NULL,
    canal          VARCHAR(20) NOT NULL,
    resultado      VARCHAR(10) NOT NULL,
    codigo_error   VARCHAR(30) NULL,
    tiempo_respuesta_ms INT    NOT NULL,
    fecha          DATETIME2   NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF01-E01 | Ejecución exitosa: solicitud registrada vía plataforma con respuesta por contrato y traza |
| RF01-E02 | Solicitud inválida: rechazo con campos/reglas incumplidas y registro del intento |
| RF01-E03 | Sistema destino (CRM/Inventario) no disponible: error controlado, compensación de reserva |
| RF01-E04 | Consumidor no autorizado: rechazo con auditoría |
| RF01-CA01..CA05 | Criterios de aceptación de RF01 |
| RF03/RF04 (apoyo) | Consume cobertura y capacidad para asegurar viabilidad técnica de la venta |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-06 | Dominio provisión, trazable a RF01, reglas de negocio fuera de los canales |
| ARQ-02 / INT-07 | El canal no llega al CRM/Inventario directamente; todo pasa por la plataforma |
| INT-01 / INT-04 / INT-05 | API versionada con contratos completos y OpenAPI |
| INT-03 | Timeouts, reintentos y circuit breaker en llamadas al CRM (vía ms-conectores-core) |
| INT-06 | Idempotencia por idempotencyKey |
| INT-08 / INT-10 | Evidencias de intercambio; validación previa a invocar sistemas core |
| ESC-03 / ESC-05 / ESC-10 | Escala horizontal; publicación de eventos asíncrona; aislado de picos de consulta |
| OBS-01 / OBS-02 / OBS-06 | Logs estructurados y trazas end-to-end con correlationId |
| SEG-01 / SEG-03 / SEG-04 / SEG-06 / SEG-09 | TLS, OAuth2, mínimo privilegio, auditoría, eventos sin datos sensibles innecesarios |
