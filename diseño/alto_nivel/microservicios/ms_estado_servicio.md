# Microservicio: ms-estado-servicio

## Descripción general
- **Dominio:** Integración / Atención (ARQ-01)
- **Requerimiento origen:** RF05 - Consultar estado de servicio (ARQ-03); apoya RNOF01 (vista consistente para Portal)
- **Nube / Runtime:** Azure Container Apps (20,000 consultas/día + consultas del portal, tráfico constante)
- **Exposición:** Azure API Management (`/v1/servicios/{servicioId}/estado`), OAuth2 Entra ID
- **Base de datos:** Azure SQL (caché materializada del estado 360, alimentada por eventos — el estado que ve el cliente es el mismo que registran OSS/CRM/Facturación)

## Funcionalidades

### F1. Consultar estado 360 del servicio

Agrega estado comercial (CRM), técnico (OSS) y de facturación (Facturación) en una sola respuesta. Sirve primero desde la vista materializada; si el consumidor exige dato en línea (`modo=directo`), consulta los sistemas vía ms-conectores-core con degradación parcial.

**Contrato de entrada** — `GET /v1/servicios/{servicioId}/estado?modo=cache|directo`
```json
{ "servicioId": "SRV-33421", "modo": "cache", "canal": "CALL_CENTER|PORTAL|APP_MOVIL", "correlationId": "uuid" }
```

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "servicioId": "SRV-33421",
  "clienteId": "CLI-99213",
  "estadoComercial": { "origen": "CRM", "estado": "CONTRATO_VIGENTE", "plan": "300MB", "actualizado": "..." },
  "estadoTecnico":   { "origen": "OSS", "estado": "ACTIVO", "fechaActivacion": "...", "actualizado": "..." },
  "estadoFacturacion": { "origen": "FACTURACION", "estado": "AL_DIA", "contrato": "CT-2026-7781", "actualizado": "..." },
  "fuentesDegradadas": []
}
```

**Errores:** `400` servicioId inválido, `401/403` no autorizado, `404` servicio inexistente, `206`-semántico: si una fuente en modo directo no responde, se retorna `200` con esa sección en `"estado": "NO_DISPONIBLE"` y la fuente en `fuentesDegradadas` (ESC-09); `503` solo si ninguna fuente ni caché responde.

**Pseudocódigo**
```
funcion consultarEstado(servicioId, modo):
    correlationId = obtenerOGenerar()
    si no autorizado(token, "estado:consultar"): auditar; retornar 401/403        # E04
    si no valido(servicioId): retornar 400                                        # E02
    si modo == "cache":
        vista = repositorio.obtenerVista(servicioId)
        si vista nula: retornar 404
        retornar 200 vista
    # modo directo: consultas en paralelo con degradación parcial
    resultados = paralelo(
        msConectoresCore.invocar("CRM", "estadoComercial", servicioId),
        msConectoresCore.invocar("OSS", "estadoTecnico", servicioId),
        msConectoresCore.invocar("FACTURACION", "estadoCuenta", servicioId))
    para cada r fallido: marcar seccion NO_DISPONIBLE; agregar a fuentesDegradadas;
        registrarTraza(correlationId, "ms-estado-servicio", r.sistema, ERROR, codigo, tiempo)   # E03
    si todas fallidas y sin vista en caché: retornar 503
    retornar 200 agregado
```

### F2. Actualizar vista de estado por eventos

Consume `ServicioActivado`, `OrdenInstalacionActualizada`, `FacturacionIniciada`, `EstadoServicioCambiado` (envolvente INT-09) y actualiza la vista materializada. Garantiza propagación ≤ 5 minutos al Portal (RNOF01).

**Contrato de entrada:** evento INT-09. **Contrato de salida:** ACK; upsert de vista; inválidos a DLQ.

**Pseudocódigo**
```
funcion alRecibirEventoEstado(evento):
    si no validarEnvolvente(evento): moverADLQ(evento); retornar
    upsert vista_estado_servicio(evento.payload, fuente=evento.sourceSystem, fecha=evento.timestamp)
    registrar latencia de propagación (evento.timestamp vs ahora)          # métrica RNOF01 ≤ 5 min
    si latencia > umbral: emitir alerta                                    # OBS-04
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE vista_estado_servicio (
    servicio_id        VARCHAR(20) PRIMARY KEY,
    cliente_id         VARCHAR(20) NOT NULL,
    contrato_numero    VARCHAR(25) NULL,
    plan_contratado    VARCHAR(20) NULL,
    estado_comercial   VARCHAR(30) NULL,
    estado_tecnico     VARCHAR(30) NULL,
    estado_facturacion VARCHAR(30) NULL,
    fecha_activacion   DATETIME2   NULL,
    actualizado_crm    DATETIME2   NULL,
    actualizado_oss    DATETIME2   NULL,
    actualizado_fact   DATETIME2   NULL
);
CREATE INDEX ix_vista_cliente ON vista_estado_servicio (cliente_id);

CREATE TABLE consulta_estado_log (
    consulta_id     BIGINT IDENTITY PRIMARY KEY,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    servicio_id     VARCHAR(20) NOT NULL,
    canal           VARCHAR(20) NOT NULL,
    modo            VARCHAR(10) NOT NULL,
    resultado       VARCHAR(10) NOT NULL,
    fuentes_degradadas VARCHAR(100) NULL,
    tiempo_respuesta_ms INT NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_consulta_estado_correlation ON consulta_estado_log (correlation_id);

CREATE TABLE propagacion_metrica (
    metrica_id      BIGINT IDENTITY PRIMARY KEY,
    event_id        UNIQUEIDENTIFIER NOT NULL,
    event_type      VARCHAR(60) NOT NULL,
    source_system   VARCHAR(30) NOT NULL,
    latencia_seg    INT NOT NULL,
    dentro_sla      BIT NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF05-E01 | Ejecución exitosa: estado consistente comercial/técnico/facturación con traza |
| RF05-E02 | Solicitud inválida rechazada con detalle |
| RF05-E03 | Sistema destino no disponible: degradación parcial controlada y registro de la falla |
| RF05-E04 | Consumidor no autorizado rechazado con auditoría |
| RF05-CA01..CA05 | Criterios de aceptación de RF05 |
| RNOF01-CA01 (apoyo) | Estado idéntico en OSS/CRM/Portal con propagación ≤ 5 minutos medida |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-06 | Responsabilidad única trazable a RF05; el Portal no agrega estados por su cuenta |
| INT-01 / INT-04 | API versionada con contrato completo |
| INT-02 / INT-09 / INT-11 | Vista alimentada por eventos con envolvente estándar y DLQ |
| INT-12 / ESC-09 | Degradación parcial ante indisponibilidad de sistemas on-premises |
| ESC-03 / ESC-04 / ESC-10 | Escala horizontal; vista materializada como caché; consultas no impactan activación/facturación |
| OBS-01 / OBS-02 / OBS-03 / OBS-04 | Logs, correlación, métrica de latencia de propagación con alerta |
| SEG-01 / SEG-03 / SEG-04 / SEG-07 | TLS, OAuth2, mínimo privilegio, rate limiting en APIM |
