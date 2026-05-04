# Specification: Financial Wellness & Expense Tracking

## 1. Feature Overview
This module empowers users to monitor their health-related expenditures. It uniquely blends automated cost tracking (derived from AI consultations) with manual logging for complete financial visibility, helping users understand where their healthcare budget is going and highlighting potential savings through preventative care.

## 2. Behavioral Specification

### 2.1 Automated Expense Logging
- **Behavior**: When a consultation pipeline completes, the system automatically logs the estimated costs of AI-suggested medicines.
- **Rules**:
  - The expense category must be set to `medicine`.
  - The `source` field must be marked as `auto`.
  - The expense must be linked to the `consultation_id` to prevent duplicate logging if a session is re-processed.

### 2.2 Manual Expense Logging
- **Behavior**: Users can manually log expenses for doctor visits, lab tests, and hospital fees.
- **Rules**:
  - Allowed categories: `consultation`, `tests`, `hospital`, `other`.
  - The `medicine` category is strictly prohibited for manual entry to maintain the integrity of automated tracking.
  - The `source` field defaults to `manual`.

### 2.3 Financial Analytics & Summaries
- **Behavior**: The system provides aggregated financial views for the user's dashboard.
- **Rules**:
  - Must calculate current month's total expenditure and compare it to the previous month (percentage change).
  - Must provide a categorical breakdown (e.g., how much spent on tests vs. medicines).
  - Must provide a list of the 20 most recent transactions, visually distinguishing between `auto` and `manual` entries.

## 3. Data Models & Database Schema

### `expenses` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `user_id` | Integer | Foreign Key (`users.id`) | The spender |
| `consultation_id`| String | Foreign Key (`consultations`) | Links auto-expenses to sessions |
| `expense_date` | DateTime | Indexed | Date of the expense |
| `category` | String | Not Null | medicine, tests, etc. |
| `amount` | Float | Not Null | Cost in Rupees |
| `description` | Text | Nullable | Optional user note |
| `source` | String | Default: 'manual' | 'auto' or 'manual' |
| `created_at` | DateTime | Default: CURRENT_TIMESTAMP | DB insertion time |

## 4. API Contracts

### `POST /finance/add-expense`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "category": "tests",
    "amount": 1500.0,
    "description": "Blood test",
    "expense_date": "2026-05-04T00:00:00Z"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Expense added successfully",
    "data": {"expense_id": 1, "new_monthly_total": 3500.0}
  }
  ```

### `GET /finance/summary`
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "monthly_total": 3500.0,
      "previous_month_total": 2000.0,
      "change_percent": 75.0,
      "breakdown": {
        "tests": 1500.0,
        "medicine": 2000.0
      },
      "savings_estimate": 500.0,
      "monthly_trend": [{"month": "Apr", "total": 2000.0}, {"month": "May", "total": 3500.0}]
    }
  }
  ```

### `GET /finance/recent`
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "category": "medicine",
        "amount": 2000.0,
        "description": "Paracetamol",
        "source": "auto",
        "expense_date": "2026-05-04T10:00:00Z"
      }
    ]
  }
  ```

## 5. UI Flows & Screen Descriptions
1. **Expenses Dashboard**: 
   - Top banner showing current month total and month-over-month trend.
   - Middle section: Side-by-side charts (Pie chart for breakdown, Bar chart for 6-month trend).
   - Bottom section: A scrollable list of recent transactions.
   - A floating action button (FAB) to open the "Add Expense" modal.
2. **Add Expense Modal**: A simple form with Date picker, Category dropdown (excluding medicine), Amount input, and Description text area.

## 6. Edge Cases & Error Handling
- **Duplicate Auto-Logging**: The backend must check if expenses matching a specific `consultation_id` already exist before running the auto-insertion logic to prevent double-billing the user in the UI.
- **Invalid Category Injection**: If a malicious request attempts to pass `category: "medicine"` to the `/add-expense` route, the API must return a `400 Bad Request` with "Invalid category".
