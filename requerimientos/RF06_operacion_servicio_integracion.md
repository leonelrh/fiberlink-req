```gherkin
Feature: Integración de fuentes de red al bus de eventos
  Como ingeniero de red del NOC
  Quiero integrar los NMS regionales, los logs de red y el inventario al bus de eventos
  Para lograr una ingesta normalizada de extremo a extremo que habilite la correlación de incidentes

  # Escenarios positivos

  Scenario: Integración exitosa de un NMS regional al bus de eventos
    Given que un NMS regional está registrado como fuente de datos autorizada
    And el conector del NMS cuenta con credenciales válidas
    And el esquema de mapeo de alarmas y traps fue configurado
    When el NMS publica eventos hacia el bus de eventos
    Then el sistema debe recibir los eventos en el tópico de ingesta
    And debe normalizar cada evento al esquema canónico de alarma
    And debe registrar la fuente, la región y la marca de tiempo de cada evento
    And debe marcar la fuente con estado "Integrada"
    And debe reflejar la nueva fuente en el indicador de cobertura de integración

  Scenario: Normalización de eventos con formatos heterogéneos
    Given que dos NMS de operadores adquiridos envían alarmas con formatos distintos
    And ambos esquemas de mapeo están configurados en la capa de normalización
    When los eventos ingresan al bus de eventos
    Then el sistema debe transformar ambos formatos al esquema canónico
    And debe conservar el identificador original del evento en cada fuente
    And debe entregar los eventos normalizados al proceso de filtrado y deduplicación
    And no debe descartar eventos por diferencias de formato

  Scenario: Sincronización del inventario de red con el motor de correlación
    Given que el inventario de red en Oracle contiene nodos, puertos y clientes
    And la tarea de sincronización está programada según la frecuencia definida
    When se ejecuta la sincronización del inventario
    Then el sistema debe actualizar la topología en el motor de correlación
    And debe registrar la fecha y hora de la última sincronización exitosa
    And debe validar la integridad referencial entre nodos y clientes
    And debe publicar el indicador de frescura del inventario en el tablero

  Scenario: Publicación de incidentes correlacionados hacia el ITSM
    Given que el motor de correlación generó un incidente con clientes afectados
    And la integración con la plataforma ITSM en Azure está disponible
    When el incidente es publicado hacia el ITSM
    Then el sistema debe crear el incidente maestro mediante la API del ITSM
    And debe recibir y almacenar el identificador del incidente creado
    And debe confirmar la publicación con un acuse de recibo
    And debe mantener la trazabilidad entre alarma, incidente interno e incidente del ITSM

  # Escenarios negativos

  Scenario: Rechazo de eventos de una fuente no autorizada
    Given que un sistema no registrado intenta publicar eventos al bus
    When los eventos llegan al punto de ingesta
    Then el sistema no debe aceptar los eventos
    And debe registrar el intento en la bitácora de seguridad
    And debe alertar al equipo de seguridad de plataformas
    And no debe entregar los eventos al proceso de normalización

  Scenario: Evento con esquema inválido o campos obligatorios ausentes
    Given que una fuente integrada envía un evento sin los campos obligatorios
    When el proceso de normalización valida el evento
    Then el sistema no debe entregar el evento al filtrado y deduplicación
    And debe enviar el evento a la cola de mensajes rechazados
    And debe registrar el motivo del rechazo con la fuente y el detalle del campo
    And debe incrementar el indicador de calidad de datos de la fuente

  Scenario: Pérdida de conectividad con un NMS regional
    Given que un NMS regional está integrado y en estado "Integrada"
    And el flujo de eventos de esa fuente se interrumpe por más del umbral definido
    When el monitoreo de ingesta detecta la ausencia de eventos
    Then el sistema debe marcar la fuente con estado "Sin señal"
    And debe alertar al operador del NOC sobre la región sin cobertura
    And debe registrar la ventana de pérdida de datos para auditoría
    And debe recuperar los eventos pendientes cuando la conexión se restablezca

  Scenario: Falla en la sincronización del inventario
    Given que la tarea de sincronización del inventario se ejecuta según programación
    When la base Oracle no está disponible o la sincronización falla
    Then el sistema no debe actualizar la topología con datos parciales
    And debe conservar la última versión válida de la topología
    And debe marcar el inventario con estado "Desactualizado" al superar el umbral de frescura
    And debe alertar al equipo de datos sobre la falla de sincronización

  Scenario: Indisponibilidad de la API del ITSM al publicar un incidente
    Given que el motor de correlación generó un incidente válido
    And la API del ITSM no responde o devuelve error
    When el sistema intenta publicar el incidente maestro
    Then el sistema no debe descartar el incidente
    And debe encolar el incidente en la cola de reintentos
    And debe reintentar la publicación según la política de reintentos con espera exponencial
    And debe alertar al operador del NOC si los reintentos se agotan

  Scenario: Saturación del bus de eventos por pico de tráfico
    Given que las fuentes integradas publican un volumen superior a la capacidad contratada
    When el bus de eventos alcanza el umbral de saturación
    Then el sistema debe aplicar el control de flujo sin perder eventos confirmados
    And debe priorizar los eventos de severidad crítica
    And debe alertar al equipo de plataforma sobre la saturación
    And debe registrar las métricas del pico para el ajuste de capacidad
```