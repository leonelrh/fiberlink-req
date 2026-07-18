#!/usr/bin/env python3
"""
Diagrama de Arquitectura Alternativa - FiberLink Andina Telecom
Generado con la librería diagrams de Python.

Combina 4 ejes de diseño frente a la arquitectura vigente (../diagrama_arquitectura.py):
  1. Backbone de eventos único cloud-agnostic (Kafka / Confluent Cloud) en vez del
     puente Azure Event Hubs <-> GCP Pub/Sub.
  2. Cómputo serverless-first (Azure Functions / GCP Cloud Functions) en vez de
     Container Apps / Cloud Run.
  3. Inventario de red replicado vía CDC (Debezium/Kafka Connect) hacia Azure,
     en vez de consulta en vivo a Oracle on-premises.
  4. Portal del Cliente consolidado en Azure (Static Web Apps + Front Door),
     eliminando AWS de la arquitectura (queda en 2 nubes: Azure + GCP).
"""

from diagrams import Diagram, Cluster, Edge

# Azure - Portal del Cliente, Captación, Instalación, Activación y EIP
from diagrams.azure.network import FrontDoors
from diagrams.azure.web import APIManagementServices, StaticApps
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.compute import FunctionApps
from diagrams.azure.database import (
    DatabaseForPostgresqlServers,
    SQLDatabases,
    CosmosDb,
    CacheForRedis,
)
from diagrams.azure.security import KeyVaults, AzureSentinel
from diagrams.azure.monitor import Monitor, ApplicationInsights, LogAnalyticsWorkspaces
from diagrams.azure.other import AzureManagedGrafana

# Backbone de eventos multi-cloud (Confluent Cloud / Kafka)
from diagrams.onprem.queue import Kafka

# GCP - Operación de Red y Analítica
from diagrams.gcp.network import LoadBalancing, Armor
from diagrams.gcp.api import Apigee
from diagrams.gcp.security import IAP, KMS as GcpKMS, SecretManager
from diagrams.gcp.compute import Functions as CloudFunctions
from diagrams.gcp.analytics import Dataflow, BigQuery, Looker
from diagrams.gcp.database import Bigtable, Firestore, Memorystore
from diagrams.gcp.operations import Monitoring, Logging

# Canales, conectividad híbrida y sistemas core
from diagrams.onprem.client import User
from diagrams.onprem.database import Oracle
from diagrams.onprem.monitoring import Prometheus
from diagrams.generic.compute import Rack
from diagrams.generic.network import VPN


