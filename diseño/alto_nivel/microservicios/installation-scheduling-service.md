# Installation Scheduling Service (Servicio de Programación de Instalaciones)

## Funcionalidades

### 1. Reprogramar Instalación de Servicio
- **Descripción**: Permite al cliente reprogramar la fecha de instalación con validaciones
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "rescheduleRequest": {
      "orderId": "string",
      "customerId": "string",
      "newSchedule": {
        "preferredDate": "string", // YYYY-MM-DD
        "timeSlot": "string", // "MORNING" | "AFTERNOON" | "EVENING"
        "specificTime": "string" // "HH:MM" opcional
      },
      "reason": "string",
      "requestSource": "string" // "CUSTOMER_PORTAL" | "CALL_CENTER" | "MOBILE_APP"
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "rescheduleResult": {
      "success": "boolean",
      "newSchedule": {
        "installationDate": "string",
        "timeSlot": "string",
        "estimatedArrival": "string",
        "technicianTeam": {
          "teamId": "string",
          "leadTechnician": "string",
          "contactPhone": "string"
        }
      },
      "previousSchedule": {
        "date": "string",
        "timeSlot": "string"
      },
      "resourcesReallocated": {
        "equipmentReserved": "boolean",
        "materialsAllocated": "boolean",
        "routeOptimized": "boolean"
      },
      "confirmationSent": "boolean",
      "errorMessage": "string" // Si success = false
    }
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ReprogramarInstalacion
    1. VALIDAR precondiciones:
       a. VERIFICAR que orden existe y está en estado "PROGRAMADA"
       b. VALIDAR que solicitud se hace con >24h anticipación
       c. CONFIRMAR que cliente está autorizado
    2. VERIFICAR disponibilidad en nueva fecha:
       a. CONSULTAR SaaS field service para cuadrillas disponibles
       b. VERIFICAR disponibilidad de equipos reservados
       c. VALIDAR capacidad de puerto aún disponible
    3. SI nueva fecha es viable:
       a. LIBERAR recursos de fecha anterior
       b. RESERVAR recursos para nueva fecha
       c. ACTUALIZAR orden de instalación en Azure SQL
       d. OPTIMIZAR rutas de cuadrilla técnica
    4. ENVIAR confirmación al cliente:
       a. GENERAR notificación personalizada
       b. ACTUALIZAR datos en CRM
       c. PROGRAMAR recordatorio 24h antes
    5. REGISTRAR reprogramación en auditoría
  END
  ```

### 2. Validar Disponibilidad de Cuadrilla
- **Descripción**: Consulta disponibilidad de técnicos para fechas específicas
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "availabilityQuery": {
      "zone": "string",
      "dateRange": {
        "from": "string",
        "to": "string"
      },
      "serviceType": "string", // "RESIDENTIAL" | "ENTERPRISE"
      "timeSlots": ["string"], // ["MORNING", "AFTERNOON", "EVENING"]
      "skillsRequired": ["string"] // ["FIBER_SPLICE", "GPON_CONFIG", "ENTERPRISE_SETUP"]
    }
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "availability": [
      {
        "date": "string",
        "timeSlot": "string",
        "availableTeams": [
          {
            "teamId": "string",
            "capacity": "number", // Instalaciones simultáneas posibles
            "currentLoad": "number",
            "skills": ["string"],
            "averageCompletionTime": "number" // minutos
          }
        ],
        "recommendedSlot": "boolean"
      }
    ]
  }
  ```

### 3. Optimizar Rutas de Instalación
- **Descripción**: Optimiza rutas diarias de cuadrillas para minimizar tiempos de traslado
- **Algoritmo**:
  ```
  BEGIN OptimizarRutas
    1. OBTENER instalaciones programadas por cuadrilla y fecha
    2. PARA cada cuadrilla:
       a. OBTENER coordenadas de todas las instalaciones asignadas
       b. CALCULAR matriz de distancias y tiempos
       c. APLICAR algoritmo de optimización de rutas (TSP)
       d. CONSIDERAR restricciones de ventanas horarias
    3. GENERAR ruta optimizada:
       a. MINIMIZAR tiempo total de traslado
       b. RESPETAR franjas horarias prometidas
       c. CONSIDERAR tiempo estimado por instalación
    4. ACTUALIZAR secuencia en sistema de field service
    5. NOTIFICAR cambios a coordinadores y técnicos
  END
  ```

## Estructura de Base de Datos

```sql
-- Tabla para órdenes de instalación
CREATE TABLE installation_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    service_type ENUM('RESIDENTIAL', 'ENTERPRISE') NOT NULL,
    current_status ENUM('CREATED', 'SCHEDULED', 'RESCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') NOT NULL,
    installation_address TEXT NOT NULL,
    coordinates_lat DECIMAL(10,8),
    coordinates_lng DECIMAL(11,8),
    plan_contracted VARCHAR(100) NOT NULL,
    equipment_required JSON NOT NULL,
    materials_needed JSON NOT NULL,
    special_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (current_status),
    INDEX idx_coordinates (coordinates_lat, coordinates_lng),
    INDEX idx_created (created_at)
);

-- Tabla para programaciones de instalación
CREATE TABLE installation_schedules (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL,
    schedule_version INTEGER NOT NULL DEFAULT 1,
    scheduled_date DATE NOT NULL,
    time_slot ENUM('MORNING', 'AFTERNOON', 'EVENING', 'SPECIFIC') NOT NULL,
    specific_time TIME NULL,
    estimated_duration INTEGER NOT NULL, -- minutos
    team_id VARCHAR(50) NOT NULL,
    lead_technician_id VARCHAR(50) NOT NULL,
    status ENUM('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') NOT NULL,
    zone VARCHAR(50) NOT NULL,
    route_sequence INTEGER NULL, -- Orden en la ruta diaria
    estimated_arrival TIME NULL,
    actual_arrival TIME NULL,
    completion_time TIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id),
    INDEX idx_scheduled_date (scheduled_date),
    INDEX idx_team_id (team_id),
    INDEX idx_status (status),
    FOREIGN KEY (order_id) REFERENCES installation_orders(order_id)
);

-- Tabla para historial de reprogramaciones
CREATE TABLE reschedule_history (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    previous_date DATE NOT NULL,
    previous_time_slot VARCHAR(20) NOT NULL,
    new_date DATE NOT NULL,
    new_time_slot VARCHAR(20) NOT NULL,
    reason_code VARCHAR(50) NOT NULL,
    reason_description TEXT,
    requested_by VARCHAR(100) NOT NULL,
    request_source ENUM('CUSTOMER_PORTAL', 'CALL_CENTER', 'MOBILE_APP', 'TECHNICIAN', 'SYSTEM') NOT NULL,
    advance_notice_hours INTEGER NOT NULL,
    resources_impact JSON, -- Equipos, rutas, etc. afectados
    approval_required BOOLEAN NOT NULL,
    approved_by VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_order_id (order_id),
    INDEX idx_request_source (request_source),
    INDEX idx_created (created_at)
);

-- Tabla para disponibilidad de cuadrillas
CREATE TABLE team_availability (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(50) NOT NULL,
    available_date DATE NOT NULL,
    time_slot ENUM('MORNING', 'AFTERNOON', 'EVENING') NOT NULL,
    max_capacity INTEGER NOT NULL, -- Instalaciones simultáneas
    current_bookings INTEGER NOT NULL DEFAULT 0,
    available_capacity INTEGER GENERATED ALWAYS AS (max_capacity - current_bookings),
    zone VARCHAR(50) NOT NULL,
    skills_available JSON NOT NULL, -- ["FIBER_SPLICE", "GPON_CONFIG", etc.]
    team_status ENUM('AVAILABLE', 'BUSY', 'MAINTENANCE', 'OFF_DUTY') NOT NULL DEFAULT 'AVAILABLE',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, available_date, time_slot),
    INDEX idx_available_date (available_date),
    INDEX idx_zone (zone),
    INDEX idx_available_capacity (available_capacity)
);

-- Tabla para optimización de rutas
CREATE TABLE daily_routes (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(100) UNIQUE NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    route_date DATE NOT NULL,
    zone VARCHAR(50) NOT NULL,
    total_installations INTEGER NOT NULL,
    estimated_total_time INTEGER NOT NULL, -- minutos
    estimated_travel_time INTEGER NOT NULL, -- minutos
    optimization_algorithm VARCHAR(50) NOT NULL, -- TSP, GENETIC, etc.
    route_efficiency_score DECIMAL(5,2), -- 0-100
    route_status ENUM('DRAFT', 'OPTIMIZED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED') NOT NULL,
    route_coordinates JSON, -- Secuencia optimizada de coordenadas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_team_date (team_id, route_date),
    INDEX idx_route_date (route_date),
    INDEX idx_status (route_status)
);

-- Tabla para métricas de programación
CREATE TABLE scheduling_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    total_orders_scheduled INTEGER NOT NULL,
    total_reschedules INTEGER NOT NULL,
    reschedule_rate DECIMAL(5,2) NOT NULL, -- Porcentaje
    avg_advance_notice_hours DECIMAL(5,2) NOT NULL,
    same_day_reschedules INTEGER NOT NULL,
    customer_initiated_reschedules INTEGER NOT NULL,
    system_initiated_reschedules INTEGER NOT NULL,
    avg_route_efficiency DECIMAL(5,2) NOT NULL,
    total_travel_time_saved INTEGER NOT NULL, -- minutos
    PRIMARY KEY (metric_date),
    INDEX idx_metric_date (metric_date)
);
```

## Features y Escenarios Cubiertos

### RF10 - Reprogramar instalación servicio internet
- **RF10-ESC01**: Reprogramación exitosa
- **RF10-ESC02**: Rechazo por solicitud fuera de plazo
- **RF10-ESC03**: Rechazo por orden en estado no reprogramable
- **RF10-ESC04**: Rechazo por falta de disponibilidad
- **RF10-ESC05**: Error técnico durante reprogramación

### Escenarios Adicionales
- **SCH-ESC01**: Optimización automática de rutas diarias
- **SCH-ESC02**: Reasignación por disponibilidad de equipos
- **SCH-ESC03**: Reprogramación masiva por eventos climáticos
- **SCH-ESC04**: Validación de capacidad técnica antes de programar
- **SCH-ESC05**: Notificaciones automáticas de confirmación

## Lineamientos Cubiertos

### ARQ-03: Responsabilidad bien definida
- Microservicio enfocado en programación y reprogramación
- Gestión integral del ciclo de vida de instalaciones

### INT-12: Consideración de sistemas on-premises
- Integración con SaaS de field service externo
- Manejo de latencia en sincronización con Azure SQL

### ESC-05: Operaciones asíncronas
- Optimización de rutas en background
- Notificaciones diferidas a clientes y técnicos

### OBS-02: Trazabilidad end-to-end
- Correlación completa desde solicitud hasta confirmación
- Visibilidad de impacto en recursos y rutas

### SEG-04: Autenticación centralizada
- Validación de autorización por canal (portal, app, call center)
- Tokens específicos por tipo de usuario

### INT-01: APIs versionadas
- Contratos estables para integraciones con portales
- Documentación OpenAPI completa

### ESC-10: Degradación controlada
- Continúa operando con disponibilidad parcial de cuadrillas
- Fallback a programación manual cuando optimización falla