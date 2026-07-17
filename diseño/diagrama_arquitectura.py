#!/usr/bin/env python3
"""
Diagrama de Arquitectura Multinube - FiberLink Andina Telecom
Generado con la librería diagrams de Python
"""

from diagrams import Diagram, Cluster, Edge

# AWS - Portal del Cliente (presentación)
from diagrams.aws.network import Route53, CloudFront
from diagrams.aws.security import WAF
from diagrams.aws.mobile import Amplify

# Azure - Captación, Instalación, Activación y EIP
from diagrams.azure.network import FrontDoors
from diagrams.azure.web import APIManagementServices
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.compute import ContainerApps, AKS, ContainerRegistries
from diagrams.azure.database import (
    DatabaseForPostgresqlServers,
    SQLDatabases,
    CosmosDb,
    CacheForRedis,
)
from diagrams.azure.integration import ServiceBus
from diagrams.azure.analytics import EventHubs
from diagrams.azure.security import KeyVaults, AzureSentinel
from diagrams.azure.monitor import Monitor, ApplicationInsights, LogAnalyticsWorkspaces
from diagrams.azure.other import AzureManagedGrafana

# GCP - Operación de Red y Analítica
from diagrams.gcp.network import LoadBalancing, Armor
from diagrams.gcp.api import Apigee
from diagrams.gcp.security import IAP, KMS as GcpKMS, SecretManager
from diagrams.gcp.compute import Run
from diagrams.gcp.analytics import PubSub, Dataflow, BigQuery, Looker
from diagrams.gcp.database import Bigtable, Firestore, Memorystore
from diagrams.gcp.operations import Monitoring, Logging

# Canales, conectividad híbrida y sistemas core
from diagrams.onprem.client import User
from diagrams.onprem.database import Oracle
from diagrams.onprem.monitoring import Prometheus
from diagrams.generic.compute import Rack
from diagrams.generic.network import VPN


