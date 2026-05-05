# SwasthyaAI — Spec-Driven Development Index

> **Project**: AI-powered health companion for Indian patients  
> **Total Features**: 9  
> **Total Documents**: 27 (9 × spec + plan + tasks)  
> **Last Updated**: 2026-05-05

---

## SDD Document Map

| # | Feature | spec.md | plan.md | tasks.md | Status |
|---|---------|---------|---------|----------|--------|
| F1 | [Authentication & User Management](f1-authentication/) | [spec](f1-authentication/spec.md) | [plan](f1-authentication/plan.md) | [tasks](f1-authentication/tasks.md) | ✅ Complete |
| F2 | [AI Consultation (Chat)](f2-consultation/) | [spec](f2-consultation/spec.md) | [plan](f2-consultation/plan.md) | [tasks](f2-consultation/tasks.md) | ✅ Complete |
| F3 | [Multi-Agent AI Pipeline](f3-multi-agent-pipeline/) | [spec](f3-multi-agent-pipeline/spec.md) | [plan](f3-multi-agent-pipeline/plan.md) | [tasks](f3-multi-agent-pipeline/tasks.md) | ✅ Complete |
| F4 | [Health Report Viewer](f4-report-viewer/) | [spec](f4-report-viewer/spec.md) | [plan](f4-report-viewer/plan.md) | [tasks](f4-report-viewer/tasks.md) | ✅ Complete |
| F5 | [PDF Generation & Cloud Storage](f5-pdf-generation/) | [spec](f5-pdf-generation/spec.md) | [plan](f5-pdf-generation/plan.md) | [tasks](f5-pdf-generation/tasks.md) | ✅ Complete |
| F6 | [Nutrition Tracker](f6-nutrition-tracker/) | [spec](f6-nutrition-tracker/spec.md) | [plan](f6-nutrition-tracker/plan.md) | [tasks](f6-nutrition-tracker/tasks.md) | ✅ Complete |
| F7 | [Medical Expense Tracker](f7-expense-tracker/) | [spec](f7-expense-tracker/spec.md) | [plan](f7-expense-tracker/plan.md) | [tasks](f7-expense-tracker/tasks.md) | ✅ Complete |
| F8 | [Dashboard](f8-dashboard/) | [spec](f8-dashboard/spec.md) | [plan](f8-dashboard/plan.md) | [tasks](f8-dashboard/tasks.md) | ✅ Complete |
| F9 | [Consultation History](f9-consultation-history/) | [spec](f9-consultation-history/spec.md) | [plan](f9-consultation-history/plan.md) | [tasks](f9-consultation-history/tasks.md) | ✅ Complete |

---

## Document Types

### `spec.md` — Specification
What the feature does. Contains:
- Overview & goals
- User stories with priority levels
- Functional requirements (FR-X.X)
- API contracts (request/response JSON)
- Data model (DB tables)
- UI specification
- External services & dependencies

### `plan.md` — Technical Plan
How the feature is built. Contains:
- Architecture diagrams (Mermaid)
- Component design & patterns
- File map (backend + frontend)
- Data flow / sequence diagrams
- Design decisions & rationale
- Known limitations & future improvements

### `tasks.md` — Task Checklist
Granular implementation tasks. Contains:
- Categorized task checklist (backend, frontend, etc.)
- Each task prefixed with ID (T-X.X)
- Status markers: `[x]` complete, `[ ]` pending, `[/]` in progress
- Verification checklist

---

## Feature Dependency Graph

```
F1 (Auth) ─────────────────────────────────────────┐
  │                                                 │
  ├── F2 (Consultation Chat)                        │
  │     │                                           │
  │     └── F3 (Multi-Agent Pipeline)               │
  │           │                                     │
  │           ├── F4 (Report Viewer)                │
  │           │                                     │
  │           ├── F5 (PDF Generation)               │
  │           │                                     │
  │           └── F6 (Nutrition Tracker)            │
  │                                                 │
  ├── F7 (Expense Tracker) ────────────────────────┤
  │                                                 │
  ├── F8 (Dashboard) ──── depends on F6, F7 ───────┤
  │                                                 │
  └── F9 (History) ──── depends on F2, F5 ─────────┘
```

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python) |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt |
| AI Agents | CrewAI + Groq (llama-3.3-70b-versatile) |
| Vector Memory | Pinecone + HuggingFace embeddings |
| PDF Generation | ReportLab |
| Cloud Storage | Cloudinary |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Charts | Chart.js |
| Geolocation | Nominatim (OpenStreetMap) |

---

## Quick Stats

- **Backend files**: 15 Python files across 6 packages
- **Frontend files**: 7 HTML pages, 8 JS files, 1 CSS file
- **Database tables**: 5 (users, consultations, expenses, refresh_tokens, notifications)
- **API endpoints**: 17 across 6 routers
- **AI agents**: 4 (intake, diagnosis, nutrition, finance)
- **External services**: 6 (Groq, Pinecone, HuggingFace, Cloudinary, Nominatim, IFCT data)
