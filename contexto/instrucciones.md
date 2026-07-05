# Instrucciones para Kiro - FiberLink Andina Telecom

## Rol / Persona
Actúa como un Arquitecto de Solución experto en arquitectura empresarial, integración OSS/BSS, soluciones multinube y diseño de microservicios.

## Contexto
FiberLink Andina Telecom es una empresa de telecomunicaciones que brinda servicios de Internet residencial por fibra óptica. La empresa opera con una arquitectura híbrida y multinube, donde conviven sistemas on premises, SaaS y servicios en AWS, Azure y Google Cloud.

Actualmente existen problemas de integración entre CRM, Inventario Oracle, OSS/OCS, Facturación, Portal de Clientes y Mesa de Ayuda. Esto genera ventas sin capacidad real, aprovisionamiento inconsistente, activaciones incompletas, errores de facturación, baja trazabilidad y dificultad para atender incidentes.

## Iniciativa a diseñar
Iniciativa 1: Plataforma de Integración Empresarial.

Esta iniciativa busca integrar los sistemas críticos de FiberLink mediante APIs, eventos y trazabilidad end-to-end, reduciendo integraciones punto a punto y habilitando procesos comerciales, operacionales y financieros más consistentes.

## Tarea / Objetivo
Diseñar la solución de la Plataforma de Integración Empresarial considerando:

- Todos los requerimientos de la carpeta `requerimientos`.
- Todos los lineamientos de la carpeta `lineamientos`.
- La volumetría del archivo `volumetria.md`.
- El contexto de negocio de FiberLink.
- La necesidad de ejecutar una solución viable en un entorno multinube con AWS, Azure y Google Cloud.
- La separación entre arquitectura empresarial, arquitectura lógica, arquitectura de microservicios y arquitectura de despliegue.

## Pasos solicitados

### 1. Diseño de microservicios
Crea una carpeta `diseño/alto_nivel/microservicios`.

Por cada microservicio incluye:
- Nombre.
- Responsabilidad principal.
- Funcionalidades.
- Requerimientos funcionales y no funcionales que cubre.
- Lineamientos aplicados con código y descripción.
- Contratos de entrada y salida.
- Eventos que publica o consume.
- Modelo de datos sugerido con SQL cuando aplique.
- Pseudocódigo.
- Escenarios Gherkin cubiertos.

### 2. Diagramas de secuencia
Crea `diseño/alto_nivel/diagramas_secuencia` y genera un diagrama Mermaid por cada archivo de requerimientos.

### 3. Diagrama de arquitectura lógica
Crea `diseño/alto_nivel/diagrama_arquitectura_logica.md` con canales, API Management, Hub de Integración, Broker de Eventos, sistemas core, observabilidad, seguridad y trazabilidad.

### 4. Diagrama de arquitectura multinube
Crea `diseño/alto_nivel/diagrama_arquitectura_multinube.md` considerando AWS, Azure, GCP y On Premises simulado.

### 5. Contratos OpenAPI
Crea `diseño/alto_nivel/openapi` con contratos para cobertura, capacidad, solicitud de servicio, estado de servicio y trazabilidad.

### 6. Decisiones de diseño
Crea `diseño/alto_nivel/decisiones_diseño.md` con decisiones, criterios, alternativas descartadas, riesgos, supuestos, modelo LLM usado y fecha.

## Restricciones
- No diseñar integraciones punto a punto entre sistemas core.
- No incluir secretos en código ni archivos planos.
- No exponer datos sensibles en logs ni eventos.
- Mantener trazabilidad entre requerimientos, escenarios, microservicios y diagramas.