# F6 — Nutrition Tracker: Tasks

> **Feature ID**: F6  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend
- [x] **T6.1**: `POST /nutrition/log-meal` — validate session ownership, lookup IFCT data, return estimated nutrients
- [x] **T6.2**: IFCT lookup: fuzzy match on food_name (English) and food_name_hindi
- [x] **T6.3**: Accumulate nutrients across all logged items (iron, protein, vitamin C, calories)
- [x] **T6.4**: `GET /nutrition/trends` — query consultations, calculate iron-based nutrition scores
- [x] **T6.5**: Return labels (date strings) + scores (0–100) + average + trend direction

### Frontend — Page Layout (`nutrition.html`)
- [x] **T6.6**: Nutrition trend chart canvas (Chart.js)
- [x] **T6.7**: Nutritional focus card
- [x] **T6.8**: Deficiency list card
- [x] **T6.9**: Meal plan card with day navigation

### Frontend — Logic (`nutrition.js`)
- [x] **T6.10**: `loadNutrition()` — fetch trends + report data
- [x] **T6.11**: `renderNutritionChart()` — Chart.js line chart (green, 0-100%)
- [x] **T6.12**: `renderFocus()` — nutritional focus text + tips
- [x] **T6.13**: `renderDeficiencies()` — deficiency list with badges, or "no deficiencies" message
- [x] **T6.14**: `renderMealPlan()` — 5 meal slots with items and nutrients for current day
- [x] **T6.15**: `prevDay()` / `nextDay()` — day navigation with bounds checking
- [x] **T6.16**: Empty state when no session_id or no meal plan data

---

## Verification

- [x] Nutrition trends chart renders with real data
- [x] Focus area and tips display from report data
- [x] Deficiency list renders with severity badges
- [x] Meal plan displays all 5 slots per day
- [x] Day navigation works correctly (Day 1–7)
- [x] Empty state shows "Start Consultation" prompt when no data
