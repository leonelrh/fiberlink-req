```gherkin
Feature: Activar el servicio de internet contratado
  Como Técnico
  Quiero que el servicio de internet se encuentre activo despues de concluida la instalación
  Para que los clientes puedan hacer uso inmediatamente del servicio contratado

  # Escenarios positivos

  Scenario: Activación exitosa del servicio de internet
    Given que el técnico registra el documento de identidad del cliente
    And selecciona la orden de instalación
    And confirma que ha configurado el router
    And confirma que ha validado la potencia óptica
    and confirma los datos del servicio instalado
    And solicita la activación del servicio
    When confirma la solicitud de activación del servicio
    Then el sistema valida valida la consistencia de cliente con la orden de instalación 
    And debe solicitar la confirmación de activación del servicio
    And debe registrar el servicio con estado "Activo"
    And debe generar el número de contrato
    And debe vincular el servicio instalado al contrato
    And debe generar los datos de facturación
    And debe cerrar la orden de instalación con estado "Exitoso"
    And debe mostrar el mensaje "Servicio activado correctamente"
    And debe enviar el contrato al correo del cliente

  # Escenarios negativos

  Scenario: Rechazo por datos incorrectos
    Given que el técnico ingresa datos de cliente que no coincide con orden de instalación
    When confirma la solicitud de activación del servicio
    Then el sistema no debe emitir la orden de activación del servicio
    And el sistema no debe generar número de contrato
    And debe mostrar el mensaje "Los datos del cliente no coincide con la orden de instalación. Verificar"


  Scenario: Error técnico durante la generación del contrato
    Given que los datos de la solicitud activación del servicio fue validado correctamente
    And la activación del servicio fue confirmada
    When ocurre un error técnico al generar el contrato
    Then el sistema debe solicitar revertir la orden de activación del servicio
    Then el sistema no debe marcar el servicio como "Activo"
    And debe mostrar el mensaje "No fue posible realizar la activación del servicio"
    And debe registrar el incidente técnico

  Scenario: Error técnico durante la activación del servicio
    Given que los datos de la solicitud activación del servicio fue validado correctamente
  When la confirmación de activación del servcio no llega luego de 30 segundos
    Then el sistema debe solicitar revertir la orden de activación del servicio
    Then el sistema no debe marcar el servicio como "Activo"
    Then el sistema no debe generar número de contrato
    And debe mostrar el mensaje "No fue posible realizar la activación del servicio"
    And debe registrar el incidente técnico
```
    