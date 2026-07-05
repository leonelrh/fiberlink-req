## Lineamientos de Seguridad

Objetivos:
- Proteger APIs, datos, eventos e integraciones de FiberLink.
- Reducir exposición de portales, plataformas OSS/BSS, sistemas on premises y servicios multinube.
- Aplicar seguridad desde el diseño.

Lineamientos:
- SEG-01: Toda comunicación entre componentes debe usar cifrado en tránsito mediante TLS 1.2 o superior.
- SEG-02: La información sensible debe almacenarse con cifrado en reposo cuando aplique.
- SEG-03: La autenticación debe centralizarse usando OAuth2, OpenID Connect, JWT o proveedor corporativo equivalente.
- SEG-04: La autorización debe aplicar mínimo privilegio por rol, sistema consumidor y tipo de operación.
- SEG-05: No se deben almacenar secretos en código fuente ni en archivos de configuración planos.
- SEG-06: Todas las operaciones críticas deben dejar registro de auditoría.
- SEG-07: Las APIs públicas o expuestas a canales deben protegerse con validación de entrada, rate limiting y WAF cuando aplique.
- SEG-08: Deben aplicarse prácticas de desarrollo seguro y análisis de vulnerabilidades sobre dependencias, imágenes y plantillas IaC.
- SEG-09: Los eventos no deben incluir datos personales o sensibles que no sean necesarios para el proceso.
- SEG-10: Las integraciones con sistemas on premises deben realizarse mediante canales seguros y controlados.
- SEG-11: Las credenciales técnicas deben rotarse y gestionarse mediante servicios de secretos o mecanismos corporativos equivalentes.
- SEG-12: Los accesos administrativos deben quedar auditados.
