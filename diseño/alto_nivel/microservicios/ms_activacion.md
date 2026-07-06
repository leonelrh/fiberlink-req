# Microservicio: ms-activacion

## Descripción general
- **Dominio:** Provisión / Activación (ARQ-01)
- **Requerimientos origen:** RF11 - Activar servicio de internet; RNOF01 (atomicidad y propagación); RNOF03 (auditoría del ciclo) (ARQ-03)
- **Nube / Runtime:** Azure Container Apps (proceso crítico de negocio, siempre activo, latencia baja)
- **Exposición:** Azure API Management (`/v1/activaciones`), OAuth2 Entra ID (app del técnico)
- **Sistemas involucrados (vía ms-conectores-core):** OSS (provisión ONT/OLT/BRAS), CRM (contrato), Facturación (alta de facturación), Inventario (equipos instalados), ERP
- **Base de datos:** Azure SQL (estado de la saga de activación y contratos)

## Funcionalidades

### F1. Activar servicio (saga con compensación)

Orquesta la activación de extremo a extremo de forma atómica (RNOF01): validación cliente↔orden → activación en OSS (timeout 30 s) → generación de contrato → vinculación → datos de facturación → cierre de orden → envío de contrato. Ante fallo parcial, revierte todo.

**Contrato de entrada** — `POST /v1/activaciones`
```json
{
  "ordenInstalacionId": "ORD-55012",
  "documentoCliente": { "tipo": "DNI", "numero": "45781234" },
  "checklistTecnico": { "routerConfigurado": true, "potenciaOpticaValidada": true, "datosServicioConfirmados": true },
  "tecnico": "jperez",
  "correlationId": "uuid",
  "idempotencyKey": "uuid"
}
```

**Contrato de salida** — `201 Created`
```json
{
  "activacionId": "ACT-90112",
  "estado": "ACTIVO",
  "numeroContrato": "CT-2026-7781",
  "servicioId": "SRV-33421",
  "facturacion": { "plan": "300MB", "fechaInicio": "2026-07-10" },
  "ordenInstalacion": { "id": "ORD-55012", "estado": "CERRADA", "resultado": "EXITOSO" },
  "mensaje": "Servicio activado correctamente",
  "correlationId": "uuid"
}
```

**Errores (mensajes funcionales del requerimiento):**
- `422 DATOS_NO_COINCIDEN` — "Los datos del cliente no coincide con la orden de instalación. Verificar" (sin orden de activación ni contrato)
- `500 ERROR_GENERACION_CONTRATO` — "No fue posible realizar la activación del servicio" (reversión de la activación en OSS, sin estado "Activo", incidente registrado)
- `504 TIMEOUT_ACTIVACION` — confirmación del OSS no llega en 30 s: reversión, sin "Activo", sin contrato, incidente registrado
- `400/401/403/404/409` estándar (`409`: idempotencyKey ya procesada → retorna resultado original)

