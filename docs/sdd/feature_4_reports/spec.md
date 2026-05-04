# Specification: Report Generation & Export

## 1. Feature Overview
This feature transforms the raw JSON output from the AI Consultation Pipeline into human-readable, professional formats. It provides an interactive web dashboard for immediate viewing and a downloadable PDF report for sharing with human healthcare providers or keeping personal records.

## 2. Behavioral Specification

### 2.1 Interactive Web Report (Dashboard)
- **Behavior**: The web UI must dynamically render the consultation results once the background pipeline completes.
- **Rules**:
  - **Symptoms**: Rendered as distinct cards showing duration and severity badges (High/Medium/Low). Must gracefully fallback to a simple list if legacy data (pre-structured string arrays) is encountered.
  - **Diagnosis**: Displayed as a likelihood-ranked table. Include clear visual disclaimers that this is AI-generated and not a definitive medical diagnosis.
  - **Nutrition**: Render the "Nutrition Focus" areas prominently, followed by the day-by-day Indian meal plan.
  - **Finance**: Display itemized medicine costs distinct from manually logged expenses.

### 2.2 PDF Generation
- **Behavior**: The backend generates a static, formatted PDF document containing the exact details shown on the web dashboard.
- **Rules**:
  - The PDF must be formatted to standard A4 size.
  - It must utilize professional, healthcare-aligned typography and color schemes (e.g., distinct colors for emergency flags, neutral backgrounds for tables).
  - Every page must contain a footer disclaimer: "SwasthyaAI | AI Health Companion for India. Consult a qualified healthcare professional for medical advice."
  - The PDF must include itemized tables for Diagnosis, Nutrition Needs, and Estimated Medicine Costs.

### 2.3 Report Storage & Retrieval
- **Behavior**: PDFs are generated on-demand or upon pipeline completion, stored locally, and linked to the `Consultation` database record.
- **Rules**:
  - The file path must be saved in the `pdf_path` column of the `consultations` table.
  - The API must serve the PDF file securely to the authenticated owner.

## 3. Data Models & Database Schema

*(Relies primarily on the existing `consultations` table)*

| Column | Type | Description |
| :--- | :--- | :--- |
| `pdf_path` | String | Local file path (e.g., `./pdfs/SwasthyaAI_Report_...pdf`) |
| `pdf_generated_at`| DateTime | Timestamp of generation |

## 4. API Contracts

### `GET /consultation/{session_id}`
*(Used by Web Dashboard to render UI)*
- **Response**: Returns the fully populated JSON of the consultation.

### `GET /consultation/{session_id}/pdf`
- **Behavior**: If a PDF already exists for the session, streams it to the client. If not, generates it synchronously and then streams it.
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="SwasthyaAI_Report.pdf"`

## 5. UI Flows & Screen Descriptions
1. **Report View**: A vertically scrolling page. 
   - Section 1: Patient demographics and global severity score.
   - Section 2: Symptom cards.
   - Section 3: Diagnosis tables with likelihood color-coding (Green for Most Likely, Yellow for Possible).
   - Section 4: Nutrition Focus and Meal Plan accordion.
   - Section 5: Finance table.
   - Floating action button: "Download PDF".

## 6. Edge Cases & Error Handling
- **Missing Data (Backward Compatibility)**: If an older consultation lacks the new structured JSON for symptoms (e.g., it is a simple string), the UI and PDF generator must detect the type and render a fallback text block rather than crashing.
- **PDF Generation Failure**: If `reportlab` fails during generation, the API must catch the exception, log it, and return a `500 Internal Server Error` stating "Unable to generate PDF at this time", preventing the frontend from breaking.
