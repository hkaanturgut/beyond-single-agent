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

## After deployment

1. Copy the `foundryProjectEndpoint` output value.
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
- The optional Azure OpenAI connection block in `modules/foundry.bicep` is
  commented out.  Uncomment and fill in your AOAI resource details to link it.
