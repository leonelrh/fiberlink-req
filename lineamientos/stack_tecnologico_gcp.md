# Stack Tecnológico GCP - FiberLink

## Uso propuesto
GCP puede actuar como capa de eventos, analítica y observabilidad complementaria para FiberLink, especialmente por el uso de Pub/Sub y BigQuery.

## Servicios recomendados
- Eventos e integración: Pub/Sub, Eventarc, Cloud Tasks.
- Cómputo: Cloud Run, Cloud Functions.
- Datos y analítica: BigQuery, Cloud Storage, Firestore.
- Seguridad: IAM, Secret Manager, Cloud KMS, Cloud Armor.
- Observabilidad: Cloud Logging, Cloud Monitoring, Cloud Trace.
- IaC: Terraform.

## Criterios de uso
- Usar Pub/Sub para eventos de negocio.
- Usar BigQuery para análisis de eventos y KPIs.
- Usar Cloud Logging y Monitoring para observabilidad.
- Usar Cloud Run para microservicios contenedorizados en GCP.
