from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from auth.dependencies import get_current_user
from db.database import get_db, Expense, Consultation, User
from models.schemas import ExpenseRequest
import json
from datetime import datetime, date

router = APIRouter()

def get_month_back(dt, months_back):
    m = dt.month - months_back
    y = dt.year
    while m <= 0:
        m += 12
        y -= 1
    return dt.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)

@router.post("/add-expense")
def add_expense(request: ExpenseRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    valid_categories = ["medicine", "consultation", "tests", "hospital", "other"]
    if request.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")
        
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be > 0")
        
    new_expense = Expense(
        user_id=current_user.id,
        amount=request.amount,
        category=request.category,
        description=getattr(request, 'description', None),
        expense_date=datetime.utcnow()
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    first_day = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= first_day
    ).scalar() or 0.0
    
    return {
        "success": True,
        "data": {
            "expense_id": new_expense.id,
            "new_monthly_total": round(total, 2)
        },
        "message": "Expense added successfully"
    }

@router.get("/summary")
def get_summary(months: int = 1, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    months = min(max(1, months), 12)
    now = datetime.utcnow()
    first_day_curr = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_day_prev = get_month_back(now, 1)
    
    curr_expenses = db.query(Expense.category, func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= first_day_curr
    ).group_by(Expense.category).all()
    
    curr_total = sum(amt for cat, amt in curr_expenses)
    breakdown = { "medicine": 0.0, "consultation": 0.0, "tests": 0.0, "hospital": 0.0, "other": 0.0 }
    for cat, amt in curr_expenses:
        c = cat.lower()
        if c in breakdown: breakdown[c] += float(amt)
        else: breakdown["other"] += float(amt)
        
    prev_total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= first_day_prev,
        Expense.expense_date < first_day_curr
    ).scalar() or 0.0
    
    change_percent = 0.0
    if prev_total > 0:
        change_percent = ((curr_total - prev_total) / prev_total) * 100.0
        
    latest_c = db.query(Consultation).filter(
        Consultation.user_id == current_user.id
    ).order_by(Consultation.session_date.desc()).first()
    
    savings_est = latest_c.savings_estimate if latest_c and latest_c.savings_estimate else 0.0
    
    trend = []
    for i in range(5, -1, -1):
        dt = get_month_back(now, i)
        next_dt = get_month_back(now, i-1) if i > 0 else now
        month_total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= dt,
            Expense.expense_date < next_dt
        ).scalar() or 0.0
        trend.append({
            "month": dt.strftime("%b %Y"),
            "total": round(float(month_total), 2)
        })
        
    return {
        "success": True,
        "data": {
            "monthly_total": round(curr_total, 2),
            "previous_month_total": round(prev_total, 2),
            "change_percent": round(change_percent, 1),
            "breakdown": breakdown,
            "savings_estimate": float(savings_est),
            "savings_disclaimer": "Estimated projections. Actual savings may vary.",
            "monthly_trend": trend
        }
    }


