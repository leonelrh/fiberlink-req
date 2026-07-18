#!/usr/bin/env python3
"""
Diagrama C4 - Nivel 3: Componentes (Cloud Functions Gen2 - GCP, Arquitectura
Alternativa) - FiberLink Andina Telecom

Descompone en componentes los tres contenedores que corren en Cloud
Functions Gen2 (GCP) en la arquitectura alternativa: network-event-ingestion,
incident-correlation-service (RF12) y notification-dispatch. Mismo algoritmo
interno que ../../c4/diagrama_c4_componentes.py (vigente); lo que cambia:

  1. Pub/Sub -> Confluent Cloud (Kafka), el mismo backbone único que usan
     los microservicios de Azure (sin Dataflow ni el pipeline cambian de
     lugar, solo la tecnología de origen).
  2. El puente a ITSM (Azure) ya no pasa por Event Hubs/Service Bus: el
     "ITSM Gateway" publica directo en el tópico Kafka.
  3. "Notification Orchestrator" <-> "Notification Request Handler" deja de
     ser una llamada directa bidireccional entre contenedores y pasa a ser
     publicación/consumo asíncrono vía Kafka (aplica el principio de
     "comunicación asíncrona por defecto" de diagrama_arquitectura_alternativa.py).

Layout: mismo criterio que la versión vigente (flujo izquierda -> derecha
que sigue el pipeline real, dependencias de datos junto al componente que
las usa) para evitar el cruce de líneas largas.
"""

from diagrams import Diagram, Cluster, Edge, Node

from diagrams.gcp.analytics import Dataflow, BigQuery
from diagrams.gcp.database import Bigtable, Firestore, Memorystore
from diagrams.gcp.api import Apigee
from diagrams.onprem.queue import Kafka
from diagrams.onprem.client import User
from diagrams.onprem.database import Oracle
from diagrams.generic.compute import Rack

COMPONENT_FILL, COMPONENT_BORDER = "#85BBF0", "#78A8D8"
CONTAINER_BOUNDARY_ATTR = {
    "bgcolor": "#F2F7FC",
    "style": "dashed",
    "pencolor": "#3379B7",
    "fontcolor": "#3379B7",
    "fontsize": "14",
    "margin": "20",
}
EXT_BOUNDARY_ATTR = {
    "bgcolor": "white",
    "style": "dashed",
    "pencolor": "#ABABAB",
    "fontcolor": "#6B6B6B",
    "fontsize": "12",
    "margin": "16",
}


def component(label: str) -> Node:
    return Node(
        f"{label}\n[Componente]",
        shape="box",
        style="filled,rounded",
        fillcolor=COMPONENT_FILL,
        color=COMPONENT_BORDER,
        fontcolor="#052E56",
        fontsize="13",
        fontname="Sans-Serif",
        fixedsize="false",
        labelloc="c",
        margin="0.25,0.16",
        width="0",
        height="0",
    )


