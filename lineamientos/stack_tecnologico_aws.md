## Stack Tecnológico

# Stack Tecnológico

**Proveedor de Nube:** Amazon Web Services (AWS)

## Servicios

### Cómputo

- **AWS Lambda**
  - Utilizar cuando la carga de trabajo es intermitente o impredecible.
  - Ideal para aplicaciones serverless, procesamiento de eventos e integraciones.

- **AWS Fargate**
  - Recomendado para microservicios ejecutados en contenedores sin administrar servidores.
  - Ideal cuando el tráfico es constante y los servicios deben permanecer disponibles 24/7.

- **Amazon ECS (Elastic Container Service)**
  - Servicio administrado para ejecutar aplicaciones en contenedores.
  - Recomendado para la mayoría de arquitecturas de microservicios por su simplicidad y menor costo operativo.

- **Amazon EKS (Elastic Kubernetes Service)**
  - Utilizar cuando se requiere Kubernetes administrado.
  - Recomendado para organizaciones que ya utilizan Kubernetes o necesitan funcionalidades avanzadas de orquestación.

- **Amazon EC2**
  - Para aplicaciones que requieren control total sobre el sistema operativo o cargas de trabajo tradicionales.

---

### Contenedores

- **Repositorio de imágenes Docker**
  - Amazon Elastic Container Registry (ECR)

- **Orquestador de contenedores**
  - Preferencia: Amazon ECS con AWS Fargate.
  - Amazon EKS cuando se requieren capacidades avanzadas de Kubernetes.

---

### Almacenamiento

- **Archivos y Objetos**
  - Amazon Simple Storage Service (S3)

- **Sistema de archivos compartido**
  - Amazon Elastic File System (EFS)

- **Almacenamiento por bloques**
  - Amazon Elastic Block Store (EBS)

---

### Bases de Datos

- **SQL**
  - Amazon Aurora PostgreSQL
  - Amazon Aurora MySQL
  - Amazon RDS

- **NoSQL**
  - Amazon DynamoDB

- **Caché**
  - Amazon ElastiCache for Redis

---

### Redes y Entrega de Contenidos

- **CDN (Content Delivery Network)**
  - Amazon CloudFront

- **API Gateway**
  - Amazon API Gateway

- **DNS (Domain Name System)**
  - Amazon Route 53

- **Balanceador de carga**
  - Application Load Balancer (ALB)
  - Network Load Balancer (NLB)

- **Red privada**
  - Amazon Virtual Private Cloud (VPC)

- **Conectividad privada**
  - AWS PrivateLink

---

### Administración y Gobierno

- AWS Systems Manager
- AWS CloudTrail
- AWS CloudFormation
- AWS Config
- AWS Organizations
- AWS Control Tower

---

### Integración de Aplicaciones

- AWS Step Functions
- Amazon Simple Notification Service (SNS)
- Amazon Simple Queue Service (SQS)
- Amazon EventBridge
- Amazon Managed Streaming for Apache Kafka (MSK)

---

### Observabilidad

- **Métricas y Logs**
  - Amazon CloudWatch
- **Trazabilidad Distribuida**
  - AWS X-Ray
- **Dashboards**
  - Amazon Managed Grafana

---

### Análisis de Datos

- Amazon Athena
- Amazon Redshift
- Amazon OpenSearch Service
- Amazon Kinesis
- AWS Glue
- AWS Lake Formation
- Amazon EMR
- Amazon QuickSight

---

### Seguridad, Identidad y Cumplimiento

- Amazon Cognito
- AWS IAM
- AWS IAM Identity Center
- AWS Secrets Manager
- AWS Key Management Service (KMS)
- AWS Certificate Manager (ACM)
- AWS Web Application Firewall (WAF)
- AWS Shield
- Amazon GuardDuty
- AWS Security Hub

---

### Front-End

- AWS Amplify
- Amazon CloudFront
- Amazon Location Service

---