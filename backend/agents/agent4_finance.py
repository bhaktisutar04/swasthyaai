import os
import json
import sqlite3
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

@tool("expense_summary_tool")
def expense_summary_tool(user_id: int) -> dict:
    """Connects to SQL DB, queries expenses from the last month, and returns sum and breakdown."""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///./swasthyaai.db")
        db_path = db_url.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT category, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = ? AND expense_date >= date('now', '-1 month')
        GROUP BY category
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        
        breakdown = {}
        total = 0.0
        for category, amt in rows:
            if category and amt:
                breakdown[category] = float(amt)
                total += float(amt)
            
        conn.close()
        
        return {"monthly_total": total, "expense_breakdown": breakdown}
        
    except Exception as e:
        print(f"Error in expense_summary_tool: {e}")
        return {}

agent4 = Agent(
    role="Medical Finance Analyst",
    goal="Calculate medical expenses and project savings",
    backstory="""You are a health finance specialist helping 
    Indian patients understand healthcare spending. You calculate 
    honest savings projections labeled as estimated.""",
    llm=llm,
    tools=[expense_summary_tool],
    allow_delegation=False,
    verbose=True
)

def create_agent4_task(patient_profile: dict) -> Task:
    user_id = patient_profile.get("user_id")
    
    description = f"""
Read expense history for user_id {user_id} using expense_summary_tool.
Calculate monthly total and breakdown by category.
Calculate savings estimate using formula:
savings = (medicine_cost * 0.6) + (consultation_cost * 0.6) - 500
where 500 = average monthly grocery increase.
Use the costs from the expense summary. If they don't exist, treat them as 0.
Always label as "Estimated projection".

Your final output must be this EXACT JSON (update values based on calculations):
{{
  "monthly_total": 0.0,
  "expense_breakdown": {{
    "medicine": 0.0,
    "consultation": 0.0,
    "tests": 0.0,
    "hospital": 0.0,
    "other": 0.0
  }},
  "savings_estimate": 0.0,
  "savings_disclaimer": "Estimated projection. Actual savings may vary."
}}
"""

    return Task(
        description=description,
        expected_output="Valid JSON with finance calculations.",
        agent=agent4
    )

def parse_finance_output(raw_output: str) -> dict:
    """Parses finance agent JSON output, returning a safe default on failure."""
    default_output = {
        "monthly_total": 0, 
        "expense_breakdown": {}, 
        "savings_estimate": 0
    }
    
    try:
        if "```json" in raw_output:
            raw_output = raw_output.split("```json")[1].split("```")[0]
        elif "```" in raw_output:
            raw_output = raw_output.split("```")[1].split("```")[0]
            
        return json.loads(raw_output.strip())
    except Exception as e:
        print(f"Error parsing finance output: {e}\nRaw output: {raw_output}")
        return default_output

