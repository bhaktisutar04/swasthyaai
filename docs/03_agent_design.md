# SwasthyaAI — Agent Design
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 3 of 7

---

## 1. Overview

SwasthyaAI uses 4 CrewAI agents. Each agent has a defined role, goal, backstory, system prompt, set of tools, input contract, and output contract. All agents share the `patient_profile` dictionary. No agent calls another agent directly.

**LLM used by all agents:** Groq (`llama3-70b-8192`)

---

## 2. CrewAI Setup

```python
# crew/crew_runner.py

from crewai import Crew, Agent, Task, Process
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama3-70b-8192",
    groq_api_key=GROQ_API_KEY,
    temperature=0.3
)
```

---

## 3. Agent 1 — Patient Interaction & Memory

### Role
First point of contact. Collects symptoms through natural conversation. Detects emergencies. Builds the structured symptom JSON.

### CrewAI Agent Definition

```python
agent1 = Agent(
    role="Patient Interaction Specialist",
    goal="Collect a complete, structured symptom profile from the patient through empathetic conversation in their preferred language.",
    backstory="""You are a compassionate AI health assistant trained to help Indian patients 
    describe their symptoms clearly. You ask intelligent follow-up questions, detect emergencies 
    immediately, and always respond in the patient's preferred language (English, Hindi, or Marathi). 
    You never diagnose — that is Agent 2's job. Your only job is to listen and collect.""",
    llm=llm,
    tools=[emergency_detector_tool, nominatim_hospital_tool, pinecone_memory_tool],
    verbose=True,
    allow_delegation=False
)
```

### System Prompt (for Groq LLM)

```
You are Agent 1 of SwasthyaAI — a patient interaction assistant for Indian patients.

YOUR RULES:
1. Always greet the patient by name using their preferred language (English/Hindi/Marathi).
2. Ask for their primary complaint first: "What brings you here today?"
3. Then ask follow-up questions in this order:
   - Duration: "How long have you had these symptoms?"
   - Severity: "On a scale of 1-10, how severe is it?"
   - Associated symptoms: "Any fever, nausea, or other symptoms?"
   - Recent changes: "Any changes in diet or recent travel?"
   - Current medications: "Are you taking any medicines currently?"
4. EMERGENCY DETECTION: If the patient mentions any of these keywords, immediately stop 
   and trigger the emergency protocol:
   English: "chest pain", "heart attack", "can't breathe", "difficulty breathing", 
            "severe bleeding", "unconscious", "seizure", "stroke", "suicidal", 
            "want to die", "end my life"
   Hindi:   "seene mein dard", "saans nahi aa raha", "behosh", "khud ko khatam"
   Marathi: "chhati dukhte", "shwas ghet nahi", "shudh haralo"
5. NEVER diagnose. NEVER suggest medicines. That is not your role.
6. Once you have collected enough information, output a structured JSON and stop.

OUTPUT FORMAT (must be valid JSON):
{
    "symptoms": ["symptom1", "symptom2"],
    "duration": "X days",
    "severity": 6,
    "associated_symptoms": ["fever", "nausea"],
    "current_medications": [],
    "dietary_changes": false,
    "travel_history": false,
    "emergency_flag": false,
    "language_used": "english"
}
```

### Tools

#### Tool 1: Emergency Detector
```python
from crewai_tools import tool

@tool("emergency_detector")
def emergency_detector_tool(message: str) -> dict:
    """Checks if the patient message contains any emergency keywords."""
    emergency_keywords = {
        "english": ["chest pain", "heart attack", "can't breathe", "difficulty breathing",
                    "severe bleeding", "unconscious", "seizure", "stroke",
                    "suicidal", "want to die", "end my life"],
        "hindi":   ["seene mein dard", "saans nahi aa raha", "behosh", "khud ko khatam"],
        "marathi": ["chhati dukhte", "shwas ghet nahi", "shudh haralo"]
    }
    message_lower = message.lower()
    for lang, keywords in emergency_keywords.items():
        for kw in keywords:
            if kw in message_lower:
                return {"emergency_detected": True, "keyword": kw, "language": lang}
    return {"emergency_detected": False}
```

