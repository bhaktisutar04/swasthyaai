import json
import uuid
import os
import requests
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from db.database import get_db, Consultation, User, SessionLocal
from models.schemas import ConsultationMessageRequest
from groq import Groq
from memory.pinecone_client import get_patient_memory
from crew.crew_runner import run_full_crew, save_consultation_to_db, save_to_pinecone

router = APIRouter()
sessions = {}

def build_patient_profile(user: User) -> dict:
    try:
        allergies_list = json.loads(user.allergies) if user.allergies else []
    except:
        allergies_list = []
    return {
        "user_id": user.id, "name": user.name, "age": user.age,
        "gender": user.gender, "city": user.city,
        "language": user.language or "english",
        "diet_pref": user.diet_pref, "allergies": allergies_list,
        "symptoms": [], "duration": "", "severity": 0,
        "emergency_flag": False, "session_id": "", "session_date": "",
        "status": "in_progress", "chat_history": [],
        "conditions": [], "medicines": [], "specialist_type": "",
        "see_doctor": False, "severity_flag": "", "deficiencies": [],
        "meal_plan": [], "monthly_total": 0, "expense_breakdown": {},
        "savings_estimate": 0, "past_conditions": [],
        "home_care": [], "red_flags": [], "nutritional_focus": "",
        "nutrition_tips": [], "daily_intake": {}, "recommended_intake": {},
        "pdf_path": None
    }

def call_groq_directly(message: str, chat_history: list,
                        patient_name: str, language: str) -> str:
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        system_content = f"""You are a compassionate AI health assistant 
for Indian patients. You are talking to {patient_name}. 
Respond in {language}.
Rules:
1. Ask ONE follow-up question at a time about symptoms
2. Collect: duration, severity (1-10), associated symptoms
3. Be empathetic and professional
4. NEVER diagnose. NEVER suggest medicines.
5. Keep responses to 2-3 sentences maximum
6. This is not a substitute for real medical advice."""
        messages = [{"role": "system", "content": system_content}]
        for msg in chat_history[-8:]:
            role = "assistant" if msg.get("role") in ["ai","assistant"] else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages, max_tokens=200, temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return "Could you tell me more about your symptoms? How long have you had them and how severe on a scale of 1 to 10?"

def run_pipeline_background(session_id: str):
    """Run full 4-agent pipeline in background thread"""
    try:
        if session_id not in sessions:
            return
        profile = sessions[session_id]
        db_session = SessionLocal()
        try:
            updated = run_full_crew(profile, db_session)
            sessions[session_id] = updated
            print(f"Pipeline complete for {session_id}")
            print(f"PDF path: {updated.get('pdf_path')}")
            print(f"Meal plan days: {len(updated.get('meal_plan', []))}")
        finally:
            db_session.close()
    except Exception as e:
        print(f"Background pipeline error: {e}")

