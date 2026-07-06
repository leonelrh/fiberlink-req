# C4 Model - Nivel 2: Contenedores - FiberLink Andina Telecom
#
# Muestra los contenedores principales (aplicaciones, servicios, bases de datos)
# que componen el sistema FiberLink y cómo se comunican entre sí.
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 c4_nivel2_contenedores.py

import os
from diagrams import Cluster, Diagram, Edge
from diagrams.generic.device import Mobile, Tablet
from diagrams.onprem.client import Users

# Azure services
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.integration import APIManagement
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.compute import ContainerApps, FunctionApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.integration import ServiceBus
from diagrams.azure.devops import ApplicationInsights

# AWS services
from diagrams.aws.network import CloudFront
from diagrams.aws.compute import Fargate
from diagrams.aws.database import Aurora, ElastiCache
from diagrams.aws.integration import SQS, Eventbridge
from diagrams.aws.analytics import KinesisDataStreams, KinesisDataFirehose
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch

try:
    from diagrams.aws.analytics import AmazonOpensearchService as OpenSearch
except ImportError:
    from diagrams.aws.analytics import ElasticsearchService as OpenSearch

from diagrams.onprem.compute import Server

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "16",
    "labelloc": "t",
    "nodesep": "1.0",
    "ranksep": "1.8",
    "splines": "polyline",
    "concentrate": "false", 
    "pad": "0.6",
    "dpi": "150",
}

