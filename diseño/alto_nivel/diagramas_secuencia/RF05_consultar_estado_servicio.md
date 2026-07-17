# Diagrama de Secuencia - RF05: Consultar Estado de Servicio

## Descripción
Flujo completo de consulta del estado comercial, técnico y de facturación del servicio para brindar respuesta consistente al cliente.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant AA as Asesor Atención
    participant CallCenter as Call Center Azure
    participant APIGw as API Gateway
    participant Auth as Servicio Autenticación
    participant PIE as Plataforma Integración
    participant SSS as Service Status Service
    participant CRM as CRM SaaS
    participant OSS as OSS On-Premises
    participant Billing as Facturación ERP
    participant ITSM as ITSM Azure
    participant Cache as Status Cache
    participant Audit as Servicio Auditoría
    participant Obs as Plataforma Observabilidad

    Note over AA, Obs: RF05-ESC01: Consulta exitosa de estado integral

    AA->>CallCenter: Ingresa ID de servicio del cliente
    CallCenter->>APIGw: GET /api/v1/service/{serviceId}/status
    Note right of CallCenter: {serviceId, customerId, includeHistory}
    
    APIGw->>Auth: Validar token y permisos
    Auth-->>APIGw: Token válido + scope "service.read"
    
    APIGw->>PIE: Reenvía consulta autenticada
    PIE->>SSS: Consultar estado integral
    Note right of PIE: Propaga correlationId
    
    SSS->>Cache: Verificar cache consolidado
    Note right of Cache: Key: serviceId + timestamp
    
    alt Cache Hit (TTL 5min válido)
        Cache-->>SSS: Estado consolidado cached
        SSS->>Obs: Log cache hit + métricas
    else Cache Miss o TTL expirado
        par Consulta Paralela de Estados
            SSS->>CRM: Consultar datos comerciales
            and
            SSS->>OSS: Consultar estado técnico
            and
            SSS->>Billing: Consultar estado facturación
            and
            SSS->>ITSM: Consultar incidentes activos
        end
        
        CRM-->>SSS: Estado comercial + plan contratado
        OSS-->>SSS: Estado técnico + equipos + señal
        Billing-->>SSS: Balance + próximo vencimiento
        ITSM-->>SSS: Tickets abiertos relacionados
        
        SSS->>SSS: Consolidar respuesta unificada
        SSS->>Cache: Guardar estado consolidado (TTL 5min)
    end
    
    SSS->>Audit: Registrar consulta exitosa
    SSS-->>PIE: Estado integral consolidado
    PIE-->>APIGw: Respuesta estructurada
    APIGw-->>CallCenter: HTTP 200 + datos completos
    CallCenter->>AA: Muestra estado unificado

    Note over AA, Obs: RF05-ESC02: Solicitud inválida por datos incompletos

    AA->>CallCenter: Ingresa ID de servicio vacío
    CallCenter->>APIGw: GET /api/v1/service//status
    Note right of CallCenter: serviceId vacío en URL
    
    APIGw->>PIE: Reenvía consulta
    PIE->>SSS: Consultar estado (serviceId vacío)
    SSS->>SSS: Validar parámetros de entrada
    Note right of SSS: serviceId requerido faltante
    
    SSS->>Audit: Registrar solicitud inválida
    SSS-->>PIE: Error 400 - serviceId requerido
    PIE-->>APIGw: Error de validación
    APIGw-->>CallCenter: HTTP 400 Bad Request
    CallCenter->>AA: "ID de servicio requerido"

    Note over AA, Obs: RF05-ESC03: Sistema CRM/OSS/Facturación no disponible

    AA->>CallCenter: Consulta estado de servicio válida
    CallCenter->>APIGw: GET con datos completos
    APIGw->>Auth: Validar autenticación
    Auth-->>APIGw: Token válido
    
    APIGw->>PIE: Consulta autenticada
    PIE->>SSS: Consultar estado integral
    SSS->>Cache: Verificar cache
    Cache-->>SSS: Cache miss
    
    par Consultas Paralelas con Fallas
        SSS->>CRM: Consultar datos comerciales
        CRM-->>SSS: Datos comerciales OK
        and
        SSS->>OSS: Consultar estado técnico
        Note right of OSS: Timeout después de 10s
        OSS--xSSS: Connection timeout
        and
        SSS->>Billing: Consultar facturación
        Billing-->>SSS: Datos de facturación OK
        and
        SSS->>ITSM: Consultar incidentes
        ITSM-->>SSS: Sin incidentes activos
    end
    
    SSS->>SSS: Aplicar degradación elegante
    Note right of SSS: Continúa con datos parciales
    
    SSS->>Obs: Registrar falla de conectividad OSS
    SSS->>Audit: Registrar respuesta parcial
    
    SSS-->>PIE: Estado parcial + advertencia
    Note right of SSS: {commercial: OK, technical: "unavailable", billing: OK}
    
    PIE-->>APIGw: Respuesta con datos disponibles
    APIGw-->>CallCenter: HTTP 200 + warning header
    CallCenter->>AA: Muestra datos parciales + aviso técnico

    Note over AA, Obs: RF05-ESC04: Consumidor no autorizado

    AA->>CallCenter: Intenta consultar estado de servicio
    CallCenter->>APIGw: GET sin token válido
    
    APIGw->>Auth: Validar token ausente
    Auth-->>APIGw: Error 401 - Token requerido
    
    APIGw->>Audit: Registrar acceso no autorizado
    APIGw-->>CallCenter: HTTP 401 Unauthorized
    CallCenter->>AA: Redirigir a autenticación

    Note over AA, Obs: Escenario adicional: Actualización de estado por evento

    OSS->>PIE: Evento cambio de estado técnico
    Note right of OSS: {serviceId, newStatus: "DEGRADED", reason: "low_signal"}
    
    PIE->>SSS: Actualizar estado del servicio
    SSS->>SSS: Validar transición de estado
    SSS->>Cache: Invalidar cache del servicio
    SSS->>CRM: Propagar cambio si necesario
    SSS->>Audit: Registrar cambio de estado
    
    SSS->>Obs: Publicar evento de estado actualizado
    SSS-->>PIE: Confirmación de actualización
    PIE-->>OSS: ACK del evento procesado

    Note over AA, Obs: Escenario: Consulta de historial extendido

    AA->>CallCenter: Solicita historial de estados
    CallCenter->>APIGw: GET /api/v1/service/{serviceId}/history
    Note right of CallCenter: {dateFrom, dateTo, domains: ["TECHNICAL"]}
    
    APIGw->>PIE: Consulta de historial
    PIE->>SSS: Obtener historial de estados
    
    SSS->>SSS: Consultar tabla status_history
    Note right of SSS: Filtrar por fechas y dominio
    
    SSS->>Audit: Registrar consulta de historial
    SSS-->>PIE: Historial de cambios técnicos
    PIE-->>APIGw: Línea de tiempo de estados
    APIGw-->>CallCenter: HTTP 200 + historial
    CallCenter->>AA: Muestra evolución del servicio

    Note over AA, Obs: Monitoreo y Métricas Continuas

    loop Consultas en tiempo real
        SSS->>Obs: Métricas de latencia por sistema
        SSS->>Obs: Rate de cache hits por tipo
        SSS->>Obs: Contadores de respuestas parciales
        Audit->>Obs: Volumen de consultas por canal
    end

    SSS->>Obs: Dashboard de estado de sistemas
    Note right of Obs: Disponibilidad CRM, OSS, Billing, ITSM
    
    SSS->>Obs: Alertas por degradación
    Note right of Obs: >5% respuestas parciales en 5min
