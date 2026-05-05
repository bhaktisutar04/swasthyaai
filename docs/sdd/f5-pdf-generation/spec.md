# F5 — PDF Report Generation & Cloud Storage: Specification

> **Feature ID**: F5  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Depends On**: F3 (Pipeline triggers PDF generation)

---

## 1. Overview

Generates a professional A4 PDF health report using ReportLab, uploads it to Cloudinary cloud storage, and provides a forced-download mechanism from the frontend. The PDF contains all analysis results: patient info, symptoms, diagnosis, medicines, 7-day meal plan, and expense summary.

---

## 2. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-5.1 | As a patient, I can download a professional PDF report of my consultation. | P0 |
| US-5.2 | As a patient, clicking "Download PDF" triggers a direct file download, not a browser preview. | P1 |
| US-5.3 | As a patient, I can download PDFs from both the report page and the history page. | P1 |
| US-5.4 | As a patient, my PDF reports are stored persistently in the cloud, not just locally on the server. | P1 |

---

## 3. Functional Requirements

### PDF Generation
- **FR-5.1**: Generate A4-sized PDF using ReportLab library.
- **FR-5.2**: PDF filename format: `SwasthyaAI_Report_{PatientName}_{YYYY-MM-DD}.pdf`.
- **FR-5.3**: PDF includes: header with patient info, symptoms section, diagnosis table, medicines list, 7-day meal plan (all days), expense summary.
- **FR-5.4**: Footer on every page: "SwasthyaAI | AI Health Companion for India" + medical advice disclaimer.
- **FR-5.5**: Color-coded severity flags (green/yellow/red) in the PDF.
- **FR-5.6**: Medical disclaimer included in PDF body.

### Cloud Upload
- **FR-5.7**: Upload PDF to Cloudinary with `resource_type="image"`.
- **FR-5.8**: Cloudinary folder: `swasthyaai_reports/`.
- **FR-5.9**: Return Cloudinary secure URL as `pdf_path`.
- **FR-5.10**: Delete local file after successful upload.
- **FR-5.11**: Fall back to local file path if Cloudinary upload fails.

### Download Mechanism
- **FR-5.12**: `GET /consultation/report/{session_id}/pdf` returns `{"success": true, "url": "https://..."}` for Cloudinary URLs.
- **FR-5.13**: For local files, return `FileResponse` with `application/pdf` media type.
- **FR-5.14**: Frontend appends `fl_attachment` flag to Cloudinary URL for forced download.
- **FR-5.15**: Frontend uses programmatic `<a>` tag click (not `window.open`) to trigger download.
- **FR-5.16**: Download available from both `report.js` and `history.js`.

---

## 4. API Contract

### GET `/consultation/report/{session_id}/pdf`
```json
// Response 200 — Cloudinary URL
{ "success": true, "url": "https://res.cloudinary.com/djsw345av/image/upload/v.../swasthyaai_reports/report.pdf" }

// Response 200 — Local file
// Returns FileResponse (binary PDF)

// Response 404
{ "detail": "PDF not yet generated. Please wait 1-2 minutes after consultation." }
```

---

## 5. External Services

| Service | Purpose | Config |
|---------|---------|--------|
| Cloudinary | PDF cloud storage | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` |
| ReportLab | PDF generation library | Python package |

---

## 6. PDF Layout Specification

| Section | Content |
|---------|---------|
| **Header** | Logo text "SwasthyaAI Health Report", patient name, age, gender, city, date |
| **Symptoms** | Bullet list of symptoms, duration, severity scale |
| **Diagnosis** | Table with condition name, confidence %, likelihood; specialist recommendation |
| **Medicines** | Table with medicine name and use description |
| **Nutrition** | 7-day meal plan: day headings → 5 meal slots with items |
| **Expenses** | Monthly total, category breakdown table, savings estimate |
| **Footer** | Page footer with branding + disclaimer |
