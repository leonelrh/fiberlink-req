# Service Status Service (Servicio de Estado de Servicio)

## Funcionalidades

### 1. Consultar Estado Integral del Servicio
- **Descripción**: Obtiene el estado comercial, técnico y de facturación unificado
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "serviceId": "string",
    "customerId": "string",
    "includeHistory": "boolean",
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "serviceStatus": {
      "serviceId": "string",
      "customerId": "string",
      "commercial": {
        "contractNumber": "string",
        "status": "string", // "ACTIVE" | "SUSPENDED" | "CANCELLED" | "PENDING"
        "plan": {
          "name": "string",
          "speed": "number",
          "type": "string" // "RESIDENTIAL" | "ENTERPRISE"
        },
        "contractDate": "string",
        "lastModified": "string"
      },
      "technical": {
        "status": "string", // "ONLINE" | "OFFLINE" | "DEGRADED" | "MAINTENANCE"
        "nodeId": "string",
        "ctoId": "string",
        "portId": "string",
        "equipment": {
          "ont": {
            "serialNumber": "string",
            "model": "string",
            "signalLevel": "number" // dBm
          },
          "router": {
            "serialNumber": "string",
            "model": "string",
            "wifiEnabled": "boolean"
          }
        },
        "lastCheck": "string",
        "uptime": "string" // duration string
      },
      "billing": {
        "status": "string", // "CURRENT" | "OVERDUE" | "SUSPENDED"
        "currentBalance": "number",
        "nextBillingDate": "string",
        "lastPayment": {
          "amount": "number",
          "date": "string",
          "method": "string"
        }
      },
      "incidents": [
        {
          "ticketId": "string",
          "type": "string",
          "status": "string",
          "reportedAt": "string",
          "estimatedResolution": "string"
        }
      ]
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ConsultarEstadoServicio
    1. VALIDAR parámetros de entrada
    2. CONSULTAR datos comerciales en CRM:
       a. OBTENER contrato activo
       b. VERIFICAR estado comercial
       c. OBTENER datos del plan contratado
    3. CONSULTAR estado técnico en OSS:
       a. VERIFICAR conectividad del servicio
       b. OBTENER datos de equipos instalados
       c. CONSULTAR último estado de señal
    4. CONSULTAR estado de facturación:
       a. OBTENER balance actual
       b. VERIFICAR pagos pendientes
       c. OBTENER fecha próximo ciclo
    5. CONSULTAR incidentes activos en ITSM
    6. CONSOLIDAR respuesta unificada
    7. APLICAR cache con TTL según criticidad
  END
  ```

### 2. Actualizar Estado del Servicio
- **Descripción**: Actualiza estado tras eventos operacionales
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "serviceId": "string",
    "statusUpdate": {
      "domain": "string", // "COMMERCIAL" | "TECHNICAL" | "BILLING"
      "newStatus": "string",
      "reason": "string",
      "effectiveDate": "string",
      "updatedBy": "string"
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ActualizarEstadoServicio
    1. VALIDAR autorización para actualizar dominio específico
    2. APLICAR reglas de negocio según dominio:
       a. COMERCIAL: validar transiciones válidas
       b. TÉCNICO: verificar compatibilidad con equipos
       c. FACTURACIÓN: validar impacto en cobro
    3. PROPAGAR cambio a sistemas correspondientes
    4. INVALIDAR cache relacionado
    5. PUBLICAR evento de cambio de estado
    6. REGISTRAR auditoría del cambio
  END
  ```

### 3. Obtener Historial de Estados
- **Descripción**: Recupera historial completo de cambios de estado
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "serviceId": "string",
    "dateFrom": "string",
    "dateTo": "string",
    "domains": ["string"] // ["COMMERCIAL", "TECHNICAL", "BILLING"]
  }
  ```

## Estructura de Base de Datos

```sql
-- Tabla principal de estado consolidado
CREATE TABLE service_status (
    service_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    contract_number VARCHAR(50),
    commercial_status ENUM('ACTIVE', 'SUSPENDED', 'CANCELLED', 'PENDING') NOT NULL,
    technical_status ENUM('ONLINE', 'OFFLINE', 'DEGRADED', 'MAINTENANCE') NOT NULL,
    billing_status ENUM('CURRENT', 'OVERDUE', 'SUSPENDED') NOT NULL,
    node_id VARCHAR(50),
    cto_id VARCHAR(50),
    port_id VARCHAR(50),
    ont_serial VARCHAR(50),
    router_serial VARCHAR(50),
    plan_name VARCHAR(100),
    plan_speed INTEGER,
    service_type ENUM('RESIDENTIAL', 'ENTERPRISE'),
    last_technical_check TIMESTAMP,
    uptime_seconds BIGINT DEFAULT 0,
    current_balance DECIMAL(10,2),
    next_billing_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_commercial_status (commercial_status),
    INDEX idx_technical_status (technical_status),
    INDEX idx_billing_status (billing_status),
    INDEX idx_updated_at (updated_at)
);

