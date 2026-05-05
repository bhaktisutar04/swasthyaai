# F6 — Nutrition Tracker: Specification

> **Feature ID**: F6  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F3 (Nutrition agent generates meal plan)

---

## 1. Overview

The Nutrition Tracker displays AI-generated nutrition analysis (deficiencies, focus areas, tips) and a personalized 7-day Indian meal plan from a completed consultation. It also provides a meal logging feature with automatic nutrient estimation using the IFCT 2017 (Indian Food Composition Table) dataset and tracks nutrition score trends over time.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-6.1 | As a patient, I can view my nutritional focus area and tips after consultation. | P0 |
| US-6.2 | As a patient, I can see my nutrient deficiencies. | P0 |
| US-6.3 | As a patient, I can browse my 7-day meal plan day by day. | P0 |
| US-6.4 | As a patient, I can see nutrient values (iron, protein, calories, vitamin C) for each meal. | P1 |
| US-6.5 | As a patient, I can log my actual meals and get estimated nutrient values. | P1 |
| US-6.6 | As a patient, I can see my nutrition score trend over the past week. | P2 |

---

## 3. Functional Requirements

### Meal Plan Display
- **FR-6.1**: Load meal plan data from the latest consultation report (`GET /consultation/report/{session_id}`).
- **FR-6.2**: Display 7 days × 5 meal slots: breakfast, mid_morning, lunch, evening_snack, dinner.
- **FR-6.3**: Each meal shows food items and nutrient breakdown (iron_mg, protein_g, calories, vitamin_c_mg).
- **FR-6.4**: Day navigation: prev/next buttons, current day label ("Day 1 — Monday").

### Nutritional Focus
- **FR-6.5**: Display `nutritional_focus` text (e.g., "Increasing Iron and Vitamin C intake").
- **FR-6.6**: Display `nutrition_tips[]` list (e.g., "Pair iron-rich foods with Vitamin C").

### Deficiency Display
- **FR-6.7**: List nutrient deficiencies with severity badges.
- **FR-6.8**: Show "No significant deficiencies detected ✅" if array is empty.

### Meal Logging
- **FR-6.9**: `POST /nutrition/log-meal` accepts: session_id, meal_type, items[] (food names), date.
- **FR-6.10**: Backend matches food items against IFCT 2017 dataset (fuzzy search on English + Hindi names).
- **FR-6.11**: Returns estimated nutrients: iron_mg, protein_g, vitamin_c_mg, calories.

### Nutrition Trends
- **FR-6.12**: `GET /nutrition/trends?days=7` returns score labels and values over N days.
- **FR-6.13**: Nutrition score calculated from deficiency data: `min(100, (current_iron / required_iron) × 100)`.
- **FR-6.14**: Displayed as a Chart.js line chart.

---

## 4. API Contract

### POST `/nutrition/log-meal`
```json
// Request
{ "session_id": "CNS-...", "meal_type": "breakfast", "items": ["poha", "chai"], "date": "2026-05-05" }
// Response 200
{ "success": true, "data": { "logged_items": ["poha", "chai"], "meal_type": "breakfast", "date": "2026-05-05", "estimated_nutrients": { "iron_mg": 3.2, "protein_g": 5.1, "vitamin_c_mg": 0, "calories": 250 } } }
```

### GET `/nutrition/trends?days=7`
```json
{ "success": true, "data": { "labels": ["May 01", "May 02", ...], "scores": [70, 78, 82, ...], "average": 76.7, "trend": "improving" } }
```

---

## 5. Data Sources

| Source | Purpose |
|--------|---------|
| `ifct_nutrition.json` (local) | Food → nutrient lookup for meal logging |
| Consultation report API | Meal plan, deficiencies, focus, tips |
| Consultation DB records | Nutrition score trend calculation |
