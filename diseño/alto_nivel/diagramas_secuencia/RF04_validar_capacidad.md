# Diagrama de Secuencia - RF04: Validar Capacidad Técnica

## Descripción
Flujo completo de validación de capacidad técnica en nodo, CTO y puertos disponibles para evitar ventas de servicios que no pueden ser instalados.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant AC as Asesor Comercial
    participant CRM as CRM SaaS
    participant APIGw as API Gateway
    participant Auth as Servicio Autenticación
    participant PIE as Plataforma Integración
    participant CapS as Capacity Service
    participant Oracle as Inventario Oracle
    participant Cache as Node Capacity Cache
    participant Audit as Servicio Auditoría
    participant Obs as Plataforma Observabilidad

    Note over AC, Obs: RF04-ESC01: Ejecución exitosa

    AC->>CRM: Selecciona plan y velocidad para cliente
    CRM->>APIGw: POST /api/v1/capacity/validate
    Note right of CRM: {nodeId, ctoId, bandwidthRequired, serviceType}
    
    APIGw->>Auth: Validar token JWT
    Auth-->>APIGw: Token válido + scope validado
    
    APIGw->>PIE: Reenvía validación autenticada
    PIE->>CapS: Validar capacidad técnica
    Note right of PIE: Propaga correlationId
    
    CapS->>Cache: Verificar cache de capacidad de nodo
    alt Cache Hit (TTL válido)
        Cache-->>CapS: Capacidad actual del nodo
        CapS->>Obs: Log cache hit
    else Cache Miss o TTL expirado
        CapS->>Oracle: Consultar capacidad del nodo
        Oracle-->>CapS: Capacidad total y utilizada
        CapS->>Cache: Actualizar cache (TTL 15min)
    end
    
    CapS->>CapS: Calcular capacidad disponible
    Note right of CapS: maxCapacity - currentLoad
    
    alt Capacidad suficiente en nodo
        CapS->>Oracle: Consultar puertos disponibles en CTO
        Oracle-->>CapS: Lista de puertos libres
        
        CapS->>Oracle: Verificar calidad de señal por puerto
        Oracle-->>CapS: Niveles de potencia óptica
        
        CapS->>CapS: Generar recomendación de puertos
        Note right of CapS: Priorizar por calidad de señal
        
        CapS->>Audit: Registrar validación exitosa
        CapS-->>PIE: Respuesta con puertos recomendados
        PIE-->>APIGw: Capacidad disponible confirmada
        APIGw-->>CRM: HTTP 200 + puertos sugeridos
        CRM->>AC: Muestra disponibilidad y opciones
    else Capacidad insuficiente
        CapS->>Audit: Registrar capacidad insuficiente
        CapS-->>PIE: Capacidad no disponible
        PIE-->>APIGw: Sin capacidad para plan solicitado
        APIGw-->>CRM: HTTP 200 + alternativas
        CRM->>AC: Sugiere planes con menor velocidad
    end

    Note over AC, Obs: RF04-ESC02: Solicitud inválida

    AC->>CRM: Solicita validación sin especificar nodo
    CRM->>APIGw: POST /api/v1/capacity/validate
    Note right of CRM: {nodeId: "", bandwidthRequired: 100}
    
    APIGw->>PIE: Reenvía consulta
    PIE->>CapS: Validar capacidad
    CapS->>CapS: Validar parámetros de entrada
    Note right of CapS: nodeId vacío detectado
    
    CapS->>Audit: Registrar validación inválida
    CapS-->>PIE: Error 400 - nodeId requerido
    PIE-->>APIGw: Error de validación
    APIGw-->>CRM: HTTP 400 con campos requeridos
    CRM->>AC: Solicitar información faltante

    Note over AC, Obs: RF04-ESC03: Sistema Oracle no disponible

    AC->>CRM: Validación de capacidad válida
    CRM->>APIGw: POST con datos completos
    APIGw->>Auth: Validar autenticación
    Auth-->>APIGw: Token válido
    
    APIGw->>PIE: Consulta autenticada
    PIE->>CapS: Validar capacidad
    CapS->>Cache: Verificar cache de nodo
    Cache-->>CapS: Cache miss
    
    CapS->>Oracle: Consultar capacidad de nodo
    Note right of Oracle: Timeout 5s, conexión fallida
    Oracle--xCapS: Connection timeout
    
    CapS->>CapS: Activar circuit breaker
    CapS->>Obs: Alertar falla de conectividad Oracle
    CapS->>Audit: Registrar error de infraestructura
    
    CapS-->>PIE: Error 503 - Sistema no disponible
    PIE-->>APIGw: Error de servicio externo
    APIGw-->>CRM: HTTP 503 Service Unavailable
    CRM->>AC: "Validación no disponible temporalmente"

    Note over AC, Obs: RF04-ESC04: Consumidor no autorizado

    AC->>CRM: Intenta validar capacidad
    CRM->>APIGw: POST con token inválido
    
    APIGw->>Auth: Verificar token expirado
    Auth-->>APIGw: Token expirado / inválido
    
    APIGw->>Audit: Registrar acceso no autorizado
    Note right of Audit: IP, timestamp, token intentado
    
    APIGw-->>CRM: HTTP 401 Unauthorized
    CRM->>AC: Redirigir a login

    Note over AC, Obs: Escenario adicional: Reserva temporal de puerto

    AC->>CRM: Confirma venta con puerto específico
    CRM->>APIGw: POST /api/v1/capacity/reserve
    Note right of CRM: {portId, orderId, customerId}
    
    APIGw->>PIE: Solicitud de reserva
    PIE->>CapS: Reservar puerto temporal
    
    CapS->>Oracle: Verificar puerto aún disponible
    Oracle-->>CapS: Puerto libre confirmado
    
    CapS->>CapS: Crear reserva con TTL 48h
    CapS->>Oracle: Marcar puerto como RESERVADO
    Oracle-->>CapS: Estado actualizado
    
    CapS->>Audit: Registrar reserva exitosa
    CapS-->>PIE: Reserva confirmada + expiración
    PIE-->>APIGw: Puerto reservado exitosamente
    APIGw-->>CRM: Confirmación de reserva
    CRM->>AC: Puerto asegurado para instalación

    Note over AC, Obs: Métricas y Monitoreo Continuo

    loop Validaciones periódicas
        CapS->>Obs: Métricas de capacidad por nodo
        CapS->>Obs: Tasa de éxito de validaciones
        CapS->>Obs: Latencia de consultas Oracle
        Audit->>Obs: Eventos de reservas y liberaciones
    end

    CapS->>Obs: Alertas por capacidad crítica
    Note right of Obs: Nodos >90% utilizados