**Pseudocódigo**
```
funcion activarServicio(solicitud):
    si no autorizado(token, "activaciones:crear"): auditar; retornar 401/403
    si existe activacion con idempotencyKey: retornar resultado original          # INT-06
    orden = repositorio.obtenerOrden(solicitud.ordenInstalacionId); si nula: retornar 404
    publicarAuditoria("SOLICITUD_ACTIVACION", tecnico)                            # RNOF03-EV05

    # Paso 0: validación de consistencia cliente-orden + validación cruzada entre plataformas
    si solicitud.documentoCliente != orden.documentoCliente:
        publicarAuditoria("VALIDACION_CONSISTENCIA", FALLIDO)
        retornar 422 DATOS_NO_COINCIDEN                                           # RF11-E02
    consistencia = msConciliacionDatos.validacionCruzada(orden, plan, cliente)    # RNOF01 validación cruzada
    si no consistencia.ok: retornar 409 INCONSISTENCIA_DATOS (alerta a operaciones)
    publicarAuditoria("VALIDACION_CONSISTENCIA", EXITOSO)                         # RNOF03-EV06

    saga = iniciarSaga("ACTIVACION", orden, correlationId)
    intentar:
        # Paso 1: activación técnica en OSS con timeout de 30 s
        resOSS = conectores.invocar("OSS", "activarServicio", orden, timeout=30s) ; saga.registrar("OSS")
        si timeout o sin confirmación:                                            # RF11-E04
            saga.compensarTodo(); publicarAuditoria("CONFIRMACION_ACTIVACION", FALLIDO)
            registrarIncidenteTecnico(); retornar 504 TIMEOUT_ACTIVACION
        publicarAuditoria("CONFIRMACION_ACTIVACION", EXITOSO)                     # RNOF03-EV07

        # Paso 2: generación de contrato en CRM
        contrato = conectores.invocar("CRM", "generarContrato", cliente, plan)    ; saga.registrar("CRM")
        si falla:                                                                 # RF11-E03
            saga.compensarTodo()      # revierte activación en OSS
            publicarAuditoria("GENERACION_CONTRATO", FALLIDO); registrarIncidenteTecnico()
            retornar 500 ERROR_GENERACION_CONTRATO
        publicarAuditoria("GENERACION_CONTRATO", EXITOSO)                         # RNOF03-EV08

        # Pasos 3-6: vinculación, facturación, inventario, cierre
        conectores.invocar("CRM", "vincularServicioContrato", ...)                ; saga.registrar
        publicarAuditoria("VINCULACION_SERVICIO", EXITOSO)                        # RNOF03-EV09
        conectores.invocar("FACTURACION", "generarDatosFacturacion",
                           contrato, plan, fechaInicio >= fechaActivacionOSS)     ; saga.registrar
        publicarAuditoria("GENERACION_FACTURACION", EXITOSO)                      # RNOF03-EV10
        conectores.invocar("INVENTARIO", "marcarEquiposInstalados", equipos, contrato) ; saga.registrar
        actualizar orden (estado=CERRADA, resultado=EXITOSO)
        publicarAuditoria("CIERRE_ORDEN", EXITOSO)                                # RNOF03-EV11

        persistir activacion + contrato (estado=ACTIVO)
        publicarEvento("ServicioActivado", envolventeINT09)     # propaga a Portal/CRM/ERP ≤ 5 min (RNOF01)
        msNotificaciones.enviarContrato(cliente.email, contrato)                  # RNOF03-EV12
        retornar 201
    capturar errorTecnico:
        saga.compensarTodo()                                                      # RNOF01 atomicidad
        publicarAuditoria("REVERSION", EXITOSO, detalle=pasosRevertidos)          # RNOF03-EV13
        registrarIncidenteTecnico()                                               # RNOF03-EV14
        retornar 500 "No fue posible realizar la activación del servicio"
```

### F2. Revertir activación (compensación explícita)

**Contrato de entrada** — `POST /v1/activaciones/{activacionId}/reversiones` `{ "motivo": "...", "usuario": "...", "correlationId": "uuid" }` (uso interno de la saga y de operaciones).
**Contrato de salida** — `200 OK` con pasos revertidos en orden inverso: facturación anulada, contrato anulado, OSS desactivado, equipos devueltos a "Reservado", orden reabierta.

**Pseudocódigo**
```
funcion revertirActivacion(activacionId, motivo):
    saga = repositorio.obtenerSaga(activacionId)
    para paso en reverso(saga.pasosEjecutados):
        conectores.invocar(paso.sistema, paso.operacionCompensacion, paso.datos)
        registrar compensacion(paso, resultado)
    actualizar activacion(estado=REVERTIDA)
    publicarEvento("ActivacionRevertida"); publicarAuditoria("REVERSION", motivo)
```

### F3. Consultar activación

**Contrato de entrada** — `GET /v1/activaciones/{activacionId}`
**Contrato de salida** — `200 OK` con estado, contrato, pasos de la saga y timestamps. Errores: `404`, `401/403`.