-- Tabla para historial de cambios de estado
CREATE TABLE service_status_history (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(100) NOT NULL,
    domain ENUM('COMMERCIAL', 'TECHNICAL', 'BILLING') NOT NULL,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    reason TEXT,
    changed_by VARCHAR(100) NOT NULL,
    change_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    correlation_id VARCHAR(100),
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_service_id (service_id),
    INDEX idx_domain (domain),
    INDEX idx_change_timestamp (change_timestamp),
    FOREIGN KEY (service_id) REFERENCES service_status(service_id)
);

-- Tabla para cache de consultas frecuentes
CREATE TABLE service_status_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    service_data JSON NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires_at (expires_at)
);

-- Tabla para métricas de consultas
CREATE TABLE status_query_metrics (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    service_id VARCHAR(100) NOT NULL,
    query_type ENUM('FULL_STATUS', 'HISTORY', 'UPDATE') NOT NULL,
    response_time_ms INTEGER NOT NULL,
    cache_hit BOOLEAN NOT NULL,
    requester_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_service_id (service_id),
    INDEX idx_timestamp (timestamp)
);

-- Tabla para gestión de incidentes asociados
CREATE TABLE service_incidents (
    id SERIAL PRIMARY KEY,
    service_id VARCHAR(100) NOT NULL,
    ticket_id VARCHAR(100) NOT NULL,
    incident_type VARCHAR(50) NOT NULL,
    status ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED') NOT NULL,
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    reported_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP NULL,
    estimated_resolution TIMESTAMP NULL,
    description TEXT,
    INDEX idx_service_id (service_id),
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_status (status),
    FOREIGN KEY (service_id) REFERENCES service_status(service_id)
);
```

## Features y Escenarios Cubiertos

### RF05 - Consultar estado de servicio
- **RF05-ESC01**: Consulta exitosa de estado integral
- **RF05-ESC02**: Solicitud inválida por datos incompletos
- **RF05-ESC03**: Sistema CRM/OSS/Facturación no disponible
- **RF05-ESC04**: Consumidor no autorizado

### Escenarios Adicionales
- **STS-ESC01**: Consulta con cache válido (optimización)
- **STS-ESC02**: Servicio con incidentes activos
- **STS-ESC03**: Discrepancia entre sistemas (alertas)
- **STS-ESC04**: Actualización de estado por evento
- **STS-ESC05**: Consulta de historial extendido

## Lineamientos Cubiertos

### ARQ-03: Responsabilidad bien definida
- Microservicio especializado en consolidación de estado
- Punto único de consulta para múltiples sistemas

### ARQ-02: Desacoplamiento entre sistemas core
- Evita integraciones directas entre CRM, OSS y Facturación
- Actúa como facade pattern para consultas de estado

### ESC-04: Cache para lecturas frecuentes
- Cache con TTL diferenciado por tipo de dato
- Reducción de carga en sistemas core

### INT-18: Degradación elegante
- Respuestas parciales cuando sistemas no están disponibles
- Cache como fallback para consultas críticas

### OBS-02: Trazabilidad end-to-end
- Correlación entre consultas y sistemas origen
- Visibilidad completa del flujo de consolidación

### SEG-05: Autorización granular
- Permisos diferenciados por dominio (comercial/técnico/facturación)
- Validación de alcance según tipo de usuario

### INT-13: Modelo canónico
- Unificación de modelos heterogéneos de estado
- Consistencia en representación independiente del sistema