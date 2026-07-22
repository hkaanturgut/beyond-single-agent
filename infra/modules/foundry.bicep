// infra/modules/foundry.bicep
// ---------------------------------------------------------------------------
// Deploys:
//   - Azure AI Foundry Hub (MachineLearningServices workspace, kind=Hub)
//   - Azure AI Foundry Project (kind=Project, linked to the hub)
//   - Azure AI Services account (AIServices)
//   - Model deployment (Azure OpenAI compatible) inside the AI Services account
//   - Hub connection to the model endpoint
// ---------------------------------------------------------------------------

@description('Name of the Foundry Hub workspace.')
param hubName string

@description('Name of the Foundry Project workspace.')
param projectName string

@description('Name of the Azure AI Services account backing the model deployment.')
param aiServicesAccountName string

@description('Model deployment name (e.g. gpt-4.1-mini).')
param modelDeploymentName string = 'gpt-4.1-mini'

@description('Azure region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Resource ID of the backing Storage Account.')
param storageAccountId string

@description('Resource ID of Application Insights (optional but recommended).')
param appInsightsId string = ''

// ---------------------------------------------------------------------------
// Foundry Hub
// ---------------------------------------------------------------------------
resource foundryHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: hubName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'Hub'
  properties: {
    description: 'Azure AI Foundry Hub for the trip-planner demo'
    storageAccount: storageAccountId
    applicationInsights: appInsightsId != '' ? appInsightsId : null
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------------------------------------
// Foundry Project (child of the Hub)
// ---------------------------------------------------------------------------
resource foundryProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'Project'
  properties: {
    description: 'Trip Planner demo project'
    hubResourceId: foundryHub.id
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------------------------------------
// Azure AI Services account + model deployment
// ---------------------------------------------------------------------------
resource aiServicesAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: aiServicesAccountName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: aiServicesAccountName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: true
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: aiServicesAccount
  name: modelDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'Microsoft'
      name: modelDeploymentName
      version: '2025-04-14'
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

// ---------------------------------------------------------------------------
// Hub connection to the AI Services account
// ---------------------------------------------------------------------------
resource modelConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01-preview' = {
  parent: foundryHub
  name: 'foundry-models'
  properties: {
    category: 'AIServices'
    target: 'https://${aiServicesAccountName}.services.ai.azure.com/models'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: aiServicesAccount.id
    }
  }
  dependsOn: [
    foundryProject
    modelDeployment
  ]
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output hubId string = foundryHub.id
output projectId string = foundryProject.id
output projectEndpoint string = 'https://${foundryProject.name}.services.ai.azure.com/api/projects/${foundryProject.name}'
output modelsAccountId string = aiServicesAccount.id
output modelsEndpoint string = 'https://${aiServicesAccount.name}.services.ai.azure.com/models'
