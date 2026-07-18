#!/usr/bin/env python3
"""
Diagrama C4 - Nivel 2: Contenedores (Arquitectura Alternativa) - FiberLink

Descompone la Plataforma FiberLink en los contenedores de la arquitectura
alternativa (../diagrama_arquitectura_alternativa.py): Azure concentra el
Portal del Cliente (se elimina AWS) + los 7 microservicios de negocio como
Azure Functions, GCP los 3 microservicios de operación de red como Cloud
Functions Gen2, y Confluent Cloud (Kafka) es el backbone único de eventos que
reemplaza el puente Service Bus/Event Hubs <-> Pub/Sub.

Se omiten, igual que en el c4_contenedores.md vigente, los contenedores
puramente transversales de seguridad/observabilidad para mantener el foco en
los contenedores de negocio.

Layout (lección aplicada de diagrama_arquitectura_alternativa.py): el
pipeline de CDC (Oracle -> Kafka Connect Source -> Kafka -> Kafka Connect
Sink -> Azure DB for PostgreSQL) se simplifica a una única flecha punteada
Oracle -> PostgreSQL; los nodos de Kafka Connect quedan conectados solo al
tópico Kafka (borde corto, sin cruzar el diagrama), evitando el conflicto de
"rank" en Graphviz que generan las cadenas largas de 4 saltos.
"""

from diagrams import Diagram, Cluster, Edge

from diagrams.azure.web import APIManagementServices, StaticApps
from diagrams.azure.compute import FunctionApps
from diagrams.azure.database import (
    DatabaseForPostgresqlServers,
    SQLDatabases,
    CosmosDb,
    CacheForRedis,
)

from diagrams.onprem.queue import Kafka

from diagrams.gcp.api import Apigee
from diagrams.gcp.compute import Functions as CloudFunctions
from diagrams.gcp.analytics import Dataflow, BigQuery, Looker
from diagrams.gcp.database import Bigtable, Firestore, Memorystore

from diagrams.onprem.client import User
from diagrams.onprem.database import Oracle
from diagrams.generic.compute import Rack

BOUNDARY_ATTR = {"bgcolor": "white", "style": "dashed", "pencolor": "#8C8C8C", "fontcolor": "#3C3C3C", "fontsize": "14"}
EXT_BOUNDARY_ATTR = {"bgcolor": "white", "style": "dashed", "pencolor": "#ABABAB", "fontcolor": "#6B6B6B", "fontsize": "12"}