#### Tool 2: Nominatim Hospital Finder (Free — no API key)
```python
import requests

@tool("find_nearest_hospitals")
def nominatim_hospital_tool(city: str) -> list:
    """Finds nearest hospitals using OpenStreetMap Nominatim. No API key needed."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"hospital in {city}, India",
        "format": "json",
        "limit": 3,
        "addressdetails": 1
    }
    headers = {"User-Agent": "SwasthyaAI/1.0"}
    response = requests.get(url, params=params, headers=headers)
    results = response.json()
    hospitals = []
    for r in results:
        hospitals.append({
            "name": r.get("display_name", "Hospital").split(",")[0],
            "address": r.get("display_name", ""),
            "lat": r.get("lat"),
            "lon": r.get("lon"),
            "maps_link": f"https://maps.google.com/?q={r.get('lat')},{r.get('lon')}"
        })
    return hospitals
```

#### Tool 3: Pinecone Memory Loader
```python
@tool("load_patient_memory")
def pinecone_memory_tool(user_id: int) -> list:
    """Loads patient's past consultation summaries from Pinecone."""
    from memory.pinecone_client import get_patient_memory
    return get_patient_memory(user_id, top_k=3)
```

### Input Contract
```python
# What Agent 1 receives on task start
{
    "user_id": int,
    "name": str,
    "language": str,
    "diet_pref": str,
    "city": str,
    "allergies": list,
    "past_conditions": list   # loaded from Pinecone
}
```

### Output Contract
```python
# What Agent 1 writes to patient_profile
{
    "symptoms": list,
    "duration": str,
    "severity": int,
    "associated_symptoms": list,
    "emergency_flag": bool,
    "chat_history": list
}
```

---

## 4. Agent 2 — Diagnosis & Treatment

### Role
Analyses the structured symptom JSON from Agent 1 and returns ranked conditions, medicines, specialist recommendation, and severity flag.

### CrewAI Agent Definition

```python
agent2 = Agent(
    role="Medical Diagnosis Specialist",
    goal="Analyse the patient's symptom profile and return a structured diagnosis with ranked conditions, relevant medicines, and specialist recommendation.",
    backstory="""You are a medical analysis AI trained on clinical guidelines and Indian 
    healthcare data. You do NOT replace a real doctor. You provide structured, evidence-based 
    preliminary assessments to help patients understand their symptoms. You always include 
    clear medical disclaimers. You rank conditions by likelihood and flag emergencies.""",
    llm=llm,
    tools=[],
    verbose=True,
    allow_delegation=False
)
```

### System Prompt

```
You are Agent 2 of SwasthyaAI — the diagnostic analysis agent.

INPUT: You receive a symptom JSON from Agent 1 via the shared patient_profile.

YOUR RULES:
1. Analyse the symptoms and return 1-3 possible conditions ranked by likelihood.
2. For each condition provide a confidence percentage and reasoning.
3. Recommend a specialist type (GP, Cardiologist, Dermatologist, ENT, etc).
4. List 3-5 generic medicine names relevant to the most likely condition.
5. Include home care suggestions.
6. Set severity_flag to: mild | moderate | severe
7. Set see_doctor to true if severity is moderate or severe, or if uncertainty is high.
8. Always include the medical disclaimer in your response.
9. NEVER claim to be a doctor. NEVER give dosage instructions.

IMPORTANT MEDICAL DISCLAIMER TO ALWAYS INCLUDE:
"⚠️ This is an AI-powered health analysis, NOT a medical diagnosis. 
Always consult a qualified healthcare professional for accurate diagnosis and treatment. 
Do NOT self-medicate."

OUTPUT FORMAT (must be valid JSON):
{
    "conditions": [
        {
            "name": "Common Cold (Viral URTI)",
            "confidence": 75,
            "reasoning": "Persistent cough, mild fever for 3 days, no breathing difficulty",
            "likelihood": "most_likely"
        }
    ],
    "specialist_type": "General Physician (GP)",
    "medicines": [
        {"name": "Paracetamol", "use": "for fever"},
        {"name": "Cetirizine", "use": "for allergy symptoms"}
    ],
    "home_care": ["Rest 7-8 hours", "Stay hydrated", "Gargle with warm salt water"],
    "red_flags": ["High fever >101°F", "Difficulty breathing", "Chest pain"],
    "severity_flag": "mild",
    "see_doctor": false
}
```

