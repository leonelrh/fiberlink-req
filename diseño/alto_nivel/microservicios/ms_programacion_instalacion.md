# Microservicio: ms-programacion-instalacion

## Descripción general
- **Dominio:** Provisión (ARQ-01)
- **Requerimientos origen:** RF08 - Programar instalación y RF10 - Reprogramar instalación (ARQ-03); genera eventos auditables RNOF03
- **Nube / Runtime:** Azure Container Apps (proceso operativo diario constante)
- **Exposición:** Azure API Management (`/v1/instalaciones`), OAuth2 Entra ID; el enlace de reprogramación del cliente entra por el Portal (AWS) → APIM
- **Sistemas involucrados (vía ms-conectores-core):** Field Service SaaS (agenda de cuadrillas), ERP (materiales), Inventario (equipos ONT/router), CRM (orden), OSS (orden técnica)
- **Base de datos:** Azure SQL

## Funcionalidades

### F1. Programar instalación

Valida disponibilidad de cuadrilla, materiales, equipos, ruta y permisos; reserva recursos de forma transaccional con compensación ante fallo (patrón saga).

**Contrato de entrada** — `POST /v1/instalaciones/programaciones`
```json
{
  "ordenInstalacionId": "ORD-55012",
  "fechaSolicitada": "2026-07-10",
  "franjaHoraria": "09:00-12:00",
  "materiales": [ { "codigo": "FIBRA-DROP", "cantidad": 60 } ],
  "equipos": ["ONT", "ROUTER"],
  "usuario": "operador.mlopez",
  "correlationId": "uuid"
}
```

**Contrato de salida** — `201 Created`
```json
{
  "ordenInstalacionId": "ORD-55012",
  "estado": "PROGRAMADA",
  "cuadrillaId": "CUAD-12",
  "tecnicoAsignado": "J. Pérez",
  "fechaConfirmada": "2026-07-10",
  "franjaHoraria": "09:00-12:00",
  "reservas": { "materiales": "RSM-771", "equipos": "RSE-902" },
  "mensaje": "Instalación programada correctamente",
  "correlationId": "uuid"
}
```

**Errores (mensajes funcionales del requerimiento):**
- `409 CUADRILLA_NO_DISPONIBLE` — "No hay cuadrilla disponible para la fecha seleccionada. Por favor elija otra fecha"
- `409 MATERIALES_INSUFICIENTES` — "Materiales insuficientes en inventario. No es posible programar la instalación"
- `409 PERMISOS_PENDIENTES` — "Los permisos de instalación son requeridos antes de programar. Verificar"
- `500 ERROR_TECNICO` — "No fue posible programar la instalación. Intente nuevamente" (con reversión de recursos)
- `400/401/403/404` estándar.

**Pseudocódigo**
```
funcion programarInstalacion(solicitud):
    si no autorizado(token, "instalaciones:programar"): auditar; retornar 401/403
    orden = repositorio.obtenerOrden(solicitud.ordenInstalacionId); si nula: retornar 404
    cuadrilla = conectores.invocar("FIELD_SERVICE", "consultarDisponibilidad", fecha, franja)
    si no cuadrilla.disponible: retornar 409 CUADRILLA_NO_DISPONIBLE            # RF08-E02 (sin asignar recursos)
    materiales = conectores.invocar("ERP", "verificarStock", solicitud.materiales)
    si no materiales.suficientes: retornar 409 MATERIALES_INSUFICIENTES        # RF08-E03 (sin reservar)
    si no orden.rutaHabilitada: retornar 409 RUTA_NO_HABILITADA
    si no orden.permisosObtenidos: retornar 409 PERMISOS_PENDIENTES            # RF08-E04 (sin asignar recursos)

    saga = iniciarSaga(orden, correlationId)                                   # RNOF01 atomicidad
    intentar:
        rsvCuadrilla = conectores.invocar("FIELD_SERVICE", "asignarCuadrilla", ...)   ; saga.registrar
        rsvMateriales = conectores.invocar("ERP", "reservarMateriales", ...)          ; saga.registrar
        rsvEquipos   = conectores.invocar("INVENTARIO", "reservarEquipos", ...)       ; saga.registrar
        actualizar orden (estado=PROGRAMADA, cuadrilla, fecha, franja)
        publicarEvento("InstalacionProgramada", envolventeINT09)               # dispara RF09 notificación
        publicarAuditoria("PROGRAMACION", EXITOSO)                             # RNOF03-EV01/EV02
        retornar 201
    capturar errorTecnico:                                                     # RF08-E05
        saga.compensarTodo()             # libera cuadrilla, materiales, equipos en orden inverso
        orden.estado se mantiene sin PROGRAMADA; no se notifica al cliente
        publicarAuditoria("PROGRAMACION", FALLIDO, error); registrarIncidenteTecnico
        retornar 500 ERROR_TECNICO
```

