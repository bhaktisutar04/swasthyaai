import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task
from crewai.tools import tool
from crewai import LLM

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

@tool("ifct_nutrition_tool")
def ifct_nutrition_tool(food_name: str) -> dict:
    """Searches IFCT 2017 nutritional dataset for a specific food item."""
    try:
        # Dynamically build path to backend/data/ifct_nutrition.json
        base_dir = os.path.dirname(os.path.dirname(__file__))
        file_path = os.path.join(base_dir, "data", "ifct_nutrition.json")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        food_name_lower = food_name.lower().strip()
        for item in data:
            if food_name_lower in item.get("food_name", "").lower() or food_name_lower in item.get("food_name_hindi", ""):
                return item
                
        return {"error": f"Food '{food_name}' not found"}
    except Exception as e:
        return {"error": f"Failed to load IFCT data: {e}"}

agent3 = Agent(
    role="Indian Nutrition Specialist",
    goal="Generate a personalized 7-day Indian meal plan based on diagnosis, respecting dietary preferences and allergies.",
    backstory="""You are a certified Indian nutritionist with deep knowledge 
    of IFCT 2017 food composition data. You create practical meal plans using 
    common Indian foods. You strictly respect veg/non-veg/vegan preferences 
    and never include allergens. You focus on fixing nutritional deficiencies 
    identified in the diagnosis.""",
    llm=llm,
    tools=[ifct_nutrition_tool],
    verbose=True,
    allow_delegation=False
)

def create_agent3_task(patient_profile: dict) -> Task:
    name = patient_profile.get("name", "Patient")
    age = patient_profile.get("age", 0)
    gender = patient_profile.get("gender", "unknown")
    diet_pref = patient_profile.get("diet_pref", "veg")
    allergies = patient_profile.get("allergies", [])
    
    conditions = [cond.get("name") for cond in patient_profile.get("conditions", [])]
    severity_flag = patient_profile.get("severity_flag", "mild")
    
    description = f"""
Patient: {name}, Age: {age}, Gender: {gender}
Diet preference: {diet_pref} — STRICTLY follow this, never suggest 
foods that violate this preference.
Allergies: {allergies} — NEVER include these foods.

Diagnosis conditions: {conditions}
Severity: {severity_flag}

Your tasks:
1. Identify nutritional deficiencies based on the diagnosis conditions
2. Generate a complete 7-day Indian meal plan
3. Each day must have: breakfast, mid_morning, lunch, evening_snack, dinner
4. Each meal must list food items and key nutrients provided
5. Focus on fixing deficiencies (iron, protein, vitamin C, B12, calcium)
6. Use only common Indian foods available in local markets
7. Keep meals practical and affordable

Diet rules:
- If diet_pref is "veg": only use diet_type "veg" foods
- If diet_pref is "non-veg": can use both veg and non-veg
- If diet_pref is "vegan": exclude all dairy and animal products

OUTPUT must be this exact JSON:
{{
  "deficiencies": [
    {{"nutrient": "Iron", "current_mg": 8.0, "required_mg": 18.0}}
  ],
  "nutritional_focus": "Increasing Iron and Vitamin C intake",
  "meal_plan": [
    {{
      "day": 1,
      "day_name": "Monday",
      "breakfast": {{
        "items": ["Poha with peanuts", "Lemon water"],
        "nutrients": {{"iron_mg": 3.0, "protein_g": 5.0, "calories": 250}}
      }},
      "mid_morning": {{
        "items": ["Amla juice", "Handful of almonds"],
        "nutrients": {{"vitamin_c_mg": 270, "protein_g": 3.0, "calories": 100}}
      }},
      "lunch": {{
        "items": ["Palak Dal", "Jowar Roti x2", "Curd"],
        "nutrients": {{"iron_mg": 5.0, "protein_g": 12.0, "calories": 450}}
      }},
      "evening_snack": {{
        "items": ["Sprouts chaat", "Green tea"],
        "nutrients": {{"protein_g": 4.0, "calories": 80}}
      }},
      "dinner": {{
        "items": ["Moong Dal Khichdi", "Steamed vegetables"],
        "nutrients": {{"iron_mg": 4.0, "protein_g": 10.0, "calories": 380}}
      }}
    }}
  ],
  "daily_intake": {{"iron_mg": 15, "protein_g": 45, "calories": 1800}},
  "recommended_intake": {{"iron_mg": 18, "protein_g": 60, "calories": 2000}},
  "nutrition_tips": [
    "Pair iron-rich foods with Vitamin C for better absorption",
    "Avoid tea/coffee immediately after meals"
  ]
}}
"""

    return Task(
        description=description,
        expected_output="Valid JSON with deficiencies and complete 7-day meal plan.",
        agent=agent3
    )

def parse_nutrition_output(raw_output: str) -> dict:
    """Safely parse nutrition agent JSON output."""
    default_output = {
        "deficiencies": [],
        "meal_plan": [],
        "nutrition_tips": [],
        "nutritional_focus": "Balanced Indian diet recommended."
    }
    try:
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0]
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0]
            
        return json.loads(raw_output.strip())
    except Exception as e:
        print(f"Error parsing nutrition output: {e}\nRaw output: {raw_output}")
        return default_output