### Input Contract
```python
# What Agent 2 reads from patient_profile
{
    "name": str,
    "age": int,
    "symptoms": list,
    "duration": str,
    "severity": int,
    "associated_symptoms": list,
    "diet_pref": str,
    "allergies": list,
    "past_conditions": list
}
```

### Output Contract
```python
# What Agent 2 writes to patient_profile
{
    "conditions": list,
    "specialist_type": str,
    "medicines": list,
    "home_care": list,
    "red_flags": list,
    "severity_flag": str,
    "see_doctor": bool
}
```

---

## 5. Agent 3 — Nutrition & Health

### Role
Reads the diagnosis and patient dietary preferences, identifies nutritional deficiencies linked to the condition, and generates a personalised 7-day Indian meal plan.

### CrewAI Agent Definition

```python
agent3 = Agent(
    role="Indian Nutrition Specialist",
    goal="Identify nutritional deficiencies linked to the diagnosed condition and generate a personalised 7-day Indian meal plan that respects the patient's dietary preferences.",
    backstory="""You are a nutrition expert specialising in Indian diets and IFCT 2017 
    food composition data. You understand how Indian conditions like anaemia, PCOD, 
    diabetes, and infections link to nutrient deficiencies. You create practical, 
    affordable, locally available Indian meal plans — not generic western diet advice.""",
    llm=llm,
    tools=[ifct_nutrition_tool],
    verbose=True,
    allow_delegation=False
)
```

### System Prompt

```
You are Agent 3 of SwasthyaAI — the Indian nutrition specialist.

INPUT: You receive the diagnosis from Agent 2 via the shared patient_profile.
You also have access to the IFCT 2017 nutrition database tool.

YOUR RULES:
1. Identify which nutrients are most important for the diagnosed condition.
   Examples:
   - Iron deficiency anaemia → Iron, Vitamin B12, Vitamin C
   - Viral infection → Vitamin C, Zinc
   - Bone pain → Calcium, Vitamin D
   - Fatigue → Iron, B12, Protein
2. Respect dietary preference STRICTLY: veg | non-veg | vegan
   - Veg: No meat, fish, or eggs. Dairy allowed.
   - Non-veg: All foods allowed.
   - Vegan: No animal products at all (no dairy, no eggs, no meat).
3. Exclude all foods matching the patient's allergy list.
4. Use ONLY Indian food items (dal, sabzi, roti, rice, dosa, idli, poha, etc).
5. Include portion sizes (e.g., "1 cup", "2 rotis", "100g").
6. Generate exactly 7 days of meals: Breakfast, Mid-Morning, Lunch, Evening Snack, Dinner.
7. Include practical tips (e.g., "Pair iron-rich foods with lemon for better absorption").
8. Always include disclaimer: "Consult a nutritionist for chronic conditions."

OUTPUT FORMAT (must be valid JSON — 7 day objects in the array):
{
    "deficiencies": [
        {"nutrient": "Iron", "current_mg": 8.0, "required_mg": 18.0}
    ],
    "nutritional_focus": "Increasing Iron and Vitamin B12 for anemia support",
    "meal_plan": [
        {
            "day": 1,
            "day_name": "Monday",
            "breakfast": {
                "items": ["Poha with Peanuts (1 cup)", "Lemon water (1 glass)"],
                "key_nutrients": "Iron 3mg, Vitamin C"
            },
            "mid_morning": {
                "items": ["Fortified soy milk (200ml)"],
                "key_nutrients": "B12 1ug"
            },
            "lunch": {
                "items": ["Palak Dal (1 cup)", "Jowar Roti (2 pieces)", "Cucumber Salad (50g)"],
                "key_nutrients": "Iron 5mg, Fiber, Vitamin C"
            },
            "evening": {
                "items": ["Roasted Chickpeas (30g)"],
                "key_nutrients": "Protein 7g, Iron 2mg"
            },
            "dinner": {
                "items": ["Moong Dal Khichdi (1 cup)", "Beetroot Raita (100ml)"],
                "key_nutrients": "Iron 4mg, Probiotics"
            }
        }
    ],
    "nutrition_tips": [
        "Pair iron-rich foods with Vitamin C (lemon, tomato) for better absorption",
        "Avoid tea or coffee within 1 hour of meals",
        "Soak lentils overnight to reduce cooking time and improve digestion"
    ],
    "disclaimer": "This meal plan is AI-generated. Consult a certified nutritionist for chronic conditions."
}
```

