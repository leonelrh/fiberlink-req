# Inventory Sync Service (Servicio de Sincronización de Inventario)

## Funcionalidades

### 1. Sincronizar Estado de Puertos en Tiempo Real
- **Descripción**: Mantiene sincronizado el estado de puertos entre Oracle e sistemas OSS
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "syncType": "string", // "PORT_RESERVATION" | "PORT_INSTALLATION" | "PORT_RELEASE"
    "portData": {
      "portId": "string",
      "ctoId": "string",
      "nodeId": "string",
      "newStatus": "string", // "AVAILABLE" | "RESERVED" | "INSTALLED" | "MAINTENANCE"
      "orderId": "string",
      "customerId": "string",
      "equipmentIds": ["string"], // Para instalaciones
      "technicalData": {
        "signalLevel": "number",
        "installationDate": "string"
      }
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "syncResult": {
      "success": "boolean",
      "portId": "string",
      "previousStatus": "string",
      "newStatus": "string",
      "syncedSystems": ["string"], // ["ORACLE", "OSS"]
      "syncTime": "string",
      "conflicts": [
        {
          "system": "string",
          "expectedStatus": "string",
          "actualStatus": "string",
          "requiresManualReview": "boolean"
        }
      ]
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN SincronizarEstadoPuerto
    1. VALIDAR datos de entrada y autorización
    2. OBTENER estado actual en Oracle y OSS
    3. DETECTAR conflictos de estado entre sistemas:
       a. SI estados coinciden Y cambio es válido: PROCEDER
       b. SI estados difieren: REGISTRAR conflicto
       c. SI transición no es válida: RECHAZAR
    4. EJECUTAR sincronización en transacción distribuida:
       a. ACTUALIZAR estado en Oracle (inventario)
       b. ACTUALIZAR estado en OSS (provisión)
       c. REGISTRAR equipos si aplica (instalación)
    5. VERIFICAR sincronización exitosa:
       a. LEER estado final de ambos sistemas
       b. CONFIRMAR consistencia
    6. SI hay fallas: REVERTIR cambios parciales
    7. PUBLICAR evento de cambio de estado
    8. REGISTRAR resultado en auditoría
  END
  ```

### 2. Detectar y Conciliar Discrepancias
- **Descripción**: Identifica inconsistencias entre sistemas y propone correcciones
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "reconciliationType": "string", // "FULL_SCAN" | "TARGETED" | "SCHEDULED"
    "scope": {
      "nodeIds": ["string"], // Opcional, para reconciliación específica
      "ctoIds": ["string"],
      "dateRange": {
        "from": "string",
        "to": "string"
      }
    }
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "reconciliationResult": {
      "totalPortsChecked": "number",
      "discrepanciesFound": "number",
      "discrepancies": [
        {
          "portId": "string",
          "ctoId": "string",
          "oracleStatus": "string",
          "ossStatus": "string",
          "severity": "string", // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
          "recommendedAction": "string",
          "autoFixable": "boolean"
        }
      ],
      "autoFixedCount": "number",
      "manualReviewRequired": "number"
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN DetectarDiscrepancias
    1. DEFINIR alcance de reconciliación
    2. OBTENER snapshot de estados en Oracle
    3. OBTENER snapshot de estados en OSS
    4. COMPARAR estados puerto por puerto:
       a. IDENTIFICAR diferencias de estado
       b. CLASIFICAR severidad según reglas de negocio
       c. DETERMINAR acción correctiva
    5. PARA discrepancias auto-reparables:
       a. APLICAR corrección automática
       b. VERIFICAR resultado
       c. REGISTRAR acción tomada
    6. PARA discrepancias complejas:
       a. GENERAR reporte para revisión manual
       b. CREAR ticket de soporte si aplica
    7. PUBLICAR métricas de reconciliación
  END
  ```

### 3. Procesar Eventos de Cambio de Estado
- **Descripción**: Reacciona a eventos asíncronos de cambios en inventario
- **Contrato de Entrada** (Event):
  ```json
  {
    "eventId": "string",
    "eventType": "INVENTORY_CHANGE",
    "sourceSystem": "string", // "ORACLE" | "OSS" | "ERP"
    "timestamp": "string",
    "payload": {
      "portId": "string",
      "changeType": "string", // "STATUS_CHANGE" | "EQUIPMENT_ASSIGNMENT"
      "previousData": "object",
      "newData": "object",
      "triggeredBy": "string"
    }
  }
  ```

## Estructura de Base de Datos

```sql
-- Tabla para estado de sincronización de puertos
CREATE TABLE port_sync_status (
    port_id VARCHAR(50) PRIMARY KEY,
    cto_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    oracle_status ENUM('AVAILABLE', 'RESERVED', 'INSTALLED', 'MAINTENANCE', 'UNKNOWN') NOT NULL,
    oss_status ENUM('AVAILABLE', 'RESERVED', 'INSTALLED', 'MAINTENANCE', 'UNKNOWN') NOT NULL,
    is_synchronized BOOLEAN GENERATED ALWAYS AS (oracle_status = oss_status),
    last_oracle_sync TIMESTAMP NOT NULL,
    last_oss_sync TIMESTAMP NOT NULL,
    sync_attempts INTEGER DEFAULT 0,
    last_sync_error TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cto_id (cto_id),
    INDEX idx_node_id (node_id),
    INDEX idx_synchronized (is_synchronized),
    INDEX idx_last_sync (GREATEST(last_oracle_sync, last_oss_sync))
);

-- Tabla para histórico de sincronizaciones
CREATE TABLE sync_operations (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    operation_type ENUM('PORT_RESERVATION', 'PORT_INSTALLATION', 'PORT_RELEASE', 'RECONCILIATION') NOT NULL,
    port_id VARCHAR(50) NOT NULL,
    previous_oracle_status VARCHAR(20),
    new_oracle_status VARCHAR(20),
    previous_oss_status VARCHAR(20),
    new_oss_status VARCHAR(20),
    operation_result ENUM('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'ROLLED_BACK') NOT NULL,
    error_message TEXT NULL,
    sync_duration_ms INTEGER NOT NULL,
    requester_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_port_id (port_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_result (operation_result),
    INDEX idx_created (created_at)
);

-- Tabla para gestión de discrepancias
CREATE TABLE inventory_discrepancies (
    id SERIAL PRIMARY KEY,
    discrepancy_id VARCHAR(100) UNIQUE NOT NULL,
    port_id VARCHAR(50) NOT NULL,
    cto_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    oracle_status VARCHAR(20) NOT NULL,
    oss_status VARCHAR(20) NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    recommended_action TEXT NOT NULL,
    auto_fixable BOOLEAN NOT NULL,
    status ENUM('DETECTED', 'IN_PROGRESS', 'RESOLVED', 'MANUAL_REVIEW') NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolution_method ENUM('AUTO_FIX', 'MANUAL_FIX', 'IGNORED') NULL,
    assigned_to VARCHAR(100) NULL,
    notes TEXT NULL,
    INDEX idx_port_id (port_id),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_detected (detected_at)
);

-- Tabla para eventos de sincronización
CREATE TABLE sync_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source_system ENUM('ORACLE', 'OSS', 'ERP', 'SYNC_SERVICE') NOT NULL,
    port_id VARCHAR(50) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    previous_data JSON,
    new_data JSON NOT NULL,
    triggered_by VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_result ENUM('SUCCESS', 'FAILED', 'SKIPPED') NOT NULL,
    error_details TEXT NULL,
    INDEX idx_event_id (event_id),
    INDEX idx_port_id (port_id),
    INDEX idx_source_system (source_system),
    INDEX idx_processed (processed_at)
);

-- Tabla para métricas de rendimiento
CREATE TABLE sync_performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    hour INTEGER NOT NULL, -- 0-23
    total_sync_operations INTEGER NOT NULL,
    successful_syncs INTEGER NOT NULL,
    failed_syncs INTEGER NOT NULL,
    avg_sync_time_ms DECIMAL(10,3) NOT NULL,
    discrepancies_detected INTEGER NOT NULL,
    discrepancies_auto_fixed INTEGER NOT NULL,
    ports_out_of_sync INTEGER NOT NULL,
    PRIMARY KEY (metric_date, hour),
    INDEX idx_metric_date (metric_date)
);
```

## Features y Escenarios Cubiertos

### RF06 - Sincronizar inventario de puertos
- **RF06-ESC01**: Reserva exitosa de puerto
- **RF06-ESC02**: Liberación de puerto por cancelación
- **RF06-ESC03**: Confirmación de instalación exitosa
- **RF06-ESC04**: Detección de discrepancia de estado
- **RF06-ESC05**: Puerto no disponible durante reserva
- **RF06-ESC06**: Transferencia de equipos entre almacenes

### Escenarios Adicionales
- **INV-ESC01**: Reconciliación programada automática
- **INV-ESC02**: Rollback por falla en sincronización
- **INV-ESC03**: Resolución automática de discrepancias menores
- **INV-ESC04**: Escalamiento de discrepancias críticas
- **INV-ESC05**: Sincronización masiva tras mantenimiento

## Lineamientos Cubiertos

### ARQ-02: Desacoplamiento entre sistemas core
- Evita integraciones directas entre Oracle y OSS
- Actúa como mediador para sincronización

### INT-06: Operaciones idempotentes
- Sincronizaciones pueden ser re-ejecutadas sin efectos adversos
- Detección de cambios previos para evitar duplicación

### ESC-09: Degradación controlada
- Continúa operando con inconsistencias menores
- Prioriza disponibilidad sobre consistencia perfecta

### OBS-08: Correlación de eventos
- Rastreo completo desde evento origen hasta sincronización
- Visibilidad de cadena de cambios

### INT-11: Reproceso de eventos fallidos
- Reintentos automáticos con backoff exponencial
- Queue de eventos para procesamiento diferido

### SEG-07: Registro de auditoría
- Trazabilidad completa de cambios de inventario
- Identificación de usuarios y procesos responsables

### ESC-05: Operaciones asíncronas
- Procesamiento en background de reconciliaciones
- Desacoplamiento temporal entre detección y corrección