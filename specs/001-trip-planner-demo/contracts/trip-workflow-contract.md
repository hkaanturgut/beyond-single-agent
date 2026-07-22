# Contract: Trip Workflow Inputs, Stage Outputs, and Routing

## Request Contract

### User Prompt Contract

- **Pattern**: `Plan my 3-day trip to <destination> in <month> with budget $<amount>`
- **Required fields**:
  - Destination
  - Month
  - Budget amount

### Parsed Request Shape

```json
{
  "destination": "Kyoto",
  "month": "October",
  "budget_usd": 1800,
  "preferences": []
}
```

## Stage Output Contracts

### ResearcherAgent output

```json
{
  "attractions": ["Fushimi Inari", "Arashiyama Bamboo Grove"],
  "weather_summary": "Mild days, cool evenings, occasional rain.",
  "events": ["Jidai Matsuri (late October)"],
  "cultural_tips": ["Carry cash for small shops", "Observe shrine etiquette"]
}
```

### PlannerAgent output

```json
{
  "days": [
    {
      "day_number": 1,
      "slots": [
        {
          "start_time": "09:00",
          "end_time": "11:00",
          "activity": "Visit Kiyomizu-dera"
        }
      ]
    }
  ],
  "conflict_flags": []
}
```

### BudgetAgent output

```json
{
  "flight_estimate": 650,
  "hotel_estimate": 540,
  "food_estimate": 240,
  "activity_estimate": 220,
  "total_estimate": 1650,
  "confidence": "medium"
}
```

## Aggregation Contract

Aggregator MUST produce:

```json
{
  "proposal_id": "trip-20260722-001",
  "request": {},
  "research": {},
  "itinerary": {},
  "budget": {}
}
```

## Routing Contract

Routing condition:

- Route to **optimizer** if:
  - `total_estimate > budget_usd`, OR
  - `conflict_flags` is non-empty.

- Route to **finalizer** otherwise.

Routing result shape:

```json
{
  "is_over_budget": false,
  "has_schedule_conflicts": false,
  "route": "finalize",
  "reasons": []
}
```

## Final Output Contract

Finalizer (or optimizer + finalizer path) MUST return:

```json
{
  "markdown": "# Trip Brief\\n...",
  "output_path": "output/trip-kyoto-20260722-102355.md",
  "generated_at": "2026-07-22T10:23:55Z"
}
```

Required markdown sections:

1. Trip Overview
2. Day-by-Day Itinerary (3 days)
3. Budget Breakdown
4. Packing/Preparation Tips
5. Optimization Notes (if optimization route was used)

