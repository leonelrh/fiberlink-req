# Diagrama de Secuencia — RF12 Correlación de incidentes de red con clientes afectados

Cubre: RF12-E01 (incidente único por falla masiva), RF12-E02 (notificación proactiva), RF12-E03 (IVR reconoce al cliente), RF12-E04 (cierre en cascada), RF12-E05 (inventario desactualizado), RF12-E06 (deduplicación), RF12-E07 (falla de canal de notificación), RF12-E08 (umbral no alcanzado), RF12-E09 (error técnico en ITSM).

```mermaid
sequenceDiagram
    autonumber
    participant PS as Pub/Sub (red-alarmas-normalizadas)
    participant COR as ms-correlacion-incidentes (Cloud Run)
    participant TOP as Topología (sincronizada por ms-ingesta-red)
    participant CON as ms-conectores-core
    participant ITSM as Mesa de ayuda ITSM (Azure)
    participant NOT as ms-notificaciones
    actor NOC as Operador del NOC
    actor Cliente as Cliente afectado
    participant IVR as IVR / Call center
    participant BQ as BigQuery → Power BI

    Note over PS,COR: Corte de fibra principal: miles de alertas simultáneas
    PS->>COR: Alarmas normalizadas (envolvente INT-09)
    alt RF12-E06 Evento duplicado de alarma ya registrada
        COR->>COR: Incrementa contador de ocurrencias
        Note over COR: No genera alarma duplicada ni nuevo incidente
    else Alarma nueva
        COR->>TOP: Consulta topología y clientes dependientes
        alt RF12-E05 Nodo inexistente o inventario desactualizado
            COR->>COR: Alarma en estado "Pendiente de correlación manual"
            COR-->>NOC: Alerta de inconsistencia de inventario
            COR--)BQ: Registra discrepancia para saneamiento de datos
            Note over COR: No crea incidente maestro automáticamente
        else Topología válida
            COR->>COR: Agrupa miles de alertas, estima causa raíz probable
            alt RF12-E08 Afectados bajo el umbral de incidente masivo
                COR->>COR: Alarma individual con clientes asociados
                Note over COR: Visible para soporte de primer nivel, sin incidente maestro
            else Falla masiva sobre el umbral (RF12-E01)
                COR->>COR: Un solo incidente + lista de afectados (empresariales con SLA marcados)
                COR->>CON: crearIncidente en ITSM (reintentos exponenciales)
                alt RF12-E09 Error técnico al registrar en ITSM
                    CON--xITSM: API no responde
                    COR->>COR: Alarmas conservadas en cola de reproceso, incidente no marcado como creado
                    COR-->>NOC: Alerta de fallo de integración + incidente técnico de plataforma
                else Incidente creado en menos de 5 minutos
                    CON->>ITSM: Alta de incidente maestro
                    ITSM-->>CON: ticketId
                    COR->>COR: Incidente estado ACTIVO con trazabilidad alarma-interno-ITSM
                end
            end
        end
    end

    Note over NOC,Cliente: RF12-E02 Notificación proactiva
    NOC->>COR: Confirma incidente maestro (mensaje + ETA)
    COR->>NOT: Evento IncidenteMaestroConfirmado (afectados, zonas IVR, portal)
    alt RF12-E07 Canal de notificaciones no disponible
        NOT--xCliente: Fallo de envío por canal
        NOT->>NOT: Registra fallo por canal y reintenta según política
        NOT-->>NOC: Alerta si los reintentos se agotan
        Note over NOT: Clientes NO marcados como notificados
    else Canales disponibles
        NOT-->>Cliente: Avisos por app y mensajería (hora de envío registrada)
        NOT->>IVR: Actualiza mensaje del incidente por zonas
        NOT->>NOT: Publica aviso de falla masiva en el portal
    end

    Note over Cliente,IVR: RF12-E03 Cliente llama al call center
    Cliente->>IVR: Llamada
    IVR->>COR: GET afectados?telefono=...
    COR-->>IVR: afectado=true, falla y tiempo estimado de reparación
    IVR-->>Cliente: Informa sin esperar a un agente y ofrece recibir actualizaciones

    Note over NOC,BQ: RF12-E04 Cierre con resolución en cascada
    NOC->>COR: Marca incidente maestro como Resuelto (reparación verificada)
    COR->>CON: Cerrar tickets hijos vinculados
    CON->>ITSM: Cierre automático en cascada
    COR->>NOT: Notificación de restablecimiento a afectados
    COR->>BQ: Duración total para SLA + indicadores al tablero Power BI
```
