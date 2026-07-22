// infra/modules/foundry.bicep
// ---------------------------------------------------------------------------
// Deploys:
//   - Azure AI Foundry Hub (MachineLearningServices workspace, kind=Hub)
//   - Azure AI Foundry Project  (kind=Project, linked to the hub)
//   - Model deployment (Azure OpenAI compatible) inside the project
// ---------------------------------------------------------------------------

@description('Name of the Foundry Hub workspace.')
param hubName string

@description('Name of the Foundry Project workspace.')
param projectName string

@description('Model deployment name (e.g. gpt-4o-mini).')
param modelDeploymentName string = 'gpt-4o-mini'

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
// Azure OpenAI connection on the Hub (add more connections here as needed)
// ---------------------------------------------------------------------------
// NOTE: An Azure OpenAI resource must already exist in your subscription.
// Uncomment and fill in the connection details to link it to the hub.
//
// resource openAiConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
//   name: 'aoai-trip-planner'
//   parent: foundryHub
//   properties: {
//     category: 'AzureOpenAI'
//     target: 'https://<your-aoai-resource>.openai.azure.com/'
//     authType: 'ApiKey'
//     credentials: {
//       key: '<your-api-key>'  // Use a Key Vault reference in production!
//     }
//   }
// }

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output hubId string = foundryHub.id
output projectId string = foundryProject.id
output projectEndpoint string = 'https://${foundryProject.name}.services.ai.azure.com/api/projects/${foundryProject.name}'
