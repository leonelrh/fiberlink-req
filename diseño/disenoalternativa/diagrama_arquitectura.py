# Diagrama de Arquitectura Multinube Cloud-Native (AWS + Azure) — FiberLink Andina Telecom
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

from diagrams.aws.analytics import (
    Athena,
    Glue,
    KinesisDataFirehose,
    KinesisDataStreams,
    Redshift,
)
from diagrams.aws.compute import Fargate
from diagrams.aws.database import Aurora, ElastiCache
from diagrams.aws.devtools import XRay
from diagrams.aws.engagement import SES
from diagrams.aws.integration import SNS, SQS, Eventbridge
from diagrams.aws.management import Cloudtrail, Cloudwatch
from diagrams.aws.ml import Sagemaker
from diagrams.aws.network import CloudFront
from diagrams.aws.security import IAM, KMS, SecretsManager
from diagrams.aws.storage import S3

try:  # el ícono de OpenSearch no existe en todas las versiones de diagrams
    from diagrams.aws.analytics import AmazonOpensearchService as OpenSearch
except ImportError:
    from diagrams.aws.analytics import ElasticsearchService as OpenSearch

from diagrams.azure.analytics import LogAnalyticsWorkspaces
from diagrams.azure.compute import ContainerApps, FunctionApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.devops import ApplicationInsights
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement, ServiceBus
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.security import KeyVaults

from diagrams.generic.device import Mobile, Tablet
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.onprem.monitoring import Grafana

try:  # el ícono de Power BI no existe en todas las versiones de diagrams
    from diagrams.azure.analytics import PowerBiEmbedded as PowerBi
except ImportError:
    from diagrams.azure.analytics import AnalysisServices as PowerBi

try:  # Tratar de usar Location Service si está disponible
    from diagrams.aws.ar import LocationService
except ImportError:
    from diagrams.aws.storage import S3 as LocationService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "16",
    "labelloc": "t",
    "nodesep": "1.0",
    "ranksep": "1.5",
    "splines": "polyline",
    "concentrate": "false", 
    "pad": "0.5",
    "dpi": "150",
}

