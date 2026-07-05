```gherkin
Feature: Recibir notificación de datos programdos para la instalación del servicio de internet
  Como Cliente
  Quiero recibir notificación de los datos programados para la instalación del servicio de internet (fecha programada, franja horaria y técnico asignado)
  Para poder confirmar fecha o poder solicitar una reprogramación antes de las 24 horas previas a la fecha programada de instalación

  # Escenarios positivos

  Scenario: Notificación exitosa de la programación de instalación al cliente
    Given que la orden de instalación ha sido registrada con estado "Programada"
    And el sistema cuenta con los datos de fecha, franja horaria y técnico asignado
    And el cliente tiene un correo electrónico y número de teléfono registrados en la orden
    When el sistema genera la notificación de programación de instalación
    Then debe enviar un correo electrónico al cliente con la fecha programada, franja horaria y nombre del técnico asignado
    And debe enviar un mensaje Whatsapp al número de teléfono del cliente con los mismos datos
    And debe registrar la notificación como enviada en la orden de instalación
    And debe incluir en la notificación el enlace para confirmar la fecha o solicitar una reprogramación
    And debe mostrar el mensaje "Notificación de instalación enviada correctamente al cliente"

  # Escenarios negativos

  Scenario: Fallo en el envío por correo electrónico no registrado
    Given que la orden de instalación ha sido registrada con estado "Programada"
    And el cliente no tiene un correo electrónico registrado en la orden
    When el sistema intenta generar la notificación de programación de instalación
    Then el sistema no debe enviar la notificación por correo electrónico
    And debe registrar la notificación como "Pendiente" en la orden de instalación
    And debe mostrar el mensaje "No es posible notificar al cliente. Correo electrónico no registrado. Verificar datos del cliente"

  Scenario: Fallo en el envío por número de teléfono no registrado
    Given que la orden de instalación ha sido registrada con estado "Programada"
    And el cliente no tiene un número de teléfono registrado en la orden
    When el sistema intenta enviar la notificación por Whataspp
    Then el sistema no debe enviar el mensaje al cliente
    And debe registrar el intento de notificación Whataspp como fallido en la orden de instalación
    And debe mostrar el mensaje "No es posible enviar mensaje al cliente. Número de teléfono no registrado. Verificar datos del cliente"

  Scenario: Fallo en el envío por orden de instalación sin datos de programación completos
    Given que existe una orden de instalación en el sistema
    And la orden no cuenta con fecha programada, franja horaria o técnico asignado
    When el sistema intenta generar la notificación de programación de instalación
    Then el sistema no debe enviar ninguna notificación al cliente
    And no debe registrar la notificación como enviada en la orden de instalación
    And debe mostrar el mensaje "No es posible notificar al cliente. La orden no cuenta con datos de programación completos. Verificar"

  Scenario: Error técnico durante el envío de la notificación
    Given que la orden de instalación ha sido registrada con estado "Programada"
    And el sistema cuenta con todos los datos necesarios para enviar la notificación
    When ocurre un error técnico durante el envío de la notificación
    Then el sistema no debe registrar la notificación como enviada en la orden de instalación
    And debe reintentar el envío de la notificación hasta 3 veces
    And debe mostrar el mensaje "No fue posible enviar la notificación al cliente. Intente nuevamente"
    And debe registrar el incidente técnico

```
    