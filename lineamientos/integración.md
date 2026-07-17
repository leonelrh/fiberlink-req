## Lineamientos de Integración

Objetivos:
- Busca que la aplicación se conecte correctamente con otros sistemas.
- Responde a: ¿Cómo se comunica la aplicación con otros sistemas de forma confiable?

Lineamientos:
- INT-01: Las integraciones síncronas deben exponerse mediante APIs versionadas, documentadas y gobernadas.
- INT-02: Las integraciones asíncronas deben desacoplarse mediante eventos, colas o mensajería.
- INT-03: Las llamadas remotas deben manejar timeouts, reintentos controlados y circuit breaker cuando aplique.
- INT-04: Toda API debe tener contratos claros de entrada, salida, errores, códigos HTTP y ejemplos.
- INT-05: Los cambios incompatibles deben publicarse como nuevas versiones de API o evento.
- INT-06: Las integraciones críticas deben ser idempotentes cuando puedan recibir reintentos o mensajes duplicados.
- INT-07: Debe minimizarse el acoplamiento directo entre sistemas core; CRM, Inventario, OSS/OCS y Facturación no deben integrarse directamente entre sí para nuevos flujos.
- INT-08: Deben registrarse evidencias de intercambio para trazabilidad, auditoría y soporte.
