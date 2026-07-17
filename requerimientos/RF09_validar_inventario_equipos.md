# RF09 - Validar inventario de equipos para instalación

## Historia de usuario
Como coordinador de instalaciones,
quiero validar la disponibilidad de equipos (ONT, router) antes de programar una instalación,
para evitar visitas fallidas por falta de equipos en el almacén asignado.

## Requerimientos funcionales
- La plataforma debe cumplir la funcionalidad de validar inventario de equipos mediante la Plataforma de Integración Empresarial.
- La funcionalidad debe operar mediante contratos explícitos de entrada, salida y errores.
- La funcionalidad debe evitar integraciones punto a punto entre sistemas core.
- La funcionalidad debe registrar evidencias de intercambio y resultado operativo.
- La funcionalidad debe propagar correlationId en todo el flujo.

## Requerimientos técnicos
- Exponer API REST versionada cuando aplique.
- Recibir y retornar mensajes JSON cuando aplique.
- Documentar contratos mediante OpenAPI.
- Registrar sistema origen, sistema destino, canal, fecha, resultado, error y tiempo de respuesta.
- Publicar o consumir eventos cuando el flujo sea asíncrono.

## Requerimientos no funcionales
- Seguridad: autenticación, autorización, cifrado en tránsito y protección de datos sensibles.
- Observabilidad: logs estructurados, métricas y trazabilidad end-to-end.
- Disponibilidad: diseño para disponibilidad objetivo de 99.9% en servicios críticos de integración.
- Escalabilidad: crecimiento progresivo mediante escalamiento horizontal, desacoplamiento y control de concurrencia.
- Optimización de costos: uso eficiente de recursos administrados, capacidad bajo demanda o infraestructura compartida.
- Performance: validación de inventario en máximo 5 segundos.

## Criterios de aceptación
- CA01: Dado un consumidor autorizado, cuando ejecute la funcionalidad, entonces la solicitud debe procesarse mediante la Plataforma de Integración Empresarial.
- CA02: Dado un flujo válido, cuando la operación finalice, entonces debe generarse respuesta funcional conforme al contrato.
- CA03: Dado un error funcional o técnico, cuando ocurra la falla, entonces la plataforma debe responder con error controlado y registrar trazabilidad.
- CA04: Dado un consumidor no autorizado, cuando intente ejecutar la funcionalidad, entonces la solicitud debe ser rechazada.
- CA05: Dada una transacción procesada, cuando se consulte su trazabilidad, entonces debe poder encontrarse por correlationId.
- CA06: Dada una validación de inventario, cuando se procese, entonces debe completarse en máximo 5 segundos.

## Escenarios Gherkin

```gherkin
Feature: Validar inventario de equipos para instalación

Scenario: Validación exitosa de disponibilidad de equipos
  Given que el consumidor está autorizado
  And la solicitud contiene plan de servicio y almacén válidos
  When se ejecuta la validación de inventario de equipos
  Then debe consultar el ERP on-premises para equipos requeridos
  And debe verificar disponibilidad de ONT compatible con el plan
  And debe verificar disponibilidad de router según especificaciones
  And debe retornar cantidad disponible por tipo de equipo
  And debe incluir almacenes alternativos si hay faltante
  And debe registrar la consulta con correlationId

Scenario: Reserva de equipos para orden de instalación
  Given que existe disponibilidad de equipos requeridos
  And la orden de instalación está programada
  When se ejecuta la reserva de equipos
  Then debe marcar los equipos como reservados en el ERP
  And debe vincular los equipos a la orden de instalación
  And debe reducir el stock disponible temporalmente
  And debe establecer fecha límite de reserva (48 horas)
  And debe registrar la reserva con correlationId

Scenario: Liberación automática de equipos reservados
  Given que equipos están reservados para una instalación
  And han transcurrido 48 horas sin confirmación de instalación
  When se ejecuta la liberación automática
  Then debe liberar la reserva de equipos en el ERP
  And debe incrementar nuevamente el stock disponible
  And debe notificar la liberación al coordinador
  And debe registrar la liberación con correlationId

Scenario: Confirmación de instalación y baja de equipos
  Given que el técnico confirma instalación exitosa
  And reporta números de serie de equipos instalados
  When se procesa la confirmación
  Then debe dar de baja los equipos del inventario ERP
  And debe marcar los equipos como instalados y vinculados al cliente
  And debe actualizar el registro de equipos en el OSS
  And debe generar trazabilidad de equipo instalado
  And debe registrar la instalación con correlationId

Scenario: Equipos insuficientes en almacén asignado
  Given que se valida inventario para una instalación
  And el almacén asignado no tiene equipos suficientes
  When se procesa la validación
  Then debe consultar almacenes alternativos en la zona
  And debe calcular distancia y tiempo de traslado de equipos
  And debe sugerir reprogramación si no hay alternativas viables
  And debe registrar la consulta y alternativas con correlationId

Scenario: Transferencia de equipos entre almacenes
  Given que se requieren equipos no disponibles en almacén local
  And existe disponibilidad en almacén alternativo
  When se solicita transferencia de equipos
  Then debe generar orden de transferencia en el ERP
  And debe actualizar inventarios de origen y destino
  And debe estimar tiempo de llegada de equipos
  And debe notificar cuando equipos estén disponibles para instalación

Scenario: Validación de compatibilidad de equipos con plan
  Given que se consulta inventario para un plan específico
  When se ejecuta la validación
  Then debe verificar que ONT soporte la velocidad del plan contratado
  And debe validar que router tenga características WiFi requeridas
  And debe confirmar compatibilidad con tecnología de red (GPON/XGS-PON)
  And debe rechazar equipos incompatibles con especificaciones del plan

Scenario: Error de conectividad con ERP de inventario
  Given que se solicita validar inventario de equipos
  And el ERP on-premises no está disponible
  When se ejecuta la validación
  Then debe retornar error controlado con código específico
  And debe registrar el error y tiempo de no disponibilidad
  And debe sugerir reprogramación de validación
  And no debe procesar reservas hasta restaurar conectividad
```