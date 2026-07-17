# Stack Tecnológico

**Proveedor de Nube:** Azure

## Servicios

### Cómputo

**Azure Functions**
- Utilizar cuando la carga de trabajo es intermitente, basada en eventos o impredecible.
- Ideal para procesos serverless, integraciones, APIs ligeras y automatización.

**Azure Container Apps**
- Recomendado para microservicios y aplicaciones en contenedores sin administrar Kubernetes.
- Escalado automático basado en HTTP, eventos o Kafka.

**Azure Kubernetes Service (AKS)**
- Utilizar cuando se requiere Kubernetes administrado.
- Recomendado para arquitecturas complejas, múltiples microservicios, service mesh y alta personalización.

**Azure App Service**
- Para aplicaciones web y APIs tradicionales con administración simplificada.
- Ideal cuando no es necesario utilizar contenedores.

---

### Contenedores

- **Repositorio de imágenes Docker**
    - Azure Container Registry (ACR)
- **Orquestador de contenedores**
    - Preferencia: Azure Container Apps para la mayoría de microservicios.
    - Azure Kubernetes Service (AKS) cuando se requieren capacidades avanzadas de Kubernetes.

---

### Almacenamiento

- **Archivos y Objetos**
    - Azure Blob Storage
- **Sistema de archivos compartido**
    - Azure Files
- **Data Lake**
    - Azure Data Lake Storage Gen2

---

### Bases de Datos

- **SQL**
    - Azure Database for PostgreSQL Flexible Server
    - Azure SQL Database
    - Azure Database for MySQL Flexible Server

- **NoSQL**
    - Azure Cosmos DB

- **Caché**
    - Azure Cache for Redis

---

### Redes y Entrega de Contenidos

- **CDN (Content Delivery Network)**
    - Azure Front Door

- **API Gateway**
    - Azure API Management (APIM)

- **DNS (Domain Name System)**
    - Azure DNS

- **Balanceador de carga**
    - Azure Load Balancer
    - Azure Application Gateway

- **Conectividad privada**
    - Azure Virtual Network (VNet)
    - Azure Private Link

---

### Administración y Gobierno

- Azure Resource Manager (ARM)
- Bicep (Infrastructure as Code)
- Azure Policy
- Azure Monitor
- Azure Advisor
- Azure Automation
- Azure Resource Graph

---

### Integración de Aplicaciones

- Azure Service Bus
- Azure Event Grid
- Azure Event Hubs
- Azure Logic Apps
- Azure Durable Functions

---

### Observabilidad

- **Métricas y Logs**
    - Azure Monitor
- **Logs Centralizados**
    - Log Analytics Workspace
- **Trazabilidad Distribuida**
    - Application Insights
- **Dashboards**
    - Azure Managed Grafana


---

### Análisis de Datos

- Azure Synapse Analytics
- Microsoft Fabric
- Azure Data Factory
- Azure Databricks
- Azure Stream Analytics
- Azure Event Hubs
- Azure Data Lake Storage Gen2
- Azure Cosmos DB Analytical Store

---

### Seguridad, Identidad y Cumplimiento

- Microsoft Entra ID
- Azure Key Vault
- Managed Identities
- Azure RBAC
- Microsoft Defender for Cloud
- Microsoft Sentinel
- Azure Web Application Firewall (WAF)
- Azure DDoS Protection
- Azure Firewall
- Microsoft Purview

---

### Front-End

- Azure Static Web Apps
- Azure App Service
- Azure Front Door
- Azure CDN
- Azure Maps
