# F9 — Consultation History: Specification

> **Feature ID**: F9  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F1 (Auth), F2 (Consultations), F5 (PDF downloads)

---

## 1. Overview

The Consultation History feature provides a paginated, filterable timeline of all past consultations. Users can search by condition, filter by status and date range, view summary stats, navigate to full reports, and download PDFs directly.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-9.1 | As a patient, I can see a timeline of all my past consultations. | P0 |
| US-9.2 | As a patient, I can see the primary condition, severity, and status for each consultation. | P0 |
| US-9.3 | As a patient, I can filter consultations by condition name search. | P1 |
| US-9.4 | As a patient, I can filter by status (completed, in_progress, follow_up_pending). | P1 |
| US-9.5 | As a patient, I can see total, completed, and follow-up pending consultation counts. | P1 |
| US-9.6 | As a patient, I can load more consultations (pagination). | P1 |
| US-9.7 | As a patient, I can click a consultation to view its full report. | P0 |
| US-9.8 | As a patient, I can download a consultation's PDF directly from the timeline. | P1 |

---

## 3. Functional Requirements

### History List
- **FR-9.1**: `GET /history` returns paginated consultation list (page, limit, total, total_pages).
- **FR-9.2**: Each consultation includes: consultation_id, session_date, primary_condition, severity_flag, status, pdf_available, pdf_path.
- **FR-9.3**: Sorted by session_date descending (newest first).
- **FR-9.4**: Supports server-side filters: date_from, date_to.
- **FR-9.5**: Supports server-side condition filter (applied client-side after fetch for flexibility).

### Client-Side Features
- **FR-9.6**: Search input filters consultations by condition name (client-side).
- **FR-9.7**: Status filter dropdown: All, Completed, In Progress, Follow-Up Pending.
- **FR-9.8**: Stats counters: total consultations, completed, follow-up pending.
- **FR-9.9**: "Load More" button for pagination (appends to existing list).
- **FR-9.10**: Each timeline card shows: date, condition, severity badge, status badge, PDF download icon (if available), "View Report" link.

### Actions
- **FR-9.11**: Click consultation → navigate to `report.html?id={consultation_id}`.
- **FR-9.12**: Download PDF: same `fl_attachment` forced download logic as F5.

---

## 4. API Contract

### GET `/history?page=1&limit=10&condition=fever&date_from=2026-01-01&date_to=2026-05-05`
```json
{ "success": true, "data": {
    "consultations": [
      { "consultation_id": "CNS-2026-05-05-A1B2C3", "session_date": "2026-05-05T...", "primary_condition": "Viral Fever", "severity_flag": "mild", "status": "completed", "pdf_available": true, "pdf_path": "https://res.cloudinary.com/..." }
    ],
    "total": 15, "page": 1, "total_pages": 2
} }
```

### GET `/history/analytics/nutrition?range=1m` (Stub)
```json
{ "success": true, "data": { "labels": ["Week 1", ...], "scores": [70, 78, ...], "current_score": 85, "change_vs_last_week": 3 } }
```

### GET `/history/analytics/expenses?range=6m` (Stub)
```json
{ "success": true, "data": { "labels": ["Nov", ...], "totals": [5200, ...], "current_month": 4500, "trend": "decreasing" } }
```

> [!NOTE]
> The analytics endpoints return hardcoded stub data. The Trends UI that consumed them has been removed from history.html. These endpoints can be cleaned up or properly implemented in a future iteration.