def create_fiberlink_architecture_alternativa():
    """Crea el diagrama de arquitectura alternativa de FiberLink Andina Telecom"""

    with Diagram(
        "Arquitectura Alternativa FiberLink - Azure+GCP - Kafka unico + Serverless + CDC",
        filename="diagrama_arquitectura_alternativa",
        show=False,
        direction="TB",
        graph_attr={
            "splines": "ortho",
            "nodesep": "1.2",
            "ranksep": "1.4",
        },
    ):

        # Canales y Actores
        with Cluster("Canales y Actores"):
            u_web = User("Cliente / Prospecto\n(Web)")
            u_app = User("App Móvil Cliente")
            u_asesor = User("Asesor Comercial\n/ Call Center")
            u_vendedor = User("Vendedor Campo\n(Tablet offline)")
            u_tecnico = User("Técnico\n(App Móvil)")
            u_noc = User("Operador NOC")

        # Azure - Portal del Cliente, Captación, Instalación, Activación y EIP
        with Cluster("Azure - Portal del Cliente, Captación, Instalación, Activación y EIP"):
            z_fd = FrontDoors("Front Door + WAF")
            z_portal = StaticApps("Portal Cliente\n(Azure Static Web Apps)")
            z_eid = ActiveDirectory("Microsoft Entra ID\n(External ID)")
            z_apim = APIManagementServices("API Management\n(EIP - Fachada API)")

            with Cluster("Microservicios (Azure Functions - Serverless)"):
                ms_cov = FunctionApps("coverage-service\n(RF03)")
                ms_cap = FunctionApps("capacity-service\n(RF04)")
                ms_st = FunctionApps("service-status-service\n(RF05)")
                ms_sync = FunctionApps("inventory-sync\n(RF06)")
                ms_eq = FunctionApps("equipment-inventory\n(RF09)")
                ms_sch = FunctionApps("installation-scheduling\n(RF10)")
                ms_act = FunctionApps("service-activation\n(RF11)")

            with Cluster("Datos"):
                z_pg = DatabaseForPostgresqlServers("Azure DB for PostgreSQL\n(réplica CDC inventario + caché)")
                z_sql = SQLDatabases("Azure SQL (Órdenes)")
                z_cos = CosmosDb("Cosmos DB")
                z_redis = CacheForRedis("Cache for Redis")

            with Cluster("Seguridad y Observabilidad"):
                z_kv = KeyVaults("Key Vault")
                z_sentinel = AzureSentinel("Sentinel")
                z_monitor = Monitor("Azure Monitor")
                z_prometheus = Prometheus("Azure Monitor\nManaged Prometheus")
                z_loganalytics = LogAnalyticsWorkspaces("Log Analytics")
                z_ai = ApplicationInsights("App Insights")
                z_grafana = AzureManagedGrafana("Managed Grafana")

        # Backbone de eventos único cloud-agnostic (Confluent Cloud / Kafka)
        with Cluster("Confluent Cloud - Kafka Multi-Cloud (Backbone Único de Eventos)"):
            k_conf = Kafka("Tópicos canónicos\n(negocio + red)")
            k_cdc_src = Kafka("Kafka Connect - Debezium\n(CDC Source Oracle)")
            k_cdc_sink = Kafka("Kafka Connect\n(Sink a Azure DB)")

        # GCP - Operación de Red y Analítica
        with Cluster("GCP - Operación de Red y Analítica"):
            g_lb = LoadBalancing("Cloud Load Balancing")
            g_armor = Armor("Cloud Armor")
            g_agw = Apigee("Apigee (API Gateway)")
            g_idp = IAP("Identity Platform / IAP")

            with Cluster("Microservicios (Cloud Functions Gen2 - Serverless)"):
                ms_inc = CloudFunctions("incident-correlation\n(RF12) *")
                ms_ingest = CloudFunctions("network-event-ingestion")
                ms_notif = CloudFunctions("notification-dispatch")

            with Cluster("Datos"):
                g_bt = Bigtable("Bigtable")
                g_fs = Firestore("Firestore")
                g_mem = Memorystore("Memorystore Redis")

            with Cluster("Analítica"):
                g_df = Dataflow("Dataflow")
                g_bq = BigQuery("BigQuery")
                g_look = Looker("Looker (Dashboards)")

            with Cluster("Seguridad y Observabilidad"):
                g_secret = SecretManager("Secret Manager")
                g_kms = GcpKMS("Cloud KMS")
                g_mon = Monitoring("Cloud Monitoring")
                g_log = Logging("Cloud Logging")

        # Conectividad Híbrida Segura
        with Cluster("Conectividad Híbrida Segura"):
            net_az = VPN("Azure ExpressRoute\n+ Private Link")
            net_gcp = VPN("Cloud Interconnect\n+ Private Service Connect")

        # Sistemas Core (On-Premises / SaaS)
        with Cluster("Sistemas Core (On-Premises / SaaS)"):
            c_crm = Rack("CRM Comercial (SaaS)")
            c_ora = Oracle("Inventario Oracle\n(Nodos/CTO/Puertos)\nFuente de verdad")
            c_gis = Rack("GIS / Shapefile")
            c_oss = Rack("OSS Provisión\n(OLT/BRAS/Auth)")
            c_erp = Rack("ERP Facturación")
            c_fs = Rack("Field Service\n(Agenda Cuadrillas)")
            c_nms = Rack("NMS / NOC\n(Alarmas)")

        # === FLUJOS DE CANAL ===
        u_web >> z_fd >> z_portal
        z_portal >> Edge(label="API (EIP)") >> z_apim
        u_app >> z_fd
        u_asesor >> z_fd
        u_vendedor >> Edge(label="Sync fin de día", style="dashed") >> z_apim
        u_tecnico >> z_fd
        u_noc >> g_lb

        z_fd >> z_apim
        z_apim >> z_eid
        z_apim >> [ms_cov, ms_cap, ms_st, ms_sync, ms_eq, ms_sch, ms_act]

        g_lb >> g_armor >> g_agw
        g_agw >> g_idp
        g_agw >> ms_inc

        # Datos por microservicio (coverage/capacity leen la réplica CDC, no Oracle en vivo)
        ms_cov >> z_redis
        ms_cov >> z_pg
        ms_cap >> z_redis
        ms_cap >> z_pg
        ms_st >> z_redis
        ms_st >> z_cos
        ms_sch >> z_sql
        ms_act >> z_sql
        ms_eq >> z_cos
        ms_sync >> z_cos
        ms_inc >> g_bt
        ms_inc >> g_fs
        ms_inc >> g_mem

        # Backbone de eventos único (Kafka multi-cloud)
        # Comunicación servicio-a-servicio que no requiere respuesta inmediata
        # (p. ej. incident-correlation -> notification-dispatch) se enruta vía
        # Kafka en lugar de una llamada directa; solo la entrega final al canal
        # humano (asesor/NOC) sigue siendo una acción directa.
        [ms_cov, ms_cap, ms_st, ms_sync, ms_eq, ms_sch, ms_act] >> Edge(dir="both") >> k_conf
        ms_ingest >> Edge(dir="both") >> k_conf
        ms_inc >> Edge(dir="both") >> k_conf
        ms_notif >> Edge(dir="both") >> k_conf
        k_conf >> g_df >> ms_inc
        k_conf >> Edge(label="Ingesta analítica", style="dashed") >> g_bq
        g_bq >> Edge(label="KPIs", style="dashed") >> g_look
        ms_notif >> u_asesor
        ms_notif >> u_noc

        # Pipeline CDC de inventario (sobre el backbone Kafka)
        net_az >> k_cdc_src >> k_conf
        k_conf >> k_cdc_sink >> z_pg

        # Acceso a sistemas core vía conectividad híbrida (mediado por EIP)
        [ms_st, ms_sync, ms_act, ms_sch, ms_eq] >> net_az
        net_az >> [c_crm, c_ora, c_gis, c_oss, c_erp, c_fs]

        # Flujo de operación de red
        c_nms >> net_gcp >> k_conf

        # Seguridad y gobierno (conexiones de configuración)
        g_secret >> [ms_inc, ms_ingest]
        g_kms >> [g_bt, g_fs]

        # Observabilidad
        z_monitor >> z_ai >> z_grafana
        z_monitor >> z_prometheus >> z_grafana
        z_monitor >> z_loganalytics >> z_sentinel
        g_mon >> g_log >> g_look


if __name__ == "__main__":
    create_fiberlink_architecture_alternativa()
    print("✅ Diagrama generado exitosamente como 'diagrama_arquitectura_alternativa.png'")
