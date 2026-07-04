```gherkin
Feature: Correlación de incidentes de red con clientes afectados
  Como operador del NOC
  Quiero que las alarmas de red se correlacionen automáticamente con la topología y los clientes afectados
  Para gestionar un incidente maestro, notificar proactivamente y evitar tickets duplicados

  # Escenarios positivos

   Scenario: Una falla grande se registra como un solo incidente
    Given que el sistema recibe constantemente las señales de la red
    And el sistema conoce qué clientes dependen de cada parte de la red
    And se corta una fibra principal y llegan miles de alertas al mismo tiempo
    When el sistema analiza las alertas
    Then debe agruparlas en un solo incidente (no miles)
    And debe indicar cuál es el origen más probable de la falla
    And debe generar la lista de clientes afectados, indicando cuáles son empresariales y tienen compromisos de servicio
    And debe abrir el incidente en la mesa de ayuda en menos de 5 minutos
    And el incidente debe quedar en estado "Activo"

  Scenario: Notificación proactiva a clientes afectados
    Given que existe un incidente maestro en estado "Activo"
    And la lista de clientes afectados fue registrada correctamente
    When el incidente maestro es confirmado por el operador del NOC
    Then el sistema debe enviar avisos proactivos por app y mensajería a los clientes afectados
    And debe actualizar el IVR con el mensaje del incidente para las zonas impactadas
    And debe mostrar el aviso de falla masiva en el portal de autogestión
    And debe registrar la hora de envío de cada notificación

  Scenario: El cliente que llama recibe la información sin esperar a un agente
    Given que hay un incidente masivo activo
    And un cliente afectado llama al call center
    When el sistema telefónico reconoce el número del cliente en la lista de afectados
    Then debe informarle de la falla y el tiempo estimado de reparación
    And debe ofrecerle recibir actualizaciones sin necesidad de hablar con un agente

  Scenario: Cierre de incidente maestro con resolución en cascada
    Given que existe un incidente maestro con tickets hijos vinculados
    And la reparación técnica fue verificada por el NOC
    When el operador marca el incidente maestro como "Resuelto"
    Then el sistema debe cerrar automáticamente los tickets hijos vinculados
    And debe enviar la notificación de restablecimiento a los clientes afectados
    And debe registrar la duración total del incidente para el cálculo de SLA
    And debe publicar los indicadores del incidente en el tablero de Power BI

  # Escenarios negativos

  Scenario: Alarma sin correlación por inventario desactualizado
    Given que el motor de correlación recibe una alarma relevante
    And el nodo reportado no existe o está desactualizado en el inventario de red
    When se intenta asociar la alarma con clientes afectados
    Then el sistema no debe crear el incidente maestro automáticamente
    And debe registrar la alarma en estado "Pendiente de correlación manual"
    And debe alertar al operador del NOC sobre la inconsistencia de inventario
    And debe registrar la discrepancia para el proceso de saneamiento de datos

  Scenario: Descarte de eventos duplicados o irrelevantes
    Given que el bus de eventos recibe múltiples eventos del mismo equipo
    And los eventos corresponden a una alarma ya registrada
    When el proceso de filtrado y deduplicación evalúa los eventos
    Then el sistema no debe generar alarmas duplicadas
    And debe incrementar el contador de ocurrencias de la alarma existente
    And no debe crear un nuevo incidente maestro

  Scenario: Falla en la entrega de notificaciones proactivas
    Given que existe un incidente maestro en estado "Activo"
    And el canal de notificaciones no está disponible
    When el sistema intenta enviar los avisos proactivos
    Then el sistema debe registrar el fallo de envío por cada canal
    And debe reintentar el envío según la política de reintentos
    And debe alertar al operador del NOC si los reintentos se agotan
    And no debe marcar a los clientes como notificados

  Scenario: Umbral no alcanzado para incidente masivo
    Given que el motor de correlación identifica una falla localizada
    And el número de clientes afectados no supera el umbral de incidente masivo
    When se evalúa la creación del incidente
    Then el sistema no debe crear un incidente maestro
    And debe registrar una alarma individual con los clientes asociados
    And debe mantener la visibilidad de la falla para soporte de primer nivel

  Scenario: Error técnico durante la creación del incidente maestro
    Given que la correlación identificó una falla masiva válida
    And la creación del incidente fue autorizada
    When ocurre un error técnico al registrar el incidente en el ITSM
    Then el sistema no debe marcar el incidente como creado
    And debe conservar las alarmas correlacionadas en cola de reproceso
    And debe alertar al operador del NOC sobre el fallo de integración
    And debe registrar el incidente técnico de la plataforma
```