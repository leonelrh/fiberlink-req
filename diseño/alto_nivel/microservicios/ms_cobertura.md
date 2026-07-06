# Microservicio: ms-cobertura

## Descripción general
- **Dominio:** Disponibilidad (ARQ-01)
- **Requerimiento origen:** RF03 - Consultar cobertura (trazabilidad ARQ-03)
- **Nube / Runtime:** Azure Container Apps (tráfico alto y constante: 150,000 consultas/día, pico 4x ≈ 25,000/hora)
- **Exposición:** Azure API Management (`/v1/cobertura`), autenticación OAuth2 con Microsoft Entra ID
- **Base de datos:** Azure SQL (réplica de lectura de cobertura, sincronizada por eventos desde Inventario Oracle y GIS; evita golpear el Oracle on-premises en cada consulta — INT-12, ESC-06)

## Funcionalidades

### F1. Consultar cobertura por dirección o coordenadas

**Contrato de entrada** — `GET /v1/cobertura?direccion=...&lat=...&lon=...`
```json
{
  "direccion": "Av. Los Álamos 123, Lima",
  "coordenadas": { "lat": -12.0464, "lon": -77.0428 },
  "canal": "CRM|PORTAL|APP_MOVIL|TABLET_CAMPO",
  "correlationId": "uuid"
}
```

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "cobertura": true,
  "tecnologia": "FTTH",
  "nodoId": "NODO-4512",
  "ctoId": "CTO-8821",
  "distanciaMetros": 120,
  "planesDisponibles": ["100MB", "300MB", "600MB"],
  "fechaConsulta": "2026-07-05T10:00:00Z"
}
```

**Errores:** `400` datos inválidos (dirección y coordenadas ausentes), `401` no autenticado, `403` consumidor sin permiso, `503` réplica no disponible y origen inaccesible. Formato: `{ "codigo", "mensaje", "detalles": [], "correlationId" }`

**Pseudocódigo**
```
funcion consultarCobertura(solicitud):
    correlationId = solicitud.correlationId ?? generarUUID()
    si no autorizado(token, "cobertura:consultar"): registrarAuditoria(intento); retornar 401/403   # CA04
    si no (solicitud.direccion o solicitud.coordenadas): retornar 400 con campos incumplidos       # E02
    clave = normalizar(direccion|coordenadas)
    resultado = cacheLocal.obtener(clave)                       # ESC-04
    si resultado es nulo:
        resultado = repositorioCobertura.buscarZona(clave)      # réplica Azure SQL
        si repositorio no disponible:
            registrarTraza(correlationId, "COBERTURA", "ERROR", "INDISPONIBILIDAD")                # E03
            retornar 503 error controlado
        cacheLocal.guardar(clave, resultado, ttl=15min)
    publicarTrazaIntegracion(correlationId, origen=canal, destino="ms-cobertura", resultado, tiempoRespuesta)  # INT-08
    retornar 200 resultado
```

### F2. Sincronizar réplica de cobertura

**Contrato de entrada** — evento Pub/Sub / Service Bus `InventarioCoberturaActualizada` (envolvente INT-09):
```json
{
  "eventId": "uuid", "eventType": "InventarioCoberturaActualizada", "version": "1.0",
  "correlationId": "uuid", "sourceSystem": "INVENTARIO_ORACLE", "timestamp": "...",
  "payload": { "nodoId": "NODO-4512", "zonas": [ { "poligono": "...", "ctoId": "CTO-8821", "estado": "ACTIVA" } ] }
}
```

**Contrato de salida:** ACK del mensaje; actualización de `zona_cobertura`; en fallo de esquema → cola de mensajes rechazados (DLQ) para reproceso (INT-11).

**Pseudocódigo**
```
funcion alRecibirEventoCobertura(evento):
    si no validarEnvolvente(evento): moverADLQ(evento, motivo); retornar
    para cada zona en evento.payload.zonas:
        upsert zona_cobertura(zona, evento.timestamp)
    actualizar sincronizacion_control(fuente=evento.sourceSystem, fecha=ahora)
    registrarTraza(evento.correlationId, evento.sourceSystem, "ms-cobertura", "OK")
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE zona_cobertura (
    zona_id          BIGINT IDENTITY PRIMARY KEY,
    nodo_id          VARCHAR(20)  NOT NULL,
    cto_id           VARCHAR(20)  NOT NULL,
    poligono         VARCHAR(MAX) NOT NULL,        -- GeoJSON
    tecnologia       VARCHAR(10)  NOT NULL DEFAULT 'FTTH',
    estado           VARCHAR(15)  NOT NULL DEFAULT 'ACTIVA',
    planes_json      VARCHAR(500) NULL,
    fecha_actualizacion DATETIME2  NOT NULL,
    CONSTRAINT uq_zona UNIQUE (nodo_id, cto_id)
);
CREATE INDEX ix_zona_nodo ON zona_cobertura (nodo_id);

CREATE TABLE consulta_cobertura_log (
    consulta_id      BIGINT IDENTITY PRIMARY KEY,
    correlation_id   UNIQUEIDENTIFIER NOT NULL,
    canal            VARCHAR(20)  NOT NULL,
    parametros       VARCHAR(1000) NOT NULL,
    resultado        VARCHAR(10)  NOT NULL,        -- OK | ERROR
    codigo_error     VARCHAR(30)  NULL,
    tiempo_respuesta_ms INT       NOT NULL,
    fecha            DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_consulta_correlation ON consulta_cobertura_log (correlation_id);

CREATE TABLE sincronizacion_control (
    fuente           VARCHAR(30) PRIMARY KEY,      -- INVENTARIO_ORACLE | GIS
    ultima_sincronizacion DATETIME2 NOT NULL,
    estado           VARCHAR(15) NOT NULL          -- OK | DESACTUALIZADO
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF03-E01 | Ejecución exitosa: consulta procesada por la plataforma, respuesta conforme al contrato, traza con correlationId |
| RF03-E02 | Solicitud inválida: rechazo indicando campos/reglas incumplidas, registro con correlationId |
| RF03-E03 | Sistema destino no disponible: error controlado, registro de sistema afectado, código y tiempo |
| RF03-E04 | Consumidor no autorizado: rechazo y auditoría del intento |
| RF03-CA01..CA05 | Procesamiento vía plataforma, respuesta por contrato, error controlado, rechazo no autorizado, búsqueda por correlationId |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 | Servicio del dominio "disponibilidad" con responsabilidad clara |
| ARQ-03 | Trazable a RF03 |
| ARQ-04 / ARQ-05 | Bajo acoplamiento; contrato explícito OpenAPI y evento versionado |
| INT-01 / INT-04 | API síncrona versionada `/v1` con contrato de entrada/salida/errores |
| INT-02 / INT-09 | Sincronización asíncrona por eventos con envolvente estándar |
| INT-08 | Evidencias de intercambio (consulta_cobertura_log + ms-trazabilidad) |
| INT-11 | Reproceso: eventos inválidos a DLQ |
| INT-12 | Réplica local evita dependencia en línea del Oracle on-premises |
| ESC-03 / ESC-04 / ESC-06 / ESC-10 | Escala horizontal, caché de lecturas, sin cuello de botella hacia on-premises, picos comerciales aislados |
| OBS-01 / OBS-02 / OBS-05 | Logs estructurados sin datos sensibles, correlationId end-to-end |
| SEG-01 / SEG-03 / SEG-04 / SEG-07 | TLS, OAuth2/Entra ID, mínimo privilegio por scope, rate limiting en APIM |
