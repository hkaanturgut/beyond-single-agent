using './main.bicep'

// Override these values for your environment.
// Run:  az deployment group create \
//         --resource-group <rg> \
//         --template-file infra/main.bicep \
//         --parameters infra/main.parameters.bicepparam

param environmentName = 'prod'
param location = 'eastus'
param modelDeploymentName = 'gpt-5-mini'
param modelPublisherFormat = 'OpenAI'
param modelVersion = '2025-08-07'
param modelSkuName = 'GlobalStandard'
// Capacity is in units of 1,000 tokens-per-minute (TPM). The workflow fans out
// several agents concurrently (researcher + planner + budget, then optimizer /
// finalizer), so a capacity of 1 (1K TPM) is far too low and triggers HTTP 429
// 'rate_limit_exceeded'. 50 (= 50K TPM) gives comfortable headroom for the demo.
// Raise or lower to fit your subscription's available quota for the model.
param modelCapacity = 50

// Add your Azure AD object ID here to get Azure AI Developer access in the Foundry UI.
// Find your OID: az ad signed-in-user show --query id -o tsv
param developerPrincipalIds = []
