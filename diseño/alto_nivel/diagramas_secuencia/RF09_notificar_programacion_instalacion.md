# Diagrama de Secuencia — RF09 Notificar programación de instalación

Cubre: RF09-E01 (notificación exitosa), RF09-E02 (correo no registrado), RF09-E03 (teléfono no registrado), RF09-E04 (datos de programación incompletos), RF09-E05 (error técnico con 3 reintentos).

```mermaid
sequenceDiagram
    autonumber
    participant SB as Service Bus (evento InstalacionProgramada)
    participant NOT as ms-notificaciones (Azure Functions)
    participant BD as Azure SQL (notificacion, intentos)
    participant MAIL as Proveedor de correo
    participant WA as Proveedor WhatsApp
    actor Cliente as Cliente
    participant TRZ as ms-trazabilidad (auditoría)

    SB->>NOT: Evento InstalacionProgramada (envolvente INT-09)
    NOT->>NOT: Valida envolvente y payload
    alt RF09-E04 Orden sin fecha, franja o técnico
        NOT->>BD: Registra NO_ENVIADA motivo DATOS_PROGRAMACION_INCOMPLETOS
        NOT--)TRZ: "No es posible notificar al cliente. La orden no cuenta con datos de programación completos. Verificar"
        Note over NOT: No se envía ninguna notificación ni se marca como enviada
    else Datos de programación completos
        alt RF09-E02 Correo no registrado
            NOT->>BD: Canal email = PENDIENTE motivo EMAIL_NO_REGISTRADO
            NOT--)TRZ: "No es posible notificar al cliente. Correo electrónico no registrado. Verificar datos del cliente"
        else Correo registrado
            loop Hasta 3 intentos si hay error técnico (RF09-E05)
                NOT->>MAIL: Enviar correo (fecha, franja, técnico, enlace confirmar/reprogramar)
                alt Envío exitoso
                    MAIL-->>Cliente: Correo con datos de instalación y enlace
                    NOT->>BD: Canal email = ENVIADA + intento OK
                else Error técnico del proveedor
                    MAIL--xNOT: Fallo de envío
                    NOT->>BD: Registra intento FALLIDO y espera exponencial
                end
            end
            Note over NOT: Si los 3 intentos fallan: "No fue posible enviar la notificación al cliente. Intente nuevamente" + incidente técnico
        end
        alt RF09-E03 Teléfono no registrado
            NOT->>BD: Intento WhatsApp = FALLIDO motivo TELEFONO_NO_REGISTRADO
            NOT--)TRZ: "No es posible enviar mensaje al cliente. Número de teléfono no registrado. Verificar datos del cliente"
        else Teléfono registrado
            NOT->>WA: Enviar WhatsApp (mismos datos y enlace)
            WA-->>Cliente: Mensaje WhatsApp
            NOT->>BD: Canal whatsapp = ENVIADA
        end
        alt RF09-E01 Ambos canales enviados
            NOT->>BD: Notificación registrada como enviada en la orden
            NOT--)TRZ: Auditoría NOTIFICACION_PROGRAMACION EXITOSO — "Notificación de instalación enviada correctamente al cliente"
        end
    end
```
