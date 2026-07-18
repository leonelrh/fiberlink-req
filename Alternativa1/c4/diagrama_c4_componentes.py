#!/usr/bin/env python3
"""
Diagrama C4 - Nivel 3: Componentes (Cloud Run - GCP) - FiberLink Andina Telecom

Descompone en componentes los tres contenedores que corren en Cloud Run
(GCP), definidos en diagrama_c4_contenedores.py / c4_contenedores.md:
network-event-ingestion, incident-correlation-service (RF12) y
notification-dispatch. Se profundiza en incident-correlation-service por ser
el de mayor volumen (2.6M eventos/hora) y complejidad de correlación,
siguiendo microservicios/incident-correlation-service.md.

Layout: flujo izquierda -> derecha que sigue el pipeline real (ingesta ->
correlación -> persistencia/ITSM -> notificación), con cada dependencia de
datos ubicada junto a (debajo de) el componente que la usa, en vez de
agrupar todos los sistemas externos en un único bloque. Esto evita el cruce
de líneas largas que tenía la primera versión (dirección TB con un solo
clúster de "Personas y Sistemas Externos").

Estilo: los componentes usan la paleta C4 estándar (Structurizr /
C4-PlantUML) para "Component" (celeste), igual convención de color que
diagrama_c4_contexto.py usa para Persona/Sistema/Sistema externo. Los
contenedores de datos y mensajería que no se descomponen (Pub/Sub, Dataflow,
Bigtable, Firestore, Memorystore, BigQuery, Event Hubs) usan sus íconos
oficiales, igual que diagrama_arquitectura.py.
"""

from diagrams import Diagram, Cluster, Edge, Node

from diagrams.gcp.analytics import PubSub, Dataflow, BigQuery
from diagrams.gcp.database import Bigtable, Firestore, Memorystore
from diagrams.gcp.api import Apigee
from diagrams.azure.integration import ServiceBus
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


def create_c4_componentes():
    with Diagram(
        "C4 Nivel 3 - Componentes - Cloud Run (GCP)",
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

        with Cluster("network-event-ingestion\n(Cloud Run)", graph_attr=CONTAINER_BOUNDARY_ATTR):
            nms_receiver = component("NMS Event Receiver")
            normalizer = component("Event Normalizer")
            ps_publisher = component("Pub/Sub Publisher")
            nms_receiver >> normalizer >> ps_publisher

        with Cluster("Backbone de eventos", graph_attr=EXT_BOUNDARY_ATTR):
            pubsub = PubSub("Pub/Sub")
            dataflow = Dataflow("Dataflow")
            pubsub >> dataflow

        # ---- Etapa 1: correlación (incident-correlation-service) ----
        with Cluster("incident-correlation-service (Cloud Run)", graph_attr=CONTAINER_BOUNDARY_ATTR):
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

        with Cluster("Ticketing (Azure)", graph_attr=EXT_BOUNDARY_ATTR):
            eventhubs = ServiceBus("Event Hubs /\nService Bus")
            itsm = Rack("ITSM")

        bigquery = BigQuery("BigQuery")

        with Cluster("Consultas de estado", graph_attr=EXT_BOUNDARY_ATTR):
            agw = Apigee("Apigee /\nAPI Gateway")
            noc = User("Operador NOC")
            ivr_in = Rack("Sistema IVR\n(consulta entrante)")
            noc >> agw

        # ---- Etapa 2: notificación proactiva ----
        with Cluster("notification-dispatch (Cloud Run)", graph_attr=CONTAINER_BOUNDARY_ATTR):
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
        ps_publisher >> pubsub
        dataflow >> Edge(label="evento enriquecido") >> event_listener

        # === Dependencias de datos por componente ===
        dedup >> Edge(label="hash dedup") >> memstore
        topology >> Edge(label="topología") >> oracle
        customer_resolver >> Edge(label="servicios activos") >> crm
        incident_repo >> firestore
        incident_repo >> bigtable
        itsm_gateway >> eventhubs >> itsm
        metrics_publisher >> bigquery

        # === Canal NOC / IVR hacia consulta de estado ===
        agw >> Edge(label="consulta correlación") >> inquiry_api
        ivr_in >> Edge(label="¿cliente afectado?") >> inquiry_api

        # === Notificación proactiva (canal único, bidireccional: solicitud + ack de entrega) ===
        notif_orchestrator >> Edge(label="solicita envío / confirma entrega", dir="both") >> notif_handler
        delivery_tracker >> Edge(label="entrega/fallo", style="dashed") >> notif_handler
        channel_router >> Edge(label="APP/SMS/EMAIL") >> cliente
        channel_router >> Edge(label="mensaje contextual") >> ivr_out
        channel_router >> Edge(label="banner falla") >> portal


if __name__ == "__main__":
    create_c4_componentes()
    print("Diagrama generado: diagrama_c4_componentes.png")
