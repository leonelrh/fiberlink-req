## Lineamientos de Observabilidad

Objetivos:
- Permitir monitorear, diagnosticar y operar la Plataforma de Integración Empresarial.
- Dar visibilidad end-to-end sobre consultas, eventos, errores, latencia e indisponibilidad de sistemas.
- Reducir tiempos de diagnóstico y mejorar soporte a clientes y operación.

Lineamientos:
- OBS-01: Todo componente debe emitir logs estructurados.
- OBS-02: Toda transacción crítica debe poder rastrearse mediante correlationId o traceId.
- OBS-03: Deben capturarse métricas técnicas y de negocio.
- OBS-04: Deben definirse alertas para disponibilidad, errores, latencia, saturación y fallos de publicación de eventos.
- OBS-05: Los logs no deben exponer datos sensibles.
- OBS-06: Las trazas distribuidas deben cubrir el flujo end-to-end entre canales, APIs, integración y sistemas core.
- OBS-07: Deben existir dashboards operativos para soporte, NOC, operación y arquitectura.
- OBS-08: Cada evento publicado debe poder correlacionarse con la transacción que lo generó.
- OBS-09: Las fallas de integración deben clasificarse por tipo: validación, autenticación, timeout, indisponibilidad, error funcional y error técnico.
- OBS-10: La plataforma debe permitir búsqueda por correlationId, sistema origen, sistema destino, cliente, servicio y rango de fechas.
