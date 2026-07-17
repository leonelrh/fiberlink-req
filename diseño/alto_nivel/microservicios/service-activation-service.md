# Service Activation Service (Servicio de Activación de Servicio)

## Funcionalidades

### 1. Activar Servicio de Internet
- **Descripción**: Ejecuta el proceso completo de activación tras instalación exitosa
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "activationRequest": {
      "orderId": "string",
      "customerId": "string",
      "customerDocument": "string", // Para validación de identidad
      "serviceDetails": {
        "planContracted": "string",
        "speed": "number",
        "serviceType": "string" // "RESIDENTIAL" | "ENTERPRISE"
      },
      "technicalValidation": {
        "routerConfigured": "boolean",
        "opticalPowerValidated": "boolean",
        "signalLevel": "number", // dBm
        "speedTestResults": {
          "downloadMbps": "number",
          "uploadMbps": "number",
          "latency": "number"
        }
      },
      "installedEquipment": [
        {
          "type": "string", // "ONT" | "ROUTER"
          "model": "string",
          "serialNumber": "string",
          "configurationApplied": "object"
        }
      ],
      "technicianId": "string"
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "activationResult": {
      "success": "boolean",
      "serviceId": "string",
      "contractGeneration": {
        "contractNumber": "string",
        "generatedAt": "string",
        "billingStartDate": "string",
        "contractSentToEmail": "boolean"
      },
      "serviceStatus": "string", // "ACTIVE" | "FAILED"
      "billingSetup": {
        "billingCycleDay": "number",
        "firstBillAmount": "number",
        "nextBillingDate": "string",
        "billingAccountCreated": "boolean"
      },
      "equipmentRegistration": {
        "equipmentLinkedToContract": "boolean",
        "inventoryUpdated": "boolean",
        "warrantyActivated": "boolean"
      },
      "orderClosure": {
        "orderStatus": "string", // "COMPLETED" | "FAILED"
        "completionTime": "string",
        "technicianConfirmed": "boolean"
      },
      "errorDetails": "string" // Si success = false
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ActivarServicioInternet
    1. VALIDAR consistencia de datos:
       a. VERIFICAR que cliente coincide con orden
       b. CONFIRMAR que instalación está técnicamente validada
       c. VALIDAR configuración de equipos
    2. SOLICITAR confirmación de activación al OSS:
       a. ENVIAR comando de activación con timeout 30s
       b. ESPERAR confirmación de provisión exitosa
       c. SI timeout: MARCAR como pendiente y reintentar
    3. SI activación OSS exitosa:
       a. GENERAR número de contrato único
       b. VINCULAR servicio instalado al contrato
       c. CREAR datos de facturación en ERP
       d. REGISTRAR equipos como instalados en inventario
    4. CERRAR orden de instalación:
       a. MARCAR orden como "EXITOSA"
       b. LIBERAR recursos asignados
       c. ACTUALIZAR métricas de completación
    5. ENVIAR contrato por email al cliente
    6. SI cualquier paso falla:
       a. EJECUTAR rollback de cambios parciales
       b. REGISTRAR incidente técnico
       c. NOTIFICAR a equipo de soporte
  END
  ```

### 2. Rollback de Activación
- **Descripción**: Revierte activación parcial por fallos técnicos
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "rollbackRequest": {
      "orderId": "string",
      "activationAttemptId": "string",
      "rollbackReason": "string",
      "systemsAffected": ["string"], // ["OSS", "ERP", "INVENTORY", "BILLING"]
      "partialDataToRevert": "object"
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN RollbackActivacion
    1. IDENTIFICAR cambios realizados durante activación fallida
    2. PARA cada sistema afectado:
       a. OSS: DESACTIVAR servicio si fue activado
       b. ERP: ELIMINAR registro de contrato si fue creado
       c. INVENTARIO: RESTAURAR equipos a estado RESERVADO
       d. FACTURACIÓN: CANCELAR setup de billing si existe
    3. RESTAURAR orden a estado PROGRAMADA
    4. NOTIFICAR al técnico sobre fallo de activación
    5. GENERAR ticket de soporte para revisión manual
  END
  ```

### 3. Validar Precondiciones de Activación
- **Descripción**: Verifica que todos los requisitos están cumplidos antes de activar
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "validationRequest": {
      "orderId": "string",
      "customerId": "string",
      "technicalChecks": ["string"], // Lista de validaciones requeridas
      "documentValidation": "boolean"
    }
  }
  ```

## Estructura de Base de Datos

```sql
-- Tabla para registro de activaciones
CREATE TABLE service_activations (
    id SERIAL PRIMARY KEY,
    activation_id VARCHAR(100) UNIQUE NOT NULL,
    correlation_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    service_id VARCHAR(100) UNIQUE NOT NULL,
    activation_status ENUM('INITIATED', 'OSS_CONFIRMED', 'CONTRACT_GENERATED', 'BILLING_SETUP', 'COMPLETED', 'FAILED', 'ROLLED_BACK') NOT NULL,
    contract_number VARCHAR(50) NULL,
    billing_account_id VARCHAR(50) NULL,
    oss_activation_time TIMESTAMP NULL,
    contract_generation_time TIMESTAMP NULL,
    billing_setup_time TIMESTAMP NULL,
    completion_time TIMESTAMP NULL,
    failure_reason TEXT NULL,
    technician_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_activation_id (activation_id),
    INDEX idx_correlation (correlation_id),
    INDEX idx_order_id (order_id),
    INDEX idx_service_id (service_id),
    INDEX idx_status (activation_status),
    INDEX idx_created (created_at)
);

-- Tabla para validaciones técnicas
CREATE TABLE activation_validations (
    id SERIAL PRIMARY KEY,
    activation_id VARCHAR(100) NOT NULL,
    validation_type ENUM('CUSTOMER_IDENTITY', 'ROUTER_CONFIG', 'OPTICAL_POWER', 'SPEED_TEST', 'EQUIPMENT_SERIAL') NOT NULL,
    validation_result ENUM('PASSED', 'FAILED', 'WARNING') NOT NULL,
    validation_data JSON, -- Datos específicos de la validación
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_by VARCHAR(100) NOT NULL,
    error_details TEXT NULL,
    INDEX idx_activation_id (activation_id),
    INDEX idx_validation_type (validation_type),
    INDEX idx_result (validation_result),
    FOREIGN KEY (activation_id) REFERENCES service_activations(activation_id)
);

-- Tabla para equipos activados
CREATE TABLE activated_equipment (
    id SERIAL PRIMARY KEY,
    activation_id VARCHAR(100) NOT NULL,
    service_id VARCHAR(100) NOT NULL,
    equipment_type ENUM('ONT', 'ROUTER', 'CABLE', 'SPLITTER') NOT NULL,
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    configuration_applied JSON NOT NULL,
    signal_level DECIMAL(5,2) NULL,
    warranty_start_date DATE NOT NULL,
    warranty_duration_months INTEGER NOT NULL DEFAULT 12,
    equipment_status ENUM('ACTIVE', 'INACTIVE', 'MAINTENANCE') NOT NULL DEFAULT 'ACTIVE',
    linked_to_contract BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_activation_id (activation_id),
    INDEX idx_service_id (service_id),
    INDEX idx_serial_number (serial_number),
    FOREIGN KEY (activation_id) REFERENCES service_activations(activation_id)
);

-- Tabla para contratos generados
CREATE TABLE generated_contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    activation_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    service_id VARCHAR(100) NOT NULL,
    plan_contracted VARCHAR(100) NOT NULL,
    monthly_fee DECIMAL(10,2) NOT NULL,
    installation_fee DECIMAL(10,2) NOT NULL DEFAULT 0,
    contract_term_months INTEGER NOT NULL,
    billing_cycle_day INTEGER NOT NULL, -- 1-28
    billing_start_date DATE NOT NULL,
    next_billing_date DATE NOT NULL,
    contract_pdf_generated BOOLEAN NOT NULL DEFAULT FALSE,
    contract_sent_to_email BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent_timestamp TIMESTAMP NULL,
    contract_acceptance_required BOOLEAN NOT NULL DEFAULT FALSE,
    accepted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract_number (contract_number),
    INDEX idx_activation_id (activation_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_billing_start (billing_start_date),
    FOREIGN KEY (activation_id) REFERENCES service_activations(activation_id)
);

-- Tabla para auditoría de rollbacks
CREATE TABLE activation_rollbacks (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) UNIQUE NOT NULL,
    original_activation_id VARCHAR(100) NOT NULL,
    rollback_reason TEXT NOT NULL,
    systems_affected JSON NOT NULL, -- ["OSS", "ERP", "INVENTORY", "BILLING"]
    rollback_actions JSON NOT NULL, -- Detalle de acciones de reversión
    rollback_status ENUM('INITIATED', 'IN_PROGRESS', 'COMPLETED', 'PARTIAL_SUCCESS', 'FAILED') NOT NULL,
    rollback_completion_time TIMESTAMP NULL,
    manual_intervention_required BOOLEAN NOT NULL DEFAULT FALSE,
    support_ticket_created VARCHAR(100) NULL,
    executed_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rollback_id (rollback_id),
    INDEX idx_original_activation (original_activation_id),
    INDEX idx_status (rollback_status)
);

