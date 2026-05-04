import json
import logging
import time
from datetime import datetime
from crewai import Crew, Process
from agents.agent1_intake import agent1, create_agent1_task
from agents.agent2_diagnosis import agent2, create_agent2_task, parse_diagnosis_output
from agents.agent3_nutrition import agent3, create_agent3_task, parse_nutrition_output
from agents.agent4_finance import agent4, create_agent4_task, parse_finance_output
from memory.pinecone_client import store_session_summary
from db.database import Consultation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_intake_crew(patient_profile: dict) -> dict:
    """Runs ONLY Agent 1 for chat session loop tracking."""
    try:
        task1 = create_agent1_task(patient_profile)
        crew = Crew(
            agents=[agent1],
            tasks=[task1],
            process=Process.sequential,
            verbose=True
        )
        
        # Crew kickoff args may be named inputs or passed manually inside strings depending on CrewAI version.
        # But we'll follow standard execution style.
        result = crew.kickoff(inputs=patient_profile)
        
        try:
            raw_output = str(result)
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0]
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0]
                
            parsed = json.loads(raw_output.strip())
            
            patient_profile["symptoms"] = parsed.get("symptoms", patient_profile.get("symptoms", []))
            patient_profile["duration"] = parsed.get("duration", patient_profile.get("duration", ""))
            patient_profile["severity"] = parsed.get("severity", patient_profile.get("severity", 0))
            patient_profile["emergency_flag"] = parsed.get("emergency_flag", patient_profile.get("emergency_flag", False))
            
        except json.JSONDecodeError:
            logger.error("Failed to parse Agent 1 output from JSON.")
            
        return patient_profile
    except Exception as e:
        logger.error(f"run_intake_crew failed: {e}")
        return patient_profile

def run_diagnosis_crew(patient_profile: dict) -> dict:
    """Runs Agent 1 and Agent 2 sequentially after session is deemed complete."""
    try:
        task1 = create_agent1_task(patient_profile)
        task2 = create_agent2_task(patient_profile)
        
        # Chain contextually
        task2.context = [task1]
        
        crew = Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff(inputs=patient_profile)
        
        diagnosis = parse_diagnosis_output(str(result))
        
        patient_profile["conditions"] = diagnosis.get("conditions", [])
        patient_profile["medicines"] = diagnosis.get("medicines", [])
        patient_profile["specialist_type"] = diagnosis.get("specialist_type", "")
        patient_profile["severity_flag"] = diagnosis.get("severity_flag", "mild")
        patient_profile["see_doctor"] = diagnosis.get("see_doctor", False)
        patient_profile["home_care"] = diagnosis.get("home_care", [])
        patient_profile["red_flags"] = diagnosis.get("red_flags", [])
        patient_profile["status"] = "completed"
        
        return patient_profile
    except Exception as e:
        logger.error(f"run_diagnosis_crew failed: {e}")
        return patient_profile

def save_consultation_to_db(patient_profile: dict, db) -> None:
    """Synchronize consultation profile dynamically into SQLAlchemy."""
    session_id = patient_profile.get("session_id")
    if not session_id:
        return
        
    try:
        record = db.query(Consultation).filter(Consultation.consultation_id == session_id).first()
        if not record:
            return
            
        record.duration = patient_profile.get("duration", "")
        record.severity = patient_profile.get("severity", 0)
        record.symptoms = json.dumps(patient_profile.get("symptoms", []))
        record.conditions = json.dumps(patient_profile.get("conditions", []))
        record.medicines = json.dumps(patient_profile.get("medicines", []))
        record.severity_flag = patient_profile.get("severity_flag", "")
        record.see_doctor = patient_profile.get("see_doctor", False)
        record.status = "completed"
        
        record.deficiencies = json.dumps(patient_profile.get("deficiencies", []))
        record.meal_plan = json.dumps(patient_profile.get("meal_plan", []))
        record.monthly_total = patient_profile.get("monthly_total", 0)
        record.expense_breakdown = json.dumps(patient_profile.get("expense_breakdown", {}))
        record.savings_estimate = patient_profile.get("savings_estimate", 0)
        record.pdf_path = patient_profile.get("pdf_path", None)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"save_consultation_to_db fail safely reversed via rollback: {e}")

def save_to_pinecone(patient_profile: dict) -> None:
    """Saves condensed patient diagnosis loop back into Pinecone vector storage."""
    try:
        user_id = patient_profile.get("user_id")
        session_id = patient_profile.get("session_id")
        name = patient_profile.get("name", "Unknown")
        age = patient_profile.get("age", "Unknown")
        
        symptoms_list = patient_profile.get("symptoms", [])
        symptoms = ", ".join(symptoms_list) if isinstance(symptoms_list, list) else str(symptoms_list)
        
        duration = patient_profile.get("duration", "unknown duration")
        severity_flag = patient_profile.get("severity_flag", "mild")
        
        conditions = patient_profile.get("conditions", [])
        if conditions and isinstance(conditions, list):
            first_condition = conditions[0].get("name", "Unknown condition")
        else:
            first_condition = "Unknown condition"
            
        summary = f"Patient {name}, {age}, presented with {symptoms} for {duration}. Diagnosed with {first_condition}. Severity: {severity_flag}."
        
        metadata = {
            "session_id": session_id,
            "session_date": str(datetime.now().date()),
            "primary_condition": first_condition,
            "severity_flag": severity_flag
        }
        
        store_session_summary(int(user_id), session_id, summary, metadata)
    except Exception as e:
        logger.error(f"Pinecone sync explicitly ignored via generic except lockalize: {e}")

