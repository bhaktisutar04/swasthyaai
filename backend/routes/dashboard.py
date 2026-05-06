from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from db.database import get_db, Consultation, Expense, Notification, User
from sqlalchemy import func, desc
import json
from datetime import datetime, date, timedelta

router = APIRouter()

def get_month_back(dt, months_back):
    m = dt.month - months_back
    y = dt.year
    while m <= 0:
        m += 12
        y -= 1
    return dt.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)

@router.get("/")
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        now = datetime.utcnow()
        today_date = now.strftime("%A, %B %d, %Y")
        
        # Defaults
        latest_c_data = None
        monthly_expense_total = 0.0
        previous_month_total = 0.0
        expense_change_percent = 0.0
        nutrition_score_this_week = 0
        nutrition_score_last_week = 0
        nutrition_labels = []
        nutrition_scores = []
        notifications_list = []
        has_consultations = False
        
        # 1. Latest Consultation
        latest_c = db.query(Consultation).filter(
            Consultation.user_id == current_user.id
        ).order_by(Consultation.session_date.desc()).first()
        
        if latest_c:
            has_consultations = True
            
            pri_cond = "Unknown"
            if latest_c.conditions:
                try:
                    conds = json.loads(latest_c.conditions)
                    if conds and isinstance(conds, list) and len(conds) > 0:
                        pri_cond = conds[0].get("name", "Unknown")
                except: pass
                
            sev_flag = latest_c.severity_flag or "mild"
            see_doc = getattr(latest_c, "see_doctor", False)
            
            follow_up_days = 7
            if sev_flag == "mild": follow_up_days = 7
            elif sev_flag == "moderate": follow_up_days = 3
            elif sev_flag == "severe": follow_up_days = 1
            
            spec_type = "General Physician (GP)"
            
            latest_c_data = {
                "consultation_id": latest_c.consultation_id,
                "session_date": latest_c.session_date.strftime("%Y-%m-%d"),
                "primary_condition": pri_cond,
                "severity_flag": sev_flag,
                "status": latest_c.status or "completed",
                "follow_up_days": follow_up_days,
                "see_doctor": see_doc,
                "specialist_type": spec_type
            }
            
        # 2. Finance
        first_day_curr = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_prev = get_month_back(now, 1)
        
        curr_total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= first_day_curr
        ).scalar() or 0.0
        
        prev_total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= first_day_prev,
            Expense.expense_date < first_day_curr
        ).scalar() or 0.0
        
        monthly_expense_total = round(float(curr_total), 1)
        previous_month_total = round(float(prev_total), 1)
        
        if previous_month_total > 0:
            expense_change_percent = round(((monthly_expense_total - previous_month_total) / previous_month_total) * 100.0, 1)
            
        # 3. Nutrition scores
        consultations = db.query(Consultation).filter(
            Consultation.user_id == current_user.id
        ).order_by(Consultation.session_date.desc()).limit(7).all()
        
        all_scores = []
        all_labels = []
        if consultations:
            # Restore chronological order
            for c in reversed(consultations):
                sc = 0
                if c.deficiencies:
                    try:
                        defs = json.loads(c.deficiencies)
                        for d in defs:
                            if d.get("nutrient", "").lower() == "iron":
                                curr = float(d.get("current_mg", 0))
                                req = float(d.get("required_mg", 1))
                                if req > 0:
                                    sc = min(100, int((curr/req)*100))
                                break
                    except: pass
                
                all_scores.append(sc)
                all_labels.append(c.session_date.strftime("%b %d"))
                
            nutrition_labels = all_labels
            nutrition_scores = all_scores
            
            nutrition_score_this_week = all_scores[-1] if len(all_scores) > 0 else 0
            nutrition_score_last_week = all_scores[-2] if len(all_scores) > 1 else 0
            
            while len(nutrition_labels) < 7:
                pad_date = now - timedelta(days=7-len(nutrition_labels))
                nutrition_labels.insert(0, pad_date.strftime("%b %d"))
                nutrition_scores.insert(0, 0)
        else:
            for i in range(6, -1, -1):
                pad_date = now - timedelta(days=i)
                nutrition_labels.append(pad_date.strftime("%b %d"))
                nutrition_scores.append(0)
        
        # 4. Notifications
        db_notifs = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == 0
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        for n in db_notifs:
            notifications_list.append({
                "id": n.id,
                "message": n.message,
                "type": n.type,
                "due_date": n.created_at.strftime("%Y-%m-%d")
            })
            
        if not notifications_list and latest_c_data and latest_c_data["see_doctor"]:
            notifications_list.append({
                "id": 0, 
                "message": f"Consider visiting a {latest_c_data['specialist_type']}", 
                "type": "follow_up", 
                "due_date": str(date.today() + timedelta(days=latest_c_data["follow_up_days"]))
            })
            
        return {
            "success": True,
            "data": {
                "greeting_name": current_user.name,
                "current_date": today_date,
                "latest_consultation": latest_c_data,
                "monthly_expense_total": monthly_expense_total,
                "previous_month_total": previous_month_total,
                "expense_change_percent": expense_change_percent,
                "nutrition_score_this_week": nutrition_score_this_week,
                "nutrition_score_last_week": nutrition_score_last_week,
                "nutrition_labels": nutrition_labels,
                "nutrition_scores": nutrition_scores,
                "notifications": notifications_list,
                "has_consultations": has_consultations
            }
        }
        
    except Exception as e:
        return {
            "success": True,
            "data": {
                "greeting_name": current_user.name if current_user else "User",
                "current_date": datetime.utcnow().strftime("%A, %B %d, %Y"),
                "latest_consultation": None,
                "monthly_expense_total": 0,
                "previous_month_total": 0,
                "expense_change_percent": 0.0,
                "nutrition_score_this_week": 0,
                "nutrition_score_last_week": 0,
                "nutrition_labels": [],
                "nutrition_scores": [],
                "notifications": [],
                "has_consultations": False
            }
        }


