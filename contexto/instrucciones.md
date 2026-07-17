## Rol / Persona
Actua como un Arquitecto de Solución experto en diseño de soluciones en nube

## Cadena de Valor
Fase 1: Captación de clientes
El CRM comercial es SaaS. El portal web corre en AWS con base PostgreSQL administrada. La appmóvil consume APIs en Azure API Management. El inventario de red está en Oracle on premises ycontiene nodos, CTO, puertos, splitters, rutas y capacidad. Los mapas GIS heredados de operadores
adquiridos se guardan en servidores locales y archivos shapefile. Los vendedores de campo usantablets con una aplicación offline que sincroniza al final del día.
Roles: prospecto, vendedor, asesor de call center, analista de cobertura, marketing, operaciones ybackoffice. Entidades de datos: cliente potencial, dirección, coordenada, plan, cobertura, puerto,nodo, promoción, solicitud y contrato. El problema grave es que la venta se realiza con datos decobertura desactualizados.
En promedio se reciben 28,000 consultas comerciales diarias. El 18% obtiene una respuesta positivaque luego requiere validación manual. En ciudades adquiridas, el inventario tiene desfases de hastaseis meses. Durante una campaña promocional se vendieron 12,400 servicios en una zona dondesolo había capacidad inmediata para 8,900. El resto quedó en espera, generó reclamos y dañó lapercepción de la marca.
Fase 2: Instalación del servicio
Una venta aprobada se convierte en orden de instalación. El cliente espera una fecha, una franjahoraria y un técnico puntual. Operaciones debe asignar cuadrilla, materiales, ruta, permisos yequipos. La instalación parece logística, pero depende de datos técnicos precisos.
Las órdenes se originan en el CRM y pasan al sistema de gestión de órdenes alojado en Azure SQL.La agenda de cuadrillas está en un SaaS de field service. El inventario de equipos se administra en elERP on premises. La provisión de ONT y router se realiza desde una plataforma OSS local. Lostécnicos usan una app móvil que captura fotos, señal óptica, serie de equipo y firma del cliente.
Participan coordinador de instalaciones, técnico, almacén, cliente, NOC, backoffice y facturación.Entidades de datos: orden, cita, cuadrilla, equipo, serie, puerto, dirección, instalación, prueba,activación y evidencia. La integración entre sistemas es por archivos batch y APIs parciales. Cuandouna orden cambia de fecha, no siempre se actualiza en todos los sistemas.
FiberLink gestiona 4,800 instalaciones diarias. El 22% se reprograma por cliente ausente, falta decapacidad, error de dirección o falta de equipo. En 9% de casos el técnico llega y descubre que elpuerto asignado no existe o está ocupado. Cada visita fallida cuesta alrededor de USD 18 entretiempo, combustible y oportunidad. En un mes con 27,000 visitas fallidas, la pérdida operativa superaUSD 486,000, sin contar el enojo del cliente.
Fase 3: Activación del servicio
La activación del servicio es el momento de la verdad. El técnico conecta la fibra, instala la ONT,configura router, valida potencia óptica y solicita activación. El cliente quiere navegar de inmediato. La
empresa necesita que el servicio quede correctamente provisionado, facturado y asociado a sucontrato.
La plataforma de provisión corre on premises y se comunica con OLT (Terminal de Línea Óptica),BRAS (Broadband Remote Access Server) y sistemas de autenticación. El CRM mantiene el contrato.Facturación tiene el plan y ciclo de cobro. El portal de clientes en AWS muestra estado del servicio. ElNOC monitorea alarmas en herramientas locales. La activación se confirma mediante mensajes entresistemas, pero algunas respuestas quedan pendientes o duplicadas.
Entidades de datos: servicio, plan, dispositivo, ONT, router, puerto, perfil, credencial, estado, contratoy ciclo de facturación. Roles: técnico, NOC, backoffice, cliente, facturación y soporte. El problemagrave ocurre cuando el servicio funciona técnicamente, pero no queda reflejado comercialmente, o alrevés.
En la última auditoría se encontraron 38,000 servicios con discrepancias entre estado técnico yestado comercial. Algunos clientes navegaban sin facturación correcta; otros eran facturados sinactivación plena. La pérdida estimada por fuga de ingresos fue de USD 1.2 millones en seis meses.Además, las discrepancias complican soporte: el agente no sabe si debe diagnosticar red, corregircontrato o escalar a facturación.
Fase 4: Operación del servicio
La operación de red nunca duerme. El NOC observa alarmas, tráfico, pérdida de paquetes, potenciaóptica, uso de enlaces y disponibilidad de nodos. Los eventos llegan por millones. Una alarma puedeafectar a un hogar, un edificio o una ciudad. La capacidad de correlacionar eventos con clientesdefine la velocidad de respuesta.
Las herramientas NMS están instaladas en data centers regionales. Los logs de red se almacenan enservidores locales con retención limitada. Parte de los eventos se envía a GCP Pub/Sub paraanalítica de fallas, pero no todos los equipos están integrados. Los tableros ejecutivos se muestran enPower BI sobre Azure. El call center usa una plataforma de mesa de ayuda en Azure que no recibealarmas en tiempo real.
Roles: operador NOC, ingeniero de red, cuadrilla de mantenimiento, soporte de primer nivel, clienteempresarial y regulatorio. Entidades de datos: alarma, equipo, nodo, enlace, cliente afectado,incidente, ticket, SLA, causa, reparación y ventana de mantenimiento. La fragmentación produce dosmundos: la red sabe que falla algo, pero atención al cliente no siempre sabe a quién afecta.
El NOC recibe 2.6 millones de eventos por hora. Solo una parte se filtra como alarma relevante. En uncorte de fibra troncal, 42,000 clientes quedaron afectados. La correlación con clientes tomó 47
minutos. Durante ese tiempo el call center abrió 8,700 tickets individuales. Muchos agentes indicaronreiniciar router porque no veían el incidente masivo. El cliente sintió desorden, aunque la reparacióntécnica fue relativamente rápida.

## Requerimientos
En base a la cadena de valor de fiberlink se realizaron los requerimientos funcionales  que se encuentran en la carpeta de requerimientos


## Tarea / Objetivo

Diseñar una arquitectura multinube considerando:
- Todos los requerimientos de carpeta "requerimientos"
- Todos los lineamientos de carpeta "lineamientos"
- Volumetría en archivo "volumetria.md"
- Microservicios de carpeta microservicios

Realiza estos pasos:
3. Diagrama de Arquitectura
   Elabora un Diagrama de Arquitectura (Architecture Diagram), en formato mermaid, que incluya todos los servicios de AWS, Azure, GCP necesarios incluyendo los microservicios. Genera un archivo markdown "diagrama_arquitectura.md" en carpeta "diseño/alto_nivel"
4. 
## Requisitos de la respuesta
- Genera un archivo "decisiones_diseño.md" en carpeta "diseño/alto_nivel" que resuma los criterios de decisión principales tomados para el diseño propuesto. Indica el modelo LLM usado y la fecha como referencia.

## Elementos adicionales
- Si consideras que hay algún lineamiento relevante no indicado en carpeta "lineamientos", inclúyelo en el diseño pero indica explícitamente el criterio utilizado en el archivo "decisiones_diseño.md"
