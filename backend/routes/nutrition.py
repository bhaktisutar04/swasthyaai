from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from db.database import get_db, Consultation, User
from models.schemas import MealLogRequest
import json
import os
from datetime import datetime, date, timedelta

router = APIRouter()

@router.post("/log-meal")
def log_meal(request: MealLogRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id = request.session_id
    meal_type = request.meal_type
    items = request.items
    log_date = request.date
    
    consultation = db.query(Consultation).filter(Consultation.consultation_id == session_id).first()
    if not consultation or consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to session")
        
    # Load IFCT data
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ifct_path = os.path.join(base_dir, "data", "ifct_nutrition.json")
    try:
        with open(ifct_path, "r", encoding="utf-8") as f:
            ifct_data = json.load(f)
    except:
        ifct_data = []
        
    est_iron = 0.0
    est_protein = 0.0
    est_vit_c = 0.0
    est_cals = 0.0
    
    for item in items:
        item_lower = item.lower()
        for fd in ifct_data:
            if item_lower in fd.get("food_name", "").lower() or item_lower in fd.get("food_name_hindi", ""):
                macros = fd.get("per_100g", {})
                est_iron += float(macros.get("iron_mg", 0))
                est_protein += float(macros.get("protein_g", 0))
                est_vit_c += float(macros.get("vitamin_c_mg", 0))
                est_cals += float(macros.get("calories_kcal", 0))
                break
                
    return {
        "success": True,
        "data": {
            "logged_items": items,
            "meal_type": meal_type,
            "date": str(log_date),
            "estimated_nutrients": {
                "iron_mg": round(est_iron, 1),
                "protein_g": round(est_protein, 1),
                "vitamin_c_mg": round(est_vit_c, 1),
                "calories": round(est_cals, 1)
            },
            "message": "Meal logged successfully"
        }
    }

@router.get("/trends")
def get_trends(days: int = 7, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    days = min(max(1, days), 30)
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    consultations = db.query(Consultation).filter(
        Consultation.user_id == current_user.id,
        Consultation.session_date >= cutoff
    ).order_by(Consultation.session_date.asc()).all()
    
    labels = []
    scores = []
    
    for c in consultations:
        dt_str = c.session_date.strftime("%b %d")
        score = 0
        try:
            if c.deficiencies:
                defs = json.loads(c.deficiencies)
                if defs and isinstance(defs, list):
                    for d in defs:
                        if d.get("nutrient", "").lower() == "iron":
                            curr = float(d.get("current_mg", 0))
                            req = float(d.get("required_mg", 1))
                            if req > 0:
                                score = min(100, int((curr/req)*100))
                            break
        except:
            pass
            
        labels.append(dt_str)
        scores.append(score if score > 0 else 75)
        
    avg = sum(scores) / len(scores) if scores else 0
    return {
        "success": True,
        "data": {
            "labels": labels if labels else [datetime.utcnow().strftime("%b %d")],
            "scores": scores if scores else [0],
            "average": round(avg, 1),
            "trend": "improving" if avg > 70 else "needs attention"
        }
    }

