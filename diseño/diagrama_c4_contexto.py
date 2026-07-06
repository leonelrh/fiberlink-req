# Diagrama C4 — Nivel 1: Contexto de Sistema — FiberLink Andina Telecom
#
# Muestra la Plataforma de Integración y Operación FiberLink como sistema en
# foco, las personas que la usan y los sistemas existentes con los que se
# integra (ARQ-09, INT-07). Basado en diagrama_arquitectura.py, usando los
# íconos oficiales de los proveedores cloud (AWS / Azure / GCP) de la librería
# `diagrams`: la plataforma se representa con sus puertas de entrada por nube
# (Azure API Management para APIs, GCP Pub/Sub para eventos, BigQuery para
# trazabilidad).
#
# Genera "diagrama_c4_contexto.png" (en esta misma carpeta).
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 diagrama_c4_contexto.py

import os

from diagrams import Cluster, Diagram, Edge

from diagrams.aws.compute import Fargate

from diagrams.azure.integration import APIManagement

from diagrams.gcp.analytics import BigQuery, PubSub

from diagrams.generic.device import Mobile, Tablet
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.onprem.database import Oracle

try:  # el ícono de Power BI no existe en todas las versiones de diagrams
    from diagrams.azure.analytics import PowerBiEmbedded as PowerBi
except ImportError:
    from diagrams.azure.analytics import AnalysisServices as PowerBi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "22",
    "labelloc": "t",
    "nodesep": "1.1",
    "ranksep": "1.4",
    "splines": "ortho",
    "concentrate": "true",   # Une rutas paralelas cuando es posible
    "pad": "0.3",
}

with Diagram(
    "C4 Nivel 1 — Contexto: Plataforma de Integración FiberLink",
    filename=os.path.join(BASE_DIR, "diagrama_c4_contexto"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    # ==================== Personas ====================
    with Cluster("Personas"):
        cliente = Users("Cliente / Prospecto\ncontrata y consulta\nsu servicio")
        vendedor = Users("Vendedor en terreno\nregistra solicitudes (RF01)")
        tecnico = Users("Técnico de campo\ninstala y activa (RF08/RF11)")
        agente = Users("Agente Call Center\nestado e incidentes (RF05/RF12)")
        operador = Users("Operador NOC / Integración\ntrazas y reprocesos (RF07, INT-11)")

    # ==================== Canales digitales existentes ====================
    with Cluster("Canales digitales (existentes)"):
        portal = Fargate("Portal de Clientes\nAWS (existente)")
        app_movil = Mobile("App Móvil")
        app_vendedores = Tablet("App Tablets Vendedores\n(sync offline)")
        app_tecnicos = Mobile("App Técnicos\nde Campo")

    # ==================== Sistema en foco ====================
    with Cluster("Plataforma de Integración y Operación FiberLink (ARQ-09, INT-07)"):
        apis = APIManagement("APIs de negocio /v1\nAzure API Management")
        eventos = PubSub("Hub de eventos\nGCP Pub/Sub")
        trazas = BigQuery("Trazabilidad y auditoría\nGCP BigQuery")

    # ==================== Sistemas core on-premises ====================
    with Cluster("Sistemas core — Data Centers FiberLink (on-premises)"):
        inventario = Oracle("Inventario de Red\nnodos, CTO, puertos")
        oss = Server("OSS/OCS de Provisión\nOLT / BRAS")
        facturacion = Server("Facturación\nUnix heredado")
        erp = Server("ERP e inventario\nde equipos")
        nms = Server("NMS regionales\nalarmas y logs (RNOF04)")
        gis = Server("GIS heredado\nshapefiles (RF03)")

    # ==================== SaaS y sistemas de negocio ====================
    with Cluster("SaaS y sistemas de negocio"):
        crm = Server("CRM Comercial\n(SaaS)")
        field_service = Server("Field Service\ncuadrillas (RF08/RF10)")
        ordenes = Server("Gestión de Órdenes\nAzure SQL (existente)")
        itsm = Server("Mesa de Ayuda / ITSM\ntickets (RF12)")
        mensajeria = Server("Correo / WhatsApp\n/ push (RF09)")

    # ==================== Analítica existente ====================
    with Cluster("Analítica (existente)"):
        power_bi = PowerBi("Power BI\ntableros ejecutivos")
        churn = BigQuery("Modelo de Churn\n(retención)")

    # ==================== Personas → canales ====================
    cliente >> Edge(label="consulta y contrata [HTTPS]") >> portal
    cliente >> Edge(label="usa") >> app_movil
    vendedor >> Edge(label="registra solicitudes (RF01)") >> app_vendedores
    tecnico >> Edge(label="ejecuta órdenes (RF08/RF11)") >> app_tecnicos
    agente >> Edge(label="gestiona casos e incidentes") >> itsm
    operador >> Edge(label="trazas y reprocesos\n(RF07, INT-11) [HTTPS/OAuth2]") >> apis

    # ==================== Canales → plataforma ====================
    portal >> Edge(label="APIs de negocio /v1\n[HTTPS / OAuth2]") >> apis
    app_movil >> Edge(label="APIs /v1 [HTTPS / OAuth2]") >> apis
    app_vendedores >> Edge(label="registra solicitudes\n[HTTPS / OAuth2]") >> apis
    app_tecnicos >> Edge(label="reporta instalación y activación\n[HTTPS / OAuth2]") >> apis

    # ==================== Plataforma → sistemas (INT-07) ====================
    apis >> Edge(label="media integración con el core\n[APIs + eventos, VPN/ExpressRoute SEG-10]") >> [
        inventario, oss, facturacion, erp,
    ]
    apis >> Edge(label="consulta cobertura [shapefiles]") >> gis
    apis >> Edge(label="crea casos y sincroniza clientes") >> crm
    apis >> Edge(label="agenda y reprograma cuadrillas") >> field_service
    apis >> Edge(label="crea y actualiza órdenes") >> ordenes
    apis >> Edge(label="tickets proactivos (RF12)") >> itsm
    eventos >> Edge(label="notificaciones (RF09)") >> mensajeria
    nms >> Edge(label="publica alarmas y logs de red\n[Pub/Sub]") >> eventos
    apis >> Edge(label="publica eventos de negocio\n(RF06, INT-09)") >> eventos
    eventos >> Edge(label="persiste trazas (OBS-02)") >> trazas

    # ==================== Plataforma → analítica ====================
    trazas >> Edge(label="KPIs, trazas y auditoría") >> [power_bi, churn]

print("Diagrama generado:", os.path.join(BASE_DIR, "diagrama_c4_contexto.png"))
