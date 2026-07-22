using './main.bicep'

// Override these values for your environment.
// Run:  az deployment group create \
//         --resource-group <rg> \
//         --template-file infra/main.bicep \
//         --parameters infra/main.parameters.bicepparam

param environmentName = 'dev'
param location = 'eastus2'
param foundryHubName = 'foundry-trip-planner-dev'
param foundryProjectName = 'trip-planner-dev'
param modelDeploymentName = 'gpt-4o-mini'
