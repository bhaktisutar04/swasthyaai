# F7 — Medical Expense Tracker: Specification

> **Feature ID**: F7  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F1 (Authentication)

---

## 1. Overview

The Medical Expense Tracker allows users to manually log medical expenses by category, view monthly summaries with category breakdowns, compare month-over-month spending, visualize 6-month trends, and see AI-estimated savings projections from the consultation pipeline.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-7.1 | As a patient, I can add a medical expense with date, category, amount, and description. | P0 |
| US-7.2 | As a patient, I can see my current month's total medical spending. | P0 |
| US-7.3 | As a patient, I can see spending broken down by category (medicine, consultation, tests, hospital, other). | P1 |
| US-7.4 | As a patient, I can see month-over-month change percentage. | P1 |
| US-7.5 | As a patient, I can see a 6-month spending trend bar chart. | P1 |
| US-7.6 | As a patient, I can see a doughnut chart showing category distribution. | P2 |
| US-7.7 | As a patient, I can see my AI-estimated savings projection. | P2 |

---

## 3. Functional Requirements

### Expense Entry
- **FR-7.1**: `POST /finance/add-expense` accepts: expense_date, category, amount, description (optional), consultation_id (optional).
- **FR-7.2**: Categories: `medicine`, `consultation`, `tests`, `hospital`, `other`.
- **FR-7.3**: Amount must be > 0.
- **FR-7.4**: Returns the new expense ID and updated monthly total.

### Expense Summary
- **FR-7.5**: `GET /finance/summary` returns: monthly_total, previous_month_total, change_percent, breakdown by category, savings_estimate, monthly_trend (6 months).
- **FR-7.6**: Breakdown initialized with all 5 categories at 0.0, then populated from DB aggregation.
- **FR-7.7**: Change percent = `((current - previous) / previous) × 100`.
- **FR-7.8**: Savings estimate pulled from latest consultation's `savings_estimate` field.
- **FR-7.9**: 6-month trend: rolling monthly totals calculated via SQL aggregation.

### Savings Formula
- **FR-7.10**: `savings = (medicine_cost × 0.6) + (consultation_cost × 0.6) - 500` (computed by Agent 4).
- **FR-7.11**: Always labeled "Estimated projections. Actual savings may vary."

---

## 4. API Contract

### POST `/finance/add-expense`
```json
// Request
{ "expense_date": "2026-05-05", "category": "medicine", "amount": 450.0, "description": "Paracetamol tablets" }
// Response 200
{ "success": true, "data": { "expense_id": 12, "new_monthly_total": 2450.00 }, "message": "Expense added successfully" }
```

### GET `/finance/summary`
```json
{ "success": true, "data": {
    "monthly_total": 2450.00, "previous_month_total": 3100.00, "change_percent": -21.0,
    "breakdown": { "medicine": 1200.0, "consultation": 500.0, "tests": 400.0, "hospital": 0.0, "other": 350.0 },
    "savings_estimate": 1200.0, "savings_disclaimer": "Estimated projections. Actual savings may vary.",
    "monthly_trend": [ { "month": "Dec 2025", "total": 3200 }, { "month": "Jan 2026", "total": 2800 }, ... ]
} }
```

---

## 5. Data Model

### Expenses Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK → users.id |
| consultation_id | String | FK → consultations.consultation_id (nullable) |
| expense_date | DateTime | indexed |
| category | String | medicine/consultation/tests/hospital/other |
| amount | Float | > 0 |
| description | Text | nullable |
| source | String | default "manual" |
| created_at | DateTime | auto-set |
