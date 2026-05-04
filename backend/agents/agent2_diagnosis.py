import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task
from crewai import LLM

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

agent2 = Agent(
    role="Medical Diagnosis Specialist",
    goal="Analyse symptom profile and return structured diagnosis with ranked conditions, medicines, and specialist recommendation.",
    backstory="""You are a medical analysis AI trained on clinical guidelines 
    and Indian healthcare data. You do NOT replace a real doctor. You provide 
    structured preliminary assessments. You always include medical disclaimers. 
    You rank conditions by likelihood and flag emergencies.""",
    llm=llm,
    tools=[],
    verbose=True,
    allow_delegation=False
)

def create_agent2_task(patient_profile: dict) -> Task:
    symptoms = patient_profile.get("symptoms", [])
    duration = patient_profile.get("duration", "unknown")
    severity = patient_profile.get("severity", 0)
    age = patient_profile.get("age", "unknown")
    gender = patient_profile.get("gender", "unknown")
    
    description = f"""Analyse the symptoms: {symptoms}
Duration: {duration}, Severity: {severity}
Patient age: {age}, gender: {gender}

Return 1-3 possible conditions ranked by likelihood.
For each condition include: name, confidence percentage, reasoning, likelihood (most_likely/possible/less_likely).
Recommend a specialist type (GP, Cardiologist, Dermatologist, ENT, etc).
List 3-5 generic medicine names with their use.
Include home care suggestions.
Set severity_flag: mild | moderate | severe.
Set see_doctor: true if moderate/severe or high uncertainty.

NEVER give dosage instructions.
ALWAYS include this disclaimer in response:
"⚠️ This is AI-powered analysis, NOT a medical diagnosis. Always consult a qualified healthcare professional."
"""

    expected_output = """{
    "conditions": [
        {
            "name": "condition name",
            "confidence": 75,
            "reasoning": "why this condition",
            "likelihood": "most_likely"
        }
    ],
    "specialist_type": "General Physician (GP)",
    "medicines": [
        {"name": "medicine name", "use": "what it treats"}
    ],
    "home_care": ["Rest 7-8 hours", "Stay hydrated"],
    "red_flags": ["High fever >101F", "Difficulty breathing"],
    "severity_flag": "mild",
    "see_doctor": false,
    "disclaimer": "⚠️ This is AI-powered analysis, NOT a medical diagnosis."
}"""

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent2
    )

def parse_diagnosis_output(raw_output: str) -> dict:
    """Parses JSON cleanly and uses a default fallback if structure is broken."""
    default_output = {
        "conditions": [],
        "specialist_type": "General Physician (GP)",
        "medicines": [],
        "home_care": [],
        "red_flags": [],
        "severity_flag": "mild",
        "see_doctor": True,
        "disclaimer": "⚠️ Please consult a doctor for proper diagnosis."
    }
    
    try:
        # Prevent markdown json blocks from breaking the parsing
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0]
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0]
            
        parsed = json.loads(raw_output.strip())
        return parsed
    except Exception as e:
        print(f"Error parsing Agent 2 diagnosis output: {e}\nRaw output: {raw_output}")
        return default_output

