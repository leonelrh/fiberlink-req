# Requerimiento No Funcional: Integridad de Datos del Servicio de Internet entre Plataformas

## Identificador
RNF-002

## Categoría
Integridad de Datos / Consistencia entre Sistemas

## Descripción
El sistema debe garantizar que los datos del servicio de internet de un cliente sean consistentes, completos y sincronizados en todas las plataformas involucradas en el ciclo de vida del servicio: Portal del Cliente, CRM, ERP, OSS, Inventario y Facturación. Cualquier actualización en uno de estos sistemas debe propagarse de forma íntegra y oportuna al resto, evitando discrepancias operativas que puedan derivar en pérdidas económicas, errores de facturación o deterioro de la experiencia del cliente.

---

## Contexto y motivación

Durante el proceso de programación de la instalación, registro de recursos, activación del servicio y generación del contrato y facturación, múltiples plataformas consumen y producen datos sobre el mismo servicio y cliente. Una inconsistencia entre estos sistemas puede generar, entre otros problemas:

- Facturación de un plan diferente al contratado por el cliente.
- Equipos (router, ONT) registrados en inventario como disponibles cuando ya fueron instalados.
- El portal del cliente mostrando un estado del servicio diferente al real.
- El CRM operando con datos de contacto desactualizados, impidiendo notificaciones correctas.
- El OSS gestionando recursos de red sin conocer el estado real del servicio activado.
- Pérdida de clientes por discrepancias visibles entre lo facturado y lo contratado.

---

## Atributos de calidad

| Atributo             | Descripción |
|----------------------|-------------|
| Integridad           | Los datos del servicio deben ser idénticos en todas las plataformas en todo momento. |
| Consistencia         | Una actualización en cualquier plataforma debe reflejarse en el resto sin contradicciones. |
| Oportunidad          | La propagación de cambios entre sistemas debe ocurrir dentro de los tiempos máximos definidos. |
| Atomicidad           | Las operaciones que involucran múltiples plataformas deben completarse en su totalidad o revertirse completamente ante un fallo. |
| Disponibilidad       | La verificación de integridad no debe interrumpir la operación normal de ninguna plataforma. |

---

## Datos maestros del servicio a mantener íntegros

Los siguientes datos deben ser consistentes en todas las plataformas en todo momento:

| Dato                              | Plataformas involucradas                              |
|-----------------------------------|-------------------------------------------------------|
| Identificador del cliente         | CRM, ERP, OSS, Portal del Cliente, Facturación        |
| Plan de servicio contratado       | CRM, ERP, OSS, Portal del Cliente, Facturación        |
| Estado del servicio               | CRM, OSS, Portal del Cliente                          |
| Número de contrato                | CRM, ERP, Facturación, Portal del Cliente             |
| Fecha de activación del servicio  | CRM, ERP, OSS, Facturación, Portal del Cliente        |
| Fecha de inicio de facturación    | ERP, Facturación                                      |
| Equipos instalados (router, ONT)  | OSS, Inventario                                       |
| Estado de equipos en inventario   | OSS, Inventario                                       |
| Datos de contacto del cliente     | CRM, Portal del Cliente, Facturación                  |
| Orden de instalación              | CRM, OSS, ERP                                         |
| Cuadrilla y técnico asignado      | OSS, CRM                                              |

---

## Reglas de integridad por plataforma

### Portal del Cliente
- El estado del servicio mostrado debe coincidir con el estado registrado en el OSS y CRM.
- El plan contratado mostrado debe coincidir con el registrado en el CRM y Facturación.
- El número de contrato y la fecha de activación deben ser los mismos que en el ERP y Facturación.

### CRM
- Los datos del cliente (nombre, documento de identidad, dirección, contacto) deben ser la fuente de verdad y estar sincronizados con el Portal del Cliente y Facturación.
- El estado de la orden de instalación debe reflejar el estado real registrado en el OSS.
- El plan de servicio contratado debe coincidir con el registrado en el ERP y Facturación.

