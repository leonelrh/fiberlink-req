# Diagrama C4 — Nivel 2: Contenedores — FiberLink Andina Telecom
#
# Descompone la Plataforma de Integración y Operación FiberLink en sus
# contenedores desplegables por nube (Azure = APIs e integración, GCP = eventos
# y analítica, AWS = huella existente del portal), según los stacks de
# lineamientos/ y diagrama_arquitectura.py, usando los íconos oficiales de los
# proveedores cloud (AWS / Azure / GCP) de la librería `diagrams`.
#
# Genera "diagrama_c4_contenedores.png" (en esta misma carpeta).
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 diagrama_c4_contenedores.py

import os

from diagrams import Cluster, Diagram, Edge

from diagrams.aws.compute import Fargate
from diagrams.aws.database import Aurora
from diagrams.aws.network import CloudFront

from diagrams.azure.compute import ContainerApps, FunctionApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement, ServiceBus
from diagrams.azure.security import KeyVaults

from diagrams.gcp.analytics import BigQuery, PubSub
from diagrams.gcp.compute import Run
from diagrams.gcp.storage import GCS

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
    "C4 Nivel 2 — Contenedores: Plataforma de Integración FiberLink",
    filename=os.path.join(BASE_DIR, "diagrama_c4_contenedores"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    # ==================== Personas y canales (fuera de la plataforma) ====================
    usuarios = Users("Usuarios de canales\nclientes, vendedores, técnicos")
    operador = Users("Operador NOC / Integración\ntrazas y reprocesos (RF07, INT-11)")

    with Cluster("AWS — Portal de Clientes (existente)"):
        cdn = CloudFront("CloudFront + WAF")
        portal = Fargate("Portal de Clientes\nECS Fargate 24/7")
        aurora = Aurora("Aurora PostgreSQL")

    # ==================== Plataforma (sistema en foco) ====================
    with Cluster("Plataforma de Integración y Operación FiberLink"):

        # ---------- Azure: exposición de APIs e integración ----------
        with Cluster("Azure — APIs e Integración"):
            apim = APIManagement("API Management\nAPIs /v1, OAuth2, rate limiting\n(INT-01, SEG-02)")
            entra = ActiveDirectory("Entra ID\nOAuth2 / scopes")
            keyvault = KeyVaults("Key Vault\nsecretos por sistema")

            with Cluster("Microservicios — Container Apps (tráfico constante)"):
                ms_solicitudes = ContainerApps("ms-solicitudes\n(RF01)")
                ms_cobertura = ContainerApps("ms-cobertura\n(RF03)")
                ms_capacidad = ContainerApps("ms-capacidad\n(RF04)")
                ms_estado = ContainerApps("ms-estado-servicio\n(RF05)")
                ms_programacion = ContainerApps("ms-programacion-\ninstalacion (RF08/RF10)")
                ms_activacion = ContainerApps("ms-activacion\n(RF11)")
                ms_conectores = ContainerApps("ms-conectores-core (RF02)\nÚNICO acceso al core (INT-07)")

            with Cluster("Microservicios — Functions (carga intermitente)"):
                ms_eventos = FunctionApps("ms-eventos-negocio\n(RF06, INT-09)")
                ms_notificaciones = FunctionApps("ms-notificaciones\n(RF09)")
                ms_conciliacion = FunctionApps("ms-conciliacion-datos\n(RNOF01)")

            service_bus = ServiceBus("Service Bus\ncolas, tópicos, DLQ\n(INT-02, INT-05)")
            azure_sql = SQLDatabases("Azure SQL\nBD por microservicio\n(ARQ-05)")

        # ---------- GCP: eventos, analítica y observabilidad ----------
        with Cluster("GCP — Eventos, Analítica y Observabilidad"):
            pubsub_negocio = PubSub("Pub/Sub\neventos de negocio")
            pubsub_red = PubSub("Pub/Sub red\ncruda / normalizadas / DLQ\n(RNOF04)")

            with Cluster("Microservicios — Cloud Run (procesamiento continuo)"):
                ms_trazabilidad = Run("ms-trazabilidad\n(RF07, RNOF03, OBS-02)")
                ms_ingesta = Run("ms-ingesta-red\n(RNOF04)")
                ms_correlacion = Run("ms-correlacion-\nincidentes (RF12)")

            bigquery = BigQuery("BigQuery\ntrazas, auditoría, KPIs")
            worm = GCS("Cloud Storage\nauditoría WORM 5 años\n(RNOF03)")

    # ==================== Sistemas externos ====================
    with Cluster("Sistemas core (SEG-10)"):
        oracle = Oracle("Inventario de Red")
        core = Server("CRM, OSS/OCS, Facturación,\nERP, Field Service, GIS,\nÓrdenes, ITSM")

    nms = Server("NMS Regionales\nalarmas y logs (on-premises)")
    mensajeria = Server("Mensajería\ncorreo / WhatsApp / push (SaaS)")

    with Cluster("Analítica existente"):
        power_bi = PowerBi("Power BI")
        churn = BigQuery("Modelo de Churn")

    # ==================== Entrada por APIM (INT-01) ====================
    usuarios >> Edge(label="usa canales [HTTPS]") >> cdn
    cdn >> portal
    portal >> aurora
    portal >> Edge(label="APIs /v1 [HTTPS / OAuth2]") >> apim
    usuarios >> Edge(label="app móvil / tablets\n[HTTPS / OAuth2]") >> apim
    operador >> Edge(label="trazas y reprocesos\n[HTTPS / OAuth2]") >> apim
    apim >> Edge(label="OAuth2", style="dashed") >> entra
    apim >> Edge(label="enruta [HTTP/JSON]") >> [
        ms_solicitudes, ms_cobertura, ms_capacidad,
        ms_estado, ms_programacion, ms_activacion,
    ]
    apim >> Edge(label="consulta trazas (RF07)") >> ms_trazabilidad

    # ==================== Orquestación síncrona ====================
    ms_solicitudes >> Edge(label="valida cobertura (RF03)") >> ms_cobertura
    ms_solicitudes >> Edge(label="valida capacidad (RF04)") >> ms_capacidad
    [ms_solicitudes, ms_estado, ms_conectores] >> Edge(label="lee/escribe [SQL]") >> azure_sql

    # ==================== Mediación con el core (INT-07) ====================
    [ms_solicitudes, ms_programacion, ms_activacion, ms_conciliacion] >> Edge(
        label="POST /v1/core/{sistema}/{operacion}"
    ) >> ms_conectores
    ms_conectores >> Edge(label="secretos", style="dashed") >> keyvault
    ms_conectores >> Edge(label="REST/SOAP/JDBC/archivo\n[VPN/ExpressRoute]") >> [oracle, core]

    # ==================== Eventos asíncronos (INT-02, INT-09) ====================
    [ms_solicitudes, ms_programacion, ms_activacion] >> Edge(label="emite eventos") >> ms_eventos
    ms_eventos >> Edge(label="publica [AMQP]") >> service_bus
    ms_eventos >> Edge(label="replica [Pub/Sub]") >> pubsub_negocio
    service_bus >> Edge(label="suscripción") >> [ms_notificaciones, ms_conciliacion, ms_estado]
    ms_notificaciones >> Edge(label="envía (RF09)") >> mensajeria
    pubsub_negocio >> Edge(label="consume") >> ms_trazabilidad
    ms_trazabilidad >> Edge(label="persiste trazas") >> bigquery
    ms_trazabilidad >> Edge(label="copia inmutable (RNOF03)") >> worm

    # ==================== Observabilidad de red (RNOF04, RF12) ====================
    nms >> Edge(label="alarmas y logs [Pub/Sub]") >> pubsub_red
    pubsub_red >> Edge(label="cruda") >> ms_ingesta
    ms_ingesta >> Edge(label="normalizadas") >> pubsub_red
    pubsub_red >> Edge(label="normalizadas") >> ms_correlacion
    [ms_ingesta, ms_correlacion] >> Edge(label="persiste") >> bigquery
    ms_correlacion >> Edge(label="tickets ITSM (RF12)") >> ms_conectores
    ms_correlacion >> Edge(label="avisos proactivos") >> ms_notificaciones

    # ==================== Analítica ====================
    bigquery >> Edge(label="KPIs y propensión de churn") >> [power_bi, churn]

print("Diagrama generado:", os.path.join(BASE_DIR, "diagrama_c4_contenedores.png"))
