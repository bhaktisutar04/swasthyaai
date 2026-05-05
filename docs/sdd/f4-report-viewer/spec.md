# F4 — Health Report Viewer: Specification

> **Feature ID**: F4  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F2 (Consultation), F3 (Pipeline generates report data)

---

## 1. Overview

The Health Report Viewer is the primary output display of SwasthyaAI. It renders a comprehensive, structured health report from a completed consultation — showing symptoms, AI diagnosis with confidence levels, a 7-day Indian meal plan, and medical expense analysis. All sections are collapsible and open by default.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-4.1 | As a patient, I can view my full health report after consultation completion. | P0 |
| US-4.2 | As a patient, I can see my symptoms listed as badges. | P1 |
| US-4.3 | As a patient, I can see ranked conditions with confidence bars and likelihood badges. | P0 |
| US-4.4 | As a patient, I can see recommended medicines (for reference only) with usage descriptions. | P1 |
| US-4.5 | As a patient, I can see home care suggestions and red flags. | P1 |
| US-4.6 | As a patient, I can navigate through a 7-day meal plan day by day. | P0 |
| US-4.7 | As a patient, I can see my medical expense summary and savings estimate. | P1 |
| US-4.8 | As a patient, I see a clear medical disclaimer that this is AI analysis, not a diagnosis. | P0 |
| US-4.9 | As a patient, I can download a PDF version of my report. | P1 |
| US-4.10 | As a patient, I can start a new consultation from the report page. | P2 |

---

## 3. Functional Requirements

### Report Data
- **FR-4.1**: Fetch report data from `GET /consultation/report/{session_id}`.
- **FR-4.2**: Data source priority: in-memory session → database fallback.
- **FR-4.3**: Report includes: session_id, session_date, status, patient info, symptoms, diagnosis, nutrition, finance, pdf_available, pdf_path.

### Report Sections
- **FR-4.4**: **Header**: Primary condition name, patient info (name, date, city), severity badge (color-coded), see-doctor badge.
- **FR-4.5**: **Symptoms Section**: Symptom badges, emergency flag alert if applicable.
- **FR-4.6**: **Diagnosis Section**: Conditions with confidence bars (0-100%), likelihood badges (most_likely/possible/less_likely), reasoning text, specialist recommendation, medicines list (name + use), home care tips, red flags.
- **FR-4.7**: **Nutrition Section**: Nutritional focus, deficiency list, 7-day meal plan with day navigation (prev/next), 5 meal slots per day (breakfast, mid_morning, lunch, evening_snack, dinner), nutrient values per meal.
- **FR-4.8**: **Finance Section**: Monthly total, category breakdown, savings estimate with disclaimer.
- **FR-4.9**: All sections collapsible (toggle on header click), open by default.

### Actions
- **FR-4.10**: "Download PDF Report" button triggers `downloadPDF()`.
- **FR-4.11**: "New Consultation" button navigates to `consultation.html`.

### UI States
- **FR-4.12**: Loading state: skeleton placeholders while data loads.
- **FR-4.13**: Empty state: prompt to start consultation if no session_id.
- **FR-4.14**: Error state: retry message on API failure.

---

## 4. API Contract

### GET `/consultation/report/{session_id}`
```json
{
  "success": true,
  "data": {
    "session_id": "CNS-2026-05-05-A1B2C3",
    "session_date": "2026-05-05T...",
    "status": "completed",
    "patient": { "name": "...", "age": 25, "gender": "Female", "city": "Pune", "diet_pref": "veg" },
    "symptoms": { "list": ["headache", "fever"], "duration": "...", "severity": 5, "emergency_flag": false },
    "diagnosis": {
      "conditions": [{ "name": "Viral Fever", "confidence": 80, "reasoning": "...", "likelihood": "most_likely" }],
      "specialist_type": "General Physician",
      "medicines": [{ "name": "Paracetamol", "use": "Fever and pain relief" }],
      "severity_flag": "mild", "see_doctor": false,
      "home_care": ["Rest 7-8 hours"], "red_flags": ["Fever > 101F"],
      "disclaimer": "⚠️ This is AI-powered analysis, NOT a medical diagnosis."
    },
    "nutrition": {
      "deficiencies": [{ "nutrient": "Iron", "current_mg": 8, "required_mg": 18 }],
      "meal_plan": [{ "day": 1, "day_name": "Monday", "breakfast": { "items": [...], "nutrients": {...} }, ... }],
      "nutritional_focus": "Increasing Iron and Vitamin C intake"
    },
    "finance": { "monthly_total": 5000, "expense_breakdown": {...}, "savings_estimate": 1200 },
    "pdf_available": true,
    "pdf_path": "https://res.cloudinary.com/..."
  }
}
```

---

## 5. UI Specification

### Layout
- Desktop: sidebar navigation (260px) + main content (max 960px centered).
- Mobile: top bar with back arrow + bottom navigation.
- Four collapsible card sections stacked vertically.
- Report header with gradient background showing primary condition and patient info.
- Action buttons row: Download PDF + New Consultation.
- Medical disclaimer banner (danger-styled) between actions and sections.
