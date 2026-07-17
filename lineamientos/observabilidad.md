## Lineamientos de Observabilidad

Objetivos:
- Busca que la aplicación pueda monitorearse, diagnosticarse y operarse bien.
- Responde a: ¿Cómo sabremos qué pasó, dónde falló y cómo corregirlo?

Lineamientos:
- OBS-01: Todo componente debe emitir logs estructurados.
- OBS-02: Toda transacción crítica debe poder rastrearse mediante correlationId o traceId.
- OBS-03: Deben capturarse métricas técnicas y de negocio.
- OBS-04: Deben definirse alertas para disponibilidad, errores, latencia, saturación y fallos de publicación de eventos.
- OBS-05: Los logs no deben exponer datos sensibles.
- OBS-06: Las trazas distribuidas deben cubrir el flujo end-to-end entre canales, APIs, integración y sistemas core.
- OBS-07: Deben existir dashboards operativos para soporte, NOC, operación y arquitectura.
