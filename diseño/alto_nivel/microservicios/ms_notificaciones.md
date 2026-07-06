# Microservicio: ms-notificaciones

## Descripción general
- **Dominio:** Canales / transversal (ARQ-01)
- **Requerimientos origen:** RF09 - Notificar programación de instalación (ARQ-03); apoya RF12 (notificaciones proactivas de incidentes) y RF11 (envío de contrato)
- **Nube / Runtime:** Azure Functions (carga dirigida por eventos e intermitente: se dispara por mensajes de Service Bus)
- **Canales de salida:** correo (SMTP/proveedor), WhatsApp (proveedor de mensajería certificado), push app móvil, actualización de IVR y aviso en Portal (vía eventos)
- **Base de datos:** Azure SQL

## Funcionalidades

### F1. Enviar notificación de programación de instalación

Se activa con el evento `InstalacionProgramada` / `InstalacionReprogramada`. Envía correo y WhatsApp con fecha, franja y técnico, incluyendo el enlace firmado para confirmar o reprogramar (antes de las 24 h previas).

**Contrato de entrada** — mensaje Service Bus (envolvente INT-09):
```json
{
  "eventId": "uuid", "eventType": "InstalacionProgramada", "version": "1.0",
  "correlationId": "uuid", "sourceSystem": "ms-programacion-instalacion", "timestamp": "...",
  "payload": {
    "ordenInstalacionId": "ORD-55012", "clienteId": "CLI-99213",
    "email": "cliente@mail.com", "telefono": "+51999888777",
    "fecha": "2026-07-10", "franja": "09:00-12:00", "tecnico": "J. Pérez",
    "enlaceGestion": "https://portal.fiberlink.pe/instalacion/ORD-55012?token=..."
  }
}
```

**Contrato de salida:** registro en `notificacion` con estado por canal; publicación del evento `NotificacionEnviada` o `NotificacionPendiente`; respuesta funcional al flujo: "Notificación de instalación enviada correctamente al cliente".

**Errores funcionales (mensajes del requerimiento):**
- `EMAIL_NO_REGISTRADO` — estado "Pendiente": "No es posible notificar al cliente. Correo electrónico no registrado. Verificar datos del cliente"
- `TELEFONO_NO_REGISTRADO` — intento WhatsApp "Fallido": "No es posible enviar mensaje al cliente. Número de teléfono no registrado. Verificar datos del cliente"
- `DATOS_PROGRAMACION_INCOMPLETOS` — no se envía nada: "No es posible notificar al cliente. La orden no cuenta con datos de programación completos. Verificar"
- `ERROR_TECNICO` — reintento hasta 3 veces: "No fue posible enviar la notificación al cliente. Intente nuevamente" + incidente técnico

**Pseudocódigo**
```
funcion alRecibirEventoProgramacion(evento):
    si no validarEnvolvente(evento): moverADLQ(evento); retornar
    p = evento.payload
    si faltan (p.fecha o p.franja o p.tecnico):
        registrar notificacion(estado=NO_ENVIADA, motivo=DATOS_PROGRAMACION_INCOMPLETOS)     # E04
        publicar respuesta funcional; retornar
    notif = crear notificacion(ordenId, correlationId)
    si p.email nulo:
        notif.canalEmail = PENDIENTE (motivo EMAIL_NO_REGISTRADO)                             # E02
    sino: enviarCanal(notif, EMAIL, plantilla con fecha/franja/tecnico/enlace)
    si p.telefono nulo:
        notif.canalWhatsapp = FALLIDO (motivo TELEFONO_NO_REGISTRADO)                         # E03
    sino: enviarCanal(notif, WHATSAPP, plantilla)
    persistir notif; publicarEvento("NotificacionEnviada"|"NotificacionPendiente")
    publicarAuditoria("NOTIFICACION_PROGRAMACION", resultado)                                 # RNOF03-EV03

funcion enviarCanal(notif, canal, mensaje):
    para intento en 1..3:                                                                     # E05
        resultado = proveedor(canal).enviar(mensaje, timeout)
        registrar notificacion_intento(canal, intento, resultado)
        si resultado.ok: notif.canal = ENVIADA; retornar
        esperaExponencial()
    notif.canal = FALLIDA; registrarIncidenteTecnico(canal, notif)
```

### F2. Enviar notificaciones masivas de incidente (RF12)

Se activa con `IncidenteMaestroConfirmado` / `IncidenteResuelto` desde ms-correlacion-incidentes (vía Pub/Sub → Service Bus).

**Contrato de entrada** — payload:
```json
{
  "incidenteId": "INC-2211", "tipo": "CONFIRMADO|RESUELTO",
  "mensajeCliente": "Estamos atendiendo una avería en tu zona...",
  "clientesAfectados": [ { "clienteId": "CLI-1", "canales": ["APP", "WHATSAPP"] } ],
  "zonasIvr": ["LIMA-NORTE"], "mostrarEnPortal": true
}
```

