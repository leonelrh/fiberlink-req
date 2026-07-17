# Diagrama de Secuencia - RF11: Activar Servicio de Internet Contratado

## Descripción
Flujo completo de activación de servicio tras instalación exitosa, incluyendo generación de contrato, configuración de facturación y cierre de orden.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant Tech as Técnico
    participant MobileApp as App Móvil Técnico
    participant APIGw as API Gateway
    participant Auth as Servicio Autenticación
    participant PIE as Plataforma Integración
    participant SAS as Service Activation Service
    participant OSS as OSS On-Premises
    participant ERP as ERP Facturación
    participant CRM as CRM SaaS
    participant ISS as Inventory Sync Service
    participant Notify as Servicio Notificación
    parameter Audit as Servicio Auditoría
    participant Obs as Plataforma Observabilidad

    Note over Tech, Obs: RF11-ESC01: Activación exitosa del servicio

    Tech->>MobileApp: Confirma instalación completada
    MobileApp->>MobileApp: Validar datos capturados
    Note right of MobileApp: Doc cliente, señal óptica, equipos configurados
    
    MobileApp->>APIGw: POST /api/v1/service/activate
    Note right of MobileApp: {orderId, customerDocument, serviceDetails, technicalValidation, equipmentInstalled}
    
    APIGw->>Auth: Validar token de técnico
    Auth-->>APIGw: Token válido + permisos activación
    
    APIGw->>PIE: Reenvía solicitud autenticada
    PIE->>SAS: Activar servicio de internet
    Note right of PIE: Propaga correlationId
    
    SAS->>SAS: Validar consistencia de datos
    Note right of SAS: Cliente coincide con orden, instalación validada
    
    SAS->>OSS: Solicitar confirmación de activación
    Note right of SAS: Timeout 30s configurado
    
    OSS->>OSS: Provisionar servicio en red
    Note right of OSS: Configurar OLT, asignar VLAN, activar puerto
    
    OSS-->>SAS: Activación confirmada en 15s
    Note right of OSS: {serviceId, activationTime, networkConfig}
    
    SAS->>SAS: Generar número de contrato único
    Note right of SAS: CTR-2024-{timestamp}-{seq}
    
    par Transacción Distribuida de Activación
        SAS->>ERP: Crear registro de contrato
        Note right of ERP: {contractNumber, customerId, plan, startDate}
        and
        SAS->>ERP: Configurar datos de facturación
        Note right of ERP: {billingCycle, firstBillDate, monthlyFee}
        and
        SAS->>ISS: Registrar equipos como instalados
        Note right of ISS: {serialNumbers, contractNumber, installationDate}
        and
        SAS->>CRM: Vincular servicio a contrato
        Note right of CRM: Actualizar estado cliente a ACTIVO
    end
    
    ERP-->>SAS: Contrato y facturación configurados
    ISS-->>SAS: Equipos vinculados al contrato
    CRM-->>SAS: Servicio vinculado exitosamente
    
    SAS->>SAS: Cerrar orden de instalación
    Note right of SAS: Estado EXITOSO, completionTime
    
    SAS->>Notify: Generar y enviar contrato por email
    Notify->>Notify: Generar PDF del contrato
    Notify->>Notify: Enviar email al cliente
    Notify-->>SAS: Contrato enviado exitosamente
    
    SAS->>Audit: Registrar activación completa
    SAS-->>PIE: Activación exitosa
    PIE-->>APIGw: Servicio activado correctamente
    APIGw-->>MobileApp: HTTP 200 + confirmación
    MobileApp->>Tech: "Servicio activado correctamente"

    Note over Tech, Obs: RF11-ESC02: Rechazo por datos incorrectos

    Tech->>MobileApp: Ingresa documento incorrecto
    MobileApp->>APIGw: POST con documento no coincidente
    
    APIGw->>PIE: Solicitud de activación
    PIE->>SAS: Activar servicio
    
    SAS->>SAS: Validar datos del cliente
    Note right of SAS: Documento no coincide con orden
    
    SAS->>CRM: Verificar datos del cliente en orden
    CRM-->>SAS: Cliente registrado con documento diferente
    
    SAS->>Audit: Registrar validación fallida
    SAS-->>PIE: Error 400 - Datos no coinciden
    PIE-->>APIGw: Error de validación
    APIGw-->>MobileApp: HTTP 400 Bad Request
    MobileApp->>Tech: "Datos no coinciden con orden - Verificar"

    Note over Tech, Obs: RF11-ESC03: Error técnico durante generación del contrato

    Tech->>MobileApp: Confirma activación válida
    MobileApp->>APIGw: POST con todos los datos correctos
    
    APIGw->>PIE: Activación autorizada
    PIE->>SAS: Procesar activación
    
    SAS->>SAS: Validación exitosa de datos
    SAS->>OSS: Solicitar activación
    OSS-->>SAS: Servicio activado exitosamente
    
    SAS->>SAS: Generar número de contrato
    
    par Transacción con Falla en ERP
        SAS->>ERP: Crear contrato
        Note right of ERP: Falla de conexión a BD
        ERP--xSAS: Database connection timeout
        and
        SAS->>ISS: Registrar equipos - PENDIENTE
        and
        SAS->>CRM: Vincular servicio - PENDIENTE
    end
    
    SAS->>SAS: Detectar falla en generación de contrato
    Note right of SAS: ERP no respondió, rollback requerido
    
    SAS->>OSS: Revertir activación de servicio
    OSS->>OSS: Desactivar servicio provisionado
    OSS-->>SAS: Servicio desactivado
    
    SAS->>Audit: Registrar rollback por falla ERP
    SAS->>Obs: Alertar falla crítica de facturación
    
    SAS-->>PIE: Error 500 - Falla generación contrato
    PIE-->>APIGw: Error de infraestructura
    APIGw-->>MobileApp: HTTP 500 Internal Error
    MobileApp->>Tech: "Error técnico - No se pudo activar"

    Note over Tech, Obs: RF11-ESC04: Error técnico durante activación OSS

    Tech->>MobileApp: Solicita activación
    MobileApp->>APIGw: POST activación
    
    APIGw->>PIE: Procesar activación
    PIE->>SAS: Activar servicio
    
    SAS->>SAS: Validación de datos exitosa
    SAS->>OSS: Solicitar activación (timeout 30s)
    
    Note right of OSS: Sistema OSS no responde
    
    loop Reintentos OSS (max 3)
        OSS--xSAS: Timeout - sin respuesta
        SAS->>SAS: Esperar 5s entre reintentos
    end
    
    SAS->>SAS: Agotar reintentos de activación
    Note right of SAS: 3 timeouts consecutivos = falla
    
    SAS->>Audit: Registrar falla de activación OSS
    SAS->>Obs: Alertar indisponibilidad crítica OSS
    
    SAS-->>PIE: Error 503 - OSS no disponible
    PIE-->>APIGw: Servicio de red no disponible
    APIGw-->>MobileApp: HTTP 503 Service Unavailable
    MobileApp->>Tech: "Sistema no disponible - Reintentar más tarde"

    Note over Tech, Obs: Escenario adicional: Activación con validaciones técnicas

    Tech->>MobileApp: Reporta instalación con señal baja
    MobileApp->>APIGw: POST con signalLevel: -28 dBm
    
    APIGw->>PIE: Solicitud de activación
    PIE->>SAS: Procesar con validación técnica
    
    SAS->>SAS: Validar parámetros técnicos
    Note right of SAS: Señal < -25 dBm = WARNING
    
    alt Señal dentro de rango aceptable (-30 a -8 dBm)
        SAS->>OSS: Proceder con activación
        OSS-->>SAS: Activación exitosa con warning
        
        SAS->>Audit: Registrar activación con señal límite
        Note right of Audit: Requiere seguimiento posterior
        
        SAS-->>PIE: Activado con advertencia técnica
        PIE-->>APIGw: HTTP 200 + warning header
        MobileApp->>Tech: "Activado - Revisar señal en 48h"
    else Señal fuera de rango (-35 dBm o peor)
        SAS->>Audit: Registrar rechazo por señal
        SAS-->>PIE: Error 422 - Señal insuficiente
        PIE-->>APIGw: Parámetros técnicos no válidos
        MobileApp->>Tech: "Señal insuficiente - Revisar instalación"
    end

    Note over Tech, Obs: Escenario: Activación con equipos defectuosos

    Tech->>MobileApp: Reporta equipo con problemas
    MobileApp->>APIGw: POST con equipment status issue
    
    APIGw->>PIE: Activación con reporte de equipo
    PIE->>SAS: Procesar activación
    
    SAS->>SAS: Evaluar impacto de equipo defectuoso
    
    alt Equipo secundario (no crítico)
        SAS->>OSS: Activar servicio parcial
        SAS->>ISS: Marcar equipo para reemplazo
        SAS-->>PIE: Activación exitosa + equipo pendiente
        MobileApp->>Tech: "Servicio activo - Programar reemplazo"
    else Equipo crítico (ONT defectuoso)
        SAS->>Audit: Registrar falla de equipo crítico
        SAS-->>PIE: Error - Equipo crítico defectuoso
        MobileApp->>Tech: "Reemplazar ONT antes de activar"
    end

    Note over Tech, Obs: Monitoreo y Métricas de Activación

    loop Cada activación
        SAS->>Obs: Tiempo total de activación
        SAS->>Obs: Tiempo de respuesta OSS
        SAS->>Obs: Tiempo de generación de contrato
        SAS->>Obs: Tasa de éxito por técnico
        SAS->>Obs: Distribución de códigos de error
        Audit->>Obs: Volumen de activaciones por hora
    end
    
    SAS->>Obs: Dashboard de activaciones
    Note right of Obs: Success rate, avg time, bottlenecks
    
    SAS->>Obs: Alertas por degradación
    Note right of Obs: Success rate <95% en 15min = alerta
    
    SAS->>Obs: Métricas de calidad técnica
    Note right of Obs: Distribución de niveles de señal
