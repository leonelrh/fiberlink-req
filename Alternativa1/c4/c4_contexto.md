# Diagrama C4 - Nivel 1: Contexto del Sistema

> Deriva de [`diagrama_arquitectura.md`](../diagrama_arquitectura.md) /
> [`diagrama_arquitectura.py`](../diagrama_arquitectura.py), pero a propósito **no**
> reproduce su contenido: un diagrama de contexto es el nivel más alto de abstracción
> de un sistema y solo debe mostrar cómo el sistema en foco interactúa con actores y
> sistemas externos, sin exponer su implementación interna. Por eso la **Plataforma
> FiberLink** aparece aquí como una única caja definida por su propósito de negocio
> (captación, instalación, activación y operación del servicio de fibra); qué nube
> aloja cada parte, qué es la EIP o cuáles son los microservicios se resuelve recién
> en el [diagrama de contenedores](c4_contenedores.md).

Este diagrama está disponible en dos formatos equivalentes:

- **Mermaid** (embebido más abajo, renderizable en GitHub/IDE).
- **Diagrams (Python)** con la paleta de color estándar del modelo C4
  (persona/sistema/sistema externo, sin íconos de producto — a este nivel de
  abstracción no corresponden): script
  [`diagrama_c4_contexto.py`](diagrama_c4_contexto.py) → imagen
  [`diagrama_c4_contexto.png`](diagrama_c4_contexto.png).
  Regenerar con: `pip install diagrams` (+ Graphviz) y `python3 diagrama_c4_contexto.py`.

![C4 Contexto](diagrama_c4_contexto.png)

## Versión Mermaid

```mermaid
C4Context
    title Diagrama de Contexto - Plataforma FiberLink

    Boundary(canalesB, "Personas (Canales)") {
        Person(cliente, "Cliente / Prospecto", "Consulta cobertura, contrata y da seguimiento a su servicio")
        Person(asesor, "Asesor Comercial / Call Center", "Registra solicitudes y atiende incidentes")
        Person(vendedor, "Vendedor de Campo", "Tablet offline, sincroniza al final del día")
        Person(tecnico, "Técnico de Campo", "Instala y activa el servicio en sitio")
        Person(noc, "Operador NOC", "Monitorea la red y gestiona incidentes")
    }

    System(plataforma, "Plataforma FiberLink", "Permite a clientes y equipos internos consultar cobertura, contratar, instalar, activar y operar el servicio de Internet por fibra óptica")

    Boundary(coreB, "Sistemas Externos (on-premises / SaaS)") {
        System_Ext(crm, "CRM Comercial", "Gestión comercial de clientes")
        System_Ext(oracle, "Inventario de Red", "Nodos, CTOs y puertos de la red de fibra")
        System_Ext(oss, "OSS de Provisión", "Aprovisionamiento de equipos de red")
        System_Ext(erp, "ERP de Facturación", "Facturación y cuentas de cliente")
        System_Ext(nms, "NMS Regional", "Monitoreo y alarmas de la red física")
    }

    Rel(cliente, plataforma, "Consulta cobertura, contrata y da seguimiento a su servicio")
    Rel(asesor, plataforma, "Registra solicitudes y atiende incidentes de clientes")
    Rel(vendedor, plataforma, "Registra solicitudes de campo")
    Rel(tecnico, plataforma, "Recibe su agenda y confirma instalación/activación")
    Rel(noc, plataforma, "Monitorea incidentes y trazabilidad de la operación")

    Rel(plataforma, crm, "Consulta y actualiza datos comerciales del cliente")
    Rel(plataforma, oracle, "Consulta topología, nodos y puertos disponibles")
    Rel(plataforma, oss, "Provisiona y activa el servicio en la red")
    Rel(plataforma, erp, "Sincroniza datos de facturación")
    Rel(nms, plataforma, "Emite alarmas y eventos de la red física")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

## Notas

- Deliberadamente **no aparecen** en este diagrama: nombres de nube (AWS/Azure/GCP),
  la EIP, microservicios, bases de datos ni protocolos de integración — eso es detalle
  de implementación y corresponde al [diagrama de contenedores](c4_contenedores.md). El
  contexto solo debe responder "¿con quién interactúa el sistema y para qué?".
- Los **sistemas externos** (CRM, Inventario de Red, OSS, ERP, NMS) son los mismos
  listados en la tabla "Distribución por nube" y el clúster `CORE` de
  `diagrama_arquitectura.md`, renombrados aquí por su rol de negocio en vez de su
  nombre de producto (p. ej. "Inventario Oracle" → "Inventario de Red").
- Se excluyen deliberadamente de este diagrama **GIS**, **Field Service** y el
  **Proveedor de Identidad**: siguen existiendo como sistemas externos/SaaS en
  `diagrama_arquitectura.md` y en el [diagrama de contenedores](c4_contenedores.md),
  pero no se representan en este nivel de contexto.