### ERP
- El número de contrato generado durante la activación debe estar vinculado al cliente correcto y al plan correcto.
- La fecha de inicio de facturación debe ser igual o posterior a la fecha de activación del servicio registrada en el OSS.
- El monto a facturar debe corresponder al plan contratado registrado en el CRM.

### OSS
- El estado del servicio (Activo, Inactivo, En instalación) debe actualizarse en tiempo real tras cada cambio operativo.
- Los equipos (router, ONT) registrados como instalados en el OSS deben coincidir con los reservados y descontados del Inventario.
- La orden de instalación cerrada en el OSS debe reflejar el mismo estado en el CRM y ERP.

### Inventario
- Los equipos reservados durante la programación de la instalación deben quedar marcados como no disponibles hasta que sean instalados o liberados.
- Los equipos instalados deben pasar de estado "Reservado" a "Instalado" y vincularse al cliente y contrato correspondiente en el OSS.
- Ningún equipo puede aparecer simultáneamente como disponible en Inventario y como instalado en el OSS.

### Facturación
- El plan facturado debe ser el mismo que el plan contratado registrado en el CRM y ERP.
- El cliente facturado debe coincidir con el cliente identificado en la orden de instalación y en el contrato.
- La facturación no debe iniciarse antes de la fecha de activación del servicio confirmada en el OSS.
- El número de contrato en el registro de facturación debe coincidir con el generado durante la activación.

---

## Mecanismos de garantía de integridad

- **Propagación de eventos:** Toda actualización de datos del servicio debe publicarse como un evento a todas las plataformas suscritas, garantizando que ninguna quede desactualizada.
- **Validación cruzada:** Antes de confirmar una operación crítica (activación, generación de contrato, inicio de facturación), el sistema debe verificar la consistencia de los datos en las plataformas involucradas.
- **Transacciones distribuidas:** Las operaciones que modifican datos en más de una plataforma (activación + generación de contrato + facturación) deben ejecutarse de forma atómica. Ante un fallo parcial, se debe revertir la operación completa.
- **Conciliación periódica:** El sistema debe ejecutar un proceso automático de conciliación de datos entre plataformas con una frecuencia máxima de 24 horas, reportando cualquier discrepancia detectada.
- **Alertas de inconsistencia:** Ante cualquier discrepancia detectada entre plataformas, el sistema debe generar una alerta al equipo de operaciones para su resolución antes de que impacte al cliente.

---

## Tiempos máximos de propagación

| Evento desencadenante                        | Tiempo máximo de propagación |
|----------------------------------------------|------------------------------|
| Activación del servicio                      | 5 minutos                    |
| Generación del número de contrato            | 5 minutos                    |
| Reserva de equipos en inventario             | 2 minutos                    |
| Instalación y baja de equipos del inventario | 10 minutos                   |
| Inicio de facturación                        | 30 minutos                   |
| Cierre de orden de instalación               | 10 minutos                   |

---

## Criterios de aceptación

- [ ] El estado del servicio es idéntico en el OSS, CRM y Portal del Cliente en todo momento, con una latencia máxima de propagación de 5 minutos tras cualquier cambio.
- [ ] El plan de servicio contratado registrado en el CRM coincide con el plan facturado en el módulo de Facturación y con el plan visible en el Portal del Cliente.
- [ ] Ningún equipo aparece simultáneamente como disponible en Inventario y como instalado en el OSS.
- [ ] La fecha de inicio de facturación es siempre igual o posterior a la fecha de activación del servicio registrada en el OSS.
- [ ] El número de contrato es idéntico en el CRM, ERP, Facturación y Portal del Cliente.
- [ ] Ante un fallo durante la activación del servicio, la reversión de la operación se aplica en todas las plataformas afectadas sin dejar datos inconsistentes.
- [ ] El proceso de conciliación automática detecta y reporta cualquier discrepancia entre plataformas en un plazo máximo de 24 horas.
- [ ] Las alertas de inconsistencia son recibidas por el equipo de operaciones antes de que la discrepancia impacte al cliente o genere una facturación incorrecta.