with Diagram(
    "FiberLink - Arquitectura Multinube Cloud-Native",
    filename=os.path.join(BASE_DIR, "diagrama_arquitectura"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    # ==================== Canales ====================
    with Cluster("Canales"):
        app_movil = Mobile("App Móvil")
        tablets = Tablet("Tablets")
        app_tecnicos = Mobile("App Técnicos")
        call_center = Users("Call Center")

    # ==================== Azure — APIs, Integración y Negocio ====================
    with Cluster("Azure — Exposición de APIs, Integración y Microservicios de Negocio"):
        agw = ApplicationGateway("App Gateway")
        apim = APIManagement("API Management")
        entra = ActiveDirectory("Entra ID")
        keyvault = KeyVaults("Key Vault")

        with Cluster("Microservicios de dominio — Container Apps"):
            ms_solicitudes = ContainerApps("ms-solicitudes")
            ms_cobertura = ContainerApps("ms-cobertura")
            ms_capacidad = ContainerApps("ms-capacidad")
            ms_estado = ContainerApps("ms-estado-servicio")
            ms_programacion = ContainerApps("ms-programacion")
            ms_activacion = ContainerApps("ms-activacion")
            ms_conectores = ContainerApps("ms-conectores-core")

        with Cluster("Dominios operativos — Container Apps"):
            ms_inventario_red = ContainerApps("ms-inventario-red")
            ms_agenda = ContainerApps("ms-agenda-cuadrillas")
            ms_facturacion = ContainerApps("ms-facturacion")
            ms_inventario_eq = ContainerApps("ms-inventario-equipos")

        with Cluster("Microservicios — Functions (carga intermitente)"):
            ms_eventos = FunctionApps("ms-eventos-negocio")
            ms_notificaciones = FunctionApps("ms-notificaciones")
            ms_conciliacion = FunctionApps("ms-conciliacion-datos")

        service_bus = ServiceBus("Service Bus")
        azure_sql = SQLDatabases("Azure SQL")
        ordenes_db = SQLDatabases("Gestión Órdenes")
        itsm = Server("Mesa de ayuda")
        app_insights = ApplicationInsights("App Insights")
        log_analytics = LogAnalyticsWorkspaces("Log Analytics")
        power_bi = PowerBi("Power BI")

    # ==================== AWS ====================
    with Cluster("AWS — Portal, Eventos, Trazabilidad, Geoespacial y Analítica"):
        with Cluster("Portal de Clientes (huella existente)"):
            cdn = CloudFront("CloudFront")
            portal = Fargate("Portal Clientes")
            aurora = Aurora("Aurora PostgreSQL")
            redis = ElastiCache("Redis")

        with Cluster("Bus de eventos y streaming"):
            eventbridge = Eventbridge("EventBridge")
            sqs = SQS("SQS")
            kinesis_cruda = KinesisDataStreams("Kinesis Cruda")
            kinesis_norm = KinesisDataStreams("Kinesis Normalizada")
            firehose = KinesisDataFirehose("Firehose")
            eb_scheduler = Eventbridge("Scheduler")

        with Cluster("Microservicios — ECS Fargate (procesamiento continuo)"):
            ms_trazabilidad = Fargate("ms-trazabilidad")
            ms_ingesta = Fargate("ms-ingesta-red")
            ms_correlacion = Fargate("ms-correlacion")

        with Cluster("Datos, geoespacial y analítica"):
            location = LocationService("Location Service")
            s3_lake = S3("S3 Data Lake")
            s3_worm = S3("S3 Auditoría")
            opensearch = OpenSearch("OpenSearch")
            glue = Glue("Glue + Athena")
            athena = Athena("Athena")
            redshift = Redshift("Redshift")
            sagemaker = Sagemaker("SageMaker")

        with Cluster("Seguridad y gobierno"):
            iam = IAM("IAM")
            secrets_mgr = SecretsManager("Secrets Manager")
            kms = KMS("KMS")
            cloudtrail = Cloudtrail("CloudTrail")

        sns_ses = SNS("SNS + SES")
        cloudwatch = Cloudwatch("CloudWatch")
        grafana = Grafana("Grafana")

    # ==================== Edge on-premises (mínimo irreducible) ====================
    with Cluster("Edge on-premises — mínimo irreducible (red física)"):
        oss_adaptadores = Server("Adaptadores OSS")
        olt_bras = Server("OLT / BRAS")
        colectores = Server("Colectores Red")

    # ==================== Externos mínimos ====================
    with Cluster("Externos mínimos (irreemplazables)"):
        crm = Server("CRM Comercial")
        pagos = Server("Pasarelas de pago")
        whatsapp = Server("WhatsApp")

    # ==================== Canales y Portal ====================
    cdn >> portal
    portal >> aurora
    portal >> redis
    portal >> pagos
    [app_movil, tablets, app_tecnicos] >> agw
    portal >> Edge(label="APIs") >> agw
    call_center >> itsm
    agw >> apim
    apim >> Edge(label="OAuth2") >> entra

    # ==================== APIs síncronas (INT-01) ====================
    apim >> [ms_solicitudes, ms_cobertura, ms_capacidad,
             ms_estado, ms_programacion, ms_activacion, ms_facturacion]
    apim >> ms_trazabilidad

    ms_solicitudes >> ms_cobertura
    ms_solicitudes >> ms_capacidad
    ms_cobertura >> ms_inventario_red
    ms_cobertura >> location
    ms_capacidad >> ms_inventario_red
    ms_programacion >> ms_agenda
    ms_programacion >> ms_inventario_eq
    ms_activacion >> ms_facturacion
    [ms_solicitudes, ms_estado, ms_inventario_red, ms_eventos] >> azure_sql
    ms_conectores >> keyvault

    # ==================== Integración con externos y edge (INT-07) ====================
    [ms_solicitudes, ms_activacion, ms_conciliacion] >> ms_conectores
    ms_conectores >> crm
    ms_conectores >> [ordenes_db, itsm]
    ms_conectores >> oss_adaptadores
    oss_adaptadores >> olt_bras

    # ==================== Eventos asíncronos (INT-02, INT-09) ====================
    [ms_solicitudes, ms_cobertura, ms_capacidad, ms_estado, ms_programacion, ms_activacion] >> ms_eventos
    ms_inventario_red >> ms_eventos
    ms_eventos >> service_bus
    ms_eventos >> eventbridge
    service_bus >> [ms_notificaciones, ms_conciliacion]
    service_bus >> ms_estado
    service_bus >> [ms_cobertura, ms_capacidad]
    service_bus >> ms_conciliacion
    ms_notificaciones >> sns_ses
    ms_notificaciones >> whatsapp

    # ==================== Trazabilidad y auditoría (RF07 / RNOF03) ====================
    eventbridge >> sqs
    sqs >> ms_trazabilidad
    ms_trazabilidad >> opensearch
    ms_trazabilidad >> firehose >> s3_lake
    ms_trazabilidad >> s3_worm

    # ==================== Observabilidad de red (RNOF04 / RF12) ====================
    colectores >> kinesis_cruda
    eb_scheduler >> ms_ingesta
    kinesis_cruda >> ms_ingesta
    ms_ingesta >> kinesis_norm
    ms_ingesta >> sqs
    ms_ingesta >> firehose
    kinesis_norm >> ms_correlacion
    ms_correlacion >> ms_conectores
    ms_correlacion >> ms_notificaciones

    # ==================== Analítica y retención ====================
    s3_lake >> glue >> athena
    glue >> redshift
    ms_correlacion >> redshift
    redshift >> power_bi
    s3_lake >> sagemaker
    sagemaker >> crm

    # ==================== Seguridad transversal ====================
    [ms_trazabilidad, ms_ingesta, ms_correlacion] >> iam
    iam >> secrets_mgr
    iam >> kms
    iam >> cloudtrail

    # ==================== Observabilidad técnica (OBS-01..07) ====================
    # Azure telemetry (simplificado)
    ms_solicitudes >> app_insights
    ms_conectores >> app_insights
    apim >> app_insights
    app_insights >> log_analytics
    
    # AWS telemetry (simplificado)
    portal >> cloudwatch
    ms_trazabilidad >> cloudwatch
    
    # Unified monitoring
    cloudwatch >> grafana
    app_insights >> grafana

print("Diagrama generado:", os.path.join(BASE_DIR, "diagrama_arquitectura.png"))