def create_fiberlink_architecture():
    """Crea el diagrama de arquitectura multinube de FiberLink Andina Telecom"""

    with Diagram(
        "Arquitectura Multinube FiberLink - AWS + Azure + GCP",
        filename="diagrama_arquitectura",
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

        # AWS - Portal del Cliente (Presentación)
        with Cluster("AWS - Portal del Cliente (Presentación)"):
            a_r53 = Route53("Route 53")
            a_cf = CloudFront("CloudFront (CDN)")
            a_waf = WAF("AWS WAF + Shield")
            a_portal = Amplify("Portal Cliente\n(Amplify / S3)")

        # Azure - Captación, Instalación, Activación y EIP
        with Cluster("Azure - Captación, Instalación, Activación y EIP"):
            z_fd = FrontDoors("Front Door + WAF")
            z_eid = ActiveDirectory("Microsoft Entra ID\n(External ID)")
            z_apim = APIManagementServices("API Management\n(EIP - Fachada API)")

            with Cluster("Cómputo de Microservicios"):
                with Cluster("Gestión de Contenedores"):
                    z_acr = ContainerRegistries("Azure Container Registry")
                    z_aks = AKS("Azure Kubernetes Service\n(AKS - cargas avanzadas / service mesh)")

                with Cluster("Microservicios (Container Apps)"):
                    ms_cov = ContainerApps("coverage-service\n(RF03)")
                    ms_cap = ContainerApps("capacity-service\n(RF04)")
                    ms_st = ContainerApps("service-status-service\n(RF05)")
                    ms_sync = ContainerApps("inventory-sync\n(RF06)")
                    ms_eq = ContainerApps("equipment-inventory\n(RF09)")
                    ms_sch = ContainerApps("installation-scheduling\n(RF10)")
                    ms_act = ContainerApps("service-activation\n(RF11)")

            with Cluster("Datos"):
                z_pg = DatabaseForPostgresqlServers("Azure DB for PostgreSQL")
                z_sql = SQLDatabases("Azure SQL (Órdenes)")
                z_cos = CosmosDb("Cosmos DB")
                z_redis = CacheForRedis("Cache for Redis")

            with Cluster("Mensajería (EIP)"):
                z_sb = ServiceBus("Service Bus + Event Grid")
                z_eh = EventHubs("Event Hubs")

            with Cluster("Seguridad y Observabilidad"):
                z_kv = KeyVaults("Key Vault")
                z_sentinel = AzureSentinel("Sentinel")
                z_monitor = Monitor("Azure Monitor")
                z_prometheus = Prometheus("Azure Monitor\nManaged Prometheus")
                z_loganalytics = LogAnalyticsWorkspaces("Log Analytics")
                z_ai = ApplicationInsights("App Insights")
                z_grafana = AzureManagedGrafana("Managed Grafana")

        # GCP - Operación de Red y Analítica
        with Cluster("GCP - Operación de Red y Analítica"):
            g_lb = LoadBalancing("Cloud Load Balancing")
            g_armor = Armor("Cloud Armor")
            g_agw = Apigee("Apigee (API Gateway)")
            g_idp = IAP("Identity Platform / IAP")

            with Cluster("Microservicios (Cloud Run)"):
                ms_inc = Run("incident-correlation\n(RF12)")
                ms_ingest = Run("network-event-ingestion")
                ms_notif = Run("notification-dispatch")

            with Cluster("Datos"):
                g_bt = Bigtable("Bigtable")
                g_fs = Firestore("Firestore")
                g_mem = Memorystore("Memorystore Redis")

            with Cluster("Analítica"):
                g_ps = PubSub("Pub/Sub\n(Eventos de Red)")
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
            c_ora = Oracle("Inventario Oracle\n(Nodos/CTO/Puertos)")
            c_gis = Rack("GIS / Shapefile")
            c_oss = Rack("OSS Provisión\n(OLT/BRAS/Auth)")
            c_erp = Rack("ERP Facturación")
            c_fs = Rack("Field Service\n(Agenda Cuadrillas)")
            c_nms = Rack("NMS / NOC\n(Alarmas)")

        # === FLUJOS DE CANAL ===
        u_web >> a_r53 >> a_cf >> a_waf >> a_portal
        a_portal >> Edge(label="API (EIP)") >> z_apim
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

        # Gestión de contenedores hacia microservicios (Container Apps + AKS)
        z_acr >> Edge(label="imágenes (7 microservicios)") >> ms_cov
        z_acr >> Edge(label="imágenes cargas avanzadas") >> z_aks

        # Datos por microservicio
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

        # Backbone de eventos canónico (EIP)
        [ms_cov, ms_cap, ms_st, ms_sync, ms_eq, ms_sch, ms_act] >> z_sb >> z_eh
        ms_ingest >> g_ps
        ms_inc >> g_ps
        z_eh >> Edge(label="Eventos canónicos", style="bold", dir="both") >> g_ps

        # Acceso a sistemas core vía conectividad híbrida (mediado por EIP)
        [ms_cov, ms_cap, ms_st, ms_sync, ms_act, ms_sch, ms_eq] >> net_az
        net_az >> [c_crm, c_ora, c_gis, c_oss, c_erp, c_fs]

        # Flujo de operación de red
        c_nms >> net_gcp >> g_ps
        g_ps >> g_df >> ms_inc
        g_ps >> g_bq
        g_df >> g_bq
        ms_inc >> ms_notif
        ms_notif >> u_asesor
        ms_notif >> u_noc

        # Analítica
        z_eh >> Edge(label="Ingesta analítica", style="dashed") >> g_bq
        g_bq >> Edge(label="KPIs", style="dashed") >> g_look

        # Seguridad y gobierno (conexiones de configuración)
        g_secret >> [ms_inc, ms_ingest]
        g_kms >> [g_bt, g_fs]

        # Observabilidad
        z_monitor >> z_ai >> z_grafana
        z_monitor >> z_prometheus >> z_grafana
        z_monitor >> z_loganalytics >> z_sentinel
        g_mon >> g_log >> g_look


if __name__ == "__main__":
    create_fiberlink_architecture()
    print("✅ Diagrama generado exitosamente como 'diagrama_arquitectura.png'")
