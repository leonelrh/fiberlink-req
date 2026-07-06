# Diagrama de Secuencia — RF10 Reprogramar instalación del servicio de internet

Cubre: RF10-E01 (reprogramación exitosa), RF10-E02 (fuera de plazo de 24 h), RF10-E03 (estado no reprogramable), RF10-E04 (sin disponibilidad), RF10-E05 (error técnico con reversión).

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as Cliente
    participant Portal as Portal de Clientes (AWS) / enlace de notificación
    participant APIM as Azure API Management
    participant PRG as ms-programacion-instalacion
    participant CON as ms-conectores-core
    participant FS as Field Service (SaaS)
    participant INV as Inventario (equipos)
    participant SB as Service Bus
    participant NOT as ms-notificaciones
    participant TRZ as ms-trazabilidad (auditoría)

    Cliente->>Portal: Accede al enlace de reprogramación (token firmado)
    Portal->>APIM: POST /v1/instalaciones/{ordenId}/reprogramaciones (nuevaFecha, nuevaFranja)
    APIM->>PRG: Solicitud con token del enlace
    PRG->>PRG: Valida token y obtiene la orden
    alt RF10-E03 Orden no está en estado PROGRAMADA
        PRG-->>Cliente: 409 "No es posible reprogramar la instalación. La orden no se encuentra en un estado válido para reprogramación. Contactar a soporte"
        Note over PRG: No se modifica ningún dato de la orden
    else Orden PROGRAMADA
        alt RF10-E02 Menos de 24 horas de anticipación
            PRG-->>Cliente: 422 "No es posible reprogramar la instalación. El plazo máximo para solicitar una reprogramación es de 24 horas antes de la fecha programada"
            Note over PRG: Fecha y recursos intactos
        else Más de 24 horas de anticipación
            PRG->>CON: consultarDisponibilidad (nuevaFecha, nuevaFranja)
            CON->>FS: Consulta agenda de cuadrillas
            FS-->>CON: Disponibilidad
            alt RF10-E04 Sin cuadrilla para la nueva fecha
                PRG-->>Cliente: 409 "No hay disponibilidad para la fecha seleccionada. Por favor elija otra fecha"
                Note over PRG: Recursos originales sin modificar
            else Disponibilidad confirmada
                Note over PRG: Inicia saga de reprogramación
                PRG->>CON: liberarCuadrilla (asignación anterior)
                CON->>FS: Libera recursos de la fecha anterior
                PRG->>CON: asignarCuadrilla (nueva fecha)
                CON->>FS: Reasigna cuadrilla y técnico
                PRG->>CON: reasignarReservaEquipos
                CON->>INV: Actualiza reserva de equipos
                alt RF10-E05 Error técnico al actualizar la orden
                    PRG--xPRG: Fallo en la actualización
                    PRG->>CON: Compensación: restaurar cuadrilla, equipos, fecha y franja originales
                    CON->>FS: Restaura asignación original
                    CON->>INV: Restaura reserva original
                    PRG--)TRZ: Auditoría REPROGRAMACION FALLIDO + incidente técnico
                    PRG-->>Cliente: 500 "No fue posible reprogramar la instalación. Intente nuevamente"
                else RF10-E01 Reprogramación exitosa
                    PRG->>PRG: Actualiza orden (nueva fecha/franja, estado se mantiene PROGRAMADA)
                    PRG->>SB: Evento InstalacionReprogramada (INT-09)
                    SB->>NOT: Notifica nueva fecha confirmada al cliente (RF09)
                    PRG--)TRZ: Auditoría REPROGRAMACION EXITOSO
                    PRG-->>Cliente: 200 "Instalación reprogramada correctamente"
                end
            end
        end
    end
```
