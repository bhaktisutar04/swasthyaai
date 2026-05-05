# F4 — Health Report Viewer: Technical Plan

> **Feature ID**: F4  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05

---

## 1. Architecture

```mermaid
flowchart LR
    A[report.html] --> B[report.js]
    B --> C[utils.js]
    B -->|apiFetch| D[GET /consultation/report/{id}]
    D --> E{In-memory session?}
    E -->|Yes| F[Return from dict]
    E -->|No| G[Query DB]
```

---

## 2. File Map

```
backend/routes/consultation.py   # GET /report/{session_id} endpoint
frontend/report.html              # Report page layout (4 collapsible sections)
frontend/js/report.js             # loadReport(), renderReport(), renderSymptoms/Diagnosis/Nutrition/Finance()
```

---

## 3. Rendering Architecture

`report.js` follows a top-down rendering pattern:

1. **`loadReport()`** — Fetches data, hides loading skeleton, shows report content, calls `renderReport()`.
2. **`renderReport(d)`** — Sets header fields (title, subtitle, badges), calls 4 sub-renderers.
3. **`renderSymptoms(s)`** — Renders symptom badges + emergency flag alert.
4. **`renderDiagnosis(d)`** — Renders conditions (with confidence bars), medicines, home care, red flags.
5. **`renderNutrition(n)`** — Renders deficiencies, day navigation, calls `renderMealDay()`.
6. **`renderMealDay(index, mealPlan)`** — Renders 5 meal slots for a specific day with nutrients.
7. **`renderFinance(f)`** — Renders monthly total, category breakdown, savings estimate.

### Data Format Handling
- Conditions can be objects `{name, confidence, likelihood}` or plain strings — renderer handles both.
- Medicines can be objects `{name, use}` or plain strings — renderer handles both.

---

## 4. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Collapsible sections | Open by default | Users expect to see full report immediately |
| Day navigation | Prev/Next buttons with day label | Simple; 7 days is manageable |
| Severity badge colors | green/yellow/red via CSS classes | Immediate visual severity communication |
| Confidence bars | CSS width percentage | Lightweight; no chart library needed |

---

## 5. Known Limitations

| Limitation | Potential Fix |
|------------|---------------|
| No print-optimized CSS | Add `@media print` styles |
| No report sharing | Add share-via-link or email |
| Finance section may show empty if no expenses logged | Show helpful "Log expenses" CTA |
