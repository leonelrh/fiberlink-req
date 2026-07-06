# Diagrama de Secuencia — RF03 Consultar cobertura

Cubre: RF03-E01 (exitoso), RF03-E02 (solicitud inválida), RF03-E03 (sistema destino no disponible), RF03-E04 (no autorizado). Incluye la sincronización asíncrona de la réplica desde Inventario/GIS.

```mermaid
sequenceDiagram
    autonumber
    actor Canal as Asesor (CRM/Portal AWS/App móvil/Tablet campo)
    participant APIM as Azure API Management
    participant COB as ms-cobertura
    participant BD as Azure SQL (réplica cobertura)
    participant TRZ as ms-trazabilidad
    participant SB as Service Bus / Pub-Sub
    participant INV as Inventario Oracle + GIS (on-premises)
    participant CON as ms-conectores-core

    Canal->>APIM: GET /v1/cobertura?direccion|coordenadas (correlationId)
    APIM->>APIM: OAuth2 + rate limiting (SEG-07)
    alt RF03-E04 Consumidor no autorizado
        APIM-->>Canal: 401/403 rechazo
        APIM--)TRZ: Auditoría del intento
    else Autorizado
        APIM->>COB: Consulta cobertura
        alt RF03-E02 Sin dirección ni coordenadas válidas
            COB-->>Canal: 400 campos/reglas incumplidas
            COB--)TRZ: Traza del intento (correlationId)
        else Parámetros válidos
            COB->>COB: Busca en caché (ESC-04)
            COB->>BD: Consulta zona de cobertura
            alt RF03-E03 Réplica no disponible
                BD--xCOB: Error de acceso
                COB-->>Canal: 503 error controlado
                COB--)TRZ: Traza FALLIDO (sistema afectado, código, tiempo)
            else RF03-E01 Ejecución exitosa
                BD-->>COB: Zona, nodo, CTO, planes
                COB-->>APIM: 200 respuesta conforme al contrato
                APIM-->>Canal: 200 cobertura + planes disponibles
                COB--)TRZ: Traza OK con correlationId
            end
        end
    end

    Note over INV,COB: Sincronización asíncrona de la réplica (INT-02)
    INV->>CON: Cambios de cobertura (canal seguro on-premises)
    CON->>SB: Evento InventarioCoberturaActualizada (INT-09)
    SB->>COB: Entrega del evento
    alt Envolvente/esquema válido
        COB->>BD: Upsert zonas de cobertura
        COB--)TRZ: Traza de sincronización OK
    else Evento inválido
        COB->>SB: Mover a DLQ para reproceso (INT-11)
    end
```
