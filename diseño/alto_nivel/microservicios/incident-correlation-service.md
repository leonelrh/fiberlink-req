# Incident Correlation Service (Servicio de Correlación de Incidentes)

## Funcionalidades

### 1. Correlacionar Incidentes de Red con Clientes Afectados
- **Descripción**: Agrupa alarmas relacionadas y identifica clientes impactados por fallas de infraestructura
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "networkEvent": {
      "eventId": "string",
      "eventType": "string", // "FIBER_CUT" | "NODE_DOWN" | "POWER_OUTAGE" | "OLT_FAILURE"
      "severity": "string", // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
      "affectedInfrastructure": {
        "nodeIds": ["string"],
        "ctoIds": ["string"],
        "fiberSegmentIds": ["string"],
        "oltIds": ["string"]
      },
      "eventTimestamp": "string",
      "reportedBy": "string", // "NMS" | "TECHNICIAN" | "CUSTOMER" | "MONITORING"
      "estimatedScope": {
        "geographicArea": "string",
        "estimatedCustomersAffected": "number"
      }
    },
    "sourceSystem": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "correlationResult": {
      "masterIncidentCreated": "boolean",
      "masterIncidentId": "string",
      "incidentClassification": {
        "type": "string", // "MASSIVE" | "LOCALIZED" | "INDIVIDUAL"
        "severity": "string",
        "estimatedResolutionTime": "string",
        "rootCauseHypothesis": "string"
      },
      "affectedCustomers": {
        "totalCount": "number",
        "residentialCount": "number",
        "enterpriseCount": "number",
        "criticalEnterpriseCount": "number", // Con SLA especial
        "customerList": [
          {
            "customerId": "string",
            "serviceId": "string",
            "customerType": "string", // "RESIDENTIAL" | "ENTERPRISE"
            "slaLevel": "string",
            "impactLevel": "string", // "TOTAL" | "PARTIAL" | "DEGRADED"
            "affectedServices": ["string"]
          }
        ]
      },
      "proactiveNotifications": {
        "sent": "boolean",
        "channels": ["string"], // ["APP", "SMS", "EMAIL", "IVR"]
        "notificationsSent": "number",
        "notificationsFailed": "number"
      },
      "relatedAlarms": [
        {
          "alarmId": "string",
          "sourceSystem": "string",
          "alarmType": "string",
          "correlatedAt": "string"
        }
      ]
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN CorrelacionarIncidentes
    1. RECIBIR y validar evento de red
    2. APLICAR filtros de deduplicación:
       a. VERIFICAR si alarma ya está correlacionada
       b. IDENTIFICAR alarmas duplicadas del mismo equipo
       c. DESCARTAR eventos irrelevantes o de prueba
    3. ANALIZAR topología de red:
       a. CONSULTAR inventario para mapear dependencias
       b. IDENTIFICAR equipos downstream afectados
       c. DETERMINAR alcance geográfico del impacto
    4. IDENTIFICAR clientes afectados:
       a. CONSULTAR servicios activos en infraestructura afectada
       b. CLASIFICAR por tipo de cliente y nivel de SLA
       c. ESTIMAR nivel de impacto por cliente
    5. EVALUAR criterios de incidente maestro:
       a. SI >100 clientes O >10 empresariales: CREAR incidente maestro
       b. SI infraestructura crítica: CREAR incidente maestro
       c. SINO: GENERAR alarma individual
    6. SI incidente maestro califica:
       a. CREAR ticket en ITSM con prioridad alta
       b. ENVIAR notificaciones proactivas a clientes
       c. ACTUALIZAR IVR con mensaje de falla masiva
       d. NOTIFICAR a equipos NOC y operación
    7. REGISTRAR correlación y métricas
  END
  ```

### 2. Enviar Notificaciones Proactivas
- **Descripción**: Notifica automáticamente a clientes afectados por incidentes masivos
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "notificationRequest": {
      "masterIncidentId": "string",
      "affectedCustomers": ["string"],
      "incidentDetails": {
        "type": "string",
        "estimatedResolution": "string",
        "affectedArea": "string"
      },
      "messageTemplate": "string",
      "channels": ["string"], // ["APP", "SMS", "EMAIL"]
      "priority": "string" // "HIGH" | "CRITICAL"
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN EnviarNotificacionesProactivas
    1. GENERAR mensaje personalizado por canal:
       a. APP: Notificación push con detalles técnicos
       b. SMS: Mensaje conciso con tiempo estimado
       c. EMAIL: Comunicación detallada con seguimiento
    2. SEGMENTAR por prioridad:
       a. CLIENTES EMPRESARIALES: Notificación inmediata
       b. CLIENTES RESIDENCIALES: Notificación en batch
    3. ENVIAR notificaciones con reintentos:
       a. USAR colas con prioridad por tipo de cliente
       b. APLICAR rate limiting para evitar saturación
       c. REGISTRAR entrega exitosa y fallos
    4. ACTUALIZAR IVR con mensaje contextual:
       a. GENERAR script específico para zona afectada
       b. INCLUIR tiempo estimado de resolución
       c. OFRECER opciones de seguimiento automático
  END
  ```

### 3. Cerrar Incidente Maestro con Resolución en Cascada
- **Descripción**: Cierra incidente principal y todos los tickets relacionados
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "resolutionRequest": {
      "masterIncidentId": "string",
      "resolutionConfirmed": "boolean",
      "resolutionDetails": {
        "rootCause": "string",
        "actionsTaken": "string",
        "repairTime": "string",
        "verificationComplete": "boolean"
      },
      "resolvedBy": "string"
    }
  }
  ```

## Estructura de Base de Datos

```sql
-- Tabla para incidentes maestros
CREATE TABLE master_incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) UNIQUE NOT NULL,
    correlation_id VARCHAR(100) NOT NULL,
    incident_type ENUM('FIBER_CUT', 'NODE_DOWN', 'POWER_OUTAGE', 'OLT_FAILURE', 'MASSIVE_DEGRADATION') NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    status ENUM('DETECTED', 'CONFIRMED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED') NOT NULL,
    affected_infrastructure JSON NOT NULL, -- nodos, CTOs, fibras afectadas
    geographic_scope JSON NOT NULL, -- área geográfica del impacto
    estimated_customers_affected INTEGER NOT NULL,
    actual_customers_affected INTEGER NULL,
    residential_customers_affected INTEGER NOT NULL DEFAULT 0,
    enterprise_customers_affected INTEGER NOT NULL DEFAULT 0,
    critical_enterprise_affected INTEGER NOT NULL DEFAULT 0,
    root_cause_hypothesis TEXT,
    confirmed_root_cause TEXT NULL,
    estimated_resolution_time TIMESTAMP NULL,
    actual_resolution_time TIMESTAMP NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    reported_by VARCHAR(100) NOT NULL,
    assigned_team VARCHAR(100) NULL,
    INDEX idx_incident_id (incident_id),
    INDEX idx_correlation (correlation_id),
    INDEX idx_type_severity (incident_type, severity),
    INDEX idx_status (status),
    INDEX idx_detected (detected_at)
);