### F2. Reprogramar instalación

**Contrato de entrada** — `POST /v1/instalaciones/{ordenId}/reprogramaciones` (token del enlace enviado al cliente)
```json
{
  "tokenReprogramacion": "jwt-firmado-del-enlace",
  "nuevaFecha": "2026-07-14",
  "nuevaFranja": "14:00-17:00",
  "correlationId": "uuid"
}
```

**Contrato de salida** — `200 OK`
```json
{ "ordenInstalacionId": "ORD-55012", "estado": "PROGRAMADA", "fechaConfirmada": "2026-07-14", "franjaHoraria": "14:00-17:00", "mensaje": "Instalación reprogramada correctamente", "correlationId": "uuid" }
```

**Errores:**
- `422 FUERA_DE_PLAZO` — "…El plazo máximo para solicitar una reprogramación es de 24 horas antes de la fecha programada"
- `409 ESTADO_NO_REPROGRAMABLE` — "…La orden no se encuentra en un estado válido para reprogramación. Contactar a soporte"
- `409 SIN_DISPONIBILIDAD` — "No hay disponibilidad para la fecha seleccionada. Por favor elija otra fecha"
- `500 ERROR_TECNICO` — "No fue posible reprogramar la instalación. Intente nuevamente" (reversión completa)

**Pseudocódigo**
```
funcion reprogramarInstalacion(ordenId, solicitud):
    si no validarTokenEnlace(solicitud.tokenReprogramacion, ordenId): retornar 401
    orden = repositorio.obtenerOrden(ordenId)
    si orden.estado != PROGRAMADA: retornar 409 ESTADO_NO_REPROGRAMABLE          # RF10-E03 (sin modificar nada)
    si (orden.fechaConfirmada - ahora) < 24 horas: retornar 422 FUERA_DE_PLAZO   # RF10-E02 (sin modificar nada)
    disponibilidad = conectores.invocar("FIELD_SERVICE", "consultarDisponibilidad", nuevaFecha, nuevaFranja)
    si no disponibilidad.disponible: retornar 409 SIN_DISPONIBILIDAD             # RF10-E04 (recursos intactos)
    saga = iniciarSaga(orden, correlationId)
    intentar:
        conectores.invocar("FIELD_SERVICE", "liberarCuadrilla", asignacionAnterior)   ; saga.registrar
        conectores.invocar("FIELD_SERVICE", "asignarCuadrilla", nuevaFecha)           ; saga.registrar
        conectores.invocar("INVENTARIO", "reasignarReservaEquipos", nuevaFecha)       ; saga.registrar
        actualizar orden (nuevaFecha, nuevaFranja, estado=PROGRAMADA)
        insertar historial_programacion (fechaAnterior -> nueva, origen=CLIENTE)
        publicarEvento("InstalacionReprogramada"); publicarAuditoria("REPROGRAMACION", EXITOSO)
        retornar 200
    capturar errorTecnico:                                                       # RF10-E05
        saga.compensarTodo()      # restaura fecha, franja y recursos originales
        publicarAuditoria("REPROGRAMACION", FALLIDO); registrarIncidenteTecnico
        retornar 500 ERROR_TECNICO
```

### F3. Consultar disponibilidad de agenda

**Contrato de entrada** — `GET /v1/instalaciones/disponibilidad?zona=...&desde=...&hasta=...`
**Contrato de salida** — `200 OK` `{ "fechas": [ { "fecha": "2026-07-14", "franjas": ["09:00-12:00", "14:00-17:00"] } ] }` (consulta al Field Service con caché corto).

