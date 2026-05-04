# Tasks: Financial Wellness & Expense Tracking

## Module 1: Database Updates
- [ ] **Task 1.1**: Add `consultation_id` (String) and `source` (String, default "manual") columns to the `Expense` model in `backend/db/database.py`.
- [ ] **Task 1.2**: Update the `init_db()` function to include safe `ALTER TABLE` schema migrations to apply these new columns to existing databases.

## Module 2: Automated Logging (Backend)
- [ ] **Task 2.1**: Implement `auto_create_medicine_expenses` in `backend/crew/crew_runner.py`.
- [ ] **Task 2.2**: Inside this function, query the `Expense` table by `consultation_id`. If records already exist, return early to prevent duplicates.
- [ ] **Task 2.3**: If no records exist, iterate over the `medicines` array produced by the AI pipeline and create `Expense` records with `category='medicine'`, `source='auto'`, and the AI-estimated cost. Commit the transaction.

## Module 3: Finance APIs
- [ ] **Task 3.1**: Create `POST /finance/add-expense` in `backend/routes/finance.py`. Implement validation logic to reject requests where `category` is "medicine".
- [ ] **Task 3.2**: Create `GET /finance/summary`. Write SQLAlchemy queries to sum current month expenses, previous month expenses, calculate the percentage change, and group expenses by category for the pie chart.
- [ ] **Task 3.3**: Create `GET /finance/recent`. Query the `Expense` table for the user's 20 most recent entries, ordered by `expense_date` descending.

## Module 4: Frontend Integration
- [ ] **Task 4.1**: Update `frontend/expenses.html` to remove "Medicine" from the category dropdown in the "Add Expense" modal.
- [ ] **Task 4.2**: In `frontend/js/expenses.js`, update `loadExpenses()` to fetch both `/finance/summary` and `/finance/recent` concurrently using `Promise.all()`.
- [ ] **Task 4.3**: Implement `renderExpensesList(expenses)`. Iterate over the recent transactions and inject HTML. Add a visual badge (e.g., green background, "auto" label) if `source === 'auto'`.
- [ ] **Task 4.4**: Implement `renderPieChart` and `renderBarChart` using the Chart.js CDN and the aggregated data from the summary endpoint.
