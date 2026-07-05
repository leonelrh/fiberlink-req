```gherkin
Feature: Programar instalación del servicio de internet
  Como Operador
  Quiero asignar y validar la disponibilidad de recursos (cuadrilla, materiales, ruta, permisos y equipos)
  Para programar la instalación del servicio de internet con datos precisos y correctos

  # Escenarios positivos

  Scenario: Programación exitosa de la instalación del servicio de internet
    Given que el operador registra el número de orden de instalación
    And verifica la disponibilidad de la cuadrilla técnica para la fecha solicitada
    And confirma la disponibilidad de los materiales requeridos para la instalación
    And confirma la disponibilidad de los equipos necesarios (router, ONT, cables)
    And valida que la ruta de acceso al domicilio del cliente está habilitada
    And confirma que los permisos de instalación han sido obtenidos
    When solicita la programación de la instalación
    Then el sistema debe validar la consistencia de los recursos asignados con la orden de instalación
    And debe registrar la instalación con estado "Programada"
    And debe asignar la cuadrilla técnica a la orden de instalación
    And debe reservar los materiales y equipos en el inventario
    And debe generar la fecha y franja horaria de instalación confirmada
    And debe notificar al cliente con los datos de la instalación programada
    And debe mostrar el mensaje "Instalación programada correctamente"

  # Escenarios negativos

  Scenario: Rechazo por cuadrilla técnica no disponible
    Given que el operador registra el número de orden de instalación
    And no existe disponibilidad de cuadrilla técnica para la fecha solicitada
    When solicita la programación de la instalación
    Then el sistema no debe registrar la instalación como "Programada"
    And no debe asignar recursos a la orden de instalación
    And debe mostrar el mensaje "No hay cuadrilla disponible para la fecha seleccionada. Por favor elija otra fecha"

  Scenario: Rechazo por falta de materiales en inventario
    Given que el operador registra el número de orden de instalación
    And la cuadrilla técnica está disponible para la fecha solicitada
    And los materiales requeridos para la instalación no están disponibles en inventario
    When solicita la programación de la instalación
    Then el sistema no debe registrar la instalación como "Programada"
    And no debe reservar recursos en el inventario
    And debe mostrar el mensaje "Materiales insuficientes en inventario. No es posible programar la instalación"

  Scenario: Rechazo por permisos de instalación no obtenidos
    Given que el operador registra el número de orden de instalación
    And la cuadrilla técnica y los materiales están disponibles
    And los permisos de instalación requeridos no han sido obtenidos
    When solicita la programación de la instalación
    Then el sistema no debe registrar la instalación como "Programada"
    And no debe asignar ningún recurso a la orden de instalación
    And debe mostrar el mensaje "Los permisos de instalación son requeridos antes de programar. Verificar"

  Scenario: Error técnico durante el registro de la programación
    Given que todos los recursos están disponibles y los datos de la orden han sido validados correctamente
    When ocurre un error técnico al registrar la programación de la instalación
    Then el sistema debe revertir la asignación de recursos realizada
    And no debe marcar la orden con estado "Programada"
    And no debe notificar al cliente
    And debe mostrar el mensaje "No fue posible programar la instalación. Intente nuevamente"
    And debe registrar el incidente técnico

```
    