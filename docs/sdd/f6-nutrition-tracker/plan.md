# F6 — Nutrition Tracker: Technical Plan

> **Feature ID**: F6  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05

---

## 1. File Map

```
backend/
├── routes/nutrition.py          # POST /log-meal, GET /trends
├── agents/agent3_nutrition.py   # AI agent (runs in F3 pipeline)
└── data/ifct_nutrition.json     # Indian Food Composition Table

frontend/
├── nutrition.html               # Nutrition page layout
└── js/nutrition.js              # Load data, render chart + meal plan + deficiencies
```

---

## 2. Architecture

```mermaid
flowchart TD
    A[nutrition.js] -->|apiFetch| B[GET /nutrition/trends]
    A -->|apiFetch| C[GET /consultation/report/{id}]
    B --> D[Nutrition Score Chart]
    C --> E[Focus + Deficiencies + Meal Plan]

    F[Log Meal Form] -->|apiFetch| G[POST /nutrition/log-meal]
    G --> H[IFCT JSON Lookup]
    H --> I[Return Estimated Nutrients]
```

---

## 3. Data Flow

1. **Page Load**: `loadNutrition()` fetches `/nutrition/trends` for chart + `/consultation/report/{id}` for meal plan data.
2. **Chart Rendering**: Chart.js line chart with green color, 0–100% y-axis.
3. **Focus + Deficiencies**: Rendered from report's `nutrition` object.
4. **Meal Plan**: Day navigation using `currentDay` index, `renderMealPlan()` reads from `mealPlan[currentDay]`.
5. **Meal Logging**: User submits food items → backend matches against IFCT → returns nutrient estimates.

### IFCT Lookup Logic
```
For each food item in request:
  lowercase the item name
  for each IFCT entry:
    if item_name in entry.food_name.lower() OR item_name in entry.food_name_hindi:
      accumulate nutrients from entry.per_100g
      break (first match only)
```

---

## 4. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| IFCT data as local JSON | No API dependency | Fast, free, offline-capable |
| Score = iron fulfillment % | Simple, single-nutrient metric | Iron is most common deficiency in India |
| Default score 75 for missing data | Avoids zero-spike in chart | Better UX than showing zeros |
| 5 meal slots per day | Indian eating pattern | Matches standard Indian meal structure |

---

## 5. Known Limitations

| Limitation | Potential Fix |
|------------|---------------|
| IFCT dataset is small (~100 items) | Expand dataset or use external nutrition API |
| No meal log persistence | Save logs to a new DB table |
| Score only based on iron | Multi-nutrient scoring algorithm |
| No food autocomplete in log form | Add typeahead from IFCT dataset |