@router.post("/start")
def start_consultation(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    # Return existing active session if found
    for sid, profile in sessions.items():
        if (profile.get("user_id") == current_user.id and
                profile.get("status") == "in_progress"):
            language = current_user.language or "english"
            name = current_user.name
            if language == "hindi":
                greeting = f"Namaste {name}! Apne symptoms batayein."
            elif language == "marathi":
                greeting = f"Namaste {name}! Tumche symptoms sanga."
            else:
                greeting = f"Namaste {name}! I'm your AI health assistant. How are you feeling today?"
            return {"success": True, "data": {
                "session_id": sid, "greeting": greeting, "language": language
            }}
    
    profile = build_patient_profile(current_user)
    session_id = f"CNS-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
    profile["session_id"] = session_id
    profile["session_date"] = datetime.now().isoformat()
    profile["past_conditions"] = get_patient_memory(current_user.id)
    sessions[session_id] = profile
    
    db.add(Consultation(
        consultation_id=session_id,
        user_id=current_user.id,
        session_date=datetime.utcnow()
    ))
    db.commit()
    
    language = (profile["language"] or "english").lower()
    name = profile["name"]
    if language == "hindi":
        greeting = f"Namaste {name}! Main aapka AI health assistant hoon. Aaj aap kaisa feel kar rahe hain?"
    elif language == "marathi":
        greeting = f"Namaste {name}! Mi tumcha AI health assistant ahe. Aaj tumhi kase vatate?"
    else:
        greeting = f"Namaste {name}! I'm your AI health assistant. How are you feeling today? Please describe your symptoms."
    
    return {"success": True, "data": {
        "session_id": session_id, "greeting": greeting, "language": language
    }}

@router.post("/message")
def process_message(request: ConsultationMessageRequest,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    session_id = request.session_id
    message = request.message
    
    if session_id not in sessions:
        consultation = db.query(Consultation).filter(
            Consultation.consultation_id == session_id).first()
        if not consultation:
            raise HTTPException(status_code=404,
                detail="Session not found. Please start a new consultation.")
        user = db.query(User).filter(User.id == consultation.user_id).first()
        if user:
            profile = build_patient_profile(user)
            profile["session_id"] = consultation.consultation_id
            profile["status"] = consultation.status
            if consultation.symptoms:
                profile["symptoms"] = json.loads(consultation.symptoms or "[]")
            sessions[session_id] = profile
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    profile = sessions[session_id]
    if profile["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Emergency check
    message_lower = message.lower()
    emergency_keywords = [
        "chest pain", "heart attack", "can't breathe",
        "difficulty breathing", "severe bleeding", "unconscious",
        "seizure", "stroke", "suicidal", "want to die", "end my life",
        "seene mein dard", "saans nahi aa raha", "behosh",
        "chhati dukhte", "shwas ghet nahi"
    ]
    if any(kw in message_lower for kw in emergency_keywords):
        profile["emergency_flag"] = True
        hospitals = []
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"hospital in {profile['city']}, India",
                        "format": "json", "limit": 3, "addressdetails": 1},
                headers={"User-Agent": "SwasthyaAI/1.0"}, timeout=5
            )
            for item in resp.json():
                hospitals.append({
                    "name": item.get("name", "Hospital"),
                    "address": item.get("display_name", ""),
                    "maps_link": f"https://www.google.com/maps/place/{item.get('lat')},{item.get('lon')}"
                })
        except:
            pass
        return {"success": True, "data": {
            "response": "🚨 Emergency detected! Please call 108 immediately or go to the nearest hospital.",
            "agent": "agent1", "emergency_detected": True,
            "hospitals": hospitals, "consultation_complete": False
        }}
    
    # Add message to history
    profile["chat_history"].append({"role": "user", "content": message})
    
    # Get AI response
    ai_response = call_groq_directly(
        message=message,
        chat_history=profile["chat_history"][:-1],
        patient_name=profile.get("name", "Patient"),
        language=profile.get("language", "english")
    )
    profile["chat_history"].append({"role": "assistant", "content": ai_response})
    
    # Check completion — trigger words OR more than 10 exchanges
    completion_triggers = [
        "that's all", "thats all", "done", "finish", "complete",
        "end consultation", "bas itna hi", "that is all",
        "nothing else", "no more", "thank you thats all",
        "no other symptoms", "no other", "thats it", "that's it"
    ]
    
    user_message_count = len([m for m in profile["chat_history"] 
                               if m.get("role") == "user"])
    
    consultation_complete = (
        any(trigger in message_lower for trigger in completion_triggers) or
        user_message_count >= 5
    )
    
    if consultation_complete:
        # Extract symptom data from chat
        user_msgs = [m["content"] for m in profile["chat_history"] 
                     if m.get("role") == "user"]
        profile["symptoms"] = user_msgs[:5]
        profile["duration"] = "As described in chat"
        profile["severity"] = 5
        profile["status"] = "completed"
        sessions[session_id] = profile
        
        # Run full 4-agent pipeline in BACKGROUND THREAD
        # So the user gets immediate response without waiting 60+ seconds
        thread = threading.Thread(
            target=run_pipeline_background,
            args=(session_id,),
            daemon=True
        )
        thread.start()
        
        return {"success": True, "data": {
            "response": f"Thank you {profile['name']}! I've collected all your symptoms. Your full health report with diagnosis, nutrition plan, and expense analysis is being prepared. It will be ready in about 1-2 minutes. Click 'View Full Report' to check.",
            "agent": "agent2", "emergency_detected": False,
            "consultation_complete": True,
            "summary": {
                "conditions": [],
                "severity_flag": "mild",
                "see_doctor": False
            }
        }}
    
    return {"success": True, "data": {
        "response": ai_response, "agent": "agent1",
        "emergency_detected": False, "consultation_complete": False
    }}

@router.get("/report/{session_id}")
def get_report(session_id: str,
               current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    # Try memory first
    if session_id in sessions:
        profile = sessions[session_id]
        if profile["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        return {"success": True, "data": {
            "session_id": session_id,
            "session_date": profile.get("session_date", ""),
            "status": profile.get("status", "completed"),
            "patient": {
                "name": profile.get("name", ""),
                "age": profile.get("age", 0),
                "gender": profile.get("gender", ""),
                "city": profile.get("city", ""),
                "diet_pref": profile.get("diet_pref", "")
            },
            "symptoms": {
                "list": profile.get("symptoms", []),
                "duration": profile.get("duration", ""),
                "severity": profile.get("severity", 0),
                "emergency_flag": profile.get("emergency_flag", False)
            },
            "diagnosis": {
                "conditions": profile.get("conditions", []),
                "specialist_type": profile.get("specialist_type", ""),
                "medicines": profile.get("medicines", []),
                "severity_flag": profile.get("severity_flag", "mild"),
                "see_doctor": profile.get("see_doctor", False),
                "home_care": profile.get("home_care", []),
                "red_flags": profile.get("red_flags", []),
                "disclaimer": "⚠️ This is AI-powered analysis, NOT a medical diagnosis."
            },
            "nutrition": {
                "deficiencies": profile.get("deficiencies", []),
                "meal_plan": profile.get("meal_plan", []),
                "nutritional_focus": profile.get("nutritional_focus", ""),
                "nutrition_tips": profile.get("nutrition_tips", []),
                "daily_intake": profile.get("daily_intake", {}),
                "recommended_intake": profile.get("recommended_intake", {})
            },
            "finance": {
                "monthly_total": profile.get("monthly_total", 0),
                "expense_breakdown": profile.get("expense_breakdown", {}),
                "savings_estimate": profile.get("savings_estimate", 0),
                "savings_disclaimer": "Estimated projection. Actual savings may vary."
            },
            "pdf_available": bool(profile.get("pdf_path"))
        }}
    
    # Fallback to database
    consultation = db.query(Consultation).filter(
        Consultation.consultation_id == session_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Report not found")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {"success": True, "data": {
        "session_id": session_id,
        "session_date": str(consultation.session_date),
        "status": consultation.status,
        "patient": {
            "name": current_user.name, "age": current_user.age,
            "gender": current_user.gender, "city": current_user.city,
            "diet_pref": current_user.diet_pref
        },
        "symptoms": {
            "list": json.loads(consultation.symptoms or "[]"),
            "duration": consultation.duration or "",
            "severity": consultation.severity or 0,
            "emergency_flag": False
        },
        "diagnosis": {
            "conditions": json.loads(consultation.conditions or "[]"),
            "specialist_type": consultation.specialist_type or "",
            "medicines": json.loads(consultation.medicines or "[]"),
            "severity_flag": consultation.severity_flag or "mild",
            "see_doctor": bool(consultation.see_doctor),
            "home_care": [], "red_flags": [],
            "disclaimer": "⚠️ This is AI-powered analysis, NOT a medical diagnosis."
        },
        "nutrition": {
            "deficiencies": json.loads(consultation.deficiencies or "[]"),
            "meal_plan": json.loads(consultation.meal_plan or "[]"),
            "nutritional_focus": "", "nutrition_tips": []
        },
        "finance": {
            "monthly_total": consultation.monthly_total or 0,
            "expense_breakdown": json.loads(consultation.expense_breakdown or "{}"),
            "savings_estimate": consultation.savings_estimate or 0,
            "savings_disclaimer": "Estimated projection. Actual savings may vary."
        },
        "pdf_available": bool(consultation.pdf_path)
    }}

@router.get("/report/{session_id}/pdf")
def get_pdf(session_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    record = db.query(Consultation).filter(
        Consultation.consultation_id == session_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check session memory for latest pdf_path
    if session_id in sessions:
        pdf_path = sessions[session_id].get("pdf_path")
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf")
    
    pdf_path = record.pdf_path
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404,
            detail="PDF not yet generated. Please wait 1-2 minutes after consultation.")
    return FileResponse(pdf_path, media_type="application/pdf")

