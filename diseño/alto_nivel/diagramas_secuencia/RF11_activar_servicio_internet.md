# Diagrama de Secuencia — RF11 Activar el servicio de internet contratado

Cubre: RF11-E01 (activación exitosa), RF11-E02 (datos incorrectos), RF11-E03 (error al generar contrato con reversión), RF11-E04 (sin confirmación del OSS en 30 s con reversión).

```mermaid
sequenceDiagram
    autonumber
    actor Tec as Técnico (app móvil)
    participant APIM as Azure API Management
    participant ACT as ms-activacion
    participant CNC as ms-conciliacion-datos
    participant CON as ms-conectores-core
    participant OSS as OSS (OLT/BRAS, on-premises)
    participant CRM as CRM (contratos)
    participant FAC as Facturación (on-premises)
    participant INV as Inventario (equipos)
    participant EVT as ms-eventos-negocio
    participant NOT as ms-notificaciones
    participant TRZ as ms-trazabilidad (auditoría)

    Tec->>APIM: POST /v1/activaciones (documento, ordenId, checklist técnico)
    APIM->>ACT: Solicitud autenticada (OAuth2)
    ACT--)TRZ: Auditoría SOLICITUD_ACTIVACION (RNOF03-EV05)
    ACT->>ACT: Compara documento del cliente con la orden
    alt RF11-E02 Datos del cliente no coinciden con la orden
        ACT--)TRZ: Auditoría VALIDACION_CONSISTENCIA FALLIDO
        ACT-->>Tec: 422 "Los datos del cliente no coincide con la orden de instalación. Verificar"
        Note over ACT: No se emite orden de activación ni número de contrato
    else Datos consistentes
        ACT->>CNC: Validación cruzada (cliente, plan, orden, equipos) — RNOF01
        CNC-->>ACT: Consistente entre plataformas
        ACT--)TRZ: Auditoría VALIDACION_CONSISTENCIA EXITOSO (EV06)
        Note over ACT: Inicia saga de activación (atomicidad RNOF01)
        ACT->>CON: activarServicio en OSS (timeout 30 s)
        CON->>OSS: Provisión ONT/OLT/BRAS
        alt RF11-E04 Confirmación no llega en 30 segundos
            OSS--xCON: Sin confirmación (timeout)
            ACT->>CON: Revertir orden de activación en OSS
            CON->>OSS: Rollback de provisión
            ACT--)TRZ: Auditoría CONFIRMACION_ACTIVACION FALLIDO + incidente técnico
            ACT-->>Tec: 504 "No fue posible realizar la activación del servicio"
            Note over ACT: Servicio no marcado Activo, sin número de contrato
        else Activación confirmada
            OSS-->>CON: Confirmación de activación
            ACT--)TRZ: Auditoría CONFIRMACION_ACTIVACION EXITOSO (EV07)
            ACT->>CON: generarContrato en CRM
            alt RF11-E03 Error técnico al generar el contrato
                CON--xCRM: Fallo
                ACT->>CON: Compensación: revertir activación en OSS
                CON->>OSS: Desactivar servicio
                ACT--)TRZ: Auditoría GENERACION_CONTRATO FALLIDO + REVERSION (EV13) + incidente (EV14)
                ACT-->>Tec: 500 "No fue posible realizar la activación del servicio"
                Note over ACT: Servicio no queda Activo
            else RF11-E01 Activación exitosa
                CRM-->>CON: Número de contrato generado
                ACT--)TRZ: Auditoría GENERACION_CONTRATO EXITOSO (EV08)
                ACT->>CON: vincularServicioContrato (CRM)
                ACT--)TRZ: Auditoría VINCULACION_SERVICIO (EV09)
                ACT->>CON: generarDatosFacturacion (fecha inicio ≥ fecha activación)
                CON->>FAC: Alta de facturación
                FAC-->>CON: OK
                ACT--)TRZ: Auditoría GENERACION_FACTURACION (EV10)
                ACT->>CON: marcarEquiposInstalados (vinculados al contrato)
                CON->>INV: Equipos RESERVADO → INSTALADO
                ACT->>ACT: Servicio estado=ACTIVO, orden cerrada EXITOSO
                ACT--)TRZ: Auditoría CIERRE_ORDEN (EV11)
                ACT->>EVT: Evento ServicioActivado (INT-09, propagación ≤ 5 min a Portal/CRM/ERP)
                ACT->>NOT: Enviar contrato al correo del cliente
                NOT-->>Tec: Confirmación de envío
                ACT--)TRZ: Auditoría ENVIO_CONTRATO (EV12)
                ACT-->>Tec: 201 "Servicio activado correctamente" + número de contrato
            end
        end
    end
```
