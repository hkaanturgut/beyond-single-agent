# Infra — Azure AI Foundry deployment (Bicep)

This directory contains the Bicep templates for the production-oriented Malta
talk deployment of the trip-planner demo.

## What gets deployed

| Resource | Type |
|---|---|
| Storage Account | `Microsoft.Storage/storageAccounts` |
| Log Analytics Workspace | `Microsoft.OperationalInsights/workspaces` |
| Application Insights | `Microsoft.Insights/components` |
| Foundry Hub | `Microsoft.MachineLearningServices/workspaces` (kind=Hub) |
| Foundry Project | `Microsoft.MachineLearningServices/workspaces` (kind=Project) |
| Azure AI Services account | `Microsoft.CognitiveServices/accounts` (kind=AIServices) |
| Model deployment | `Microsoft.CognitiveServices/accounts/deployments` |
| Hub connection to model endpoint | `Microsoft.MachineLearningServices/workspaces/connections` |

## Prerequisites

- Azure CLI ≥ 2.60
- An Azure subscription with Contributor rights on a resource group
- A resource group already created

## Deploy

```bash
# One-time login
az login

# Create or target an existing resource group
az group create --name rg-trip-planner-dev --location eastus2

# Deploy
az deployment group create \
  --resource-group rg-trip-planner-dev \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.bicepparam
```

## Deploy with GitHub Actions

The repo includes `.github/workflows/deploy-foundry.yml`, which deploys the same Bicep stack with Azure Login OIDC.

### Required GitHub secrets

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

### Required Azure setup

1. Create a Microsoft Entra application or user-assigned managed identity.
2. Add a federated identity credential for this repository.
3. Grant the identity `Contributor` on the target resource group.

### Run it

1. Open **Actions** in GitHub.
2. Select **Deploy Azure infrastructure**.
3. Click **Run workflow**.
4. Keep the default inputs or override the resource group, region, and environment name.

## After deployment

1. Copy the `foundryProjectEndpoint` output value.
   The deployment also emits `foundryModelsEndpoint` if you want the raw model
   inference endpoint.
2. Set it in your `.env` file:

   ```
   TRIP_BACKEND=foundry
   FOUNDRY_PROJECT_ENDPOINT=<output value>
   ```

3. Run `az login` (or set a service principal in `.env`) so
   `DefaultAzureCredential` can authenticate.

4. Run the demo:

   ```bash
   python -m trip_planner "Plan my 3-day trip to Lisbon in May with budget $2600"
   ```

## Notes

- No API keys are stored in Bicep.  The Foundry backend uses
  `DefaultAzureCredential` (supports az login, managed identity, and service
  principal via env vars).
- The workflow deploys a `gpt-5-mini` model by default; change
  `infra/main.parameters.bicepparam` or override the workflow input if you want
  a different deployment name.