```

## Escenarios Cubiertos

### ESC01: Ejecución Exitosa
- **Flujo Principal**: Validación completa con cache y consulta a Oracle
- **Optimización**: Cache de capacidad de nodo para reducir latencia
- **Recomendación**: Algoritmo de selección de mejores puertos

### ESC02: Solicitud Inválida
- **Validaciones**: nodeId, ctoId, bandwidth obligatorios
- **Respuesta**: Error estructurado con campos específicos faltantes
- **Auditoría**: Registro para análisis de calidad de datos

### ESC03: Sistema Oracle No Disponible
- **Resilencia**: Circuit breaker evita saturar Oracle
- **Monitoreo**: Alertas automáticas por indisponibilidad
- **Fallback**: Respuesta controlada sin afectar otros flujos

### ESC04: Consumidor No Autorizado
- **Seguridad**: Validación estricta de tokens y scopes
- **Auditoría**: Trazabilidad de intentos no autorizados
- **Protección**: Sin revelar información de infraestructura

### ESC05: Reserva Temporal de Puerto
- **Funcionalidad**: Reserva con TTL automático
- **Consistencia**: Verificación antes de reservar
- **Liberación**: Job automático tras 48 horas

## Lineamientos Aplicados

- **ARQ-03**: Responsabilidad especializada en validación de capacidad
- **ESC-03**: Escalamiento horizontal con cache distribuido
- **ESC-06**: Prevención de cuellos de botella en Oracle
- **INT-06**: Operaciones idempotentes en reservas
- **SEG-07**: Auditoría completa de validaciones y reservas
- **OBS-03**: Métricas técnicas y de negocio integradas