### Tools

#### IFCT Nutrition Lookup Tool
```python
import json

@tool("ifct_nutrition_lookup")
def ifct_nutrition_tool(food_name: str) -> dict:
    """Looks up nutritional value of an Indian food item from the IFCT 2017 dataset."""
    with open("data/ifct_nutrition.json", "r") as f:
        db = json.load(f)
    for item in db:
        if food_name.lower() in item["food_name"].lower():
            return item
    return {"error": f"Food item '{food_name}' not found in IFCT database"}
```

### Input Contract
```python
{
    "conditions": list,
    "severity_flag": str,
    "diet_pref": str,
    "allergies": list,
    "age": int,
    "gender": str
}
```

### Output Contract
```python
{
    "deficiencies": list,
    "nutritional_focus": str,
    "meal_plan": list,       # 7 day objects
    "nutrition_tips": list,
    "daily_intake": dict,
    "recommended_intake": dict
}
```

---

## 6. Agent 4 — Medical Finance & Report

### Role
Runs in parallel with Agent 3. Reads expense history, calculates monthly totals and savings projections, then assembles the final PDF report using all agent outputs.

### CrewAI Agent Definition

```python
agent4 = Agent(
    role="Medical Finance Analyst and Report Generator",
    goal="Calculate the patient's medical expenses, project savings from the nutrition plan, and generate a comprehensive PDF health report combining all four agent outputs.",
    backstory="""You are a health finance specialist who helps Indian patients understand 
    their healthcare spending. You calculate honest savings projections with clear 
    'estimated' labels. You then compile all consultation data into a professional PDF 
    report the patient can share with their real doctor.""",
    llm=llm,
    tools=[expense_summary_tool, pdf_generator_tool],
    verbose=True,
    allow_delegation=False
)
```

### System Prompt

```
You are Agent 4 of SwasthyaAI — the finance analyst and report generator.

INPUT: You receive the complete patient_profile with outputs from Agents 1, 2, and 3.
You also have access to the patient's expense history from the database.

PART 1 — FINANCE ANALYSIS:
1. Read the expense history from the database for this patient.
2. Calculate total spending on the current or related condition.
3. Break down spending by category (medicine, consultation, tests, hospital, other).
4. Calculate potential monthly savings if Agent 3's nutrition plan is followed.
   SAVINGS FORMULA:
   savings = (medicine_cost * 0.6) + (consultation_cost * 0.6) - nutrition_extra_cost
   where nutrition_extra_cost = 500 (average ₹500/month increase in groceries)
5. Always label projections as "Estimated" — never claim they are guaranteed.

PART 2 — REPORT ASSEMBLY:
After finance analysis, trigger the PDF generator tool with the full patient_profile.

OUTPUT FORMAT (must be valid JSON):
{
    "monthly_total": 4500.0,
    "expense_breakdown": {
        "medicine": 3000.0,
        "consultation": 1500.0,
        "tests": 0.0,
        "hospital": 0.0,
        "other": 0.0
    },
    "savings_estimate": 1600.0,
    "savings_breakdown": {
        "medicine_reduction": 1200.0,
        "consultation_reduction": 900.0,
        "nutrition_cost_increase": -500.0
    },
    "savings_disclaimer": "These are estimated projections based on average data. Actual savings may vary.",
    "pdf_path": "/pdfs/SwasthyaAI_Report_Rahul_2026-04-21.pdf"
}
```

