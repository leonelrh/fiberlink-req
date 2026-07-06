# Diagrama de Arquitectura Multinube — FiberLink Andina Telecom
#
# Genera "diagrama_arquitectura.png" (en esta misma carpeta) con la librería
# `diagrams` de Python, tomando como referencia diagrama_arquitectura.md.
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 diagrama_arquitectura.py

import os

from diagrams import Cluster, Diagram, Edge

from diagrams.aws.compute import Fargate
from diagrams.aws.database import Aurora, ElastiCache
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import CloudFront

from diagrams.azure.analytics import LogAnalyticsWorkspaces
from diagrams.azure.compute import ContainerApps, FunctionApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.devops import ApplicationInsights
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement, ServiceBus
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.security import KeyVaults

from diagrams.gcp.analytics import BigQuery, PubSub
from diagrams.gcp.compute import Run
from diagrams.gcp.devtools import Scheduler
from diagrams.gcp.operations import Monitoring
from diagrams.gcp.storage import GCS

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
    "nodesep": "0.8",
    "ranksep": "1.3",
    "splines": "ortho",
    "concentrate": "true",   # Une rutas paralelas cuando es posible
    "pad": "0.3",
}

with Diagram(
    "Arquitectura Multinube FiberLink Andina Telecom",
    filename=os.path.join(BASE_DIR, "diagrama_arquitectura"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    # ==================== Canales ====================
    with Cluster("Canales"):
        app_movil = Mobile("App Móvil")
        tablets = Tablet("Tablets vendedores\n(sync offline)")
        app_tecnicos = Mobile("App técnicos\nde campo")
        call_center = Users("Call Center")

    # ==================== AWS — Portal existente ====================
    with Cluster("AWS — Portal de Clientes (huella existente)"):
        cdn = CloudFront("CloudFront + WAF")
        portal = Fargate("Portal de Clientes\nECS Fargate 24/7")
        aurora = Aurora("Aurora PostgreSQL")
        redis = ElastiCache("ElastiCache Redis")
        cloudwatch = Cloudwatch("CloudWatch")

    # ==================== Azure — APIs e Integración ====================
    with Cluster("Azure — Exposición de APIs e Integración Empresarial"):
        agw = ApplicationGateway("App Gateway + WAF")
        apim = APIManagement("API Management\nAPIs /v1, rate limiting")
        entra = ActiveDirectory("Entra ID\nOAuth2 / scopes")
        keyvault = KeyVaults("Key Vault")

        with Cluster("Microservicios — Container Apps (tráfico constante)"):
            ms_solicitudes = ContainerApps("ms-solicitudes\n(RF01)")
            ms_cobertura = ContainerApps("ms-cobertura\n(RF03)")
            ms_capacidad = ContainerApps("ms-capacidad\n(RF04)")
            ms_estado = ContainerApps("ms-estado-servicio\n(RF05)")
            ms_programacion = ContainerApps("ms-programacion-\ninstalacion (RF08/RF10)")
            ms_activacion = ContainerApps("ms-activacion\n(RF11)")
            ms_conectores = ContainerApps("ms-conectores-core\n(RF02) único acceso a core")

        with Cluster("Microservicios — Functions (carga intermitente)"):
            ms_eventos = FunctionApps("ms-eventos-negocio\n(RF06)")
            ms_notificaciones = FunctionApps("ms-notificaciones\n(RF09)")
            ms_conciliacion = FunctionApps("ms-conciliacion-datos\n(RNOF01)")

        service_bus = ServiceBus("Service Bus\ncolas, tópicos, DLQ")
        azure_sql = SQLDatabases("Azure SQL\nBD por microservicio")
        ordenes_db = SQLDatabases("Gestión de Órdenes\n(existente)")
        itsm = Server("Mesa de ayuda / ITSM\n(existente)")
        app_insights = ApplicationInsights("Application Insights")
        log_analytics = LogAnalyticsWorkspaces("Log Analytics")
        power_bi = PowerBi("Power BI\ntableros ejecutivos")

    # ==================== GCP — Eventos, Analítica, Observabilidad ====================
    with Cluster("GCP — Eventos, Analítica y Observabilidad"):
        pubsub_negocio = PubSub("Pub/Sub\neventos de negocio")
        pubsub_red = PubSub("Pub/Sub red\ncruda / normalizadas / DLQ")

        with Cluster("Microservicios — Cloud Run (procesamiento continuo)"):
            ms_trazabilidad = Run("ms-trazabilidad\n(RF07/RNOF03)")
            ms_ingesta = Run("ms-ingesta-red\n(RNOF04)")
            ms_correlacion = Run("ms-correlacion-\nincidentes (RF12)")

        scheduler = Scheduler("Cloud Scheduler")
        bigquery = BigQuery("BigQuery\ntrazas, auditoría, KPIs")
        worm = GCS("Cloud Storage\nauditoría WORM 5 años")
        churn = BigQuery("Modelo de churn\n(existente)")
        gcp_monitoring = Monitoring("Cloud Logging\n+ Monitoring")

    # ==================== On-Premises ====================
    with Cluster("On-Premises — Data Centers FiberLink"):
        oracle = Oracle("Inventario de Red\nnodos, CTO, puertos")
        oss = Server("OSS/OCS provisión\nOLT / BRAS")
        facturacion = Server("Facturación\nUnix heredado")
        erp = Server("ERP e inventario\nde equipos")
        nms = Server("NMS regionales\n+ logs de red")
        gis = Server("GIS heredado\n(shapefiles)")

    # ==================== SaaS externos ====================
    with Cluster("SaaS externos"):
        crm = Server("CRM Comercial")
        field_service = Server("Field Service\ncuadrillas")
        marketing = Server("Marketing\nretención")
        pagos = Server("Pasarelas de pago")
        mensajeria = Server("Correo / WhatsApp\n/ push")

    # ==================== Canales y Portal ====================
    cdn >> portal
    portal >> aurora
    portal >> redis
    portal >> Edge(label="pagos") >> pagos
    [app_movil, tablets, app_tecnicos] >> agw
    portal >> Edge(label="APIs de negocio") >> agw
    call_center >> itsm
    agw >> apim
    apim >> Edge(label="OAuth2", style="dashed") >> entra

    # ==================== APIs síncronas (INT-01) ====================
    apim >> [ms_solicitudes, ms_cobertura, ms_capacidad,
             ms_estado, ms_programacion, ms_activacion]
    apim >> Edge(label="consulta trazas") >> ms_trazabilidad

    ms_solicitudes >> Edge(label="cobertura") >> ms_cobertura
    ms_solicitudes >> Edge(label="capacidad") >> ms_capacidad
    [ms_solicitudes, ms_estado, ms_eventos] >> azure_sql
    ms_conectores >> Edge(label="secretos", style="dashed") >> keyvault

    # ==================== Plataforma de Integración (INT-07) ====================
    [ms_solicitudes, ms_programacion, ms_activacion, ms_conciliacion] >> ms_conectores
    ms_conectores >> Edge(label="VPN / ExpressRoute (SEG-10)") >> [oracle, oss, facturacion, erp]
    ms_conectores >> [crm, field_service, gis, itsm, ordenes_db]

    # ==================== Eventos asíncronos (INT-02, INT-09) ====================
    [ms_solicitudes, ms_programacion, ms_activacion] >> Edge(label="eventos") >> ms_eventos
    ms_eventos >> service_bus
    ms_eventos >> pubsub_negocio
    service_bus >> [ms_notificaciones, ms_conciliacion]
    service_bus >> Edge(label="proyección estado 360") >> ms_estado
    service_bus >> Edge(label="sync réplicas") >> [ms_cobertura, ms_capacidad]
    ms_notificaciones >> mensajeria
    pubsub_negocio >> ms_trazabilidad
    ms_trazabilidad >> bigquery
    ms_trazabilidad >> Edge(label="copia inmutable (RNOF03)") >> worm

    # ==================== Observabilidad de red (RNOF04 / RF12) ====================
    nms >> Edge(label="alarmas y logs") >> pubsub_red
    scheduler >> ms_ingesta
    pubsub_red >> Edge(label="cruda") >> ms_ingesta
    ms_ingesta >> Edge(label="normalizadas") >> pubsub_red
    pubsub_red >> Edge(label="normalizadas") >> ms_correlacion
    [ms_ingesta, ms_correlacion] >> bigquery
    ms_correlacion >> Edge(label="tickets ITSM") >> ms_conectores
    ms_correlacion >> Edge(label="avisos proactivos") >> ms_notificaciones

    # ==================== Analítica y retención ====================
    bigquery >> [power_bi, churn]
    churn >> Edge(label="propensión") >> crm
    crm >> marketing

    # ==================== Observabilidad técnica (OBS-01..07) ====================
    obs = Edge(style="dotted", color="gray", label="logs, métricas,\ntrazas (correlationId)")
    ms_conectores >> obs >> app_insights
    app_insights >> Edge(style="dotted", color="gray") >> log_analytics
    ms_trazabilidad >> Edge(style="dotted", color="gray") >> gcp_monitoring
    portal >> Edge(style="dotted", color="gray") >> cloudwatch

print("Diagrama generado:", os.path.join(BASE_DIR, "diagrama_arquitectura.png"))
