# Technical Plan: Report Generation & Export

## 1. Architecture Overview

```text
[ Database (Consultations) ]
        |
        | JSON Payload
        v
[ FastAPI Route ] ---> [ JSON API ] ---> [ Web Dashboard (JS) ]
        |                                        |
        | triggers                               | renders
        v                                        v
[ PDF Generator (ReportLab) ]               [ HTML DOM ]
        |
        +---> [ /pdfs/ Storage ] ---> [ Download to User ]
```

## 2. Tech Stack & Rationale
- **Vanilla JavaScript (Frontend)**: For the web dashboard, native DOM manipulation with template literals is sufficient for rendering the structured JSON without the overhead of heavy frameworks like React, keeping the client lightweight.
- **ReportLab (Backend)**: An industry-standard Python library for generating complex PDFs. Chosen for its programmatic, flowable-based architecture (`Platypus`), which easily handles dynamic text wrapping and table pagination—crucial when the length of AI-generated content (like meal plans) varies wildly.

## 3. Component Breakdown
1. **Frontend Rendering Engine (`frontend/js/report.js`)**:
   - Contains functions like `renderSymptoms`, `renderDiagnosis`, and `renderFinance`.
   - Implements type-checking (e.g., `typeof s === 'string'`) to support rendering older database records alongside the new structured JSON.
2. **PDF Generation Service (`backend/pdf/report_generator.py`)**:
   - A utility module containing the `generate_report(patient_profile: dict) -> str` function.
   - Defines custom `ParagraphStyle` and `TableStyle` configurations to match the SwasthyaAI branding (Colors: Primary Blue, Danger Red, Success Green).
   - Generates tables for Symptoms, Diagnosis, and Itemized Medicines.
3. **API Endpoint (`backend/routes/consultation.py`)**:
   - The `/pdf` route verifies ownership of the consultation, calls `report_generator.py` if the PDF doesn't exist, and serves the file using FastAPI's `FileResponse`.

## 4. Dependencies & Risks
### Dependencies
- `reportlab`: For PDF generation.
- `dotenv`: For reading the `PDF_STORAGE_PATH` configuration.

### Risks & Mitigations
- **Risk**: Variable length of AI output causing text to overflow off the PDF page or break tables awkwardly.
- **Mitigation**: Utilize ReportLab's `Platypus` framework (Flowables like `Paragraph`, `Table`, `Spacer`), which automatically handles page breaks and text wrapping.
- **Risk**: Local storage bloat from accumulating PDF files.
- **Mitigation**: Ensure PDFs are generated with distinct filenames (e.g., `<name>_<date>.pdf`). In future iterations, implement a cleanup cron job or move storage to an S3 bucket.
