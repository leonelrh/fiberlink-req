# Diagrama de Secuencia — RF04 Validar capacidad técnica

Cubre: RF04-E01 (exitoso), RF04-E02 (solicitud inválida), RF04-E03 (sistema destino no disponible con degradación), RF04-E04 (no autorizado).

```mermaid
sequenceDiagram
    autonumber
    actor Asesor as Asesor comercial
    participant APIM as Azure API Management
    participant CAP as ms-capacidad
    participant BD as Azure SQL (réplica nodos/CTO/puertos)
    participant CON as ms-conectores-core
    participant INV as Inventario Oracle (on-premises)
    participant TRZ as ms-trazabilidad

    Asesor->>APIM: POST /v1/capacidad/validaciones (nodo, CTO, plan, correlationId)
    APIM->>APIM: OAuth2 + scope capacidad:validar
    alt RF04-E04 Consumidor no autorizado
        APIM-->>Asesor: 401/403 rechazo
        APIM--)TRZ: Auditoría del intento
    else Autorizado
        APIM->>CAP: Validar capacidad
        alt RF04-E02 Campos obligatorios ausentes
            CAP-->>Asesor: 400 detalle de campos incumplidos
            CAP--)TRZ: Traza del intento
        else Datos válidos
            CAP->>BD: Consulta CTO, puertos libres y reservas vigentes
            alt Réplica disponible (camino normal)
                BD-->>CAP: Puertos y ocupación de splitter
                CAP-->>APIM: 200 capacidadDisponible, puertoSugerido
                APIM-->>Asesor: 200 respuesta conforme al contrato (RF04-E01)
                CAP--)TRZ: Traza OK (correlationId, tiempo de respuesta)
            else Réplica no disponible: degradación controlada (ESC-09)
                CAP->>CON: invocar INVENTARIO consultarCapacidad (timeout, retry)
                alt RF04-E03 Inventario tampoco responde
                    CON--xINV: Timeout / indisponibilidad
                    CON-->>CAP: 503 error clasificado
                    CAP-->>Asesor: 503 error controlado
                    CAP--)TRZ: Traza FALLIDO (sistema INVENTARIO, código, tiempo)
                else Consulta directa exitosa
                    CON->>INV: Consulta de capacidad (canal seguro)
                    INV-->>CON: Datos de nodo/CTO/puertos
                    CON-->>CAP: 200 respuesta canónica
                    CAP-->>Asesor: 200 capacidad validada (RF04-E01)
                    CAP--)TRZ: Traza OK
                end
            end
        end
    end

    Note over CAP,TRZ: La reserva de puerto (F2) sigue el mismo control: idempotente por solicitudId (INT-06)
```
