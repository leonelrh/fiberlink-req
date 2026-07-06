# Diagrama C4 — Nivel 3: Componentes de ms-conectores-core — FiberLink Andina Telecom
#
# Descompone el contenedor ms-conectores-core (RF02, INT-07) — el único punto de
# acceso a los sistemas core — en sus componentes internos, según
# microservicios/ms_conectores_core.md (F1 mediación síncrona, F2 entrega de
# eventos, F3 reprocesos). Usa los íconos oficiales de los proveedores cloud
# (Azure / GCP) de la librería `diagrams`: los componentes internos se
# representan con el ícono de Azure Container Apps (su runtime) y los vecinos
# con el ícono del servicio correspondiente.
#
# Genera "diagrama_c4_componentes.png" (en esta misma carpeta).
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 diagrama_c4_componentes.py

import os

from diagrams import Cluster, Diagram, Edge

from diagrams.azure.compute import ContainerApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.devops import ApplicationInsights
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement, ServiceBus
from diagrams.azure.security import KeyVaults

from diagrams.gcp.analytics import PubSub

from diagrams.onprem.compute import Server
from diagrams.onprem.database import Oracle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "22",
    "labelloc": "t",
    "nodesep": "1.4",
    "ranksep": "1.4",
    "splines": "ortho",
    "concentrate": "true",   # Une rutas paralelas cuando es posible
    "pad": "0.3",
}

with Diagram(
    "C4 Nivel 3 — Componentes: ms-conectores-core (RF02, INT-07)",
    filename=os.path.join(BASE_DIR, "diagrama_c4_componentes"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    # ==================== Contenedores vecinos (contexto del componente) ====================
    consumidores = ContainerApps("Microservicios consumidores\nms-solicitudes, ms-programacion,\nms-activacion, ms-conciliacion,\nms-correlacion")
    apim = APIManagement("API Management\nexpone /v1/core/reprocesos\nal operador NOC (SEG-12)")

    with Cluster("Buses de eventos (INT-02)"):
        service_bus = ServiceBus("Azure Service Bus")
        pubsub = PubSub("GCP Pub/Sub")

    with Cluster("Seguridad y observabilidad"):
        entra = ActiveDirectory("Entra ID\nOAuth2 por consumidor (SEG-04)")
        keyvault = KeyVaults("Key Vault\nsecretos por sistema (RG-03)")
        app_insights = ApplicationInsights("Application Insights\ntelemetría con correlationId\n(OBS-01/02)")

    with Cluster("Sistemas core (SEG-10)"):
        oracle = Oracle("Inventario de Red")
        core = Server("CRM, OSS/OCS, Facturación,\nERP, Field Service, GIS, ITSM")

    # ==================== Contenedor en foco ====================
    with Cluster("ms-conectores-core — Azure Container Apps"):
        api_mediacion = ContainerApps("API de Mediación Síncrona\n[Componente — controlador REST]\nF1: POST /v1/core/{sistema}/{operacion}")
        api_reprocesos = ContainerApps("API de Reprocesos\n[Componente — controlador REST]\nF3: POST /v1/core/reprocesos (INT-11)")
        autorizador = ContainerApps("Autorizador de Consumidores\n[Componente]\ncredencial por sistema/operación\n(SEG-04, SEG-12, RG-03)")
        validador = ContainerApps("Validador de Esquema Canónico\n[Componente]\npayload y envolvente\n(INT-09, INT-10)")
        catalogo = ContainerApps("Catálogo de Sistemas y Operaciones\n[Componente]\nconector, esquemas, timeout,\nreintentos, umbral CB")
        resiliencia = ContainerApps("Circuit Breaker y Reintentos\n[Componente]\nespera exponencial, degradación\n(INT-03, ESC-09, INT-12)")
        transformador = ContainerApps("Motor de Transformación\n[Componente]\ncanónico ↔ nativo")
        adaptadores = ContainerApps("Adaptadores de Protocolo\n[Componente]\nREST / SOAP / JDBC / Archivo")
        consumidor_eventos = ContainerApps("Consumidor de Eventos\n[Componente — listener]\nF2: idempotencia por eventId (INT-06)")
        gestor_entregas = ContainerApps("Gestor de Entregas y Suscripciones\n[Componente]\nreintentos, DLQ, alertas\n(RNOF01, OBS-04)")
        registrador = ContainerApps("Registro de Intercambios\n[Componente]\nclasifica fallas (INT-08, OBS-09)")
        db = SQLDatabases("Base de datos Azure SQL\nsistema_core, operacion_core,\nintercambio, suscripcion,\nentrega_evento, reproceso")

    # ==================== F1: mediación síncrona ====================
    consumidores >> Edge(label="POST /v1/core/{sistema}/{operacion}\n[HTTP/JSON]") >> api_mediacion
    api_mediacion >> Edge(label="1. autoriza consumidor") >> autorizador
    api_mediacion >> Edge(label="2. resuelve operación") >> catalogo
    api_mediacion >> Edge(label="3. valida payload (INT-10)") >> validador
    api_mediacion >> Edge(label="4. ejecuta con resiliencia") >> resiliencia
    resiliencia >> Edge(label="invoca adaptador") >> adaptadores
    adaptadores >> Edge(label="transforma canónico ↔ nativo") >> transformador
    adaptadores >> Edge(label="REST / SOAP / JDBC / archivo\n[VPN/ExpressRoute]") >> [oracle, core]
    api_mediacion >> Edge(label="5. evidencia resultado (INT-08)") >> registrador

    # ==================== F2: mediación asíncrona ====================
    [service_bus, pubsub] >> Edge(label="eventos con envolvente INT-09") >> consumidor_eventos
    consumidor_eventos >> Edge(label="valida envolvente") >> validador
    consumidor_eventos >> Edge(label="entrega a suscriptores") >> gestor_entregas
    gestor_entregas >> Edge(label="reusa mediación F1") >> api_mediacion
    gestor_entregas >> Edge(label="fallos agotados → DLQ [AMQP]") >> service_bus
    gestor_entregas >> Edge(label="registra entrega_evento") >> registrador

    # ==================== F3: reprocesos ====================
    apim >> Edge(label="POST /v1/core/reprocesos\n[HTTP/JSON]") >> api_reprocesos
    api_reprocesos >> Edge(label="valida rol (SEG-12)") >> autorizador
    api_reprocesos >> Edge(label="reencola con marca de usuario\n(SEG-06)") >> gestor_entregas

    # ==================== Persistencia y transversales ====================
    [catalogo, registrador, gestor_entregas] >> Edge(label="lee/escribe [SQL]") >> db
    autorizador >> Edge(label="valida token", style="dashed") >> entra
    adaptadores >> Edge(label="obtiene secretos", style="dashed") >> keyvault
    registrador >> Edge(label="telemetría con correlationId (OBS-02)", style="dotted", color="gray") >> app_insights

print("Diagrama generado:", os.path.join(BASE_DIR, "diagrama_c4_componentes.png"))