**Contrato de salida:** envíos por lote con registro de hora por cliente y canal; actualización de IVR y aviso en Portal (evento `AvisoMasivoPublicado`); si un canal no está disponible: reintentos por política, alerta al NOC si se agotan y clientes NO marcados como notificados (RF12-E07).

**Pseudocódigo**
```
funcion alRecibirIncidente(evento):
    para cada lote de clientesAfectados (tamaño N, control de concurrencia ESC-07):
        para cada cliente: enviarCanal(...); registrar horaEnvio por canal
    actualizar IVR(zonasIvr, mensaje); publicar aviso Portal
    si canal caído: encolar reintentos; si agotados: alertarNOC(); mantener no-notificados
    si tasaErrores > 5% en 5 min: detener proceso y alertar          # RNOF02-RG06 circuit breaker
```

### F3. Reenviar notificaciones pendientes o fallidas

**Contrato de entrada** — `POST /v1/notificaciones/reintentos` `{ "notificacionIds": [...], "usuario": "operador" }` (o timer automático para PENDIENTE con datos corregidos).
**Contrato de salida** — `202 Accepted` con resumen por notificación.

**Pseudocódigo**
```
funcion reenviar(peticion):
    si no autorizado(rol OPERADOR): retornar 403
    para cada id: notif = repositorio.obtener(id)
        si datosContacto ahora completos: enviarCanal(...)
        sino: mantener PENDIENTE
    retornar 202 resumen
```

## Estructura de base de datos (Azure SQL)

```sql
CREATE TABLE plantilla (
    plantilla_id  VARCHAR(30) PRIMARY KEY,
    canal         VARCHAR(15) NOT NULL,   -- EMAIL | WHATSAPP | PUSH | IVR | PORTAL
    version       VARCHAR(10) NOT NULL,
    contenido     VARCHAR(MAX) NOT NULL,
    activa        BIT NOT NULL DEFAULT 1
);

CREATE TABLE notificacion (
    notificacion_id BIGINT IDENTITY PRIMARY KEY,
    correlation_id  UNIQUEIDENTIFIER NOT NULL,
    referencia_tipo VARCHAR(20) NOT NULL,  -- ORDEN_INSTALACION | INCIDENTE | CONTRATO
    referencia_id   VARCHAR(20) NOT NULL,
    cliente_id      VARCHAR(20) NOT NULL,
    plantilla_id    VARCHAR(30) NOT NULL REFERENCES plantilla(plantilla_id),
    estado          VARCHAR(15) NOT NULL,  -- ENVIADA | PENDIENTE | FALLIDA | NO_ENVIADA
    motivo          VARCHAR(60) NULL,
    fecha_creacion  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX ix_notif_referencia ON notificacion (referencia_tipo, referencia_id);
CREATE INDEX ix_notif_correlation ON notificacion (correlation_id);

CREATE TABLE notificacion_intento (
    intento_id      BIGINT IDENTITY PRIMARY KEY,
    notificacion_id BIGINT NOT NULL REFERENCES notificacion(notificacion_id),
    canal           VARCHAR(15) NOT NULL,
    numero_intento  INT NOT NULL,
    resultado       VARCHAR(10) NOT NULL,  -- OK | FALLIDO
    codigo_error    VARCHAR(30) NULL,
    fecha_envio     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## Features y escenarios cubiertos

| Código | Descripción |
|--------|-------------|
| RF09-E01 | Notificación exitosa por correo y WhatsApp con enlace de confirmación/reprogramación, registrada en la orden |
| RF09-E02 | Correo no registrado: notificación "Pendiente" con mensaje de verificación |
| RF09-E03 | Teléfono no registrado: intento WhatsApp "Fallido" registrado |
| RF09-E04 | Datos de programación incompletos: ninguna notificación enviada ni registrada como enviada |
| RF09-E05 | Error técnico: hasta 3 reintentos, incidente técnico registrado |
| RF12-E02 | Notificación proactiva a afectados por app/mensajería, IVR y portal con hora de envío |
| RF12-E07 | Falla de canal: registro por canal, reintentos, alerta al NOC, clientes no marcados como notificados |
| RF11-E01 (apoyo) | Envío del contrato al correo del cliente |
| RNOF03-EV03/EV12 | Auditoría de notificación de programación y envío de contrato |

## Lineamientos cubiertos

| Código | Descripción |
|--------|-------------|
| ARQ-01 / ARQ-03 / ARQ-08 | Responsabilidad única de mensajería; Functions por carga intermitente dirigida por eventos |
| INT-02 / INT-03 / INT-06 / INT-09 / INT-11 | Consumo asíncrono, reintentos con espera, idempotencia por eventId, envolvente estándar, DLQ/reproceso |
| ESC-05 / ESC-07 | Envíos asíncronos por lotes con límites de concurrencia hacia proveedores externos |
| OBS-01 / OBS-02 / OBS-04 | Logs estructurados, correlationId, alertas por agotamiento de reintentos |
| SEG-05 / SEG-09 / SEG-11 | Credenciales de proveedores en Key Vault con rotación; mensajes solo con datos necesarios |
| RNOF02-RG06 | Circuit breaker: detención automática si la tasa de error supera 5% en 5 minutos |
