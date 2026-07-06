# C4 Model - Nivel 1: Contexto - FiberLink Andina Telecom
#
# Muestra la vista de más alto nivel del sistema, incluyendo usuarios,
# sistemas externos y el sistema FiberLink como una caja negra.
#
# Requisitos:
#   brew install graphviz          (macOS; en Linux: apt-get install graphviz)
#   pip install diagrams
# Ejecución:
#   python3 c4_nivel1_contexto.py

import os
from diagrams import Cluster, Diagram, Edge
from diagrams.generic.device import Mobile, Tablet
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.generic.blank import Blank

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

graph_attr = {
    "fontsize": "18",
    "labelloc": "t",
    "nodesep": "1.2",
    "ranksep": "2.0",
    "splines": "polyline",
    "concentrate": "false", 
    "pad": "0.8",
    "dpi": "150",
}

with Diagram(
    "C4 Nivel 1: Contexto - Sistema FiberLink",
    filename=os.path.join(BASE_DIR, "c4_nivel1_contexto"),
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
):
    
    # ==================== USUARIOS ====================
    with Cluster("Usuarios del Sistema"):
        clientes = Mobile("Clientes\n(App Móvil + Portal Web)")
        vendedores = Tablet("Vendedores de Campo\n(Tablets)")
        tecnicos = Mobile("Técnicos de Campo\n(App Móvil)")
        call_center = Users("Agentes Call Center")
        noc_ops = Users("Operadores NOC")
        ejecutivos = Users("Ejecutivos\n(Reportes y KPIs)")
    
    # ==================== SISTEMA PRINCIPAL ====================
    fiberlink_system = Server("Sistema FiberLink\n\nPlataforma de Integración\nEmpresarial Multinube\n(AWS + Azure)\n\n• Gestión de Solicitudes\n• Cobertura y Capacidad\n• Programación/Activación\n• Trazabilidad\n• Observabilidad de Red")
    
    # ==================== SISTEMAS EXTERNOS ====================
    with Cluster("Sistemas Externos"):
        crm_comercial = Server("CRM Comercial\n(SaaS)\n\nContratos y\nCasos de Venta")
        
        pagos = Server("Pasarelas de Pago\n\nProcesamiento\nde Pagos Online")
        
        whatsapp = Server("WhatsApp Business\n(Meta)\n\nNotificaciones\nInstantáneas")
        
        ordenes_legacy = Server("Sistema de Órdenes\n(Legacy)\n\nGestión de Órdenes\nExistentes")
        
        itsm = Server("Mesa de Ayuda\n(ITSM)\n\nGestión de\nIncidentes y Casos")
    
    # ==================== INFRAESTRUCTURA DE RED ====================
    with Cluster("Infraestructura de Red Física"):
        red_fibra = Server("Red de Fibra Óptica\n(OLT/BRAS)\n\nInfraestructura\nFísica de Red")
    
    # ==================== FLUJOS PRINCIPALES ====================
    
    # Usuarios principales -> Sistema FiberLink
    clientes >> Edge(label="Consulta servicios,\nEstado, Pagos") >> fiberlink_system
    vendedores >> Edge(label="Registra solicitudes,\nConsulta cobertura") >> fiberlink_system
    tecnicos >> Edge(label="Actualiza estado\nde instalaciones") >> fiberlink_system
    call_center >> Edge(label="Gestiona casos\ny consultas") >> fiberlink_system
    noc_ops >> Edge(label="Monitorea red,\nGestiona incidentes") >> fiberlink_system
    ejecutivos >> Edge(label="Consulta KPIs\ny reportes") >> fiberlink_system
    
    # Sistema FiberLink -> Sistemas Externos
    fiberlink_system >> Edge(label="Sincroniza contratos\ny casos de venta") >> crm_comercial
    fiberlink_system >> Edge(label="Procesa pagos") >> pagos
    fiberlink_system >> Edge(label="Envía notificaciones\nWhatsApp") >> whatsapp
    fiberlink_system >> Edge(label="Consulta/Actualiza\nórdenes existentes") >> ordenes_legacy
    fiberlink_system >> Edge(label="Crea/Actualiza\ntickets e incidentes") >> itsm
    
    # Sistema FiberLink <-> Infraestructura Red
    fiberlink_system >> Edge(label="Provisiona servicios,\nConfigura equipos") >> red_fibra
    red_fibra >> Edge(label="Telemetría, alarmas,\nEstado de equipos") >> fiberlink_system

print("Diagrama C4 Nivel 1 - Contexto generado:", os.path.join(BASE_DIR, "c4_nivel1_contexto.png"))