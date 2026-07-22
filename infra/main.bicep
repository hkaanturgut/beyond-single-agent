// infra/main.bicep
// ---------------------------------------------------------------------------
// Main deployment entry point for the Beyond a Single Agent — Trip Planner demo.
// Deploys:
//   - Azure AI Foundry hub
//   - Foundry project
//   - Azure AI Services account + model deployment
//   - Hub-to-model connection
//   - Storage Account (required by Foundry)
//   - Application Insights (optional observability)
// ---------------------------------------------------------------------------

targetScope = 'resourceGroup'

@description('Short environment label used as a resource-name suffix.')
param environmentName string = 'dev'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Name of the Foundry Hub resource.')
param foundryHubName string = 'foundry-trip-planner-${environmentName}'

@description('Name of the Foundry Project resource.')
param foundryProjectName string = 'trip-planner-${environmentName}'

@description('Name of the Azure AI Services account that hosts the deployed model.')
param aiServicesAccountName string = 'aitrip${uniqueString(resourceGroup().id, environmentName)}'

@description('Model deployment name inside the Foundry project.')
param modelDeploymentName string = 'gpt-4.1-mini'

@description('Tags applied to all resources.')
param tags object = {
  project: 'beyond-single-agent'
  environment: environmentName
}

// ---------------------------------------------------------------------------
// Storage account — required backing store for the Foundry resource
// ---------------------------------------------------------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'sttrip${uniqueString(resourceGroup().id, environmentName)}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// ---------------------------------------------------------------------------
// Application Insights — optional but recommended for production observability
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
// Azure AI Foundry Hub (Microsoft.MachineLearningServices/workspaces kind=Hub)
// ---------------------------------------------------------------------------
module foundry 'modules/foundry.bicep' = {
  name: 'foundry-deploy'
  params: {
    hubName: foundryHubName
    projectName: foundryProjectName
    aiServicesAccountName: aiServicesAccountName
    modelDeploymentName: modelDeploymentName
    location: location
    tags: tags
    storageAccountId: storageAccount.id
    appInsightsId: appInsights.id
  }
}

// ---------------------------------------------------------------------------
// Outputs — used by azd (azure.yaml) and the quickstart guide
// ---------------------------------------------------------------------------
output foundryProjectEndpoint string = foundry.outputs.projectEndpoint
output foundryModelsEndpoint string = foundry.outputs.modelsEndpoint
output storageAccountName string = storageAccount.name
output appInsightsConnectionString string = appInsights.properties.ConnectionString
