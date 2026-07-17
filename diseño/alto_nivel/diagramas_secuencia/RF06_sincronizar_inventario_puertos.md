# Diagrama de Secuencia - RF06: Sincronizar Inventario de Puertos en Tiempo Real

## Descripción
Flujo completo de sincronización de estado de puertos entre sistemas para evitar visitas fallidas por puertos inexistentes u ocupados.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant Tech as Técnico Instalación
    participant MobileApp as App Móvil
    participant APIGw as API Gateway
    participant Auth as Servicio Autenticación
    participant PIE as Plataforma Integración
    participant ISS as Inventory Sync Service
    participant Oracle as Inventario Oracle
    participant OSS as OSS On-Premises
    parameter EventBus as Event Bus
    participant Audit as Servicio Auditoría
    participant Obs as Plataforma Observabilidad

    Note over Tech, Obs: RF06-ESC01: Reserva exitosa de puerto

    Tech->>MobileApp: Confirma puerto disponible para orden
    MobileApp->>APIGw: POST /api/v1/inventory/ports/reserve
    Note right of MobileApp: {portId, orderId, customerId}
    
    APIGw->>Auth: Validar token técnico
    Auth-->>APIGw: Token válido + permisos de campo
    
    APIGw->>PIE: Reenvía reserva autenticada
    PIE->>ISS: Sincronizar reserva de puerto
    Note right of PIE: Propaga correlationId
    
    ISS->>Oracle: Verificar estado actual del puerto
    Oracle-->>ISS: Puerto DISPONIBLE confirmado
    
    ISS->>OSS: Verificar consistencia en sistema OSS
    OSS-->>ISS: Puerto libre en sistema de provisión
    
    ISS->>ISS: Validar transición DISPONIBLE → RESERVADO
    Note right of ISS: Aplicar reglas de negocio
    
    par Transacción Distribuida de Reserva
        ISS->>Oracle: UPDATE puerto SET status=RESERVED
        and
        ISS->>OSS: Marcar puerto como reservado
    end
    
    Oracle-->>ISS: Estado actualizado en Oracle
    OSS-->>ISS: Estado actualizado en OSS
    
    ISS->>ISS: Verificar sincronización exitosa
    ISS->>EventBus: Publicar evento PORT_RESERVED
    Note right of EventBus: {portId, orderId, timestamp, expiresAt}
    
    ISS->>Audit: Registrar reserva exitosa
    Note right of Audit: Tiempo <2min según SLA
    
    ISS-->>PIE: Confirmación de reserva
    PIE-->>APIGw: Puerto reservado exitosamente
    APIGw-->>MobileApp: HTTP 200 + detalles reserva
    MobileApp->>Tech: Puerto asegurado para instalación

    Note over Tech, Obs: RF06-ESC02: Liberación de puerto por cancelación

    MobileApp->>APIGw: DELETE /api/v1/orders/{orderId}/cancel
    Note right of MobileApp: Técnico cancela instalación
    
    APIGw->>PIE: Cancelación de orden
    PIE->>ISS: Liberar puerto por cancelación
    
    ISS->>Oracle: Consultar puertos reservados para orden
    Oracle-->>ISS: {portId: "PTO-001", status: "RESERVED"}
    
    par Transacción Distribuida de Liberación
        ISS->>Oracle: UPDATE puerto SET status=AVAILABLE
        and
        ISS->>OSS: Marcar puerto como disponible
    end
    
    ISS->>EventBus: Publicar evento PORT_RELEASED
    Note right of EventBus: {portId, reason: "ORDER_CANCELLED"}
    
    ISS->>Audit: Registrar liberación
    ISS-->>PIE: Puerto liberado exitosamente
    PIE-->>APIGw: Cancelación procesada
    APIGw-->>MobileApp: Orden cancelada + recursos liberados

    Note over Tech, Obs: RF06-ESC03: Confirmación de instalación exitosa

    Tech->>MobileApp: Confirma instalación completada
    MobileApp->>APIGw: POST /api/v1/installations/complete
    Note right of MobileApp: {portId, equipmentIds, signalLevel, customerId}
    
    APIGw->>PIE: Confirmación de instalación
    PIE->>ISS: Confirmar instalación de puerto
    
    ISS->>Oracle: Verificar puerto en estado RESERVADO
    Oracle-->>ISS: Puerto reservado confirmado
    
    par Transacción de Instalación Completada
        ISS->>Oracle: UPDATE puerto SET status=INSTALLED, customer_id
        and
        ISS->>OSS: Vincular puerto a servicio de cliente
        and
        ISS->>OSS: Registrar equipos instalados
    end
    
    ISS->>EventBus: Publicar evento PORT_INSTALLED
    Note right of EventBus: {portId, customerId, installationDate}
    
    ISS->>Audit: Registrar instalación exitosa
    ISS-->>PIE: Instalación confirmada
    PIE-->>APIGw: Puerto instalado y vinculado
    APIGw-->>MobileApp: Instalación registrada exitosamente

    Note over Tech, Obs: RF06-ESC04: Detección de discrepancia de estado

    loop Reconciliación Programada (cada 4 horas)
        ISS->>Oracle: Obtener snapshot de estados
        ISS->>OSS: Obtener snapshot de estados
        
        ISS->>ISS: Comparar estados puerto por puerto
        Note right of ISS: Identificar discrepancias
        
        alt Discrepancia Detectada
            ISS->>ISS: Clasificar severidad de discrepancia
            Note right of ISS: Oracle: DISPONIBLE, OSS: INSTALADO
            
            ISS->>Audit: Registrar discrepancia CRÍTICA
            ISS->>Obs: Generar alerta de inconsistencia
            
            ISS->>ISS: Determinar acción correctiva
            Note right of ISS: Requiere revisión manual
            
            ISS->>EventBus: Publicar evento DISCREPANCY_DETECTED
        end
    end

    Note over Tech, Obs: RF06-ESC05: Puerto no disponible durante reserva

    Tech->>MobileApp: Intenta reservar puerto específico
    MobileApp->>APIGw: POST /api/v1/inventory/ports/reserve
    Note right of MobileApp: {portId: "PTO-001", orderId: "ORD-123"}
    
    APIGw->>PIE: Solicitud de reserva
    PIE->>ISS: Reservar puerto específico
    
    ISS->>Oracle: Verificar estado del puerto
    Oracle-->>ISS: Puerto INSTALADO (no disponible)
    
    ISS->>ISS: Rechazar reserva por puerto ocupado
    ISS->>Oracle: Consultar puertos alternativos en CTO
    Oracle-->>ISS: Lista de puertos disponibles
    
    ISS->>Audit: Registrar intento fallido
    ISS-->>PIE: Error + puertos alternativos
    PIE-->>APIGw: HTTP 409 Conflict + alternativas
    APIGw-->>MobileApp: Puerto no disponible
    MobileApp->>Tech: Muestra opciones alternativas

    Note over Tech, Obs: RF06-ESC06: Transferencia de equipos entre almacenes

    Note over ISS: Este flujo se integra con Equipment Inventory Service
    
    EventBus->>ISS: Evento EQUIPMENT_TRANSFER_COMPLETED
    Note right of EventBus: {equipmentIds, fromWarehouse, toWarehouse}
    
    ISS->>ISS: Verificar puertos afectados por transferencia
    ISS->>Oracle: Actualizar disponibilidad de instalación
    Oracle-->>ISS: Disponibilidad actualizada
    
    ISS->>EventBus: Publicar EQUIPMENT_AVAILABILITY_UPDATED
    ISS->>Audit: Registrar actualización por transferencia

    Note over Tech, Obs: Métricas y Monitoreo en Tiempo Real

    loop Cada operación de sincronización
        ISS->>Obs: Métricas de tiempo de sincronización
        ISS->>Obs: Contadores por tipo de operación
        ISS->>Obs: Tasa de discrepancias detectadas
        Audit->>Obs: Volumen de transacciones por hora
    end
    
    ISS->>Obs: Dashboard de salud de sincronización
    Note right of Obs: Puertos sincronizados vs. con discrepancias
    
    ISS->>Obs: Alertas por SLA de sincronización
    Note right of Obs: >2min para reservas = alerta crítica

    Note over Tech, Obs: Rollback por falla en sincronización

    Tech->>MobileApp: Confirma instalación
    MobileApp->>APIGw: POST instalación completa
    APIGw->>PIE: Confirmación
    PIE->>ISS: Confirmar instalación
    
    par Transacción con Falla Parcial
        ISS->>Oracle: UPDATE puerto - OK
        and
        ISS->>OSS: Vincular servicio - TIMEOUT
    end
    
    ISS->>ISS: Detectar falla parcial
    Note right of ISS: Rollback requerido
    
    ISS->>Oracle: ROLLBACK - restaurar estado RESERVADO
    Oracle-->>ISS: Estado revertido
    
    ISS->>Audit: Registrar rollback de sincronización
    ISS->>Obs: Alertar falla de sincronización
    ISS-->>PIE: Error 500 - Sincronización fallida
    PIE-->>APIGw: Error de infraestructura
    APIGw-->>MobileApp: Instalación falló - reintentar