**Pseudocódigo**
```
funcion consultarActivacion(id):
    si no autorizado: retornar 401/403
    a = repositorio.obtener(id); si nula: retornar 404
    retornar 200 { a, pasosSaga }
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE activacion (
    activacion_id   VARCHAR(20) PRIMARY KEY,
    idempotency_key UNIQUEIDENTIFIER NOT NULL UNIQUE,
    orden_id        VARCHAR(20) NOT NULL,
    cliente_id      VARCHAR(20) NOT NULL,
    servicio_id     VARCHAR(20) NULL,
    estado          VARCHAR(20) NOT NULL,   -- EN_PROCESO | ACTIVO | REVERTIDA | FALLIDA
    tecnico         VARCHAR(50) NOT NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    fecha_activacion DATETIME2 NULL,
    fecha_creacion  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_activacion_orden ON activacion (orden_id);
CREATE INDEX ix_activacion_correlation ON activacion (correlation_id);

CREATE TABLE contrato (
    contrato_numero VARCHAR(25) PRIMARY KEY,
    activacion_id   VARCHAR(20) NOT NULL REFERENCES activacion(activacion_id),
    cliente_id      VARCHAR(20) NOT NULL,
    plan_contratado VARCHAR(20) NOT NULL,
    monto_mensual   DECIMAL(10,2) NOT NULL,
    fecha_inicio_facturacion DATE NOT NULL,
    estado          VARCHAR(15) NOT NULL,   -- VIGENTE | ANULADO
    enviado_email   BIT NOT NULL DEFAULT 0,
    fecha_generacion DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT ck_fecha_fact CHECK (fecha_inicio_facturacion >= CAST(fecha_generacion AS DATE))
);

CREATE TABLE activacion_saga_paso (
    paso_id         BIGINT IDENTITY PRIMARY KEY,
    activacion_id   VARCHAR(20) NOT NULL REFERENCES activacion(activacion_id),
    orden_paso      INT NOT NULL,
    sistema         VARCHAR(20) NOT NULL,   -- OSS | CRM | FACTURACION | INVENTARIO
    operacion       VARCHAR(60) NOT NULL,
    operacion_compensacion VARCHAR(60) NOT NULL,
    estado          VARCHAR(15) NOT NULL,   -- EJECUTADO | COMPENSADO | FALLIDO
    respuesta_json  VARCHAR(MAX) NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE incidente_tecnico (
    incidente_id    BIGINT IDENTITY PRIMARY KEY,
    activacion_id   VARCHAR(20) NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    tipo            VARCHAR(30) NOT NULL,   -- TIMEOUT_OSS | ERROR_CONTRATO | ERROR_TECNICO
    detalle         VARCHAR(1000) NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF11-E01 | Activación exitosa: validación cliente-orden, estado "Activo", contrato generado y vinculado, datos de facturación, orden cerrada "Exitoso", contrato por correo |
| RF11-E02 | Datos de cliente no coinciden: sin orden de activación ni contrato, mensaje de verificación |
| RF11-E03 | Error al generar contrato: reversión de la activación, sin estado "Activo", incidente registrado |
| RF11-E04 | Sin confirmación del OSS en 30 s: reversión total, sin "Activo" ni contrato, incidente registrado |
| RNOF01-CA | Atomicidad multi-plataforma (saga + compensación), fecha facturación ≥ fecha activación, contrato idéntico en CRM/ERP/Facturación/Portal, reversión sin datos inconsistentes |
| RNOF03-EV05..EV14 | Auditoría de solicitud, validación, confirmación, contrato, vinculación, facturación, cierre, envío, reversión e incidentes |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-06 | Dominio provisión; trazable a RF11; la lógica de activación no vive en la app del técnico |
| ARQ-02 / INT-07 | OSS, CRM, Facturación e Inventario solo se tocan vía ms-conectores-core |
| INT-01 / INT-03 / INT-04 / INT-06 | API versionada, timeout explícito de 30 s, contratos completos, idempotencia |
| INT-02 / INT-09 | Evento ServicioActivado con envolvente estándar para propagación ≤ 5 min |
| ESC-02 / ESC-09 / ESC-10 | Objetivo de latencia definido (30 s), degradación controlada, aislado de picos de consultas |
| OBS-01 / OBS-02 / OBS-03 / OBS-06 | Logs, correlationId end-to-end, métricas de activaciones/fallos, trazas distribuidas |
| SEG-03 / SEG-04 / SEG-06 | OAuth2 del técnico, mínimo privilegio, auditoría de toda operación crítica |
