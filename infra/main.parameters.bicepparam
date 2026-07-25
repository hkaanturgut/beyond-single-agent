using './main.bicep'

// Override these values for your environment.
// Run:  az deployment group create \
//         --resource-group <rg> \
//         --template-file infra/main.bicep \
//         --parameters infra/main.parameters.bicepparam

param environmentName = 'prod'
param location = 'eastus'
param foundryHubName = 'foundry-trip-planner-prod'
param foundryProjectName = 'trip-planner-prod'
param modelDeploymentName = 'gpt-5-mini'
param modelPublisherFormat = 'OpenAI'
param modelVersion = '2025-08-07'
param modelSkuName = 'GlobalStandard'
param modelCapacity = 1

// Add your Azure AD object ID here to get Azure AI Developer access in the Foundry UI.
// Find your OID: az ad signed-in-user show --query id -o tsv
param developerPrincipalIds = []
