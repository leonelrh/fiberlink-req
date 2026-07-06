# Requerimiento No Funcional: Seguridad de las Plataformas del Servicio de Internet

## Identificador
RNOFO2

## Categoría
Seguridad / Gestión de Riesgos

## Descripción
El sistema debe garantizar la seguridad de todos los canales, plataformas e integraciones involucradas en el ciclo de vida del servicio de internet, protegiendo los datos personales de los clientes, las credenciales de acceso, la configuración de los servicios de red, la disponibilidad de la infraestructura y los procesos de facturación. La exposición simultánea de múltiples superficies de ataque (portal web, app móvil, APIs, CRM, OSS y facturación), el alto volumen de operaciones automatizadas y la existencia de integraciones heredadas con credenciales compartidas elevan el nivel de riesgo y exigen controles de seguridad explícitos y auditables.

---

## Contexto y motivación

El ecosistema de plataformas expone las siguientes superficies de riesgo identificadas:

- **Portal del Cliente (AWS):** Permite autogestión del servicio y procesamiento de pagos. Una brecha puede comprometer datos personales, credenciales y transacciones financieras de clientes.
- **App Móvil:** Canal de autogestión que puede ser vector de ataques de ingeniería social, robo de sesión o distribución de versiones maliciosas.
- **APIs de integración:** No todos los endpoints aplican rate limiting ni validación estricta de tokens, lo que los expone a ataques de fuerza bruta, scraping masivo o abuso de automatización.
- **CRM:** Contiene datos personales, historial de contacto y estado de contratos. Un acceso no autorizado afecta la privacidad de los clientes y la operación comercial.
- **OSS:** Gestiona la configuración de servicios de red y activaciones. Una manipulación no autorizada puede afectar la disponibilidad del servicio para múltiples clientes.
- **Facturación (ERP):** Procesa cobros y genera contratos. Un compromiso puede derivar en fraude financiero, cobros incorrectos o pérdida de ingresos.
- **Integraciones heredadas:** Operadores adquiridos usan credenciales técnicas compartidas para cargar datos de cobertura y activación, lo que dificulta la trazabilidad de acciones y amplía la superficie de ataque ante una credencial comprometida.

---

## Atributos de calidad

| Atributo              | Descripción |
|-----------------------|-------------|
| Confidencialidad      | Los datos personales, credenciales y configuraciones de red solo deben ser accesibles por actores autorizados. |
| Integridad            | Los datos no deben poder ser modificados por actores no autorizados en ningún punto del flujo. |
| Disponibilidad        | Los controles de seguridad no deben degradar la disponibilidad del servicio ni bloquear operaciones legítimas. |
| Autenticidad          | Toda acción sobre el sistema debe poder atribuirse de forma fehaciente a un actor identificado. |
| No repudio            | Ningún actor puede negar haber ejecutado una acción registrada y autenticada en el sistema. |
| Resiliencia           | El sistema debe mantener operación degradada ante un ataque activo, sin comprometer datos ni propagar el incidente. |

---

## Riesgos identificados y controles requeridos

### RG-01 — Acceso no autorizado al Portal del Cliente y App Móvil

**Riesgo:** Robo de credenciales de clientes, suplantación de identidad, acceso a datos personales y medios de pago almacenados.

**Controles requeridos:**
- Autenticación multifactor (MFA) obligatoria para operaciones sensibles: cambio de contraseña, actualización de datos de pago y solicitud de reprogramación o cancelación del servicio.
- Bloqueo temporal de cuenta tras 5 intentos de autenticación fallidos consecutivos.
- Tokens de sesión con tiempo de expiración máximo de 30 minutos de inactividad.
- Cifrado TLS 1.2 o superior en todas las comunicaciones entre el cliente y el portal o la app.
- Almacenamiento de contraseñas con algoritmos de hash seguros (bcrypt, Argon2). Prohibido almacenar contraseñas en texto plano.
- Validación de sesión activa en cada operación que involucre datos personales o pagos.

---

### RG-02 — Abuso de APIs por falta de rate limiting y validación de tokens

**Riesgo:** Ataques de fuerza bruta, scraping masivo de datos de clientes, abuso de endpoints de activación o facturación mediante automatización.

**Controles requeridos:**
- Aplicación de rate limiting en todos los endpoints expuestos, con límites diferenciados por tipo de operación:
  - Consulta de datos: máximo 100 solicitudes por minuto por IP.
  - Operaciones de escritura (activación, programación, facturación): máximo 20 solicitudes por minuto por token autenticado.
  - Endpoints de autenticación: máximo 10 intentos por minuto por IP.
- Validación estricta de tokens JWT o equivalente en cada llamada a la API, incluyendo verificación de firma, expiración y alcance (scope) del token.
- Rechazo explícito de solicitudes sin token válido con código de respuesta 401, sin revelar información del sistema.
- Implementación de listas de bloqueo dinámicas para IPs con comportamiento anómalo detectado.
- Revisión y cobertura de rate limiting en el 100% de los endpoints expuestos como parte del ciclo de despliegue.

---

### RG-03 — Credenciales técnicas compartidas en integraciones heredadas

**Riesgo:** Una credencial comprometida de un operador adquirido permite acceso indiscriminado a datos de cobertura, activaciones y configuraciones de red, sin posibilidad de atribución individual de acciones.