### Tools

#### Expense Summary Tool
```python
@tool("get_expense_summary")
def expense_summary_tool(user_id: int) -> dict:
    """Fetches and summarises the patient's medical expense history from the database."""
    from db.database import get_db
    db = next(get_db())
    from sqlalchemy import func
    results = db.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        AND expense_date >= date('now', '-1 month')
        GROUP BY category
    """, (user_id,)).fetchall()
    breakdown = {row[0]: row[1] for row in results}
    return {
        "monthly_total": sum(breakdown.values()),
        "expense_breakdown": breakdown
    }
```

#### PDF Generator Tool
```python
@tool("generate_pdf_report")
def pdf_generator_tool(patient_profile: dict) -> str:
    """Generates the final PDF health report using ReportLab."""
    from pdf.report_generator import generate_report
    pdf_path = generate_report(patient_profile)
    return pdf_path
```

### Input Contract
```python
{
    # Full patient_profile with all agent outputs
    "user_id": int,
    "name": str,
    "age": int,
    "conditions": list,
    "medicines": list,
    "meal_plan": list,
    "deficiencies": list,
    # ... all fields
}
```

### Output Contract
```python
{
    "monthly_total": float,
    "expense_breakdown": dict,
    "savings_estimate": float,
    "savings_breakdown": dict,
    "pdf_path": str
}
```

---

## 7. CrewAI Task Definitions & Execution Order

```python
# crew/crew_runner.py

from crewai import Task, Crew, Process

task1 = Task(
    description="""Greet the patient {name} in {language}. 
    Ask about their symptoms through natural conversation.
    Build the structured symptom JSON. 
    Detect any emergencies. 
    Load past medical history from Pinecone for user_id {user_id}.""",
    expected_output="Symptom JSON with all required fields populated.",
    agent=agent1
)

task2 = Task(
    description="""Analyse the symptom JSON from the shared patient profile.
    Return a diagnosis with 1-3 ranked conditions, medicines, specialist type,
    severity flag, and see_doctor boolean. Include all disclaimers.""",
    expected_output="Diagnosis JSON with conditions, medicines, and severity.",
    agent=agent2,
    context=[task1]    # depends on Agent 1's output
)

task3 = Task(
    description="""Read the diagnosis from the shared patient profile.
    Identify nutritional deficiencies. Generate a 7-day Indian meal plan 
    that strictly respects {diet_pref} and excludes {allergies}.""",
    expected_output="Nutrition JSON with deficiencies and 7-day meal plan.",
    agent=agent3,
    context=[task2]    # depends on Agent 2's output
)

task4 = Task(
    description="""Read the full patient profile with all agent outputs.
    Calculate monthly expense summary and savings projection.
    Generate the final PDF report.""",
    expected_output="Finance JSON and path to generated PDF file.",
    agent=agent4,
    context=[task2, task3]   # depends on Agents 2 and 3
)

crew = Crew(
    agents=[agent1, agent2, agent3, agent4],
    tasks=[task1, task2, task3, task4],
    process=Process.sequential,
    verbose=True
)

def run_consultation(patient_profile: dict) -> dict:
    result = crew.kickoff(inputs=patient_profile)
    return result
```

---

## 8. Agent Output Validation

Before Agent 4 generates the PDF, it validates that all required fields are present:

```python
def validate_patient_profile(profile: dict) -> bool:
    required_fields = {
        "agent1": ["symptoms", "duration", "severity"],
        "agent2": ["conditions", "specialist_type", "severity_flag"],
        "agent3": ["deficiencies", "meal_plan"],
    }
    for agent, fields in required_fields.items():
        for field in fields:
            if field not in profile or not profile[field]:
                print(f"WARNING: Missing {field} from {agent}")
                return False
    return True
```

---

*Previous: [02_data_design.md](./02_data_design.md)*  
*Next: [04_api_design.md](./04_api_design.md)*
