# F3 — Multi-Agent AI Pipeline (CrewAI): Specification

> **Feature ID**: F3  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F2 (Consultation triggers pipeline)

---

## 1. Overview

The Multi-Agent AI Pipeline is the analytical brain of SwasthyaAI. After a consultation chat completes, a sequential 4-agent pipeline runs in the background to produce a comprehensive health analysis: symptom structuring, medical diagnosis, personalized Indian nutrition plan, and financial impact analysis. Results are saved to the database, stored in Pinecone vector memory, and compiled into a downloadable PDF report.

---

## 2. Goals

1. Structure raw symptom conversations into a clinically organized profile.
2. Provide AI-powered preliminary diagnosis with ranked conditions, confidence scores, and specialist recommendations.
3. Generate a personalized 7-day Indian meal plan respecting dietary preferences and allergies.
4. Analyze medical expenses and project potential savings through improved nutrition.
5. Persist all results to database and vector memory for future reference.
6. Generate a professional PDF report and upload to cloud storage.

---

## 3. Agent Specifications

### Agent 1 — Patient Interaction Specialist
| Property | Value |
|----------|-------|
| Role | Patient Interaction Specialist |
| Goal | Collect complete structured symptom profile through empathetic conversation |
| LLM | `groq/llama-3.3-70b-versatile`, temperature 0.3 |
| Tools | `emergency_detector_tool`, `nominatim_hospital_tool`, `pinecone_memory_tool` |
| Output | JSON: symptoms[], duration, severity (1-10), associated_symptoms, current_medications, emergency_flag, language_used |

### Agent 2 — Medical Diagnosis Specialist
| Property | Value |
|----------|-------|
| Role | Medical Diagnosis Specialist |
| Goal | Analyze symptom profile, return structured diagnosis with ranked conditions |
| LLM | `groq/llama-3.3-70b-versatile`, temperature 0.3 |
| Tools | None |
| Output | JSON: conditions[] (name, confidence%, reasoning, likelihood), specialist_type, medicines[] (name, use), home_care[], red_flags[], severity_flag, see_doctor, disclaimer |

### Agent 3 — Indian Nutrition Specialist
| Property | Value |
|----------|-------|
| Role | Indian Nutrition Specialist |
| Goal | Generate personalized 7-day Indian meal plan based on diagnosis |
| LLM | `groq/llama-3.3-70b-versatile`, temperature 0.3 |
| Tools | `ifct_nutrition_tool` (IFCT 2017 food database lookup) |
| Output | JSON: deficiencies[] (nutrient, current_mg, required_mg), nutritional_focus, meal_plan[7 days × 5 slots], daily_intake, recommended_intake, nutrition_tips[] |

### Agent 4 — Medical Finance Analyst
| Property | Value |
|----------|-------|
| Role | Medical Finance Analyst |
| Goal | Calculate medical expenses and project savings |
| LLM | `groq/llama-3.3-70b-versatile`, temperature 0.3 |
| Tools | `expense_summary_tool` (SQLite DB query) |
| Output | JSON: monthly_total, expense_breakdown{}, savings_estimate, savings_disclaimer |

---

## 4. Functional Requirements

### Pipeline Execution
- **FR-3.1**: Agents run sequentially: Agent 1 → Agent 2 → Agent 3 → Agent 4.
- **FR-3.2**: 15-second delay between agent crews to respect Groq API rate limits.
- **FR-3.3**: Agent 2's task receives Agent 1's output as context.
- **FR-3.4**: Each agent's output is parsed from raw string to JSON, stripping markdown code fences.
- **FR-3.5**: If any agent fails, use robust defaults and continue the pipeline.

### Tools
- **FR-3.6**: `emergency_detector_tool` — keyword-based detection in English, Hindi, Marathi.
- **FR-3.7**: `nominatim_hospital_tool` — OpenStreetMap search for up to 3 hospitals in patient's city.
- **FR-3.8**: `pinecone_memory_tool` — retrieves top 3 past medical summaries for the user.
- **FR-3.9**: `ifct_nutrition_tool` — searches local IFCT 2017 JSON dataset by food name (English + Hindi).
- **FR-3.10**: `expense_summary_tool` — queries SQLite for last month's expenses grouped by category.

### Post-Pipeline
- **FR-3.11**: Generate PDF report via ReportLab and upload to Cloudinary.
- **FR-3.12**: Save all results to `consultations` table via `save_consultation_to_db()`.
- **FR-3.13**: Store condensed session summary in Pinecone via `save_to_pinecone()`.
- **FR-3.14**: Update in-memory session dict with all computed data.

### Diet Rules
- **FR-3.15**: If `diet_pref = "veg"` → only vegetarian foods.
- **FR-3.16**: If `diet_pref = "non-veg"` → both veg and non-veg allowed.
- **FR-3.17**: If `diet_pref = "vegan"` → exclude all dairy and animal products.
- **FR-3.18**: Never include foods matching the patient's allergy list.

### Diagnosis Rules
- **FR-3.19**: Return 1-3 possible conditions ranked by likelihood (most_likely → possible → less_likely).
- **FR-3.20**: Set `see_doctor = true` if severity is moderate/severe or high uncertainty.
- **FR-3.21**: Never provide medicine dosage instructions.
- **FR-3.22**: Always include medical disclaimer.

### Savings Formula
- **FR-3.23**: `savings_estimate = (medicine_cost × 0.6) + (consultation_cost × 0.6) − 500`
- **FR-3.24**: Always label as "Estimated projection. Actual savings may vary."

---

## 5. External Services

| Service | Used By | Purpose | Rate Limit |
|---------|---------|---------|------------|
| Groq API | All 4 agents | LLM inference | Free tier limits; 15s delays mitigate |
| Nominatim | Agent 1 tool | Hospital geolocation | 1 req/sec (OSM policy) |
| Pinecone | Agent 1 tool + post-pipeline | Vector storage/retrieval | Free tier: 1 index |
| HuggingFace Inference | Pinecone client | Text embeddings (`all-MiniLM-L6-v2`) | Free tier limits |
| IFCT 2017 JSON | Agent 3 tool | Indian food nutrition data | Local file, no limit |

---

## 6. Data Model (Pinecone)

### Vector Record
| Field | Value |
|-------|-------|
| ID | session_id |
| Vector | 384-dim embedding of session summary text |
| Metadata | `user_id`, `session_id`, `session_date`, `primary_condition`, `severity_flag`, `summary` |
