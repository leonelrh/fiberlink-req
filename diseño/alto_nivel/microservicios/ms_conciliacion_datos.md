# Microservicio: ms-conciliacion-datos

## Descripción general
- **Dominio:** Integridad de datos / Integración (ARQ-01)
- **Requerimiento origen:** RNOF01 - Integridad de datos del servicio de internet entre plataformas (ARQ-03)
- **Nube / Runtime:** Azure Functions (ejecución programada por timer — carga intermitente) + endpoint síncrono de validación cruzada
- **Sistemas comparados (vía ms-conectores-core):** Portal del Cliente (AWS), CRM, ERP, OSS, Inventario, Facturación
- **Base de datos:** Azure SQL

## Funcionalidades

### F1. Validación cruzada previa a operaciones críticas

Usada por ms-activacion antes de confirmar activación/contrato/facturación: verifica que cliente, plan, orden y equipos sean consistentes entre las plataformas involucradas.

**Contrato de entrada** — `POST /v1/conciliacion/validaciones-cruzadas`
```json
{
  "operacion": "ACTIVACION",
  "clienteId": "CLI-99213",
  "ordenInstalacionId": "ORD-55012",
  "planEsperado": "300MB",
  "equipos": ["ONT-8912", "RTR-5521"],
  "correlationId": "uuid"
}
```

**Contrato de salida** — `200 OK`
```json
{
  "correlationId": "uuid",
  "consistente": true,
  "verificaciones": [
    { "regla": "PLAN_CRM_VS_ERP", "resultado": "OK" },
    { "regla": "CLIENTE_ORDEN_VS_CRM", "resultado": "OK" },
    { "regla": "EQUIPOS_RESERVADOS_INVENTARIO", "resultado": "OK" }
  ]
}
```
Si `consistente=false`, incluye la lista de discrepancias con plataforma, campo, valor esperado y valor encontrado. Errores: `400`, `401/403`, `503` (si una plataforma indispensable no responde, la operación crítica no debe confirmarse).

**Pseudocódigo**
```
funcion validacionCruzada(peticion):
    si no autorizado(consumidor interno): retornar 401/403
    reglas = regla_conciliacion.buscar(peticion.operacion)
    resultados = []
    para cada regla en reglas:
        datos = paralelo(conectores.invocar(plataforma, operacionLectura) para plataforma en regla.plataformas)
        resultados.agregar(comparar(datos, regla))
    si alguna discrepancia:
        registrar discrepancia(origen=VALIDACION_CRUZADA); alertar operaciones     # RNOF01 alertas
    retornar 200 { consistente, verificaciones }
```

### F2. Conciliación periódica (≤ 24 horas)

Timer diario (y bajo demanda). Compara los datos maestros de RNOF01 entre todas las plataformas: identificador de cliente, plan, estado del servicio, contrato, fechas de activación/facturación, equipos y su estado, orden, cuadrilla.

**Contrato de entrada** — trigger timer o `POST /v1/conciliacion/ejecuciones` `{ "alcance": "COMPLETA|INCREMENTAL", "desde": "..." }`
**Contrato de salida** — `202 Accepted`; resultado consultable: totales comparados, discrepancias por tipo y plataforma, y alertas emitidas.

**Pseudocódigo**
```
funcion ejecutarConciliacion(alcance):
    ejecucion = crear ejecucion_conciliacion(estado=EN_CURSO)
    servicios = obtenerServiciosModificados(desde ultima ejecucion si INCREMENTAL)
    para cada lote de servicios (paginado, ESC-07):
        datosPorPlataforma = conectores.invocar(cada plataforma, "obtenerDatosServicio", lote)
        para cada servicio: para cada regla de datos maestros:
            si valores difieren entre plataformas:
                registrar discrepancia(servicio, dato, plataformas, valores)
                si dato crítico (plan facturado, contrato, estado, equipo duplicado):
                    emitir alerta inmediata a operaciones                       # antes de impactar al cliente
    ejecucion.finalizar(totales); publicarEvento("ConciliacionFinalizada")
    publicarAuditoria("CONCILIACION", resumen)
```

### F3. Gestionar discrepancias

**Contrato de entrada** — `GET /v1/conciliacion/discrepancias?estado=ABIERTA&plataforma=...&dato=...` y `PATCH /v1/conciliacion/discrepancias/{id}` `{ "estado": "RESUELTA", "resolucion": "...", "usuario": "..." }`
**Contrato de salida** — lista paginada / discrepancia actualizada con auditoría de resolución.

