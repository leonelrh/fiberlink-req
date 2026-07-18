#!/usr/bin/env python3
"""
Diagrama C4 - Nivel 1: Contexto del Sistema (Arquitectura Alternativa) - FiberLink

Idéntico en actores y sistemas externos al contexto de la arquitectura vigente
(../../c4/diagrama_c4_contexto.py): los ejes que distinguen a la alternativa
(Kafka/Confluent como backbone único, cómputo serverless, CDC de inventario,
Portal consolidado en Azure) son detalle de implementación que un diagrama de
contexto C4 no debe exponer. Único cambio: la etiqueta de "Inventario de Red"
aclara que ahora se accede vía réplica CDC.

Estilo: mismas cajas de color solidas con la paleta estandar del modelo C4
(persona en azul oscuro, sistema en foco en azul medio, sistemas externos en
gris) que ../../c4/diagrama_c4_contexto.py.
"""

from diagrams import Diagram, Cluster, Edge, Node

PERSON_FILL, PERSON_BORDER = "#08427B", "#052E56"
SYSTEM_FILL, SYSTEM_BORDER = "#1168BD", "#0B4884"
EXT_FILL, EXT_BORDER = "#8C8C8C", "#6B6B6B"

BOUNDARY_ATTR = {"bgcolor": "white", "style": "dashed", "pencolor": "#8C8C8C", "fontcolor": "#3C3C3C"}


def _box(label: str, tag: str, fill: str, border: str) -> Node:
    return Node(
        f"{label}\n[{tag}]",
        shape="box",
        style="filled,rounded",
        fillcolor=fill,
        color=border,
        fontcolor="white",
        fontsize="14",
        fontname="Sans-Serif",
        fixedsize="false",
        labelloc="c",
        margin="0.28,0.2",
        width="0",
        height="0",
    )


def person(label: str) -> Node:
    return _box(label, "Persona", PERSON_FILL, PERSON_BORDER)


def system_focus(label: str) -> Node:
    return _box(label, "Sistema de software", SYSTEM_FILL, SYSTEM_BORDER)


def system_ext(label: str) -> Node:
    return _box(label, "Sistema externo", EXT_FILL, EXT_BORDER)


def create_c4_context_alternativa():
    with Diagram(
        "C4 Nivel 1 - Contexto - Plataforma FiberLink (Alternativa)",
        filename="diagrama_c4_contexto",
        show=False,
        direction="TB",
        graph_attr={
            "fontsize": "22",
            "labelloc": "t",
            "splines": "ortho",
            "nodesep": "0.9",
            "ranksep": "1.3",
            "pad": "0.3",
            "bgcolor": "white",
        },
        edge_attr={
            "fontsize": "12",
            "fontname": "Sans-Serif",
            "fontcolor": "#3C3C3C",
            "color": "#8C8C8C",
        },
    ):
        with Cluster("Personas (Canales)", graph_attr=BOUNDARY_ATTR):
            u_cliente = person("Cliente / Prospecto\nConsulta cobertura, contrata y\nda seguimiento a su servicio")
            u_asesor = person("Asesor Comercial / Call Center\nRegistra solicitudes y atiende\nincidentes de clientes")
            u_vendedor = person("Vendedor de Campo\nRegistra solicitudes en campo\n(tablet offline)")
            u_tecnico = person("Técnico de Campo\nInstala y activa el\nservicio en sitio")
            u_noc = person("Operador NOC\nMonitorea la red y\ngestiona incidentes")

        plataforma = system_focus(
            "Plataforma FiberLink\nPermite consultar cobertura, contratar, instalar,\n"
            "activar y operar el servicio de Internet por fibra"
        )

        with Cluster("Sistemas Externos (on-premises / SaaS)", graph_attr=BOUNDARY_ATTR):
            crm = system_ext("CRM Comercial\nGestión comercial de clientes")
            oracle = system_ext("Inventario de Red\nNodos, CTOs y puertos\n(fuente de verdad, replicado vía CDC)")
            oss = system_ext("OSS de Provisión\nAprovisiona equipos de red")
            erp = system_ext("ERP de Facturación\nFacturación y cuentas de cliente")
            nms = system_ext("NMS Regional\nMonitoreo y alarmas de red")

        u_cliente >> Edge(label="usa") >> plataforma
        u_asesor >> Edge(label="usa") >> plataforma
        u_vendedor >> Edge(style="dashed") >> plataforma
        u_tecnico >> Edge(label="usa") >> plataforma
        u_noc >> Edge(label="usa") >> plataforma

        plataforma >> Edge(label="consulta/actualiza\ndatos comerciales") >> crm
        plataforma >> Edge(label="consulta topología,\nnodos y puertos") >> oracle
        plataforma >> Edge(label="provisiona y activa\nel servicio") >> oss
        plataforma >> Edge(label="sincroniza datos\nde facturación") >> erp
        nms >> Edge(label="emite alarmas y eventos\n(2.6M eventos/hora)") >> plataforma


if __name__ == "__main__":
    create_c4_context_alternativa()
    print("Diagrama generado: diagrama_c4_contexto.png")
