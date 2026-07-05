# Requerimiento No Funcional: Trazabilidad y Auditabilidad del Proceso de Activación y Facturación

## Identificador
RNF-001

## Categoría
Trazabilidad y Auditabilidad

## Descripción
El sistema debe registrar y conservar un registro de auditoría completo e inmutable de todos los eventos ocurridos durante el ciclo de vida de una orden de instalación, desde su programación hasta la generación de los datos de facturación, de manera que un auditor pueda verificar en cualquier momento la consistencia entre los datos de activación del servicio de internet y los datos de facturación asociados.

---

## Atributos de calidad

| Atributo        | Descripción |
|-----------------|-------------|
| Trazabilidad    | Cada evento significativo del proceso debe quedar registrado con usuario, fecha, hora y datos involucrados. |
| Auditabilidad   | Los registros deben ser consultables por un auditor autorizado de forma íntegra, sin posibilidad de alteración posterior. |
| Integridad      | Los datos de activación y facturación deben poder correlacionarse de manera unívoca mediante identificadores comunes. |
| No repudio      | Ningún actor del proceso (operador, técnico, sistema) puede negar haber ejecutado una acción registrada en el log de auditoría. |
| Disponibilidad  | Los registros de auditoría deben estar disponibles para consulta en cualquier momento, sin afectar la operación del sistema. |

---

## Datos mínimos a registrar por evento

Cada entrada del registro de auditoría debe contener al menos:

- **Identificador de la orden de instalación**
- **Identificador del cliente**
- **Tipo de evento** (programación, instalación, activación, generación de contrato, generación de facturación)
- **Estado anterior y estado nuevo** de la orden o servicio
- **Usuario o proceso** que ejecutó la acción
- **Fecha y hora exacta** del evento (timestamp con zona horaria)
- **Datos relevantes del evento** (número de contrato, plan contratado, monto de facturación, equipos instalados, técnico asignado)
- **Resultado del evento** (Exitoso / Fallido)
- **Mensaje de error** en caso de fallo

---

## Eventos auditables del proceso

Los siguientes eventos deben quedar registrados obligatoriamente en el log de auditoría:

1. Registro y programación de la orden de instalación
2. Asignación de cuadrilla, materiales y equipos a la orden
3. Notificación de programación enviada al cliente
4. Registro de la instalación realizada en campo (conexión de fibra, configuración de equipos, potencia óptica)
5. Solicitud de activación del servicio por parte del técnico
6. Validación de consistencia de datos del cliente con la orden de instalación
7. Confirmación de activación del servicio
8. Generación del número de contrato
9. Vinculación del servicio instalado al contrato
10. Generación de los datos de facturación
11. Cierre de la orden de instalación
12. Envío del contrato al correo del cliente
13. Reversión de cualquier operación fallida
14. Registro de incidentes técnicos

---

## Consistencia entre activación y facturación

Para garantizar que el auditor pueda verificar la consistencia entre los datos de activación del servicio y los datos de facturación, el sistema debe cumplir con las siguientes condiciones:

- El número de contrato generado durante la activación debe estar presente en el registro de facturación correspondiente.
- El plan de servicio contratado registrado en la activación debe coincidir con el plan facturado.
- La fecha de inicio de facturación debe ser igual o posterior a la fecha de activación del servicio.
- El cliente identificado en la orden de instalación debe ser el mismo cliente asociado al contrato y al registro de facturación.
- Los equipos (router, ONT) registrados durante la instalación deben estar vinculados al contrato activo.
- Cualquier discrepancia detectada entre los datos de activación y los datos de facturación debe quedar registrada como un evento de inconsistencia en el log de auditoría.

---

## Restricciones sobre el log de auditoría

- Los registros de auditoría **no deben poder ser modificados ni eliminados** una vez creados, ni siquiera por administradores del sistema.
- Los registros deben conservarse por un período mínimo de **5 años** desde la fecha del evento.
- El acceso al log de auditoría debe estar restringido a roles autorizados (Auditor, Administrador de Sistemas).
- El sistema debe proveer una interfaz de consulta que permita filtrar los registros por: número de orden, identificador de cliente, número de contrato, rango de fechas y tipo de evento.
- Las consultas sobre el log de auditoría **no deben impactar el rendimiento** de los procesos operativos del sistema.

---

## Criterios de aceptación

- [ ] El sistema registra un evento de auditoría por cada uno de los 14 eventos auditables definidos.
- [ ] Cada registro contiene todos los datos mínimos especificados.
- [ ] Un auditor con rol autorizado puede consultar el log completo de una orden de instalación, desde la programación hasta la facturación, en una sola vista.
- [ ] El auditor puede verificar que el número de contrato, el plan contratado y el cliente son consistentes entre el registro de activación y el registro de facturación.
- [ ] Ningún usuario, incluido el administrador, puede modificar o eliminar un registro del log de auditoría.
- [ ] Los registros de auditoría se conservan disponibles por al menos 5 años.
- [ ] Las consultas al log de auditoría no degradan el tiempo de respuesta de las operaciones del sistema.
