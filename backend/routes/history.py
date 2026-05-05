from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from db.database import get_db, Consultation, User
import json
from datetime import datetime
import math

router = APIRouter()

@router.get("/")
def get_history(
    page: int = 1, 
    limit: int = 10, 
    condition: str = None, 
    date_from: str = None, 
    date_to: str = None, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Consultation).filter(Consultation.user_id == current_user.id)
    
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace('Z', ''))
            query = query.filter(Consultation.session_date >= dt_from)
        except: pass
        
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to.replace('Z', ''))
            query = query.filter(Consultation.session_date <= dt_to)
        except: pass
        
    query = query.order_by(Consultation.session_date.desc())
    total = query.count()
    
    offset = (page - 1) * limit
    consultations = query.offset(offset).limit(limit).all()
    
    results = []
    for c in consultations:
        primary_cond = "Unknown"
        if c.conditions:
            try:
                conds = json.loads(c.conditions)
                if conds and isinstance(conds, list):
                    primary_cond = conds[0].get("name", "Unknown")
            except: pass
            
        results.append({
            "consultation_id": c.consultation_id,
            "session_date": c.session_date.isoformat(),
            "primary_condition": primary_cond,
            "severity_flag": c.severity_flag or "mild",
            "status": c.status or "completed",
            "pdf_available": True if c.pdf_path else False,
            "pdf_path": c.pdf_path or None

        })
        
    if condition:
        results = [r for r in results if condition.lower() in r["primary_condition"].lower()]
        total = len(results)
        
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "success": True,
        "data": {
            "consultations": results,
            "total": total,
            "page": page,
            "total_pages": total_pages
        }
    }

@router.get("/analytics/nutrition")
def get_nutrition_analytics(range_str: str = Query("1m", alias="range"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
    scores = [70, 78, 82, 85]
    
    return {
        "success": True,
        "data": {
            "labels": labels,
            "scores": scores,
            "current_score": 85,
            "change_vs_last_week": 3
        }
    }

@router.get("/analytics/expenses")
def get_expenses_analytics(range_str: str = Query("6m", alias="range"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    labels = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
    totals = [5200, 4800, 5000, 4700, 5000, 4500]
    
    return {
        "success": True,
        "data": {
            "labels": labels,
            "totals": totals,
            "current_month": 4500,
            "trend": "decreasing"
        }
    }

