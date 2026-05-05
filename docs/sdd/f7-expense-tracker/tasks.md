# F7 — Medical Expense Tracker: Tasks

> **Feature ID**: F7  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend — Data Layer
- [x] **T7.1**: Define `Expense` SQLAlchemy model (user_id, consultation_id, expense_date, category, amount, description, source, created_at)
- [x] **T7.2**: Add safe migrations for `consultation_id` and `source` columns in `init_db()`
- [x] **T7.3**: Create `ExpenseRequest` Pydantic schema with category validator and amount > 0

### Backend — API Endpoints
- [x] **T7.4**: `POST /finance/add-expense` — validate category, insert record, return new monthly total
- [x] **T7.5**: `GET /finance/summary` — aggregate current month total + breakdown by category
- [x] **T7.6**: Calculate previous month total and change percentage
- [x] **T7.7**: Build 6-month trend array with monthly totals
- [x] **T7.8**: Pull savings estimate from latest consultation record
- [x] **T7.9**: Implement `get_month_back()` utility for month boundary calculation

### Frontend — Page Layout (`expenses.html`)
- [x] **T7.10**: Monthly summary card (total + change %)
- [x] **T7.11**: Savings estimate card (conditional display)
- [x] **T7.12**: Toggle-able "Add Expense" form (date, category, amount, description)
- [x] **T7.13**: Doughnut chart canvas for category breakdown
- [x] **T7.14**: Bar chart canvas for 6-month trend
- [x] **T7.15**: Expenses list by category

### Frontend — Logic (`expenses.js`)
- [x] **T7.16**: `loadExpenses()` — fetch summary, populate all UI elements
- [x] **T7.17**: `renderPieChart()` — Chart.js doughnut with 5 category colors
- [x] **T7.18**: `renderBarChart()` — Chart.js bar with rounded corners, filter zero months
- [x] **T7.19**: `renderExpensesList()` — category rows with monthly totals
- [x] **T7.20**: `toggleExpenseForm()` — show/hide form, clear errors
- [x] **T7.21**: `saveExpense()` — validate, POST to API, reload data on success
- [x] **T7.22**: Set today's date as default in date input
- [x] **T7.23**: Error handling for invalid inputs and network failures

---

## Verification

- [x] Adding an expense updates the monthly total
- [x] Category breakdown doughnut chart renders correctly
- [x] 6-month bar chart shows trend data
- [x] Month-over-month change percentage displays with correct color/arrow
- [x] Savings estimate shows when available, hidden otherwise
- [x] Empty state shows when no expenses logged