def run_full_crew(patient_profile: dict, db) -> dict:
    """Runs all 4 agents in sequence."""
    try:
        task1 = create_agent1_task(patient_profile)
        task2 = create_agent2_task(patient_profile)
        
        diagnosis_crew = Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=True
        )
        diagnosis_result = diagnosis_crew.kickoff(
            inputs=patient_profile
        )
        # Parse diagnosis and update patient_profile
        diagnosis = parse_diagnosis_output(str(diagnosis_result))
        patient_profile["conditions"] = diagnosis.get("conditions", [])
        patient_profile["medicines"] = diagnosis.get("medicines", [])
        patient_profile["specialist_type"] = diagnosis.get("specialist_type", "")
        patient_profile["severity_flag"] = diagnosis.get("severity_flag", "mild")
        patient_profile["see_doctor"] = diagnosis.get("see_doctor", False)
        patient_profile["home_care"] = diagnosis.get("home_care", [])
        patient_profile["red_flags"] = diagnosis.get("red_flags", [])

        time.sleep(15)  # Wait 15 seconds for rate limit reset

        task3 = create_agent3_task(patient_profile)
        nutrition_crew = Crew(
            agents=[agent3],
            tasks=[task3],
            process=Process.sequential,
            verbose=True
        )
        try:
            nutrition_result = nutrition_crew.kickoff(
                inputs=patient_profile
            )
            nutrition = parse_nutrition_output(str(nutrition_result))
            patient_profile["deficiencies"] = nutrition.get("deficiencies", [])
            patient_profile["meal_plan"] = nutrition.get("meal_plan", [])
            patient_profile["nutritional_focus"] = nutrition.get("nutritional_focus", "")
            patient_profile["nutrition_tips"] = nutrition.get("nutrition_tips", [])
            patient_profile["daily_intake"] = nutrition.get("daily_intake", {})
            patient_profile["recommended_intake"] = nutrition.get("recommended_intake", {})
        except Exception as e:
            print(f"Nutrition agent failed: {e}")
            patient_profile["meal_plan"] = []

        time.sleep(15)  # Wait 15 seconds again

        task4 = create_agent4_task(patient_profile)
        finance_crew = Crew(
            agents=[agent4],
            tasks=[task4],
            process=Process.sequential,
            verbose=True
        )
        try:
            finance_result = finance_crew.kickoff(
                inputs=patient_profile
            )
            finance = parse_finance_output(str(finance_result))
            patient_profile["monthly_total"] = finance.get("monthly_total", 0)
            patient_profile["expense_breakdown"] = finance.get("expense_breakdown", {})
            patient_profile["savings_estimate"] = finance.get("savings_estimate", 0)
            patient_profile["pdf_path"] = finance.get("pdf_path", None)
        except Exception as e:
            print(f"Finance agent failed: {e}")

        # Generate PDF directly with all data
        try:
            from pdf.report_generator import generate_report
            pdf_path = generate_report(patient_profile)
            if pdf_path:
                patient_profile["pdf_path"] = pdf_path
                print(f"PDF generated with full data: {pdf_path}")
        except Exception as e:
            print(f"PDF generation error: {e}")

        patient_profile["status"] = "completed"
        
        # Save to database and Pinecone
        save_consultation_to_db(patient_profile, db)
        save_to_pinecone(patient_profile)
        
        return patient_profile
    except Exception as e:
        logger.error(f"run_full_crew failed: {e}")
        return patient_profile

def run_nutrition_only(patient_profile: dict) -> dict:
    """Runs only Agent 3 in isolation."""
    try:
        task3 = create_agent3_task(patient_profile)
        crew = Crew(agents=[agent3], tasks=[task3], process=Process.sequential)
        result = crew.kickoff(inputs=patient_profile)
        
        nutrition = parse_nutrition_output(str(result))
        
        patient_profile["deficiencies"] = nutrition.get("deficiencies", [])
        patient_profile["meal_plan"] = nutrition.get("meal_plan", [])
        patient_profile["nutritional_focus"] = nutrition.get("nutritional_focus", "")
        patient_profile["nutrition_tips"] = nutrition.get("nutrition_tips", [])
        patient_profile["daily_intake"] = nutrition.get("daily_intake", {})
        patient_profile["recommended_intake"] = nutrition.get("recommended_intake", {})
        
        return patient_profile
    except Exception as e:
        logger.error(f"run_nutrition_only failed: {e}")
        return patient_profile


