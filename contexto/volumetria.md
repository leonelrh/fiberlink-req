# Volumetría - FiberLink Andina Telecom

## Contexto de uso
La Plataforma de Integración Empresarial será consumida por Portal de Clientes, App Móvil, Call Center, CRM, OSS/OCS, Facturación y componentes de observabilidad/analítica.

## Volumetría estimada
- 1.9 millones de clientes residenciales.
- 46,000 clientes empresariales.
- 12,000 nodos activos.
- 14,500 km de fibra.
- 150,000 consultas de cobertura por día.
- 80,000 validaciones de capacidad por día.
- 40,000 solicitudes de servicio por día.
- 20,000 consultas de estado de servicio por día.
- 60% de las transacciones son consultas.
- 40% de las transacciones generan escritura, evento o auditoría.
- Hora pico estimada: 4 veces el promedio.
- Cada evento ocupa entre 2 KB y 5 KB.
- Cada registro de auditoría ocupa entre 1 KB y 3 KB.

## Implicancias arquitectónicas
- Debe existir escalamiento horizontal en componentes de integración.
- Las consultas frecuentes pueden optimizarse con caché cuando no comprometan consistencia.
- Las operaciones diferibles deben procesarse de forma asíncrona.
- La trazabilidad debe permitir búsqueda por correlationId.
- La arquitectura debe soportar crecimiento gradual sin rediseño completo.