```

## Escenarios Cubiertos

### ESC01: Reserva Exitosa de Puerto
- **Transacción Distribuida**: Actualización consistente en Oracle y OSS
- **SLA**: Sincronización completada en <2 minutos
- **Eventos**: Publicación para otros sistemas interesados

### ESC02: Liberación por Cancelación
- **Automatización**: Liberación inmediata de recursos
- **Trazabilidad**: Razón de liberación registrada
- **Disponibilidad**: Puerto nuevamente disponible para otros técnicos

### ESC03: Confirmación de Instalación
- **Completitud**: Vinculación de puerto, cliente y equipos
- **Consistencia**: Estados finales sincronizados
- **Auditoría**: Registro completo de la instalación

### ESC04: Detección de Discrepancia
- **Reconciliación**: Proceso automático programado
- **Clasificación**: Severidad según impacto operacional
- **Escalamiento**: Alertas para discrepancias críticas

### ESC05: Puerto No Disponible
- **Validación**: Verificación antes de reservar
- **Alternativas**: Sugerencia de puertos disponibles
- **Experiencia**: Evita frustración del técnico

### ESC06: Transferencia de Equipos
- **Integración**: Con Equipment Inventory Service
- **Actualización**: Disponibilidad según equipos transferidos
- **Cadena**: Eventos en cascada para mantener consistencia

### ESC07: Rollback por Falla
- **Atomicidad**: Transacciones todo-o-nada
- **Recuperación**: Restauración automática ante fallos
- **Alertamiento**: Notificación inmediata de problemas

## Lineamientos Aplicados

- **ARQ-02**: Mediador entre Oracle y OSS sin acoplamiento directo
- **INT-06**: Operaciones idempotentes con detección de duplicados
- **ESC-09**: Degradación controlada ante fallos parciales
- **OBS-08**: Correlación completa de eventos de sincronización
- **INT-11**: Reproceso automático con políticas de retry
- **SEG-07**: Auditoría completa de cambios de inventario