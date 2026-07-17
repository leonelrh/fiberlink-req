# RF06 - Sincronizar inventario de puertos en tiempo real

## Historia de usuario
Como técnico de instalación,
quiero que el puerto asignado esté verificado y disponible al momento de llegar al domicilio,
para evitar visitas fallidas por puertos inexistentes u ocupados.

## Requerimientos funcionales
- La plataforma debe cumplir la funcionalidad de sincronizar estado de puertos entre sistemas mediante la Plataforma de Integración Empresarial.
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
- Performance: sincronización de estado de puerto en máximo 2 minutos.

## Criterios de aceptación
- CA01: Dado un consumidor autorizado, cuando ejecute la funcionalidad, entonces la solicitud debe procesarse mediante la Plataforma de Integración Empresarial.
- CA02: Dado un flujo válido, cuando la operación finalice, entonces debe generarse respuesta funcional conforme al contrato.
- CA03: Dado un error funcional o técnico, cuando ocurra la falla, entonces la plataforma debe responder con error controlado y registrar trazabilidad.
- CA04: Dado un consumidor no autorizado, cuando intente ejecutar la funcionalidad, entonces la solicitud debe ser rechazada.
- CA05: Dada una transacción procesada, cuando se consulte su trazabilidad, entonces debe poder encontrarse por correlationId.
- CA06: Dado un puerto reservado, cuando se confirme la instalación, entonces el estado debe actualizarse en máximo 2 minutos en todos los sistemas.

## Escenarios Gherkin

```gherkin
Feature: Sincronizar inventario de puertos

Scenario: Reserva exitosa de puerto
  Given que el consumidor está autorizado
  And la solicitud contiene datos válidos de puerto disponible
  When se ejecuta la reserva del puerto
  Then la Plataforma de Integración debe procesar la solicitud
  And debe marcar el puerto como reservado en el inventario Oracle
  And debe actualizar el estado en el sistema OSS
  And debe registrar la trazabilidad con correlationId
  And la sincronización debe completarse en máximo 2 minutos

Scenario: Liberación de puerto por cancelación
  Given que existe un puerto reservado para una orden
  And la orden de instalación es cancelada
  When se ejecuta la liberación del puerto
  Then el puerto debe marcarse como disponible en inventario Oracle
  And debe actualizarse el estado en el sistema OSS
  And debe registrar la liberación con correlationId
  And debe notificar la disponibilidad a sistemas interesados

Scenario: Confirmación de instalación exitosa
  Given que un puerto está reservado para instalación
  And el técnico confirma la instalación exitosa
  When se ejecuta la confirmación de instalación
  Then el puerto debe marcarse como ocupado/instalado en inventario
  And debe vincularse al cliente y contrato en el OSS
  And debe actualizarse el inventario de equipos
  And debe registrar la instalación con correlationId

Scenario: Detección de discrepancia de estado
  Given que el sistema ejecuta conciliación periódica
  And detecta un puerto marcado como disponible en inventario pero ocupado en OSS
  When se procesa la discrepancia
  Then debe generar una alerta de inconsistencia
  And debe registrar la discrepancia en el log de auditoría
  And debe marcar el puerto para revisión manual

Scenario: Puerto no disponible durante reserva
  Given que se solicita reservar un puerto
  And el puerto ya está ocupado o reservado
  When se ejecuta la reserva
  Then debe rechazar la solicitud con error controlado
  And debe sugerir puertos alternativos disponibles en la misma CTO
  And debe registrar el intento fallido con correlationId
```