def create_c4_contenedores_alternativa():
    with Diagram(
        "C4 Nivel 2 - Contenedores - Plataforma FiberLink (Alternativa)",
        filename="diagrama_c4_contenedores",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "22",
            "labelloc": "t",
            "splines": "spline",
            "nodesep": "0.85",
            "ranksep": "1.2",
            "pad": "0.3",
            "bgcolor": "white",
        },
        edge_attr={
            "fontsize": "11",
            "fontname": "Sans-Serif",
            "fontcolor": "#3C3C3C",
            "color": "#8C8C8C",
        },
    ):
        with Cluster("Canales", graph_attr=EXT_BOUNDARY_ATTR):
            usuarios = User("Cliente, Asesor,\nVendedor, Técnico")
            noc = User("Operador NOC")

        with Cluster("Azure - Portal, Captación, Instalación, Activación y EIP", graph_attr=BOUNDARY_ATTR):
            portal = StaticApps("Portal del Cliente\n(Azure Static Web Apps)")
            apim = APIManagementServices("API Management\n(EIP)")

            with Cluster("Microservicios (Azure Functions)"):
                coverage = FunctionApps("coverage-service\n(RF03)")
                capacity = FunctionApps("capacity-service\n(RF04)")
                status = FunctionApps("service-status-service\n(RF05)")
                sync = FunctionApps("inventory-sync-service\n(RF06)")
                equipment = FunctionApps("equipment-inventory-service\n(RF09)")
                scheduling = FunctionApps("installation-scheduling-service\n(RF10)")
                activation = FunctionApps("service-activation-service\n(RF11)")

            with Cluster("Datos"):
                pg = DatabaseForPostgresqlServers("Azure DB for PostgreSQL\n(réplica CDC + caché)")
                sql = SQLDatabases("Azure SQL\n(Órdenes)")
                cosmos = CosmosDb("Cosmos DB")
                redis = CacheForRedis("Cache for Redis")

        with Cluster("Confluent Cloud - Kafka Multi-Cloud (Backbone Único)", graph_attr=BOUNDARY_ATTR):
            kconf = Kafka("Tópicos canónicos")
            kcdcsrc = Kafka("Kafka Connect\nDebezium (CDC Source)")
            kcdcsink = Kafka("Kafka Connect\n(Sink a Azure DB)")

        with Cluster("GCP - Operación de Red y Analítica", graph_attr=BOUNDARY_ATTR):
            agw = Apigee("Apigee\n(API Gateway)")

            with Cluster("Microservicios (Cloud Functions Gen2)"):
                incident = CloudFunctions("incident-correlation\n-service (RF12) *")
                ingestion = CloudFunctions("network-event\n-ingestion")
                notify = CloudFunctions("notification\n-dispatch")

            dataflow = Dataflow("Dataflow")

            with Cluster("Datos"):
                bigtable = Bigtable("Bigtable")
                firestore = Firestore("Firestore")
                memstore = Memorystore("Memorystore\nRedis")

            with Cluster("Analítica"):
                bigquery = BigQuery("BigQuery")
                looker = Looker("Looker")

        with Cluster("Sistemas Core (on-premises / SaaS)", graph_attr=EXT_BOUNDARY_ATTR):
            crm = Rack("CRM Comercial")
            oracle = Oracle("Inventario Oracle\n(fuente de verdad)")
            gis = Rack("GIS / Shapefile")
            oss = Rack("OSS Provisión")
            erp = Rack("ERP Facturación")
            fieldservice = Rack("Field Service")
            nms = Rack("NMS / NOC Regional")

        # === Canales ===
        usuarios >> Edge(label="Navega") >> portal
        portal >> Edge(label="API (EIP)") >> apim
        usuarios >> Edge(label="app móvil / directo") >> apim
        noc >> Edge(label="consulta correlación") >> agw

        # === Enrutamiento EIP ===
        apim >> [coverage, capacity, status, sync, equipment, scheduling, activation]
        agw >> incident

        # === Datos por microservicio ===
        coverage >> redis
        coverage >> Edge(label="lee réplica CDC") >> pg
        capacity >> redis
        capacity >> Edge(label="lee réplica CDC") >> pg
        status >> redis
        status >> cosmos
        scheduling >> sql
        activation >> sql
        equipment >> cosmos
        sync >> cosmos
        incident >> bigtable
        incident >> firestore
        incident >> memstore

        # === Backbone de eventos único (Kafka) ===
        [coverage, capacity, status, sync, equipment, scheduling, activation] >> kconf
        ingestion >> kconf
        incident >> Edge(dir="both", label="publica/consume") >> kconf
        notify >> Edge(dir="both", label="publica/consume") >> kconf
        kconf >> dataflow >> incident
        kconf >> Edge(label="ingesta analítica", style="dashed") >> bigquery
        bigquery >> Edge(label="KPIs", style="dashed") >> looker

        # === Pipeline CDC (simplificado: 1 flecha representativa) ===
        kcdcsrc >> kconf
        kconf >> kcdcsink
        oracle >> Edge(label="CDC continuo\n(Debezium -> Kafka -> sink)", style="dashed", color="gray45") >> pg

        # === Conectividad híbrida (sin cambios respecto a la vigente, salvo coverage/capacity) ===
        status >> Edge(style="dashed") >> oracle
        sync >> Edge(style="dashed") >> oracle
        equipment >> Edge(style="dashed") >> oracle
        scheduling >> Edge(style="dashed") >> fieldservice
        activation >> Edge(style="dashed") >> oss
        coverage >> Edge(style="dashed") >> gis
        activation >> Edge(style="dashed") >> erp
        scheduling >> Edge(style="dashed") >> crm
        nms >> Edge(label="alarmas") >> kconf


if __name__ == "__main__":
    create_c4_contenedores_alternativa()
    print("Diagrama generado: diagrama_c4_contenedores.png")