-- Tabla para clientes afectados por incidente
CREATE TABLE incident_affected_customers (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    service_id VARCHAR(100) NOT NULL,
    customer_type ENUM('RESIDENTIAL', 'ENTERPRISE') NOT NULL,
    sla_level ENUM('STANDARD', 'PREMIUM', 'ENTERPRISE', 'CRITICAL') NOT NULL,
    impact_level ENUM('TOTAL_OUTAGE', 'PARTIAL_DEGRADATION', 'INTERMITTENT') NOT NULL,
    affected_services JSON NOT NULL, -- servicios específicos impactados
    impact_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    impact_end_time TIMESTAMP NULL,
    proactive_notification_sent BOOLEAN NOT NULL DEFAULT FALSE,
    notification_channels JSON, -- canales donde se envió notificación
    customer_called_support BOOLEAN NOT NULL DEFAULT FALSE,
    compensation_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    INDEX idx_incident_id (incident_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_customer_type (customer_type),
    INDEX idx_sla_level (sla_level),
    FOREIGN KEY (incident_id) REFERENCES master_incidents(incident_id)
);

-- Tabla para alarmas correlacionadas
CREATE TABLE correlated_alarms (
    id SERIAL PRIMARY KEY,
    alarm_id VARCHAR(100) UNIQUE NOT NULL,
    incident_id VARCHAR(100) NOT NULL,
    source_system VARCHAR(50) NOT NULL, -- NMS origen de la alarma
    alarm_type VARCHAR(100) NOT NULL,
    equipment_id VARCHAR(100) NOT NULL,
    alarm_severity ENUM('INFO', 'WARNING', 'MINOR', 'MAJOR', 'CRITICAL') NOT NULL,
    alarm_timestamp TIMESTAMP NOT NULL,
    correlation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    correlation_confidence DECIMAL(3,2) NOT NULL, -- 0.00-1.00
    alarm_description TEXT NOT NULL,
    correlation_reason TEXT, -- Por qué se correlacionó con este incidente
    alarm_cleared BOOLEAN NOT NULL DEFAULT FALSE,
    cleared_timestamp TIMESTAMP NULL,
    INDEX idx_alarm_id (alarm_id),
    INDEX idx_incident_id (incident_id),
    INDEX idx_source_system (source_system),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_alarm_timestamp (alarm_timestamp),
    FOREIGN KEY (incident_id) REFERENCES master_incidents(incident_id)
);

-- Tabla para notificaciones proactivas enviadas
CREATE TABLE proactive_notifications (
    id SERIAL PRIMARY KEY,
    notification_id VARCHAR(100) UNIQUE NOT NULL,
    incident_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    notification_channel ENUM('APP', 'SMS', 'EMAIL', 'IVR', 'WHATSAPP') NOT NULL,
    notification_type ENUM('INITIAL_ALERT', 'UPDATE', 'RESOLUTION', 'FOLLOW_UP') NOT NULL,
    message_content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status ENUM('SENT', 'DELIVERED', 'READ', 'FAILED', 'BOUNCED') NOT NULL,
    delivery_timestamp TIMESTAMP NULL,
    failure_reason TEXT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    customer_response TEXT NULL, -- Si cliente responde
    response_timestamp TIMESTAMP NULL,
    INDEX idx_notification_id (notification_id),
    INDEX idx_incident_id (incident_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_channel (notification_channel),
    INDEX idx_sent_at (sent_at),
    FOREIGN KEY (incident_id) REFERENCES master_incidents(incident_id)
);

-- Tabla para tickets hijos vinculados
CREATE TABLE linked_support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(100) UNIQUE NOT NULL,
    incident_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    ticket_source ENUM('CALL_CENTER', 'CUSTOMER_PORTAL', 'MOBILE_APP', 'AUTO_GENERATED') NOT NULL,
    ticket_type ENUM('SERVICE_OUTAGE', 'SLOW_INTERNET', 'INTERMITTENT_CONNECTION', 'BILLING_INQUIRY') NOT NULL,
    ticket_status ENUM('OPEN', 'IN_PROGRESS', 'PENDING_CUSTOMER', 'RESOLVED', 'CLOSED') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    auto_closed BOOLEAN NOT NULL DEFAULT FALSE, -- Cerrado automáticamente por resolución de incidente maestro
    customer_satisfaction_score INTEGER NULL, -- 1-5
    resolution_method ENUM('INCIDENT_RESOLUTION', 'INDIVIDUAL_FIX', 'COMPENSATION') NULL,
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_incident_id (incident_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (ticket_status),
    FOREIGN KEY (incident_id) REFERENCES master_incidents(incident_id)
);

-- Tabla para métricas de correlación
CREATE TABLE correlation_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    hour INTEGER NOT NULL, -- 0-23
    total_alarms_received INTEGER NOT NULL,
    alarms_correlated INTEGER NOT NULL,
    alarms_deduplicated INTEGER NOT NULL,
    alarms_discarded INTEGER NOT NULL,
    master_incidents_created INTEGER NOT NULL,
    avg_correlation_time_seconds DECIMAL(8,3) NOT NULL,
    avg_customers_per_incident DECIMAL(8,2) NOT NULL,
    proactive_notifications_sent INTEGER NOT NULL,
    notification_success_rate DECIMAL(5,2) NOT NULL,
    customer_calls_prevented INTEGER NOT NULL, -- Estimado
    incidents_auto_resolved INTEGER NOT NULL,
    PRIMARY KEY (metric_date, hour),
    INDEX idx_metric_date (metric_date)
);

-- Tabla para configuración de reglas de correlación
CREATE TABLE correlation_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(100) UNIQUE NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT NOT NULL,
    equipment_type_pattern VARCHAR(100), -- Patrón para tipos de equipo
    alarm_type_pattern VARCHAR(100), -- Patrón para tipos de alarma
    severity_threshold ENUM('INFO', 'WARNING', 'MINOR', 'MAJOR', 'CRITICAL') NOT NULL,
    customer_threshold INTEGER NOT NULL, -- Mín. clientes para incidente maestro
    time_window_seconds INTEGER NOT NULL, -- Ventana para correlación
    geographic_radius_meters INTEGER NOT NULL, -- Radio geográfico
    rule_active BOOLEAN NOT NULL DEFAULT TRUE,
    rule_priority INTEGER NOT NULL DEFAULT 100, -- Mayor prioridad = menor número
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rule_id (rule_id),
    INDEX idx_active_priority (rule_active, rule_priority)
);
```

## Features y Escenarios Cubiertos

### RF12 - Correlación de incidentes de red con clientes
- **RF12-ESC01**: Una falla grande se registra como un solo incidente
- **RF12-ESC02**: Notificación proactiva a clientes afectados
- **RF12-ESC03**: El cliente que llama recibe información sin esperar agente
- **RF12-ESC04**: Cierre de incidente maestro con resolución en cascada
- **RF12-ESC05**: Alarma sin correlación por inventario desactualizado
- **RF12-ESC06**: Descarte de eventos duplicados o irrelevantes
- **RF12-ESC07**: Falla en entrega de notificaciones proactivas
- **RF12-ESC08**: Umbral no alcanzado para incidente masivo
- **RF12-ESC09**: Error técnico durante creación del incidente maestro

### Escenarios Adicionales
- **COR-ESC01**: Correlación automática de alarmas relacionadas
- **COR-ESC02**: Escalamiento por severidad y tipo de cliente
- **COR-ESC03**: Actualización de incidente con nuevas alarmas
- **COR-ESC04**: Gestión de falsos positivos en correlación
- **COR-ESC05**: Métricas de efectividad de notificaciones proactivas

## Lineamientos Cubiertos

### OBS-08: Correlación de eventos con contexto de cliente
- Motor de correlación que identifica clientes afectados automáticamente
- Contexto completo del impacto por tipo de cliente y SLA

### OBS-13: Integración con NOC
- Correlación automática de eventos técnicos con impactos de negocio
- Identificación inmediata de clientes empresariales críticos afectados

### OBS-14: Integración con ITSM
- Creación automática de tickets maestros
- Escalamiento basado en severidad y cierre en cascada

### ARQ-03: Responsabilidad bien definida
- Microservicio especializado en correlación de eventos de red
- Separación clara entre detección, correlación y notificación

### ESC-05: Operaciones asíncronas
- Procesamiento de alarmas en tiempo real sin bloqueo
- Envío de notificaciones en background con reintentos

### INT-17: Estrategia basada en eventos
- Consumo de eventos de múltiples NMS
- Publicación de eventos de incidentes para otros sistemas

### OBS-15: SLAs de observabilidad
- Detección de problemas en menos de 5 minutos
- Correlación y notificación automática según umbrales definidos