# Diagrama de Secuencia — RF07 Registrar trazabilidad de integración

Cubre: RF07-E01 (exitoso), RF07-E02 (solicitud inválida), RF07-E03 (almacén no disponible), RF07-E04 (no autorizado). Incluye ingesta y consulta.

```mermaid
sequenceDiagram
    autonumber
    participant MS as Microservicios de la plataforma
    participant PS as GCP Pub/Sub (tópico trazabilidad-integracion)
    participant TRZ as ms-trazabilidad (Cloud Run)
    participant BQ as BigQuery (traza_integracion)
    participant DLQ as Tópico DLQ
    actor Soporte as Responsable operación y soporte
    participant APIM as Azure API Management

    Note over MS,BQ: Ingesta continua de evidencias (INT-08)
    MS--)PS: Evidencia de intercambio (envolvente INT-09)
    PS->>TRZ: Entrega del mensaje
    alt Envolvente válida
        TRZ->>TRZ: Enmascara datos sensibles (OBS-05)
        TRZ->>BQ: Inserción streaming (particionada por fecha)
    else Mensaje malformado
        TRZ->>DLQ: Publica a DLQ para reproceso (INT-11)
    end

    Note over Soporte,BQ: Consulta de trazabilidad (OBS-10)
    Soporte->>APIM: GET /v1/trazas?correlationId=...&sistema=...&fechas=...
    APIM->>APIM: OAuth2 + rol de soporte
    alt RF07-E04 Consumidor no autorizado
        APIM-->>Soporte: 401/403 rechazo
        APIM--)TRZ: Auditoría del intento
    else Autorizado
        APIM->>TRZ: Consulta con filtros
        alt RF07-E02 Sin filtros mínimos o rango mayor a 90 días
            TRZ-->>Soporte: 400 campos/reglas incumplidas
        else Filtros válidos
            alt RF07-E03 BigQuery no disponible
                TRZ--xBQ: Error de consulta
                TRZ-->>Soporte: 503 error controlado (sistema, código, tiempo)
            else RF07-E01 Consulta exitosa
                TRZ->>BQ: SELECT por correlationId/sistema/cliente/fechas
                BQ-->>TRZ: Trazas ordenadas por timestamp
                TRZ->>TRZ: Registra la consulta (usuario, filtros) (SEG-12)
                TRZ-->>Soporte: 200 flujo end-to-end de la transacción
            end
        end
    end
```
