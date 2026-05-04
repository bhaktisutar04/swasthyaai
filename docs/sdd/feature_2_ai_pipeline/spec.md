# Specification: Multi-Agent AI Consultation Pipeline

## 1. Feature Overview
This feature forms the core diagnostic and advisory engine of SwasthyaAI. It processes user-reported symptoms through a sequential pipeline of specialized AI agents (CrewAI) to generate structured symptom extraction, medical diagnosis, personalized Indian nutritional advice, and financial cost estimations.

## 2. Behavioral Specification

### 2.1 Agent 1: Intake & Symptom Extraction
- **Behavior**: Parses natural language input to identify specific symptoms.
- **Rules**:
  - Extracts symptoms as structured objects: `name`, `duration`, `severity` (1-10 scale), and `notes`.
  - Computes a global `severity` index as the maximum severity among all reported symptoms.
  - Flags `emergency_flag = true` if severe keywords (e.g., "chest pain", "breathing difficulty") are detected.

### 2.2 Agent 2: Diagnosis & Specialist Recommendation
- **Behavior**: Uses the structured symptoms from Agent 1 to formulate potential medical conditions.
- **Rules**:
  - Outputs 1-3 possible conditions, ranked by `likelihood` ("most_likely", "possible", "less_likely") and a percentage `confidence`.
  - Recommends an appropriate specialist (e.g., "Cardiologist", "General Physician").
  - Suggests generic medicines relevant to the condition, assigning an `estimated_cost` in Indian Rupees based on a predefined lookup map.
  - Highlights `red_flags` indicating when to seek immediate care.

### 2.3 Agent 3: Personalized Nutrition
- **Behavior**: Formulates dietary advice based on the diagnosed conditions and user profile preferences.
- **Rules**:
  - Generates symptom-specific `nutrition_focus` areas (e.g., "Hydration" for fever, "Iron" for fatigue).
  - Creates a 7-day Indian meal plan strictly adhering to the user's `diet_pref` (veg, non-veg, vegan).
  - Uses only locally available Indian ingredients.

### 2.4 Agent 4: Financial Estimation
- **Behavior**: Analyzes the cost implications of the consultation.
- **Rules**:
  - Sums the `estimated_cost` of all recommended medicines.
  - Estimates potential monthly health savings if the user follows the prescribed nutrition plan (e.g., reduced reliance on supplements).

## 3. Data Models & Database Schema

### `consultations` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key | Unique DB identifier |
| `consultation_id` | String | Unique, Indexed | UUID for the session |
| `user_id` | Integer | Foreign Key | The patient |
| `status` | String | Default: 'in_progress' | Pipeline status |
| `symptoms` | Text | Nullable | JSON string of structured symptoms |
| `severity` | String | Nullable | Max severity score |
| `emergency_flag` | Boolean | Default: False | True if critical |
| `conditions` | Text | Nullable | JSON array of conditions |
| `medicines` | Text | Nullable | JSON array of medicines & costs |
| `specialist_type`| String | Nullable | Recommended doctor |
| `meal_plan` | Text | Nullable | JSON array for 7 days |
| `expense_breakdown`| Text | Nullable | JSON of estimated costs |

## 4. API Contracts

### `POST /consultation/start`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "query": "I have had a severe headache for 2 days and feel nauseous."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "consultation_id": "uuid-1234",
    "message": "Consultation pipeline started in background."
  }
  ```

### `GET /consultation/status/{consultation_id}`
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "status": "completed",
    "data": {
      "symptoms": [{"name": "Headache", "severity": 8, "duration": "2 days"}],
      "emergency_flag": false,
      "conditions": [...],
      "nutrition_focus": [...],
      "medicines": [{"name": "Paracetamol", "estimated_cost": 30}]
    }
  }
  ```

## 5. Edge Cases & Error Handling
- **Ambiguous Input**: If the user query is unrelated to health, Agent 1 must return an error flag, halting the pipeline and asking the user to provide valid medical symptoms.
- **LLM Rate Limits/Timeouts**: The Crew orchestration must include `try-except` blocks. If Groq API fails, the pipeline status changes to `failed` and prompts the user to retry.
- **Empty Output Parsing**: If an Agent fails to return valid JSON, the pipeline must implement a fallback text parser or retry the specific agent task.
