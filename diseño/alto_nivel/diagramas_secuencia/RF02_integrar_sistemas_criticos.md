# Diagrama de Secuencia — RF02 Integrar sistemas críticos

Cubre: RF02-E01 (exitoso), RF02-E02 (solicitud inválida), RF02-E03 (sistema destino no disponible), RF02-E04 (no autorizado). Muestra la mediación síncrona y la entrega asíncrona de eventos a sistemas suscritos (sin integraciones punto a punto — INT-07).

```mermaid
sequenceDiagram
    autonumber
    participant MS as Microservicio consumidor (ej. ms-activacion)
    participant CON as ms-conectores-core
    participant KV as Azure Key Vault
    participant CORE as Sistema core (CRM/Inventario/OSS/Facturacion/ERP)
    participant SB as Azure Service Bus
    participant TRZ as ms-trazabilidad
    participant DLQ as Cola DLQ / reproceso

    Note over MS,CON: Mediación síncrona
    MS->>CON: POST /v1/core/{sistema}/{operacion} (correlationId, credencial individual)
    alt RF02-E04 Consumidor no autorizado
        CON-->>MS: 401/403 rechazo
        CON--)TRZ: Auditoría del intento
    else Autorizado
        alt RF02-E02 Payload no cumple esquema canónico
            CON-->>MS: 400 campos/reglas incumplidas (INT-10)
            CON--)TRZ: Traza tipo VALIDACION
        else Payload válido
            CON->>KV: Obtener credencial del sistema core (rotada)
            alt RF02-E03 Sistema core no disponible
                CON--xCORE: Timeout / circuit breaker abierto
                CON->>CON: Reintentos con espera exponencial (INT-03)
                CON-->>MS: 503/504 error controlado
                CON--)TRZ: Traza FALLIDO (sistema, código, tiempo respuesta)
            else RF02-E01 Ejecución exitosa
                CON->>CORE: Operación traducida al protocolo del sistema
                CORE-->>CON: Respuesta
                CON-->>MS: 200 respuesta canónica conforme al contrato
                CON--)TRZ: Traza OK (origen, destino, canal, tiempo)
            end
        end
    end

    Note over SB,CORE: Entrega asíncrona a sistemas suscritos
    SB->>CON: Evento de negocio (envolvente INT-09)
    CON->>CON: Valida envolvente y busca suscriptores
    loop Por cada sistema core suscrito
        CON->>CORE: Entregar evento (idempotente por eventId)
        alt Entrega exitosa
            CORE-->>CON: ACK
            CON--)TRZ: Entrega registrada (latencia de propagación)
        else Fallo de entrega
            CON->>DLQ: Encolar reintento exponencial
            Note over DLQ: Agotados los reintentos: alerta a operaciones y reproceso manual (INT-11)
        end
    end
```
