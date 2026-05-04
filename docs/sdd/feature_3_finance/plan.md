# Technical Plan: Financial Wellness & Expense Tracking

## 1. Architecture Overview

```text
[ Frontend Dashboard ]
        |
        | GET /finance/summary
        | GET /finance/recent
        | POST /finance/add-expense
        v
[ FastAPI Router (/finance) ]
        |
        +-- [ Input Validation (schemas.py) ]
        |
[ SQLAlchemy ORM (Expense Model) ]
        |
        +-- (Automated sync from CrewRunner)
        |
[ Database ]
```

## 2. Tech Stack & Rationale
- **SQLAlchemy Aggregate Functions**: Utilizes `func.sum()` and `group_by` to calculate monthly totals and categorical breakdowns efficiently at the database level, rather than pulling all records into Python memory.
- **Chart.js (Frontend)**: Chosen for its lightweight footprint and ease of rendering responsive pie and bar charts directly in the browser canvas.
- **Pydantic**: Ensures strict validation of manual expense categories and amounts before hitting the database.

## 3. Component Breakdown
1. **Automated Logging Logic (`backend/crew/crew_runner.py`)**: A utility function `auto_create_medicine_expenses` that fires immediately after the AI pipeline finishes. It iterates through the LLM-generated medicines list and inserts `Expense` records.
2. **Finance Routes (`backend/routes/finance.py`)**:
   - `add_expense`: Validates category and creates a manual record.
   - `get_summary`: Uses SQLAlchemy to aggregate the current month's expenses, calculate the percentage change against the previous month, and format data for Chart.js.
   - `get_recent`: Queries the top 20 most recent expenses ordered by `expense_date` descending.
3. **Database Migrations (`backend/db/database.py`)**: `init_db` includes safe schema updates (`ALTER TABLE`) to ensure existing databases receive the `consultation_id` and `source` columns without data loss.
4. **Frontend JS (`frontend/js/expenses.js`)**: Fetches summary and recent data concurrently using `Promise.all()`, updates the DOM metric cards, and instantiates Chart.js graphs.

## 4. Dependencies & Risks
### Dependencies
- `Chart.js` via CDN for frontend data visualization.

### Risks & Mitigations
- **Risk**: Database bloat from automated logging if a single consultation fails and retries multiple times.
  - **Mitigation**: The `auto_create_medicine_expenses` function first queries the `expenses` table for the specific `consultation_id`. If records already exist, it skips insertion.
- **Risk**: Timezone discrepancies causing expenses to appear in the wrong month's summary.
  - **Mitigation**: Standardize all backend database insertions and queries to use `datetime.utcnow()`. Convert to local timezone only on the frontend during rendering.
