import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task
from crewai.tools import tool
from crewai import LLM
from db.database import get_db, Expense
from sqlalchemy.orm import Session
from datetime import datetime

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

def get_expense_summary(user_id: int, db: Session):
    now = datetime.utcnow()
    m = now.month - 1
    y = now.year
    if m <= 0:
        m += 12
        y -= 1
    try:
        one_month_ago = now.replace(year=y, month=m)
    except ValueError:
        one_month_ago = now.replace(year=y, month=m, day=28)
        
    expenses = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= one_month_ago
    ).all()
    return expenses

@tool("expense_summary_tool")
def expense_summary_tool(user_id: int) -> dict:
    """Connects to SQL DB, queries expenses from the last month, and returns sum and breakdown."""
    try:
        db = next(get_db())
        expenses = get_expense_summary(user_id, db)
        
        breakdown = {}
        total = 0.0
        for exp in expenses:
            if exp.category and exp.amount:
                breakdown[exp.category] = breakdown.get(exp.category, 0.0) + float(exp.amount)
                total += float(exp.amount)
            
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

