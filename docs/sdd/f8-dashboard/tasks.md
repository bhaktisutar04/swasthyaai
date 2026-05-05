# F8 — Dashboard: Tasks

> **Feature ID**: F8  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend
- [x] **T8.1**: Define `Notification` SQLAlchemy model (user_id, message, type, due_date, is_read, created_at)
- [x] **T8.2**: `GET /dashboard` — single aggregation endpoint
- [x] **T8.3**: Query latest consultation, extract primary condition from JSON
- [x] **T8.4**: Calculate follow-up days by severity (mild=7, moderate=3, severe=1)
- [x] **T8.5**: Aggregate current + previous month expenses, compute change %
- [x] **T8.6**: Calculate nutrition scores from last 7 consultations (iron fulfillment %)
- [x] **T8.7**: Pad nutrition data to 7 points with zeros
- [x] **T8.8**: Query up to 5 unread notifications
- [x] **T8.9**: Auto-generate follow-up notification if `see_doctor=true` and no DB notifications
- [x] **T8.10**: Implement `get_month_back()` utility
- [x] **T8.11**: Wrap entire endpoint in try/except with safe defaults

### Frontend — Page Layout (`dashboard.html`)
- [x] **T8.12**: Top bar with avatar circle (user initial), greeting text, date text
- [x] **T8.13**: Two stat cards: nutrition score + monthly expense
- [x] **T8.14**: Latest consultation card with condition badge, severity, see-doctor banner, "View Full Report" button
- [x] **T8.15**: Nutrition trend chart canvas
- [x] **T8.16**: Notifications/reminders list
- [x] **T8.17**: Bottom navigation bar
- [x] **T8.18**: Quick action buttons: "Start New Consultation", "Log Expense"

### Frontend — Logic (`dashboard.js`)
- [x] **T8.19**: Set greeting (time-based) + user name + date on page load
- [x] **T8.20**: Set user initial in avatar circle
- [x] **T8.21**: `loadDashboard()` — fetch `/dashboard`, populate all UI elements
- [x] **T8.22**: Render nutrition score + weekly change (up/down arrow with color)
- [x] **T8.23**: Render monthly expense total + change % (up/down arrow with color)
- [x] **T8.24**: Render latest consultation card or empty state
- [x] **T8.25**: `renderNutritionChart()` — Chart.js line chart (blue, 0-100%)
- [x] **T8.26**: `renderNotifications()` — icon-based list with type icons and due dates
- [x] **T8.27**: Error state with retry link
- [x] **T8.28**: Auth guard (`requireAuth()`) and idle timer on page load

---

## Verification

- [x] Dashboard loads with greeting showing correct time of day + user name
- [x] Nutrition score card shows percentage + weekly change
- [x] Expense card shows monthly total + month-over-month change
- [x] Latest consultation card shows condition, severity badge, follow-up
- [x] Chart renders with 7 data points
- [x] Notifications list displays with correct icons
- [x] Empty state renders when no consultations exist
- [x] "View Full Report" navigates to correct report page
