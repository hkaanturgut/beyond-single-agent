// infra/main.bicep
// ---------------------------------------------------------------------------
// Main deployment entry point for the Beyond a Single Agent — Trip Planner demo.
// Deploys:
//   - Azure AI Services account (new Foundry resource type)
//   - Foundry Project (CognitiveServices/accounts/projects — new API)
//   - Model deployment (gpt-5-mini by default)
//   - Application Insights for observability
// ---------------------------------------------------------------------------

targetScope = 'resourceGroup'

@description('Short environment label used as a resource-name suffix.')
param environmentName string = 'prod'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Name of the Azure AI Services account (also the services.ai.azure.com subdomain).')
param aiServicesAccountName string = 'aitrip${uniqueString(resourceGroup().id, environmentName)}'

@description('Name of the Foundry Project.')
param foundryProjectName string = 'trip-planner-${environmentName}'

@description('Model deployment name.')
param modelDeploymentName string = 'gpt-5-mini'

@description('Model provider format.')
param modelPublisherFormat string = 'OpenAI'

@description('Model version.')
param modelVersion string = '2025-08-07'

@description('Model deployment SKU name.')
param modelSkuName string = 'GlobalStandard'

@description('Model deployment capacity.')
param modelCapacity int = 1

@description('Tags applied to all resources.')
param tags object = {
  project: 'beyond-single-agent'
  environment: environmentName
}

@description('Azure AD principal IDs that receive Azure AI Developer role (for Foundry UI access).')
param developerPrincipalIds array = []

// ---------------------------------------------------------------------------
// Application Insights — observability
// ---------------------------------------------------------------------------
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-trip-${environmentName}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-trip-${environmentName}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// ---------------------------------------------------------------------------
// Azure AI Foundry (new CognitiveServices-based pattern)
// ---------------------------------------------------------------------------
module foundry 'modules/foundry.bicep' = {
  name: 'foundry-deploy'
  params: {
    aiServicesAccountName: aiServicesAccountName
    projectName: foundryProjectName
    modelDeploymentName: modelDeploymentName
    modelPublisherFormat: modelPublisherFormat
    modelVersion: modelVersion
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
    location: location
    tags: tags
    developerPrincipalIds: developerPrincipalIds
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output foundryProjectEndpoint string = foundry.outputs.projectEndpoint
output foundryModelsEndpoint string = foundry.outputs.modelsEndpoint
output appInsightsConnectionString string = appInsights.properties.ConnectionString