```

## Escenarios Cubiertos

### ESC01: Consulta Exitosa de Estado Integral
- **Consolidación**: Datos de CRM, OSS, Facturación e ITSM unificados
- **Optimización**: Cache con TTL corto (5min) para datos críticos
- **Paralelización**: Consultas simultáneas para reducir latencia

### ESC02: Solicitud Inválida por Datos Incompletos
- **Validación**: serviceId obligatorio y formato válido
- **Respuesta**: Error estructurado con campo específico faltante
- **Auditoría**: Registro para mejora de interfaz de usuario

### ESC03: Sistema Core No Disponible
- **Resilencia**: Degradación elegante con datos parciales
- **Continuidad**: Servicio funcional con información disponible
- **Transparencia**: Indicadores claros de datos faltantes

### ESC04: Consumidor No Autorizado
- **Seguridad**: Validación de token y scope específico
- **Protección**: Sin revelar información del servicio
- **Auditoría**: Trazabilidad de accesos no autorizados

### ESC05: Actualización por Evento
- **Reactividad**: Invalidación de cache ante cambios
- **Propagación**: Sincronización entre sistemas
- **Trazabilidad**: Auditoría de cambios de estado

### ESC06: Consulta de Historial
- **Funcionalidad**: Acceso a evolución temporal del servicio
- **Filtrado**: Por fechas y dominios específicos
- **Performance**: Índices optimizados para consultas históricas

## Lineamientos Aplicados

- **ARQ-02**: Desacoplamiento entre CRM, OSS y Facturación
- **ARQ-03**: Responsabilidad clara como facade de consulta
- **ESC-04**: Cache estratégico para datos frecuentes
- **INT-18**: Degradación elegante ante fallos parciales
- **OBS-02**: Trazabilidad completa con correlationId
- **SEG-05**: Autorización granular por dominio de datos