-- Tabla para métricas de activación
CREATE TABLE activation_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    hour INTEGER NOT NULL, -- 0-23
    total_activation_attempts INTEGER NOT NULL,
    successful_activations INTEGER NOT NULL,
    failed_activations INTEGER NOT NULL,
    rollback_count INTEGER NOT NULL,
    avg_activation_time_seconds INTEGER NOT NULL,
    avg_oss_response_time_ms INTEGER NOT NULL,
    avg_contract_generation_time_ms INTEGER NOT NULL,
    success_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_activation_attempts > 0 
            THEN (successful_activations * 100.0 / total_activation_attempts)
            ELSE 0 
        END
    ),
    PRIMARY KEY (metric_date, hour),
    INDEX idx_metric_date (metric_date)
);

-- Tabla para seguimiento de timeouts OSS
CREATE TABLE oss_timeouts (
    id SERIAL PRIMARY KEY,
    activation_id VARCHAR(100) NOT NULL,
    timeout_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timeout_duration_seconds INTEGER NOT NULL,
    retry_attempt_number INTEGER NOT NULL,
    oss_response_received BOOLEAN NOT NULL DEFAULT FALSE,
    final_activation_result ENUM('SUCCESS_AFTER_RETRY', 'TIMEOUT_PERMANENT', 'MANUAL_INTERVENTION') NULL,
    INDEX idx_activation_id (activation_id),
    INDEX idx_timeout_occurrence (timeout_occurrence)
);
```

## Features y Escenarios Cubiertos

### RF11 - Activar servicio internet
- **RF11-ESC01**: Activación exitosa del servicio
- **RF11-ESC02**: Rechazo por datos incorrectos
- **RF11-ESC03**: Error técnico durante generación del contrato
- **RF11-ESC04**: Error técnico durante activación del servicio

### Escenarios Adicionales
- **ACT-ESC01**: Timeout en confirmación OSS con retry
- **ACT-ESC02**: Rollback completo por falla parcial
- **ACT-ESC03**: Validación de equipos antes de activar
- **ACT-ESC04**: Generación y envío automático de contrato
- **ACT-ESC05**: Configuración automática de ciclo de facturación

## Lineamientos Cubiertos

### RNOF01: Integridad de datos entre plataformas
- Transacciones distribuidas para mantener consistencia
- Rollback automático ante fallos parciales
- Sincronización entre OSS, ERP, inventario y facturación

### RNOF03: Trazabilidad y auditabilidad
- Registro completo del proceso de activación
- Trazabilidad desde solicitud hasta contrato generado
- Auditoría de rollbacks y fallos

### ARQ-03: Responsabilidad bien definida
- Microservicio especializado en orquestación de activación
- Coordinación entre múltiples sistemas sin acoplamiento directo

### INT-06: Operaciones idempotentes
- Activaciones pueden ser reinvocadas sin duplicación
- Detección de activaciones previas exitosas

### ESC-05: Operaciones asíncronas
- Generación de contratos en background
- Envío de emails diferido con reintentos

### SEG-07: Auditoría completa
- Registro de todos los pasos del proceso
- Identificación clara de usuarios y sistemas responsables

### OBS-02: Trazabilidad end-to-end
- Correlación desde instalación hasta facturación
- Visibilidad completa del flujo de activación