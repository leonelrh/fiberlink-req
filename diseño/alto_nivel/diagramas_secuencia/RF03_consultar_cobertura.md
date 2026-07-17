# Diagrama de Secuencia - RF03: Consultar Cobertura

## Descripción
Flujo completo de consulta de cobertura de fibra óptica por dirección o coordenadas a través de la Plataforma de Integración Empresarial.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant AC as Asesor Comercial
    participant CRM as CRM SaaS
    participant APIGw as API Gateway
    participant Auth as Servicio Autenticación
    participant PIE as Plataforma Integración
    participant CS as Coverage Service
    participant Oracle as Inventario Oracle
    participant Cache as Redis Cache
    participant Audit as Servicio Auditoría
    participant Obs as Plataforma Observabilidad

    Note over AC, Obs: RF03-ESC01: Ejecución exitosa

    AC->>CRM: Ingresa dirección del prospecto
    CRM->>APIGw: POST /api/v1/coverage/validate
    Note right of CRM: {address, coordinates, correlationId}
    
    APIGw->>Auth: Validar token JWT
    Auth-->>APIGw: Token válido
    
    APIGw->>PIE: Reenvía consulta autenticada
    PIE->>CS: Consultar cobertura
    Note right of PIE: Propaga correlationId
    
    CS->>Cache: Verificar cache por address_hash
    alt Cache Hit (Datos válidos)
        Cache-->>CS: Datos de cobertura cached
        CS->>Obs: Log cache hit + métricas
    else Cache Miss o Expirado
        CS->>Oracle: Consultar nodos y CTOs cercanos
        Note right of CS: Radio 500m, filtrar activos
        Oracle-->>CS: Lista de nodos disponibles
        
        CS->>Oracle: Verificar capacidad por CTO
        Oracle-->>CS: Detalles de capacidad
        
        CS->>CS: Calcular distancias y tecnología
        CS->>Cache: Guardar resultado (TTL 1h)
    end
    
    CS->>Audit: Registrar consulta
    Note right of Audit: correlationId, requesterId, resultado
    
    CS-->>PIE: Respuesta de cobertura
    PIE-->>APIGw: Resultado estructurado
    APIGw-->>CRM: Respuesta HTTP 200
    CRM->>AC: Muestra disponibilidad y velocidades

    Note over AC, Obs: RF03-ESC02: Solicitud inválida

    AC->>CRM: Ingresa dirección incompleta
    CRM->>APIGw: POST /api/v1/coverage/validate
    Note right of CRM: {address: {street: ""}}
    
    APIGw->>PIE: Reenvía consulta
    PIE->>CS: Consultar cobertura
    CS->>CS: Validar formato de entrada
    Note right of CS: Dirección incompleta detectada
    
    CS->>Audit: Registrar intento fallido
    CS-->>PIE: Error 400 - Datos incompletos
    PIE-->>APIGw: Error estructurado
    APIGw-->>CRM: HTTP 400 con detalles
    CRM->>AC: Solicitar campos faltantes

    Note over AC, Obs: RF03-ESC03: Sistema Oracle no disponible

    AC->>CRM: Consulta cobertura válida
    CRM->>APIGw: POST /api/v1/coverage/validate
    APIGw->>Auth: Validar token
    Auth-->>APIGw: Token válido
    
    APIGw->>PIE: Consulta autenticada
    PIE->>CS: Consultar cobertura
    CS->>Cache: Verificar cache
    Cache-->>CS: Cache miss
    
    CS->>Oracle: Consultar inventario
    Note right of Oracle: Timeout después de 5s
    Oracle--xCS: Connection timeout
    
    CS->>CS: Aplicar circuit breaker
    CS->>Obs: Registrar falla de conectividad
    CS->>Audit: Registrar error técnico
    
    CS-->>PIE: Error 503 - Sistema no disponible
    PIE-->>APIGw: Error de infraestructura
    APIGw-->>CRM: HTTP 503
    CRM->>AC: "Servicio temporalmente no disponible"

    Note over AC, Obs: RF03-ESC04: Consumidor no autorizado

    AC->>CRM: Intenta consultar cobertura
    CRM->>APIGw: POST sin token válido
    
    APIGw->>Auth: Validar token ausente/inválido
    Auth-->>APIGw: Error 401 - No autorizado
    
    APIGw->>Audit: Registrar intento no autorizado
    APIGw-->>CRM: HTTP 401 Unauthorized
    CRM->>AC: Solicitar nueva autenticación

    Note over AC, Obs: Métricas y Observabilidad

    loop Cada consulta
        CS->>Obs: Métricas de latencia
        CS->>Obs: Contadores por tipo de resultado
        Audit->>Obs: Eventos de auditoría
        Oracle->>Obs: Métricas de conectividad
    end

    PIE->>Obs: Dashboard de consultas de cobertura
    Note right of Obs: Rate, latencia, errores, cache hit ratio
```

## Escenarios Cubiertos

### ESC01: Ejecución Exitosa
- **Flujo Principal**: Consulta válida con respuesta exitosa desde cache o Oracle
- **Validaciones**: Autenticación, formato de dirección, coordenadas válidas
- **Optimización**: Cache Redis para reducir carga en Oracle

### ESC02: Solicitud Inválida
- **Validaciones**: Campos obligatorios, formato de coordenadas
- **Respuesta**: Error estructurado con campos faltantes
- **Auditoría**: Registro de intentos fallidos para análisis

### ESC03: Sistema Oracle No Disponible
- **Resilencia**: Circuit breaker para evitar cascada de fallos
- **Fallback**: Respuesta controlada sin comprometer otros sistemas
- **Monitoreo**: Alertas automáticas por indisponibilidad

### ESC04: Consumidor No Autorizado
- **Seguridad**: Validación de tokens JWT en API Gateway
- **Auditoría**: Registro de intentos no autorizados
- **Respuesta**: Error estándar sin revelar información interna

## Lineamientos Aplicados

- **ARQ-03**: Responsabilidad clara del Coverage Service
- **INT-01**: API versionada con contratos documentados
- **SEG-04**: Autenticación centralizada
- **ESC-04**: Cache para optimizar performance
- **OBS-02**: Trazabilidad end-to-end con correlationId
- **INT-18**: Degradación elegante ante fallos de Oracle