# Stack Tecnológico Azure - FiberLink

## Uso propuesto
Azure puede actuar como capa principal de exposición, gobierno de APIs e integración empresarial, especialmente porque FiberLink ya utiliza Azure API Management y mesa de ayuda.

## Servicios recomendados
- APIs e integración: Azure API Management, Azure Functions, Azure Service Bus, Event Grid, Logic Apps.
- Cómputo: Azure Functions, Azure Container Apps, App Service.
- Datos: Azure SQL, Cosmos DB, Storage Account.
- Seguridad: Microsoft Entra ID, Key Vault, Managed Identity, Application Gateway/WAF.
- Observabilidad: Application Insights, Azure Monitor, Log Analytics Workspace.
- IaC: Bicep o Terraform.

## Criterios de uso
- Usar API Management para exponer APIs de negocio.
- Usar Functions o Container Apps para la capa de integración.
- Usar Application Insights para correlationId y trazabilidad.
- Usar Key Vault para secretos.