**Controles requeridos:**
- Eliminación progresiva de credenciales técnicas compartidas. Cada operador o sistema integrado debe contar con credenciales individuales e intransferibles.
- Mientras existan credenciales compartidas, su uso debe quedar registrado en el log de auditoría con el identificador del sistema origen de cada llamada.
- Rotación obligatoria de credenciales técnicas cada 90 días.
- Principio de mínimo privilegio: cada credencial técnica debe tener acceso únicamente a los recursos y operaciones estrictamente necesarios para su función (carga de cobertura o activación, no ambas si no es requerido).
- Almacenamiento de credenciales técnicas en un gestor de secretos centralizado (AWS Secrets Manager o equivalente). Prohibido almacenar credenciales en código fuente, archivos de configuración o variables de entorno sin cifrar.
- Monitoreo de uso anómalo de credenciales técnicas: volumen inusual de llamadas, horarios atípicos o acceso a recursos fuera del scope habitual deben generar una alerta inmediata.

---

### RG-04 — Exposición de datos personales y financieros en el Portal (AWS)

**Riesgo:** Configuración incorrecta de recursos en AWS (buckets S3 públicos, políticas IAM permisivas, puertos expuestos) puede exponer datos de clientes, contratos o registros de pago.

**Controles requeridos:**
- Revisión de configuración de seguridad en AWS antes de cada despliegue mediante herramientas de análisis estático de infraestructura (AWS Config, Security Hub o equivalente).
- Buckets S3 que contengan datos de clientes, contratos o evidencias de instalación deben tener acceso público bloqueado explícitamente.
- Políticas IAM con principio de mínimo privilegio: ningún rol o usuario de servicio debe tener permisos de administrador salvo justificación documentada y revisada.
- Datos de tarjetas de crédito y medios de pago no deben almacenarse en los sistemas propios. El procesamiento de pagos debe delegarse a un proveedor certificado PCI-DSS.
- Cifrado en reposo obligatorio para todos los almacenamientos que contengan datos personales o financieros (RDS, S3, backups).
- Auditoría periódica de grupos de seguridad y reglas de firewall para eliminar puertos o rangos de IP innecesariamente expuestos.

---

### RG-05 — Manipulación no autorizada de configuraciones en el OSS

**Riesgo:** Un acceso no autorizado al OSS puede modificar la configuración de servicios activos, provocar cortes masivos o activar servicios sin contrato válido.

**Controles requeridos:**
- Acceso al OSS restringido a roles operativos autorizados (Operador, Técnico, Administrador de Red). Ningún perfil de cliente o sistema externo debe tener acceso directo al OSS.
- Toda modificación de configuración de servicio en el OSS debe requerir autenticación y debe quedar registrada en el log de auditoría con usuario, fecha, hora y parámetros modificados.
- Implementación de flujos de aprobación para cambios masivos de configuración (modificaciones que afecten a más de 50 servicios simultáneamente requieren doble autorización).
- Segregación de ambientes: los ambientes de prueba y desarrollo del OSS no deben tener conectividad directa con los recursos de red de producción.

---

### RG-06 — Errores de configuración amplificados por automatización

**Riesgo:** El alto volumen de activaciones, programaciones y notificaciones automatizadas puede propagar un error de configuración a miles de registros antes de ser detectado.

**Controles requeridos:**
- Implementación de circuit breakers en los flujos automatizados: si la tasa de errores supera el 5% en una ventana de 5 minutos, el proceso automatizado debe detenerse y generar una alerta al equipo de operaciones.
- Validación de datos de entrada en todos los procesos automatizados antes de ejecutar operaciones sobre CRM, OSS, Inventario o Facturación.
- Ejecución de procesos masivos en modo de simulación (dry run) con revisión de muestra antes de aplicar cambios en producción para lotes superiores a 100 registros.
- Revisión obligatoria de logs de errores tras cada ejecución de proceso automatizado antes de considerar el proceso como exitoso.

---

## Requisitos transversales de seguridad

- **Gestión de vulnerabilidades:** El sistema debe someterse a análisis de vulnerabilidades (DAST/SAST) al menos una vez por trimestre y antes de cada release mayor. Las vulnerabilidades críticas deben ser remediadas en un plazo máximo de 72 horas desde su detección.
- **Registro de eventos de seguridad:** Todos los eventos de seguridad (autenticaciones fallidas, accesos denegados, cambios de credenciales, alertas de rate limiting) deben registrarse en un sistema centralizado de logs con retención mínima de 1 año.
- **Plan de respuesta a incidentes:** Debe existir un procedimiento documentado y probado para responder a brechas de seguridad, que incluya contención, notificación a clientes afectados y reporte a autoridades regulatorias en los plazos legales aplicables.
- **Capacitación:** El personal con acceso a sistemas críticos (CRM, OSS, Facturación) debe completar capacitación en seguridad de la información al menos una vez al año.

---

## Criterios de aceptación

- [ ] El 100% de los endpoints de la API aplican rate limiting y validación estricta de tokens antes del despliegue a producción.
- [ ] No existen credenciales técnicas compartidas entre operadores integrados. Cada sistema tiene credenciales individuales almacenadas en un gestor de secretos.
- [ ] Los buckets S3 y almacenamientos con datos de clientes tienen bloqueado el acceso público y cifrado en reposo habilitado.
- [ ] El portal del cliente y la app móvil requieren MFA para operaciones sensibles (cambio de datos de pago, cancelación, reprogramación).
- [ ] Una credencial técnica comprometida no otorga acceso a recursos fuera de su scope definido por el principio de mínimo privilegio.
- [ ] Un circuit breaker detiene automáticamente un proceso automatizado cuando la tasa de errores supera el 5% en 5 minutos y genera una alerta al equipo de operaciones.
- [ ] Los análisis de vulnerabilidades se ejecutan trimestralmente y las vulnerabilidades críticas se remedian en menos de 72 horas.
- [ ] Todos los eventos de seguridad quedan registrados en el sistema centralizado de logs con retención mínima de 1 año.
- [ ] El plan de respuesta a incidentes está documentado, probado y disponible para el equipo de seguridad y operaciones.