with Diagram(
    "C4 Nivel 2: Contenedores - Sistema FiberLink",
    filename=os.path.join(BASE_DIR, "c4_nivel2_contenedores"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    
    # ==================== USUARIOS ====================
    with Cluster("Usuarios"):
        usuarios_movil = Mobile("Apps Móviles")
        usuarios_web = Users("Portal Web")
        tablets_campo = Tablet("Tablets Campo")
        call_center = Users("Call Center")
    
    # ==================== CAPA DE EXPOSICIÓN - AZURE ====================
    with Cluster("Azure - Capa de Exposición y APIs"):
        app_gateway = ApplicationGateway("Application Gateway\n+ WAF")
        api_mgmt = APIManagement("API Management\n/v1/* endpoints\nRate limiting")
        entra_id = ActiveDirectory("Entra ID\nOAuth 2.0")
        
        with Cluster("Microservicios de Negocio"):
            ms_solicitudes = ContainerApps("ms-solicitudes\nContainer App")
            ms_cobertura = ContainerApps("ms-cobertura\nContainer App") 
            ms_capacidad = ContainerApps("ms-capacidad\nContainer App")
            ms_estado = ContainerApps("ms-estado-servicio\nContainer App")
            ms_programacion = ContainerApps("ms-programacion\nContainer App")
            ms_activacion = ContainerApps("ms-activacion\nContainer App")
            ms_conectores = ContainerApps("ms-conectores-core\nContainer App")
            
        with Cluster("Microservicios Operativos"):
            ms_inventario = ContainerApps("ms-inventario-red\nContainer App")
            ms_agenda = ContainerApps("ms-agenda\nContainer App")
            ms_facturacion = ContainerApps("ms-facturacion\nContainer App")
            
        with Cluster("Servicios de Integración"):
            ms_eventos = FunctionApps("ms-eventos-negocio\nFunction App")
            ms_notificaciones = FunctionApps("ms-notificaciones\nFunction App")
            
        service_bus = ServiceBus("Service Bus\nColas y Tópicos")
        azure_sql = SQLDatabases("Azure SQL\nBase de Datos")
        app_insights = ApplicationInsights("Application Insights\nMonitoreo")
    
    # ==================== CONTENEDORES AWS ====================
    with Cluster("AWS - Portal, Eventos y Datos"):
        with Cluster("Portal de Clientes"):
            cloudfront = CloudFront("CloudFront\nCDN + WAF")
            portal_app = Fargate("Portal Web App\nECS Fargate")
            aurora_db = Aurora("Aurora PostgreSQL\nBase de Datos")
            redis_cache = ElastiCache("ElastiCache\nRedis Cache")
            
        with Cluster("Bus de Eventos"):
            eventbridge = Eventbridge("EventBridge\nEvent Bus")
            sqs_queues = SQS("SQS\nMessage Queues")
            kinesis_raw = KinesisDataStreams("Kinesis\nRaw Data Stream")
            kinesis_processed = KinesisDataStreams("Kinesis\nProcessed Stream")
            firehose = KinesisDataFirehose("Kinesis Firehose\nData Pipeline")
            
        with Cluster("Procesamiento de Datos"):
            ms_trazabilidad = Fargate("ms-trazabilidad\nECS Fargate")
            ms_ingesta = Fargate("ms-ingesta-red\nECS Fargate")
            ms_correlacion = Fargate("ms-correlacion\nECS Fargate")
            
        with Cluster("Almacenamiento y Búsqueda"):
            s3_datalake = S3("S3 Data Lake\nObject Storage")
            s3_audit = S3("S3 Audit\nImmutable Storage")
            opensearch = OpenSearch("OpenSearch\nSearch Engine")
            
        cloudwatch = Cloudwatch("CloudWatch\nMonitoreo AWS")
    
    # ==================== SISTEMAS EXTERNOS ====================
    with Cluster("Sistemas Externos"):
        crm_externo = Server("CRM Comercial\nSistema Externo")
        pagos_externo = Server("Pasarelas Pago\nSistema Externo")
        whatsapp_api = Server("WhatsApp API\nSistema Externo")
        itsm_externo = Server("ITSM\nSistema Externo")
        red_fisica = Server("Red Fibra Óptica\nInfraestructura")
    
    # ==================== FLUJOS PRINCIPALES ====================
    
    # Usuarios -> Capa de exposición
    [usuarios_movil, tablets_campo] >> app_gateway
    usuarios_web >> cloudfront >> portal_app
    call_center >> app_gateway
    
    # Capa de exposición
    app_gateway >> api_mgmt
    api_mgmt >> entra_id
    portal_app >> api_mgmt
    
    # APIs -> Microservicios
    api_mgmt >> [ms_solicitudes, ms_cobertura, ms_capacidad, 
                ms_estado, ms_programacion, ms_activacion]
    
    # Microservicios -> Bases de datos
    [ms_solicitudes, ms_cobertura, ms_capacidad, ms_estado, 
     ms_programacion, ms_activacion, ms_inventario, ms_agenda, 
     ms_facturacion] >> azure_sql
    
    portal_app >> aurora_db
    portal_app >> redis_cache
    
    # Eventos entre microservicios
    [ms_solicitudes, ms_cobertura, ms_capacidad, ms_estado, 
     ms_programacion, ms_activacion, ms_inventario] >> ms_eventos
    
    ms_eventos >> service_bus
    ms_eventos >> eventbridge
    
    service_bus >> [ms_notificaciones, ms_estado]
    eventbridge >> sqs_queues >> ms_trazabilidad
    
    # Integración externa
    ms_conectores >> [crm_externo, pagos_externo, itsm_externo]
    ms_notificaciones >> whatsapp_api
    ms_conectores >> red_fisica
    
    # Flujos de datos de red
    red_fisica >> kinesis_raw >> ms_ingesta
    ms_ingesta >> kinesis_processed >> ms_correlacion
    ms_ingesta >> firehose >> s3_datalake
    
    # Trazabilidad
    ms_trazabilidad >> opensearch
    ms_trazabilidad >> s3_datalake
    ms_trazabilidad >> s3_audit
    
    # Monitoreo
    [ms_solicitudes, ms_cobertura, ms_capacidad] >> app_insights
    [ms_trazabilidad, ms_ingesta, ms_correlacion, portal_app] >> cloudwatch

print("Diagrama C4 Nivel 2 - Contenedores generado:", os.path.join(BASE_DIR, "c4_nivel2_contenedores.png"))