**Pseudocódigo**
```
funcion consultarDisponibilidad(zona, rango):
    si cache tiene (zona, rango): retornar cache          # ESC-04, TTL 5 min
    resultado = conectores.invocar("FIELD_SERVICE", "consultarDisponibilidad", zona, rango)
    guardar cache; retornar 200 resultado
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE orden_instalacion (
    orden_id        VARCHAR(20) PRIMARY KEY,
    solicitud_id    VARCHAR(20) NOT NULL,
    cliente_id      VARCHAR(20) NOT NULL,
    estado          VARCHAR(20) NOT NULL,   -- PENDIENTE | PROGRAMADA | EN_CAMPO | INSTALADA | CERRADA | CANCELADA
    fecha_confirmada DATE       NULL,
    franja_horaria  VARCHAR(15) NULL,
    cuadrilla_id    VARCHAR(15) NULL,
    tecnico_asignado VARCHAR(80) NULL,
    ruta_habilitada BIT NOT NULL DEFAULT 0,
    permisos_obtenidos BIT NOT NULL DEFAULT 0,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    fecha_creacion  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_orden_cliente ON orden_instalacion (cliente_id);
CREATE INDEX ix_orden_estado_fecha ON orden_instalacion (estado, fecha_confirmada);

CREATE TABLE asignacion_recurso (
    asignacion_id   BIGINT IDENTITY PRIMARY KEY,
    orden_id        VARCHAR(20) NOT NULL REFERENCES orden_instalacion(orden_id),
    tipo_recurso    VARCHAR(15) NOT NULL,   -- CUADRILLA | MATERIAL | EQUIPO
    referencia_externa VARCHAR(30) NOT NULL, -- id de reserva en FieldService/ERP/Inventario
    estado          VARCHAR(15) NOT NULL,   -- RESERVADO | CONFIRMADO | LIBERADO
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE historial_programacion (
    historial_id    BIGINT IDENTITY PRIMARY KEY,
    orden_id        VARCHAR(20) NOT NULL REFERENCES orden_instalacion(orden_id),
    fecha_anterior  DATE NULL,
    franja_anterior VARCHAR(15) NULL,
    fecha_nueva     DATE NOT NULL,
    franja_nueva    VARCHAR(15) NOT NULL,
    origen          VARCHAR(15) NOT NULL,   -- OPERADOR | CLIENTE
    usuario         VARCHAR(50) NOT NULL,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE saga_ejecucion (
    saga_id         UNIQUEIDENTIFIER PRIMARY KEY,
    orden_id        VARCHAR(20) NOT NULL,
    operacion       VARCHAR(20) NOT NULL,   -- PROGRAMACION | REPROGRAMACION
    estado          VARCHAR(15) NOT NULL,   -- EN_CURSO | COMPLETADA | COMPENSADA
    pasos_json      VARCHAR(MAX) NOT NULL,  -- pasos ejecutados y compensaciones
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    fecha           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF08-E01 | Programación exitosa: validaciones, reservas, estado "Programada", notificación al cliente |
| RF08-E02 | Rechazo por cuadrilla no disponible (sin asignar recursos) |
| RF08-E03 | Rechazo por falta de materiales (sin reservar) |
| RF08-E04 | Rechazo por permisos no obtenidos (sin asignar recursos) |
| RF08-E05 | Error técnico: reversión de recursos, sin estado "Programada", sin notificación, incidente registrado |
| RF10-E01 | Reprogramación exitosa: verificación, liberación y reasignación de recursos, notificación |
| RF10-E02 | Rechazo por plazo < 24 horas |
| RF10-E03 | Rechazo por estado no reprogramable |
| RF10-E04 | Rechazo por falta de disponibilidad en nueva fecha |
| RF10-E05 | Error técnico con reversión completa e incidente registrado |
| RNOF03-EV01/EV02 | Auditoría de programación y asignación de recursos |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-06 | Dominio provisión; trazable a RF08/RF10; regla de las 24 h vive aquí, no en el canal |
| ARQ-02 / INT-07 | CRM, ERP, Inventario y Field Service solo se tocan vía ms-conectores-core |
| INT-01 / INT-03 / INT-04 / INT-06 | API versionada, resiliencia en llamadas, contratos completos, saga idempotente |
| INT-02 / INT-09 | Eventos InstalacionProgramada/Reprogramada con envolvente estándar |
| ESC-05 / ESC-07 / ESC-09 | Notificación asíncrona, control de concurrencia por orden, degradación controlada |
| OBS-01 / OBS-02 / OBS-03 | Logs, correlationId, métricas de programaciones/rechazos |
| SEG-03 / SEG-04 / SEG-06 | OAuth2; enlace de cliente con token firmado de alcance único; auditoría completa |
