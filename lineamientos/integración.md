## Lineamientos de Integración

Objetivos:
- Asegurar que FiberLink conecte sus sistemas críticos de forma confiable, trazable y desacoplada.
- Reemplazar gradualmente integraciones punto a punto, procesos batch frágiles y dependencias directas entre sistemas.
- Habilitar integración síncrona para consultas y asíncrona para eventos de negocio.

Lineamientos:
- INT-01: Las integraciones síncronas deben exponerse mediante APIs versionadas, documentadas y gobernadas.
- INT-02: Las integraciones asíncronas deben desacoplarse mediante eventos, colas o mensajería.
- INT-03: Las llamadas remotas deben manejar timeouts, reintentos controlados y circuit breaker cuando aplique.
- INT-04: Toda API debe tener contratos claros de entrada, salida, errores, códigos HTTP y ejemplos.
- INT-05: Los cambios incompatibles deben publicarse como nuevas versiones de API o evento.
- INT-06: Las integraciones críticas deben ser idempotentes cuando puedan recibir reintentos o mensajes duplicados.
- INT-07: Debe minimizarse el acoplamiento directo entre sistemas core; CRM, Inventario, OSS/OCS y Facturación no deben integrarse directamente entre sí para nuevos flujos.
- INT-08: Deben registrarse evidencias de intercambio para trazabilidad, auditoría y soporte.
- INT-09: Todo evento debe incluir eventId, eventType, version, correlationId, sourceSystem, timestamp y payload.
- INT-10: La Plataforma de Integración debe validar formato, obligatoriedad y consistencia mínima antes de invocar sistemas core.
- INT-11: La Plataforma de Integración debe permitir reproceso controlado de eventos fallidos.
- INT-12: Las integraciones con sistemas on premises deben considerar latencia, indisponibilidad parcial y degradación controlada.