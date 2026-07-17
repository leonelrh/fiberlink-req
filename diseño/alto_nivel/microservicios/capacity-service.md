# Capacity Service (Servicio de Validación de Capacidad)

## Funcionalidades

### 1. Validar Capacidad Técnica de Nodo
- **Descripción**: Verifica disponibilidad de capacidad en nodo, CTO y puertos
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "nodeId": "string",
    "ctoId": "string",
    "serviceType": "string", // "RESIDENTIAL" | "ENTERPRISE"
    "bandwidthRequired": "number", // Mbps
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "capacity": {
      "available": "boolean",
      "node": {
        "id": "string",
        "currentLoad": "number", // percentage
        "maxCapacity": "number", // Mbps
        "availableCapacity": "number" // Mbps
      },
      "cto": {
        "id": "string",
        "availablePorts": "number",
        "totalPorts": "number",
        "technology": "string"
      },
      "recommendedPorts": [
        {
          "portId": "string",
          "splitterId": "string",
          "signalQuality": "string" // "EXCELLENT" | "GOOD" | "FAIR"
        }
      ]
    },
    "responseTime": "string"
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ValidarCapacidadTecnica
    1. VALIDAR parámetros de entrada (nodeId, ctoId, bandwidth)
    2. CONSULTAR estado actual del nodo en inventario Oracle:
       a. VERIFICAR si nodo está activo
       b. OBTENER capacidad total y utilizada
       c. CALCULAR capacidad disponible
    3. SI capacidad de nodo es suficiente:
       a. CONSULTAR puertos disponibles en CTO especificada
       b. VERIFICAR estado de splitters asociados
       c. EVALUAR calidad de señal por puerto
    4. GENERAR lista de puertos recomendados:
       a. PRIORIZAR puertos con mejor señal
       b. CONSIDERAR distribución de carga
       c. VALIDAR compatibilidad con tipo de servicio
    5. RETORNAR resultado de validación
    6. REGISTRAR auditoría de consulta
  END
  ```

### 2. Reservar Puerto Temporal
- **Descripción**: Reserva temporalmente un puerto específico para instalación
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "portId": "string",
    "orderId": "string",
    "customerId": "string",
    "reservationDuration": "number", // horas
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "reservation": {
      "reservationId": "string",
      "portId": "string",
      "status": "string", // "RESERVED" | "FAILED"
      "expiresAt": "string", // ISO timestamp
      "orderId": "string"
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ReservarPuertoTemporal
    1. VALIDAR que puerto existe y está disponible
    2. VERIFICAR que no hay reserva activa en el puerto
    3. CREAR registro de reserva temporal:
       a. GENERAR reservationId único
       b. ESTABLECER timestamp de expiración
       c. MARCAR puerto como RESERVADO en inventario
    4. PROGRAMAR job de liberación automática
    5. REGISTRAR evento en auditoría
  END
  ```

### 3. Liberar Reserva de Puerto
- **Descripción**: Libera una reserva temporal de puerto
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "reservationId": "string",
    "reason": "string" // "INSTALLED" | "CANCELLED" | "EXPIRED"
  }
  ```

## Estructura de Base de Datos

```sql
-- Tabla para cache de capacidad de nodos
CREATE TABLE node_capacity_cache (
    node_id VARCHAR(50) PRIMARY KEY,
    max_capacity_mbps INTEGER NOT NULL,
    current_load_mbps INTEGER NOT NULL,
    available_capacity_mbps INTEGER GENERATED ALWAYS AS (max_capacity_mbps - current_load_mbps),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    technology VARCHAR(20) NOT NULL, -- GPON, XGS-PON
    status ENUM('ACTIVE', 'MAINTENANCE', 'INACTIVE') NOT NULL,
    INDEX idx_available_capacity (available_capacity_mbps),
    INDEX idx_technology (technology),
    INDEX idx_last_updated (last_updated)
);

-- Tabla para gestión de reservas temporales
CREATE TABLE port_reservations (
    id SERIAL PRIMARY KEY,
    reservation_id VARCHAR(100) UNIQUE NOT NULL,
    port_id VARCHAR(50) NOT NULL,
    cto_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    status ENUM('RESERVED', 'CONFIRMED', 'CANCELLED', 'EXPIRED') NOT NULL,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP NULL,
    released_at TIMESTAMP NULL,
    requester_id VARCHAR(100) NOT NULL,
    INDEX idx_port_id (port_id),
    INDEX idx_order_id (order_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_status (status),
    UNIQUE KEY uk_active_port_reservation (port_id, status) -- Solo una reserva activa por puerto
);

-- Tabla para auditoría de validaciones
CREATE TABLE capacity_audit (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    operation_type ENUM('VALIDATE', 'RESERVE', 'RELEASE') NOT NULL,
    node_id VARCHAR(50),
    cto_id VARCHAR(50),
    port_id VARCHAR(50),
    order_id VARCHAR(100),
    bandwidth_requested INTEGER,
    capacity_available BOOLEAN,
    ports_recommended INTEGER,
    requester_id VARCHAR(100) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_created (created_at)
);

-- Tabla para métricas de utilización
CREATE TABLE capacity_metrics (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    total_capacity_mbps INTEGER NOT NULL,
    used_capacity_mbps INTEGER NOT NULL,
    active_services INTEGER NOT NULL,
    available_ports INTEGER NOT NULL,
    reserved_ports INTEGER NOT NULL,
    INDEX idx_node_timestamp (node_id, timestamp),
    INDEX idx_timestamp (timestamp)
);
```

## Features y Escenarios Cubiertos

### RF04 - Validar capacidad técnica
- **RF04-ESC01**: Ejecución exitosa de validación
- **RF04-ESC02**: Solicitud inválida por datos incompletos
- **RF04-ESC03**: Sistema Oracle no disponible
- **RF04-ESC04**: Consumidor no autorizado

### Escenarios Adicionales
- **CAP-ESC01**: Nodo sin capacidad suficiente
- **CAP-ESC02**: CTO con puertos agotados
- **CAP-ESC03**: Reserva temporal exitosa
- **CAP-ESC04**: Liberación automática por expiración
- **CAP-ESC05**: Conflicto de reserva simultánea

## Lineamientos Cubiertos

### ARQ-03: Responsabilidad bien definida
- Microservicio enfocado en validación de capacidad técnica
- Gestión completa del ciclo de vida de reservas

### ESC-03: Escalamiento horizontal
- Cache local para reducir consultas a Oracle
- Procesamiento paralelo de validaciones múltiples

### ESC-06: Prevención de cuellos de botella
- Límites de concurrencia en consultas Oracle
- Cache con TTL para datos de capacidad

### SEG-07: Auditoría completa
- Registro de todas las operaciones de validación y reserva
- Trazabilidad de cambios de estado de puertos

### INT-06: Operaciones idempotentes
- Reservas pueden ser reinvocadas sin duplicación
- Liberación segura de reservas ya expiradas

### OBS-03: Métricas técnicas y de negocio
- Captura de latencia, throughput y errores
- Métricas de utilización de nodos y puertos

### INT-14: Adaptadores especializados
- Abstracción del modelo Oracle mediante adaptador
- Transformación a modelo canónico de capacidad