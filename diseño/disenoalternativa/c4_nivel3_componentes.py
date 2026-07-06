# C4 Model - Nivel 3: Componentes - FiberLink Andina Telecom
#
# Muestra los componentes internos de los contenedores más importantes,
# enfocándose en los microservicios de negocio críticos.
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 c4_nivel3_componentes.py

import os
from diagrams import Cluster, Diagram, Edge
from diagrams.generic.device import Mobile
from diagrams.onprem.client import Users

# Componentes genéricos para representar módulos internos
from diagrams.programming.framework import React
from diagrams.programming.language import Java, Python
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.generic.network import Router
from diagrams.onprem.queue import Rabbitmq

# Azure y AWS para contexto
from diagrams.azure.integration import APIManagement
from diagrams.azure.compute import ContainerApps
from diagrams.azure.database import SQLDatabases
from diagrams.azure.integration import ServiceBus
from diagrams.aws.integration import Eventbridge

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "14",
    "labelloc": "t",
    "nodesep": "0.8",
    "ranksep": "1.5",
    "splines": "polyline",
    "concentrate": "false", 
    "pad": "0.4",
    "dpi": "150",
}

with Diagram(
    "C4 Nivel 3: Componentes - Microservicios FiberLink",
    filename=os.path.join(BASE_DIR, "c4_nivel3_componentes"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    
    # ==================== USUARIOS Y SISTEMAS EXTERNOS ====================
    usuarios_api = Mobile("APIs Clientes")
    api_gateway = APIManagement("API Management")
    service_bus_ext = ServiceBus("Service Bus")
    eventbridge_ext = Eventbridge("EventBridge")
    
    # ==================== MS-SOLICITUDES - COMPONENTES INTERNOS ====================
    with Cluster("ms-solicitudes (Container App)"):
        # Controladores API
        sol_api_controller = React("Solicitudes\nAPI Controller")
        sol_validation = Java("Validation\nComponent")
        
        # Lógica de negocio
        sol_orchestrator = Python("Solicitud\nOrchestrator")
        sol_cobertura_client = Router("Cobertura\nClient")
        sol_capacidad_client = Router("Capacidad\nClient")
        
        # Persistencia
        sol_repository = SQL("Solicitudes\nRepository")
        sol_event_publisher = Rabbitmq("Event\nPublisher")
        
        # Flujos internos
        sol_api_controller >> sol_validation >> sol_orchestrator
        sol_orchestrator >> sol_cobertura_client
        sol_orchestrator >> sol_capacidad_client
        sol_orchestrator >> sol_repository
        sol_orchestrator >> sol_event_publisher
    
    # ==================== MS-COBERTURA - COMPONENTES INTERNOS ====================
    with Cluster("ms-cobertura (Container App)"):
        cob_api_controller = React("Cobertura\nAPI Controller")
        cob_validation = Java("Address\nValidator")
        
        cob_service = Python("Cobertura\nService")
        cob_geo_client = Router("Geocoding\nClient")
        cob_inventario_client = Router("Inventario\nClient")
        
        cob_cache = Rack("Coverage\nCache")
        cob_repository = SQL("Cobertura\nRepository")
        
        # Flujos internos
        cob_api_controller >> cob_validation >> cob_service
        cob_service >> cob_geo_client
        cob_service >> cob_inventario_client
        cob_service >> cob_cache
        cob_service >> cob_repository
    
    # ==================== MS-PROGRAMACION - COMPONENTES INTERNOS ====================
    with Cluster("ms-programacion (Container App)"):
        prog_api_controller = React("Programacion\nAPI Controller")
        prog_validation = Java("Schedule\nValidator")
        
        prog_saga_orchestrator = Python("Saga\nOrchestrator")
        prog_agenda_client = Router("Agenda\nClient")
        prog_inventario_client = Router("Inventario Equipos\nClient")
        
        prog_repository = SQL("Programacion\nRepository")
        prog_compensation = Python("Compensation\nHandler")
        prog_event_publisher = Rabbitmq("Event\nPublisher")
        
        # Flujos internos
        prog_api_controller >> prog_validation >> prog_saga_orchestrator
        prog_saga_orchestrator >> prog_agenda_client
        prog_saga_orchestrator >> prog_inventario_client
        prog_saga_orchestrator >> prog_repository
        prog_saga_orchestrator >> prog_event_publisher
        prog_saga_orchestrator >> prog_compensation
    
    # ==================== MS-EVENTOS-NEGOCIO - COMPONENTES INTERNOS ====================
    with Cluster("ms-eventos-negocio (Function App)"):
        evt_trigger = Rabbitmq("Event\nTrigger")
        evt_validator = Java("Event Schema\nValidator")
        evt_enricher = Python("Event\nEnricher")
        
        evt_azure_publisher = Router("Azure SB\nPublisher")
        evt_aws_publisher = Router("AWS EB\nPublisher")
        evt_correlation = Rack("Correlation\nTracker")
        
        # Flujos internos
        evt_trigger >> evt_validator >> evt_enricher
        evt_enricher >> evt_correlation
        evt_enricher >> evt_azure_publisher
        evt_enricher >> evt_aws_publisher
    
    # ==================== MS-TRAZABILIDAD - COMPONENTES INTERNOS ====================
    with Cluster("ms-trazabilidad (ECS Fargate)"):
        trz_queue_consumer = Rabbitmq("SQS\nConsumer")
        trz_processor = Python("Trace\nProcessor")
        trz_correlation_engine = Rack("Correlation\nEngine")
        
        trz_search_indexer = Router("Search\nIndexer")
        trz_datalake_writer = Router("DataLake\nWriter")
        trz_audit_writer = Router("Audit\nWriter")
        trz_api_controller = React("Query\nAPI Controller")
        
        # Flujos internos
        trz_queue_consumer >> trz_processor >> trz_correlation_engine
        trz_correlation_engine >> trz_search_indexer
        trz_correlation_engine >> trz_datalake_writer
        trz_correlation_engine >> trz_audit_writer
    
    # ==================== SISTEMAS DE DATOS ====================
    azure_sql_db = SQLDatabases("Azure SQL")
    
    # ==================== CONEXIONES ENTRE MICROSERVICIOS ====================
    
    # Entrada desde API Gateway
    usuarios_api >> api_gateway >> sol_api_controller
    usuarios_api >> api_gateway >> cob_api_controller
    usuarios_api >> api_gateway >> prog_api_controller
    usuarios_api >> api_gateway >> trz_api_controller
    
    # Comunicación entre microservicios
    sol_cobertura_client >> cob_api_controller
    sol_capacidad_client >> Edge(label="Capacidad\nAPI Call", style="dashed") >> api_gateway
    
    prog_agenda_client >> Edge(label="Agenda\nAPI Call", style="dashed") >> api_gateway
    prog_inventario_client >> Edge(label="Inventario\nAPI Call", style="dashed") >> api_gateway
    
    cob_inventario_client >> Edge(label="Inventario Red\nAPI Call", style="dashed") >> api_gateway
    
    # Eventos de negocio
    sol_event_publisher >> service_bus_ext >> evt_trigger
    prog_event_publisher >> service_bus_ext
    
    evt_azure_publisher >> service_bus_ext
    evt_aws_publisher >> eventbridge_ext
    
    # Trazabilidad
    eventbridge_ext >> Edge(label="Audit Events") >> trz_queue_consumer
    
    # Persistencia
    sol_repository >> azure_sql_db
    cob_repository >> azure_sql_db
    prog_repository >> azure_sql_db

print("Diagrama C4 Nivel 3 - Componentes generado:", os.path.join(BASE_DIR, "c4_nivel3_componentes.png"))