def create_c4_componentes_alternativa():
    with Diagram(
        "C4 Nivel 3 - Componentes - Cloud Functions Gen2 (GCP) - Alternativa",
        filename="diagrama_c4_componentes",
        show=False,
        direction="LR",
        graph_attr={
            "fontsize": "24",
            "labelloc": "t",
            "splines": "spline",
            "nodesep": "0.55",
            "ranksep": "1.0",
            "pad": "0.35",
            "bgcolor": "white",
            "concentrate": "false",
        },
        edge_attr={
            "fontsize": "11",
            "fontname": "Sans-Serif",
            "fontcolor": "#3C3C3C",
            "color": "#9A9A9A",
        },
    ):
        # ---- Etapa 0: origen de eventos de red ----
        nms = Rack("NMS Regional")

        with Cluster("network-event-ingestion\n(Cloud Functions Gen2)", graph_attr=CONTAINER_BOUNDARY_ATTR):
            nms_receiver = component("NMS Event Receiver")
            normalizer = component("Event Normalizer")
            k_publisher = component("Kafka Publisher")
            nms_receiver >> normalizer >> k_publisher

        with Cluster("Backbone de eventos", graph_attr=EXT_BOUNDARY_ATTR):
            kconf = Kafka("Confluent Cloud\n(Tópicos canónicos)")
            dataflow = Dataflow("Dataflow")
            kconf >> dataflow

        # ---- Etapa 1: correlación (incident-correlation-service) ----
        with Cluster("incident-correlation-service (Cloud Functions Gen2) *", graph_attr=CONTAINER_BOUNDARY_ATTR):
            event_listener = component("Event Listener")
            dedup = component("Deduplication\nFilter")
            topology = component("Topology\nAnalyzer")
            customer_resolver = component("Customer Impact\nResolver")
            evaluator = component("Master Incident\nEvaluator")
            incident_repo = component("Incident\nRepository")
            itsm_gateway = component("ITSM Gateway")
            notif_orchestrator = component("Notification\nOrchestrator")
            inquiry_api = component("Customer\nStatus API")
            metrics_publisher = component("Metrics\nPublisher")

            event_listener >> dedup >> topology >> customer_resolver >> evaluator
            evaluator >> incident_repo
            evaluator >> Edge(label="calificado") >> itsm_gateway
            itsm_gateway >> notif_orchestrator
            incident_repo >> metrics_publisher
            inquiry_api >> Edge(style="dashed") >> incident_repo

        # ---- Dependencias, ubicadas junto al componente que las usa ----
        memstore = Memorystore("Memorystore\nRedis")

        with Cluster("Sistemas Core", graph_attr=EXT_BOUNDARY_ATTR):
            oracle = Oracle("Inventario\nOracle")
            crm = Rack("CRM Comercial")

        with Cluster("Datos ICS", graph_attr=EXT_BOUNDARY_ATTR):
            firestore = Firestore("Firestore")
            bigtable = Bigtable("Bigtable")

        with Cluster("ITSM (Azure)", graph_attr=EXT_BOUNDARY_ATTR):
            itsm = Rack("ITSM")

        bigquery = BigQuery("BigQuery")

        with Cluster("Consultas de estado", graph_attr=EXT_BOUNDARY_ATTR):
            agw = Apigee("Apigee /\nAPI Gateway")
            noc = User("Operador NOC")
            ivr_in = Rack("Sistema IVR\n(consulta entrante)")
            noc >> agw

        # ---- Etapa 2: notificación proactiva ----
        with Cluster("notification-dispatch (Cloud Functions Gen2)", graph_attr=CONTAINER_BOUNDARY_ATTR):
            notif_handler = component("Notification\nRequest Handler")
            channel_router = component("Channel\nRouter")
            delivery_tracker = component("Delivery\nTracker")
            notif_handler >> channel_router >> delivery_tracker

        with Cluster("Canales", graph_attr=EXT_BOUNDARY_ATTR):
            cliente = User("Cliente afectado")
            ivr_out = Rack("Sistema IVR\n(mensaje saliente)")
            portal = Rack("Portal del Cliente")

        # === Flujo principal (izquierda -> derecha) ===
        nms >> Edge(label="alarmas (2.6M/hora)") >> nms_receiver
        k_publisher >> kconf
        dataflow >> Edge(label="evento enriquecido") >> event_listener

        # === Dependencias de datos por componente ===
        dedup >> Edge(label="hash dedup") >> memstore
        topology >> Edge(label="topología") >> oracle
        customer_resolver >> Edge(label="servicios activos") >> crm
        incident_repo >> firestore
        incident_repo >> bigtable
        itsm_gateway >> Edge(label="publica evento\nde ticket") >> kconf
        kconf >> Edge(label="consumido por\nintegración Azure") >> itsm
        metrics_publisher >> bigquery

        # === Canal NOC / IVR hacia consulta de estado ===
        agw >> Edge(label="consulta correlación") >> inquiry_api
        ivr_in >> Edge(label="¿cliente afectado?") >> inquiry_api

        # === Notificación proactiva: async vía Kafka (ya no es llamada directa) ===
        notif_orchestrator >> Edge(label="publica solicitud\nde notificación") >> kconf
        kconf >> Edge(label="consume solicitud") >> notif_handler
        delivery_tracker >> Edge(label="entrega/fallo", style="dashed") >> notif_handler
        notif_handler >> Edge(label="publica confirmación\nde entrega") >> kconf
        kconf >> Edge(label="consume confirmación", style="dashed") >> notif_orchestrator
        channel_router >> Edge(label="APP/SMS/EMAIL") >> cliente
        channel_router >> Edge(label="mensaje contextual") >> ivr_out
        channel_router >> Edge(label="banner falla") >> portal


if __name__ == "__main__":
    create_c4_componentes_alternativa()
    print("Diagrama generado: diagrama_c4_componentes.png")