```

## Escenarios Cubiertos

### ESC01: Activación Exitosa del Servicio
- **Validación Integral**: Documento, instalación técnica, equipos configurados
- **Transacción Distribuida**: OSS, ERP, CRM e inventario sincronizados
- **Generación de Contrato**: Número único + PDF enviado por email
- **Auditoría Completa**: Trazabilidad desde técnico hasta cliente activo

### ESC02: Rechazo por Datos Incorrectos
- **Validación de Identidad**: Documento debe coincidir con orden
- **Verificación Cruzada**: Consulta a CRM para confirmar datos
- **Feedback Específico**: Mensaje claro sobre qué datos no coinciden

### ESC03: Error Técnico durante Generación de Contrato
- **Rollback Automático**: Reversión de activación OSS ante falla ERP
- **Transacciones Atómicas**: Todo exitoso o nada
- **Alertamiento**: Notificación inmediata por falla crítica

### ESC04: Error Técnico durante Activación OSS
- **Reintentos Controlados**: 3 intentos con backoff
- **Timeout Configurado**: 30s por intento
- **Escalamiento**: Alerta crítica tras agotar reintentos

### ESC05: Validaciones Técnicas Avanzadas
- **Parámetros de Calidad**: Nivel de señal óptica validado
- **Rangos Aceptables**: -30 a -8 dBm para activación
- **Advertencias**: Activación con seguimiento si está en límite

### ESC06: Gestión de Equipos Defectuosos
- **Clasificación de Criticidad**: ONT crítico vs. accesorios opcionales
- **Activación Parcial**: Servicio funcional con equipo secundario defectuoso
- **Flujo de Reemplazo**: Integración con gestión de equipos

## Lineamientos Aplicados

- **RNOF01**: Integridad de datos entre OSS, ERP, CRM e inventario
- **RNOF03**: Trazabilidad completa del proceso de activación
- **ARQ-03**: Responsabilidad especializada en orquestación de activación
- **INT-06**: Operaciones idempotentes con detección de duplicados
- **ESC-05**: Generación de contratos y notificaciones asíncronas
- **SEG-07**: Auditoría de todos los pasos del proceso
- **OBS-02**: Trazabilidad end-to-end con correlationId único