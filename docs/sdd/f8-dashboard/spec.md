# F8 — Dashboard: Specification

> **Feature ID**: F8  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F1 (Auth), F6 (Nutrition data), F7 (Expense data)

---

## 1. Overview

The Dashboard is the central hub of SwasthyaAI — the first page users see after login. It aggregates data from consultations, nutrition, expenses, and notifications into a unified overview with at-a-glance stats, charts, and actionable reminders.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-8.1 | As a patient, I see a personalized greeting with my name and current date. | P0 |
| US-8.2 | As a patient, I see my latest consultation summary (condition, severity, follow-up). | P0 |
| US-8.3 | As a patient, I see my current nutrition score with weekly change. | P1 |
| US-8.4 | As a patient, I see my monthly medical expense total with change vs last month. | P1 |
| US-8.5 | As a patient, I see a nutrition score trend chart over recent consultations. | P1 |
| US-8.6 | As a patient, I see health reminders and notifications. | P2 |
| US-8.7 | As a patient, I can navigate to my latest report from the dashboard. | P1 |
| US-8.8 | As a patient, I can start a new consultation from the dashboard. | P0 |

---

## 3. Functional Requirements

### Dashboard Data
- **FR-8.1**: `GET /dashboard` returns a single aggregated payload with all dashboard data.
- **FR-8.2**: Greeting name from user profile.
- **FR-8.3**: Latest consultation: consultation_id, session_date, primary_condition, severity_flag, status, follow_up_days, see_doctor, specialist_type.
- **FR-8.4**: Expense data: monthly_total, previous_month_total, change_percent.
- **FR-8.5**: Nutrition data: score_this_week, score_last_week, labels[] (7 points), scores[] (7 points).
- **FR-8.6**: Notifications: up to 5 unread from DB + auto-generated follow-up reminders.

### Follow-Up Logic
- **FR-8.7**: Follow-up days based on severity: mild=7, moderate=3, severe=1.
- **FR-8.8**: If `see_doctor=true` and no DB notifications exist, auto-generate a follow-up reminder.

### Nutrition Score
- **FR-8.9**: Calculated from last 7 consultations' deficiency data (iron fulfillment %).
- **FR-8.10**: Chart padded to 7 data points with zeros if fewer consultations exist.

### Expense Summary
- **FR-8.11**: Current month total via SQLAlchemy `func.sum()`.
- **FR-8.12**: Change percent vs previous month.

---

## 4. API Contract

### GET `/dashboard`
```json
{ "success": true, "data": {
    "greeting_name": "Bhakti",
    "current_date": "Monday, May 05, 2026",
    "latest_consultation": { "consultation_id": "CNS-...", "session_date": "2026-05-05", "primary_condition": "Viral Fever", "severity_flag": "mild", "status": "completed", "follow_up_days": 7, "see_doctor": false, "specialist_type": "General Physician (GP)" },
    "monthly_expense_total": 2450.0, "previous_month_total": 3100.0, "expense_change_percent": -21.0,
    "nutrition_score_this_week": 85, "nutrition_score_last_week": 78,
    "nutrition_labels": ["Apr 29", "Apr 30", ...], "nutrition_scores": [70, 78, 82, ...],
    "notifications": [{ "id": 1, "message": "Consider visiting a GP", "type": "follow_up", "due_date": "2026-05-12" }],
    "has_consultations": true
} }
```

---

## 5. Data Model

### Notifications Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK → users.id |
| message | Text | notification text |
| type | String | follow_up, refill, general |
| due_date | DateTime | nullable |
| is_read | Integer | 0=unread, 1=read |
| created_at | DateTime | auto-set |
