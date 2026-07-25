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
// several agents concurrently, and each runs hosted tool loops (web_search /
// code_interpreter) with reasoning — so the first seconds produce a burst of
// requests. Capacity 1 hard-fails with 429; even 50 still bursts past the
// per-window limit. 150 (= 150K TPM) gives comfortable headroom for the demo.
// Check your remaining quota first:
//   az cognitiveservices usage list -l <region> \
//     --query "[?contains(name.value,'gpt-5-mini')].{n:name.value,cur:currentValue,lim:limit}" -o table
param modelCapacity = 150

// Add your Azure AD object ID here to get Azure AI Developer access in the Foundry UI.
// Find your OID: az ad signed-in-user show --query id -o tsv
param developerPrincipalIds = []
