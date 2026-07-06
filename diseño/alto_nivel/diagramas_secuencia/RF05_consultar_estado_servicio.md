# Diagrama de Secuencia — RF05 Consultar estado de servicio

Cubre: RF05-E01 (exitoso), RF05-E02 (solicitud inválida), RF05-E03 (sistema no disponible con degradación parcial), RF05-E04 (no autorizado).

```mermaid
sequenceDiagram
    autonumber
    actor Canal as Asesor atención (Call Center/Portal AWS/App)
    participant APIM as Azure API Management
    participant EST as ms-estado-servicio
    participant BD as Azure SQL (vista estado 360)
    participant CON as ms-conectores-core
    participant CRM as CRM (SaaS)
    participant OSS as OSS (on-premises)
    participant FAC as Facturación (on-premises)
    participant TRZ as ms-trazabilidad
    participant SB as Service Bus

    Canal->>APIM: GET /v1/servicios/{id}/estado?modo=cache|directo
    APIM->>APIM: OAuth2 + rate limiting
    alt RF05-E04 Consumidor no autorizado
        APIM-->>Canal: 401/403 rechazo
        APIM--)TRZ: Auditoría del intento
    else Autorizado
        APIM->>EST: Consulta estado
        alt RF05-E02 servicioId inválido
            EST-->>Canal: 400 detalle de validación
            EST--)TRZ: Traza del intento
        else Solicitud válida
            alt Modo caché (vista materializada)
                EST->>BD: Obtener vista estado 360
                BD-->>EST: Estado comercial + técnico + facturación
                EST-->>Canal: 200 respuesta consistente (RF05-E01)
                EST--)TRZ: Traza OK (correlationId)
            else Modo directo (dato en línea)
                par Consulta comercial
                    EST->>CON: invocar CRM estadoComercial
                    CON->>CRM: Consulta
                    CRM-->>CON: Estado contrato/plan
                and Consulta técnica
                    EST->>CON: invocar OSS estadoTecnico
                    CON--xOSS: RF05-E03 OSS no responde (timeout)
                and Consulta facturación
                    EST->>CON: invocar FACTURACION estadoCuenta
                    CON->>FAC: Consulta
                    FAC-->>CON: Estado de cuenta
                end
                EST->>EST: Sección OSS = NO_DISPONIBLE (degradación parcial ESC-09)
                EST-->>Canal: 200 agregado con fuentesDegradadas=[OSS]
                EST--)TRZ: Traza FALLIDO parcial (sistema OSS, código, tiempo)
            end
        end
    end

    Note over SB,BD: Actualización asíncrona de la vista (propagación ≤ 5 min — RNOF01)
    SB->>EST: Evento ServicioActivado / EstadoServicioCambiado (INT-09)
    EST->>BD: Upsert vista estado 360
    EST->>EST: Mide latencia de propagación y alerta si excede SLA (OBS-04)
```
