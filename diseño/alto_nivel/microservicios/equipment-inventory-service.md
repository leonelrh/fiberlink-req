# Equipment Inventory Service (Servicio de Inventario de Equipos)

## Funcionalidades

### 1. Validar Inventario de Equipos
- **Descripción**: Verifica disponibilidad de ONT y router para instalaciones
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "validationRequest": {
      "planType": "string", // Plan contratado para determinar equipos
      "serviceSpeed": "number", // Mbps
      "warehouseId": "string",
      "alternateWarehouses": ["string"],
      "requiredEquipment": [
        {
          "type": "string", // "ONT" | "ROUTER" | "CABLE" | "SPLITTER"
          "specifications": {
            "technology": "string", // "GPON" | "XGS-PON"
            "wifiStandard": "string", // Para routers
            "ports": "number"
          }
        }
      ]
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "inventoryValidation": {
      "available": "boolean",
      "warehouseId": "string",
      "equipmentAvailability": [
        {
          "type": "string",
          "model": "string",
          "availableQuantity": "number",
          "reservedQuantity": "number",
          "specifications": "object"
        }
      ],
      "alternativeOptions": [
        {
          "warehouseId": "string",
          "distance": "number", // km
          "transferTime": "string", // estimated hours
          "equipmentAvailable": "boolean"
        }
      ],
      "recommendedKit": [
        {
          "type": "string",
          "model": "string",
          "serialNumbers": ["string"], // Pre-seleccionados para reserva
          "warehouseLocation": "string"
        }
      ]
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ValidarInventarioEquipos
    1. VALIDAR parámetros y determinar equipos necesarios según plan
    2. CONSULTAR ERP on-premises para stock disponible:
       a. VERIFICAR disponibilidad en almacén principal
       b. FILTRAR equipos compatibles con especificaciones
       c. EXCLUIR equipos reservados o en mantenimiento
    3. SI stock suficiente en almacén principal:
       a. PRE-SELECCIONAR equipos específicos
       b. GENERAR kit recomendado con seriales
    4. SI stock insuficiente:
       a. CONSULTAR almacenes alternativos en zona
       b. CALCULAR distancias y tiempos de transferencia
       c. EVALUAR viabilidad de transferencia
    5. GENERAR recomendación final con opciones
    6. REGISTRAR consulta en auditoría
  END
  ```

### 2. Reservar Equipos para Orden
- **Descripción**: Reserva temporalmente equipos específicos para instalación
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "reservationRequest": {
      "orderId": "string",
      "customerId": "string",
      "scheduledDate": "string", // Fecha programada de instalación
      "equipmentKit": [
        {
          "type": "string",
          "model": "string",
          "serialNumber": "string",
          "warehouseId": "string"
        }
      ],
      "reservationDuration": "number" // horas (default 48)
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "reservationResult": {
      "reservationId": "string",
      "status": "string", // "CONFIRMED" | "PARTIAL" | "FAILED"
      "reservedEquipment": [
        {
          "type": "string",
          "serialNumber": "string",
          "status": "RESERVED",
          "expiresAt": "string"
        }
      ],
      "failedReservations": [
        {
          "type": "string",
          "serialNumber": "string",
          "reason": "string"
        }
      ]
    }
  }
  ```

### 3. Confirmar Instalación y Dar de Baja
- **Descripción**: Confirma equipos instalados y los retira del inventario
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "installationConfirmation": {
      "orderId": "string",
      "customerId": "string",
      "contractNumber": "string",
      "installedEquipment": [
        {
          "type": "string",
          "serialNumber": "string",
          "installationData": {
            "installedAt": "string",
            "location": "string",
            "technicianId": "string",
            "signalLevel": "number", // Para ONT
            "configurationApplied": "object"
          }
        }
      ]
    }
  }
  ```

### 4. Liberar Equipos Reservados
- **Descripción**: Libera reservas por cancelación o expiración
- **Algoritmo**:
  ```
  BEGIN LiberarEquiposReservados
    1. IDENTIFICAR reservas vencidas o canceladas
    2. PARA cada equipo reservado:
       a. CAMBIAR estado de RESERVADO a DISPONIBLE
       b. ACTUALIZAR inventario en ERP
       c. NOTIFICAR disponibilidad a coordinadores
    3. GENERAR métricas de liberación
    4. LIMPIAR registros de reserva expirados
  END
  ```


### 5. Consultar Topología de Red

- **Descripción**: Consulta el sistema de inventario Oracle (Oracle UIM o equivalente) para obtener la topología de red de un recurso de infraestructura (Nodo, OLT, CTO, Splitter o segmento de fibra). Esta información es utilizada por otros microservicios, como Incident Correlation Service, para identificar dependencias, calcular impacto y determinar los clientes potencialmente afectados por un incidente.

- **Contrato de Entrada**:

```json
{
  "correlationId": "string",
  "topologyRequest": {
    "resourceType": "string", // "NODE" | "OLT" | "CTO" | "SPLITTER" | "FIBER_SEGMENT"
    "resourceId": "string",
    "includeParents": true,
    "includeChildren": true,
    "includeAttributes": true,
    "maxDepth": 5
  },
  "requesterId": "string"
}
```

- **Contrato de Salida**:

```json
{
  "correlationId": "string",
  "networkTopology": {
    "resource": {
      "id": "NODE-001",
      "type": "NODE",
      "name": "Nodo Lima Sur",
      "status": "ACTIVE",
      "location": "Lima"
    },
    "parents": [
      {
        "id": "OLT-001",
        "type": "OLT",
        "name": "OLT Chorrillos",
        "status": "ACTIVE"
      }
    ],
    "children": [
      {
        "id": "CTO-101",
        "type": "CTO",
        "status": "ACTIVE"
      },
      {
        "id": "CTO-102",
        "type": "CTO",
        "status": "ACTIVE"
      }
    ],
    "relationships": [
      {
        "source": "OLT-001",
        "target": "NODE-001",
        "relationshipType": "CONNECTED_TO"
      },
      {
        "source": "NODE-001",
        "target": "CTO-101",
        "relationshipType": "SERVES"
      },
      {
        "source": "NODE-001",
        "target": "CTO-102",
        "relationshipType": "SERVES"
      }
    ],
    "metadata": {
      "generatedAt": "2026-07-12T14:30:00Z",
      "source": "Oracle Inventory"
    }
  }
}
```

## Estructura de Base de Datos

```sql
-- Tabla para cache de inventario de equipos
CREATE TABLE equipment_inventory_cache (
    id SERIAL PRIMARY KEY,
    warehouse_id VARCHAR(50) NOT NULL,
    equipment_type ENUM('ONT', 'ROUTER', 'CABLE', 'SPLITTER', 'OTHER') NOT NULL,
    model VARCHAR(100) NOT NULL,
    available_quantity INTEGER NOT NULL,
    reserved_quantity INTEGER NOT NULL,
    total_quantity INTEGER GENERATED ALWAYS AS (available_quantity + reserved_quantity),
    specifications JSON NOT NULL, -- Specs técnicas del modelo
    last_erp_sync TIMESTAMP NOT NULL,
    cache_expires_at TIMESTAMP NOT NULL,
    INDEX idx_warehouse_type (warehouse_id, equipment_type),
    INDEX idx_model (model),
    INDEX idx_expires (cache_expires_at)
);

-- Tabla para reservas de equipos
CREATE TABLE equipment_reservations (
    id SERIAL PRIMARY KEY,
    reservation_id VARCHAR(100) UNIQUE NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    equipment_type ENUM('ONT', 'ROUTER', 'CABLE', 'SPLITTER', 'OTHER') NOT NULL,
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    warehouse_id VARCHAR(50) NOT NULL,
    status ENUM('RESERVED', 'CONFIRMED', 'INSTALLED', 'CANCELLED', 'EXPIRED') NOT NULL,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP NULL,
    installed_at TIMESTAMP NULL,
    released_at TIMESTAMP NULL,
    technician_id VARCHAR(50) NULL,
    installation_location TEXT NULL,
    requester_id VARCHAR(100) NOT NULL,
    INDEX idx_reservation_id (reservation_id),
    INDEX idx_order_id (order_id),
    INDEX idx_serial_number (serial_number),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    UNIQUE KEY uk_active_equipment_reservation (serial_number, status)
);

-- Tabla para equipos instalados (histórico)
CREATE TABLE installed_equipment (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(100) UNIQUE NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    equipment_type ENUM('ONT', 'ROUTER', 'CABLE', 'SPLITTER', 'OTHER') NOT NULL,
    model VARCHAR(100) NOT NULL,
    contract_number VARCHAR(50) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    installation_date TIMESTAMP NOT NULL,
    installation_location TEXT NOT NULL,
    technician_id VARCHAR(50) NOT NULL,
    signal_level DECIMAL(5,2) NULL, -- Para equipos ópticos
    configuration_data JSON NULL,
    status ENUM('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'RETIRED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_serial_number (serial_number),
    INDEX idx_contract_number (contract_number),
    INDEX idx_customer_id (customer_id),
    INDEX idx_installation_date (installation_date)
);

-- Tabla para auditoría de operaciones de inventario
CREATE TABLE equipment_audit (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    operation_type ENUM('VALIDATE', 'RESERVE', 'CONFIRM_INSTALL', 'RELEASE', 'TRANSFER') NOT NULL,
    order_id VARCHAR(100),
    equipment_type VARCHAR(50),
    serial_number VARCHAR(100),
    warehouse_id VARCHAR(50),
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    operation_result ENUM('SUCCESS', 'PARTIAL', 'FAILED') NOT NULL,
    error_details TEXT NULL,
    requester_id VARCHAR(100) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_serial_number (serial_number),
    INDEX idx_created (created_at)
);

-- Tabla para transferencias entre almacenes
CREATE TABLE equipment_transfers (
    id SERIAL PRIMARY KEY,
    transfer_id VARCHAR(100) UNIQUE NOT NULL,
    equipment_type ENUM('ONT', 'ROUTER', 'CABLE', 'SPLITTER', 'OTHER') NOT NULL,
    model VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    from_warehouse_id VARCHAR(50) NOT NULL,
    to_warehouse_id VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('REQUESTED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED') NOT NULL,
    requested_by VARCHAR(100) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_arrival TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    tracking_info JSON NULL,
    INDEX idx_transfer_id (transfer_id),
    INDEX idx_from_warehouse (from_warehouse_id),
    INDEX idx_to_warehouse (to_warehouse_id),
    INDEX idx_status (status)
);

-- Tabla para métricas de inventario
CREATE TABLE inventory_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    warehouse_id VARCHAR(50) NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    total_stock INTEGER NOT NULL,
    available_stock INTEGER NOT NULL,
    reserved_stock INTEGER NOT NULL,
    installed_count INTEGER NOT NULL, -- Equipos dados de baja por instalación
    transfer_in_count INTEGER NOT NULL,
    transfer_out_count INTEGER NOT NULL,
    stock_turnover_ratio DECIMAL(5,3) NOT NULL,
    PRIMARY KEY (metric_date, warehouse_id, equipment_type, model),
    INDEX idx_metric_date (metric_date),
    INDEX idx_warehouse_id (warehouse_id)
);


-- Cache local de topología de red
CREATE TABLE network_topology_cache (
    id SERIAL PRIMARY KEY,
    resource_id VARCHAR(100) NOT NULL,
    resource_type ENUM('NODE','OLT','CTO','SPLITTER','FIBER_SEGMENT') NOT NULL,
    topology_json JSON NOT NULL,
    oracle_version VARCHAR(50),
    last_sync TIMESTAMP NOT NULL,
    cache_expires_at TIMESTAMP NOT NULL,
    INDEX idx_resource (resource_id, resource_type),
    INDEX idx_expiration (cache_expires_at)
);

-- Auditoría de consultas de topología
CREATE TABLE topology_query_audit (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    requester_id VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    operation_result ENUM('SUCCESS','FAILED','PARTIAL') NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_details TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_resource (resource_id),
    INDEX idx_created_at (created_at)
);
```



## Features y Escenarios Cubiertos

### RF10 - Consultar Topología de Red

- **RF10-ESC01**: Consulta exitosa de topología por Nodo.
- **RF10-ESC02**: Consulta de topología por OLT.
- **RF10-ESC03**: Consulta de topología por CTO.
- **RF10-ESC04**: Consulta de segmento de fibra.
- **RF10-ESC05**: Recurso inexistente.
- **RF10-ESC06**: Timeout al consultar Oracle Inventory.
- **RF10-ESC07**: Respuesta parcial por indisponibilidad temporal.
- **RF10-ESC08**: Uso de caché ante indisponibilidad del inventario Oracle.

### RF09 - Validar inventario de equipos
- **RF09-ESC01**: Validación exitosa de disponibilidad
- **RF09-ESC02**: Reserva de equipos para orden
- **RF09-ESC03**: Liberación automática de reservas
- **RF09-ESC04**: Confirmación de instalación y baja
- **RF09-ESC05**: Equipos insuficientes en almacén
- **RF09-ESC06**: Transferencia entre almacenes
- **RF09-ESC07**: Validación de compatibilidad con plan
- **RF09-ESC08**: Error de conectividad con ERP

### Escenarios Adicionales
- **EQP-ESC01**: Optimización de kit por proximidad
- **EQP-ESC02**: Alertas de stock crítico
- **EQP-ESC03**: Rotación automática de inventario
- **EQP-ESC04**: Conciliación con ERP programada
- **EQP-ESC05**: Gestión de equipos defectuosos
- **TOP-ESC01**: Consulta recursiva de dependencias.
- **TOP-ESC02**: Consulta limitada por profundidad.
- **TOP-ESC03**: Actualización automática de caché.
- **TOP-ESC04**: Invalidación de caché por cambios en Oracle.
- **TOP-ESC05**: Degradación controlada utilizando caché local.

## Lineamientos Cubiertos

### ARQ-03: Responsabilidad bien definida
- Microservicio especializado en gestión de inventario de equipos
- Separación clara entre validación, reserva e instalación

### ESC-04: Cache para lecturas frecuentes
- Cache local de inventario con sincronización programada
- Reducción significativa de consultas al ERP

### INT-12: Consideración de sistemas on-premises
- Manejo de latencia y timeouts con ERP heredado
- Estrategias de fallback y degradación controlada

### ESC-06: Prevención de cuellos de botella
- Distribución de carga entre múltiples almacenes
- Optimización de transferencias según demanda

### SEG-07: Auditoría completa
- Trazabilidad de equipos desde reserva hasta instalación
- Registro de cadena de custodia completa

### OBS-03: Métricas técnicas y de negocio
- Métricas de rotación de inventario y eficiencia
- Indicadores de disponibilidad y tiempos de transferencia

### INT-06: Operaciones idempotentes
- Reservas y liberaciones pueden ser re-ejecutadas
- Detección de duplicados en confirmaciones de instalación