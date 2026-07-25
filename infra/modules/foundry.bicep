// infra/modules/foundry.bicep
// ---------------------------------------------------------------------------
// Deploys:
//   - Azure AI Services account (AIServices kind) - the new Foundry resource
//   - Azure AI Foundry Project (CognitiveServices/accounts/projects) - new API
//     This creates a project visible in the new Foundry UI accessible via:
//     https://<ai-services>.services.ai.azure.com/api/projects/<project>
//   - Model deployment (Azure OpenAI compatible)
//   - RBAC: Azure AI Developer role for optional user principals
// ---------------------------------------------------------------------------

@description('Name of the Azure AI Services account (becomes the services.ai.azure.com subdomain).')
param aiServicesAccountName string

@description('Name of the Foundry Project under the AI Services account.')
param projectName string

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

@description('Azure region.')
param location string

@description('Resource tags.')
param tags object = {}


@description('Principal IDs that receive the Azure AI Developer role on the AI Services account.')
param developerPrincipalIds array = []

// ---------------------------------------------------------------------------
// Azure AI Services account
// ---------------------------------------------------------------------------
resource aiServicesAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
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
    disableLocalAuth: false
    allowProjectManagement: true
  }
}

// ---------------------------------------------------------------------------
// Model deployment
// ---------------------------------------------------------------------------
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
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
// Foundry Project under the AI Services account
// This is the new CognitiveServices project type that the azure-ai-projects
// SDK v2+ and new Foundry UI require.
// ---------------------------------------------------------------------------
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiServicesAccount
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Trip Planner multi-agent demo project'
    displayName: 'Trip Planner'
  }
  dependsOn: [
    modelDeployment
  ]
}

// ---------------------------------------------------------------------------
// RBAC: Azure AI Developer + Foundry Owner on the AI Services account
// Azure AI Developer: read models, call endpoints.
// Foundry Owner: create/run/manage agents (Microsoft.CognitiveServices/* data actions).
// ---------------------------------------------------------------------------
var aiDeveloperRoleId = '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
var foundryOwnerRoleId = 'c883944f-8b7b-4483-af10-35834be79c4a' // Foundry Owner

resource aiDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in developerPrincipalIds: {
  name: guid(aiServicesAccount.id, principalId, aiDeveloperRoleId)
  scope: aiServicesAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', aiDeveloperRoleId)
    principalId: principalId
    principalType: 'User'
  }
}]

resource foundryOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in developerPrincipalIds: {
  name: guid(aiServicesAccount.id, principalId, foundryOwnerRoleId)
  scope: aiServicesAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryOwnerRoleId)
    principalId: principalId
    principalType: 'User'
  }
}]

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output projectId string = foundryProject.id
output modelsAccountId string = aiServicesAccount.id
output projectEndpoint string = 'https://${aiServicesAccount.name}.services.ai.azure.com/api/projects/${foundryProject.name}'
output modelsEndpoint string = 'https://${aiServicesAccount.name}.services.ai.azure.com/models'
