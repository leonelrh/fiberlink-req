# Diagrama de Secuencia — RF08 Programar instalación del servicio de internet

Cubre: RF08-E01 (programación exitosa), RF08-E02 (cuadrilla no disponible), RF08-E03 (materiales insuficientes), RF08-E04 (permisos no obtenidos), RF08-E05 (error técnico con reversión).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operador
    participant APIM as Azure API Management
    participant PRG as ms-programacion-instalacion
    participant CON as ms-conectores-core
    participant FS as Field Service (SaaS agenda cuadrillas)
    participant ERP as ERP (materiales, on-premises)
    participant INV as Inventario (equipos ONT/router)
    participant SB as Service Bus
    participant NOT as ms-notificaciones
    participant TRZ as ms-trazabilidad (auditoría)

    Op->>APIM: POST /v1/instalaciones/programaciones (ordenId, fecha, franja)
    APIM->>PRG: Solicitud autenticada (OAuth2)
    PRG->>CON: consultarDisponibilidad cuadrilla (fecha, franja)
    CON->>FS: Consulta agenda
    FS-->>CON: Disponibilidad
    alt RF08-E02 Sin cuadrilla disponible
        PRG-->>Op: 409 "No hay cuadrilla disponible para la fecha seleccionada. Por favor elija otra fecha"
        Note over PRG: No se registra PROGRAMADA ni se asignan recursos
    else Cuadrilla disponible
        PRG->>CON: verificarStock materiales
        CON->>ERP: Consulta stock
        ERP-->>CON: Stock disponible
        alt RF08-E03 Materiales insuficientes
            PRG-->>Op: 409 "Materiales insuficientes en inventario. No es posible programar la instalación"
            Note over PRG: No se reservan recursos
        else Materiales suficientes
            alt RF08-E04 Permisos de instalación no obtenidos
                PRG-->>Op: 409 "Los permisos de instalación son requeridos antes de programar. Verificar"
                Note over PRG: Ningún recurso asignado
            else Ruta habilitada y permisos OK
                Note over PRG: Inicia saga de reservas (RNOF01 atomicidad)
                PRG->>CON: asignarCuadrilla
                CON->>FS: Reserva cuadrilla
                FS-->>CON: cuadrillaId, técnico
                PRG->>CON: reservarMateriales
                CON->>ERP: Reserva materiales
                ERP-->>CON: reservaId
                PRG->>CON: reservarEquipos (ONT, router)
                CON->>INV: Reserva equipos
                INV-->>CON: reservaId
                alt RF08-E05 Error técnico al registrar la programación
                    PRG--xPRG: Fallo al persistir
                    PRG->>CON: Compensar: liberar cuadrilla, materiales y equipos (orden inverso)
                    CON->>FS: Liberar cuadrilla
                    CON->>ERP: Liberar materiales
                    CON->>INV: Liberar equipos
                    PRG--)TRZ: Auditoría PROGRAMACION FALLIDO + incidente técnico
                    PRG-->>Op: 500 "No fue posible programar la instalación. Intente nuevamente"
                    Note over PRG,NOT: La orden no queda PROGRAMADA y no se notifica al cliente
                else RF08-E01 Programación exitosa
                    PRG->>PRG: Orden estado=PROGRAMADA, fecha y franja confirmadas
                    PRG->>SB: Evento InstalacionProgramada (INT-09)
                    SB->>NOT: Dispara notificación al cliente (RF09)
                    PRG--)TRZ: Auditoría PROGRAMACION y ASIGNACION_RECURSOS EXITOSO
                    PRG-->>Op: 201 "Instalación programada correctamente"
                end
            end
        end
    end
```