**Pseudocódigo**
```
funcion resolverDiscrepancia(id, resolucion, usuario):
    si rol(usuario) not in [OPERACIONES]: retornar 403
    d = repositorio.obtener(id); si nula: retornar 404
    actualizar d(estado=RESUELTA, resolucion, usuario, fecha)
    publicarAuditoria("RESOLUCION_DISCREPANCIA", d)
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE regla_conciliacion (
    regla_id        VARCHAR(40) PRIMARY KEY,   -- ej. PLAN_CRM_VS_FACTURACION
    dato_maestro    VARCHAR(50) NOT NULL,      -- según tabla de datos maestros RNOF01
    plataformas     VARCHAR(200) NOT NULL,     -- CSV: CRM,ERP,FACTURACION
    operacion_asociada VARCHAR(20) NULL,       -- ACTIVACION | FACTURACION | NULL (solo batch)
    criticidad      VARCHAR(10) NOT NULL,      -- ALTA | MEDIA | BAJA
    activa          BIT NOT NULL DEFAULT 1
);

CREATE TABLE ejecucion_conciliacion (
    ejecucion_id    BIGINT IDENTITY PRIMARY KEY,
    alcance         VARCHAR(15) NOT NULL,      -- COMPLETA | INCREMENTAL
    estado          VARCHAR(15) NOT NULL,      -- EN_CURSO | FINALIZADA | FALLIDA
    servicios_comparados INT NULL,
    discrepancias_detectadas INT NULL,
    fecha_inicio    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    fecha_fin       DATETIME2 NULL
);

CREATE TABLE discrepancia (
    discrepancia_id BIGINT IDENTITY PRIMARY KEY,
    ejecucion_id    BIGINT NULL REFERENCES ejecucion_conciliacion(ejecucion_id),
    origen          VARCHAR(20) NOT NULL,      -- BATCH | VALIDACION_CRUZADA
    servicio_id     VARCHAR(20) NULL,
    cliente_id      VARCHAR(20) NULL,
    dato_maestro    VARCHAR(50) NOT NULL,
    plataforma_a    VARCHAR(20) NOT NULL,
    valor_a         VARCHAR(300) NULL,
    plataforma_b    VARCHAR(20) NOT NULL,
    valor_b         VARCHAR(300) NULL,
    criticidad      VARCHAR(10) NOT NULL,
    estado          VARCHAR(15) NOT NULL DEFAULT 'ABIERTA',  -- ABIERTA | EN_ANALISIS | RESUELTA
    alerta_emitida  BIT NOT NULL DEFAULT 0,
    resolucion      VARCHAR(500) NULL,
    usuario_resolucion VARCHAR(50) NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    fecha_deteccion DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    fecha_resolucion DATETIME2 NULL
);
CREATE INDEX ix_discrepancia_estado ON discrepancia (estado, criticidad);
CREATE INDEX ix_discrepancia_servicio ON discrepancia (servicio_id);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RNOF01-CA01 | Estado idéntico OSS/CRM/Portal verificado (latencia ≤ 5 min medida por ms-estado-servicio, verificada aquí) |
| RNOF01-CA02 | Plan CRM = plan facturado = plan visible en Portal |
| RNOF01-CA03 | Ningún equipo simultáneamente disponible en Inventario e instalado en OSS |
| RNOF01-CA04 | Fecha de inicio de facturación ≥ fecha de activación en OSS |
| RNOF01-CA05 | Número de contrato idéntico en CRM/ERP/Facturación/Portal |
| RNOF01-CA07 | Conciliación automática detecta y reporta discrepancias en ≤ 24 h |
| RNOF01-CA08 | Alertas de inconsistencia llegan a operaciones antes de impactar al cliente |
| RNOF01 (mecanismos) | Validación cruzada previa a operaciones críticas; conciliación periódica; alertas |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-08 | Responsabilidad única de integridad; Functions por carga intermitente programada |
| ARQ-02 / INT-07 | Lee todas las plataformas exclusivamente vía ms-conectores-core |
| INT-01 / INT-04 / INT-12 | API interna versionada; tolerancia a indisponibilidad parcial de on-premises |
| ESC-05 / ESC-07 | Conciliación batch asíncrona por lotes con límites de concurrencia (no degrada operación — RNOF01 disponibilidad) |
| OBS-01 / OBS-02 / OBS-03 / OBS-04 | Logs, correlación, métricas de discrepancias, alertas de inconsistencia |
| SEG-04 / SEG-06 | Acceso interno con mínimo privilegio; auditoría de resoluciones |
