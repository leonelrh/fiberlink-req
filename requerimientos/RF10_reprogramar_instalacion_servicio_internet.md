```gherkin
Feature: Reprogramar la instalación del servicio de internet
  Como Cliente
  Quiero solicitar una nueva fecha y franja horaria para la instalación del servicio de internet
  Para poder estar presente en el domicilio durante la visita del técnico y garantizar el éxito de la instalación

  # Escenarios positivos

  Scenario: Reprogramación exitosa de la instalación del servicio de internet
    Given que el cliente accede al enlace de reprogramación recibido en la notificación
    And la orden de instalación se encuentra en estado "Programada"
    And la solicitud de reprogramación se realiza con más de 24 horas de anticipación a la fecha programada
    And el cliente selecciona una nueva fecha y franja horaria disponible
    When confirma la solicitud de reprogramación
    Then el sistema debe verificar la disponibilidad de cuadrilla técnica para la nueva fecha seleccionada
    And debe liberar los recursos asignados a la fecha anterior
    And debe reasignar la cuadrilla técnica y los equipos a la nueva fecha confirmada
    And debe actualizar la orden de instalación con la nueva fecha y franja horaria
    And debe mantener el estado de la orden como "Programada"
    And debe notificar al cliente con los datos de la nueva fecha de instalación confirmada
    And debe mostrar el mensaje "Instalación reprogramada correctamente"

  # Escenarios negativos

  Scenario: Rechazo por solicitud fuera del plazo permitido
    Given que el cliente accede al enlace de reprogramación recibido en la notificación
    And la orden de instalación se encuentra en estado "Programada"
    And la solicitud de reprogramación se realiza con menos de 24 horas de anticipación a la fecha programada
    When intenta confirmar la solicitud de reprogramación
    Then el sistema no debe reprogramar la instalación
    And no debe modificar la fecha ni los recursos asignados a la orden de instalación
    And debe mostrar el mensaje "No es posible reprogramar la instalación. El plazo máximo para solicitar una reprogramación es de 24 horas antes de la fecha programada"

  Scenario: Rechazo por orden de instalación en estado no reprogramable
    Given que el cliente accede al enlace de reprogramación recibido en la notificación
    And la orden de instalación no se encuentra en estado "Programada"
    When intenta confirmar la solicitud de reprogramación
    Then el sistema no debe reprogramar la instalación
    And no debe modificar ningún dato de la orden de instalación
    And debe mostrar el mensaje "No es posible reprogramar la instalación. La orden no se encuentra en un estado válido para reprogramación. Contactar a soporte"

  Scenario: Rechazo por falta de disponibilidad en la nueva fecha seleccionada
    Given que el cliente accede al enlace de reprogramación recibido en la notificación
    And la orden de instalación se encuentra en estado "Programada"
    And la solicitud de reprogramación se realiza con más de 24 horas de anticipación
    And no existe disponibilidad de cuadrilla técnica para la nueva fecha seleccionada por el cliente
    When intenta confirmar la solicitud de reprogramación
    Then el sistema no debe reprogramar la instalación con la fecha seleccionada
    And no debe modificar los recursos asignados a la orden de instalación
    And debe mostrar el mensaje "No hay disponibilidad para la fecha seleccionada. Por favor elija otra fecha"

  Scenario: Error técnico durante el proceso de reprogramación
    Given que el cliente ha seleccionado una nueva fecha y franja horaria disponible
    And la solicitud cumple con todos los requisitos para ser procesada
    When ocurre un error técnico durante la actualización de la orden de instalación
    Then el sistema debe revertir cualquier cambio realizado en la orden de instalación
    And debe mantener la fecha y recursos asignados originalmente
    And debe mostrar el mensaje "No fue posible reprogramar la instalación. Intente nuevamente"
    And debe registrar el incidente técnico
```
