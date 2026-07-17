# Stack Tecnológico GCP - FiberLink

# Stack Tecnológico

**Proveedor de Nube:** Google Cloud Platform (GCP)

## Servicios

### Cómputo

- **Cloud Functions**
    - Utilizar cuando la carga de trabajo es intermitente, basada en eventos o impredecible.
    - Ideal para procesos serverless, integraciones, APIs ligeras y automatización.

- **Cloud Run**
    - Recomendado para aplicaciones y microservicios empaquetados en contenedores.
    - Escala automáticamente hasta cero cuando no existe tráfico.
    - Ideal para APIs REST, aplicaciones web y procesamiento de eventos.

- **Google Kubernetes Engine (GKE)**
    - Utilizar cuando se requiere Kubernetes administrado.
    - Recomendado para arquitecturas complejas, múltiples microservicios y necesidades avanzadas de orquestación.

- **Compute Engine**
    - Para aplicaciones que requieren máquinas virtuales con mayor control sobre el sistema operativo y la infraestructura.

---

### Contenedores

- **Repositorio de imágenes Docker**
    - Artifact Registry

- **Orquestador de contenedores**
    - Preferencia: Cloud Run para la mayoría de microservicios.
    - Google Kubernetes Engine (GKE) cuando se requieren capacidades avanzadas de Kubernetes.

---

### Almacenamiento

- **Archivos y Objetos**
    - Cloud Storage

- **Sistema de archivos compartido**
    - Filestore

- **Data Lake**
    - Cloud Storage

---

### Bases de Datos

- **SQL**
    - Cloud SQL (PostgreSQL, MySQL, SQL Server)

- **NoSQL**
    - Firestore
    - Bigtable

- **Caché**
    - Memorystore for Redis

---

### Redes y Entrega de Contenidos

- **CDN (Content Delivery Network)**
    - Cloud CDN

- **API Gateway**
    - API Gateway
    - Apigee (para gestión avanzada de APIs)

- **DNS (Domain Name System)**
    - Cloud DNS

- **Balanceador de carga**
    - Cloud Load Balancing

- **Conectividad privada**
    - Virtual Private Cloud (VPC)
    - Private Service Connect



---

### Integración de Aplicaciones

- Pub/Sub
- Eventarc
- Cloud Tasks
- Workflows
- Cloud Scheduler

---

### Observabilidad

- **Métricas y Logs**
    - Cloud Monitoring
    - Cloud Logging

- **Trazabilidad Distribuida**
    - Cloud Trace

- **Profiling**
    - Cloud Profiler

- **Dashboards**
    - Managed Service for Grafana


---

### Análisis de Datos

- BigQuery
- Dataflow
- Dataproc
- Pub/Sub
- Bigtable
- Dataplex
- Data Fusion
- Looker

---

### Seguridad, Identidad y Cumplimiento

- Cloud IAM
- Secret Manager
- Cloud Key Management Service (Cloud KMS)
- Identity-Aware Proxy (IAP)
- Cloud Armor
- Security Command Center
- Cloud Audit Logs
- VPC Service Controls

---

### Front-End

- Firebase Hosting
- Cloud Run
- Cloud CDN
- Maps Platform

---
