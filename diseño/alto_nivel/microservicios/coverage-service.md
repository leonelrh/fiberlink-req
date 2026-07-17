# Coverage Service (Servicio de Cobertura)

## Funcionalidades

### 1. Consultar Cobertura por Dirección
- **Descripción**: Valida si existe cobertura de fibra óptica en una dirección específica
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "address": {
      "street": "string",
      "number": "string",
      "neighborhood": "string",
      "city": "string",
      "coordinates": {
        "latitude": "number",
        "longitude": "number"
      }
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**:
  ```json
  {
    "correlationId": "string",
    "coverage": {
      "available": "boolean",
      "technology": "string", // "GPON" | "XGS-PON"
      "maxSpeed": "number", // Mbps
      "nodeId": "string",
      "ctoId": "string",
      "estimatedDistance": "number" // metros
    },
    "responseTime": "string"
  }
  ```
- **Algoritmo**:
  ```
  BEGIN ConsultarCobertura
    1. VALIDAR formato de dirección y coordenadas
    2. NORMALIZAR dirección según estándares GIS
    3. CONSULTAR inventario Oracle para nodos cercanos (radio 500m)
    4. PARA cada nodo encontrado:
       a. VERIFICAR estado activo del nodo
       b. CONSULTAR CTOs disponibles en el nodo
       c. CALCULAR distancia desde coordenadas a CTO
    5. SI existen CTOs disponibles:
       a. DETERMINAR tecnología (GPON/XGS-PON)
       b. CALCULAR velocidad máxima soportada
       c. RETORNAR cobertura disponible
    6. SINO:
       a. RETORNAR cobertura no disponible
    7. REGISTRAR auditoría de consulta
  END
  ```

### 2. Validar Cobertura por Coordenadas
- **Descripción**: Consulta cobertura usando únicamente coordenadas GPS
- **Contrato de Entrada**:
  ```json
  {
    "correlationId": "string",
    "coordinates": {
      "latitude": "number",
      "longitude": "number"
    },
    "requesterId": "string"
  }
  ```
- **Contrato de Salida**: Similar al anterior
- **Algoritmo**:
  ```
  BEGIN ValidarCoberturaCoordenadas
    1. VALIDAR formato de coordenadas GPS
    2. CONSULTAR mapas GIS heredados para zona
    3. IDENTIFICAR nodos dentro del radio de cobertura
    4. APLICAR mismo flujo de consulta que por dirección
  END
  ```

## Estructura de Base de Datos

```sql
-- Tabla para caché de consultas frecuentes
CREATE TABLE coverage_cache (
    id SERIAL PRIMARY KEY,
    address_hash VARCHAR(64) UNIQUE NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    node_id VARCHAR(50),
    cto_id VARCHAR(50),
    coverage_available BOOLEAN NOT NULL,
    technology VARCHAR(20),
    max_speed INTEGER,
    estimated_distance INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_coordinates (latitude, longitude),
    INDEX idx_address_hash (address_hash),
    INDEX idx_expires (expires_at)
);

-- Tabla para registro de auditoría
CREATE TABLE coverage_audit (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    requester_id VARCHAR(100) NOT NULL,
    request_type ENUM('ADDRESS', 'COORDINATES') NOT NULL,
    address_requested TEXT,
    coordinates_lat DECIMAL(10,8),
    coordinates_lng DECIMAL(11,8),
    coverage_found BOOLEAN NOT NULL,
    node_id VARCHAR(50),
    cto_id VARCHAR(50),
    response_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_correlation (correlation_id),
    INDEX idx_requester (requester_id),
    INDEX idx_created (created_at)
);

-- Tabla para gestión de errores
CREATE TABLE coverage_errors (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Features y Escenarios Cubiertos

### RF03 - Consultar cobertura
- **RF03-ESC01**: Ejecución exitosa de consulta por dirección
- **RF03-ESC02**: Solicitud inválida por datos incompletos
- **RF03-ESC03**: Sistema Oracle no disponible
- **RF03-ESC04**: Consumidor no autorizado

### Escenarios Adicionales
- **COV-ESC01**: Consulta con caché válido (optimización de performance)
- **COV-ESC02**: Consulta en zona sin cobertura
- **COV-ESC03**: Múltiples CTOs disponibles (selección óptima)
- **COV-ESC04**: Degradación por latencia alta a Oracle

## Lineamientos Cubiertos

### ARQ-03: Responsabilidad bien definida
- Microservicio enfocado exclusivamente en consultas de cobertura
- Separación clara entre validación y consulta de inventario

### INT-01: APIs versionadas y documentadas
- Contratos explícitos de entrada y salida
- Documentación OpenAPI integrada

### SEG-04: Autenticación centralizada
- Validación de tokens JWT en cada consulta
- Integración con plataforma de seguridad transversal

### ESC-04: Caché para lecturas frecuentes
- Implementación de caché con TTL configurable
- Reducción de carga en inventario Oracle

### OBS-02: Trazabilidad end-to-end
- Propagación de correlationId en todo el flujo
- Registro completo en auditoría

### INT-13: Modelo canónico
- Adaptación entre modelo de consulta y modelo Oracle
- Normalización de respuestas independiente del sistema origen