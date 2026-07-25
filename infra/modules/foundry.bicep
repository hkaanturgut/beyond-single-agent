// infra/modules/foundry.bicep
// ---------------------------------------------------------------------------
// Deploys:
//   - Azure AI Foundry Hub (MachineLearningServices workspace, kind=Hub)
//   - Azure AI Foundry Project (kind=Project, linked to the hub)
//   - Azure AI Services account (AIServices)
//   - Model deployment (Azure OpenAI compatible) inside the AI Services account
//   - Hub connection to the model endpoint
//   - RBAC: Azure AI Developer role for deployer and optional user principals
// ---------------------------------------------------------------------------

@description('Name of the Foundry Hub workspace.')
param hubName string

@description('Name of the Foundry Project workspace.')
param projectName string

@description('Name of the Azure AI Services account backing the model deployment.')
param aiServicesAccountName string

@description('Model deployment name (e.g. gpt-5-mini).')
param modelDeploymentName string = 'gpt-5-mini'

@description('Model provider format (for Azure OpenAI models, use OpenAI).')
param modelPublisherFormat string = 'OpenAI'

@description('Model version available in the target region/subscription.')
param modelVersion string = '2025-08-07'

@description('Model deployment SKU name available in the target region/subscription.')
param modelSkuName string = 'GlobalStandard'

@description('Model deployment capacity.')
param modelCapacity int = 1

@description('Azure region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Resource ID of the backing Storage Account.')
param storageAccountId string

@description('Resource ID of Application Insights (optional but recommended).')
param appInsightsId string = ''

@description('Principal IDs that should receive the Azure AI Developer role on the AI Services account. Enables Foundry UI access and agent management.')
param developerPrincipalIds array = []

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
    name: modelSkuName
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: modelPublisherFormat
      name: modelDeploymentName
      version: modelVersion
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
// RBAC: Grant Azure AI Developer on the AI Services account
// Azure AI Developer allows data-plane operations: create/run agents,
// call model endpoints, and view agents in the Foundry UI.
// ---------------------------------------------------------------------------
var aiDeveloperRoleId = '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer

resource aiDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in developerPrincipalIds: {
  name: guid(aiServicesAccount.id, principalId, aiDeveloperRoleId)
  scope: aiServicesAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', aiDeveloperRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output hubId string = foundryHub.id
output projectId string = foundryProject.id
output projectEndpoint string = 'https://${foundryProject.name}.services.ai.azure.com/api/projects/${foundryProject.name}'
output modelsAccountId string = aiServicesAccount.id
output modelsEndpoint string = 'https://${aiServicesAccount.name}.services.ai.azure.com/models'
