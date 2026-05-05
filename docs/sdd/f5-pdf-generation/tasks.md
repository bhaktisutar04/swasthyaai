# F5 — PDF Report Generation & Cloud Storage: Tasks

> **Feature ID**: F5  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend — PDF Generation
- [x] **T5.1**: Configure Cloudinary SDK with env variables (cloud_name, api_key, api_secret)
- [x] **T5.2**: Define color constants (PRIMARY, SUCCESS, WARNING, DANGER)
- [x] **T5.3**: Create PDF styles (title, heading, body, disclaimer)
- [x] **T5.4**: Implement `add_footer()` — page footer with branding and disclaimer
- [x] **T5.5**: Implement `generate_report(patient_profile)` — full PDF generation pipeline
- [x] **T5.6**: Build PDF header section (patient name, age, gender, city, date)
- [x] **T5.7**: Build symptoms section (bullet list with duration, severity)
- [x] **T5.8**: Build diagnosis table (condition name, confidence, likelihood)
- [x] **T5.9**: Build medicines table (name, use)
- [x] **T5.10**: Build 7-day meal plan section (day headers → 5 meal slots)
- [x] **T5.11**: Build expense summary section (monthly total, breakdown, savings)
- [x] **T5.12**: Upload PDF to Cloudinary with `resource_type="image"`, folder `swasthyaai_reports/`
- [x] **T5.13**: Return Cloudinary `secure_url` as pdf_path
- [x] **T5.14**: Delete local PDF file after successful upload
- [x] **T5.15**: Fallback to local file path if Cloudinary upload fails

### Backend — PDF Endpoint
- [x] **T5.16**: `GET /consultation/report/{session_id}/pdf` — check memory then DB for pdf_path
- [x] **T5.17**: Return JSON `{"url": "..."}` for Cloudinary URLs
- [x] **T5.18**: Return `FileResponse` for local file paths
- [x] **T5.19**: Return 404 if PDF not yet generated
- [x] **T5.20**: Authorization check — user can only download own PDFs

### Frontend — Download Logic
- [x] **T5.21**: `downloadPDF()` in `report.js` — handle Cloudinary URLs with `fl_attachment`
- [x] **T5.22**: `downloadPDF()` in `history.js` — same logic for history page
- [x] **T5.23**: Insert `fl_attachment` transformation into Cloudinary URL path
- [x] **T5.24**: Hidden `<a>` tag creation + programmatic click for forced download
- [x] **T5.25**: Fallback: fetch PDF endpoint → handle JSON `url` or binary blob response
- [x] **T5.26**: Error handling with user-friendly alert messages

---

## Verification

- [x] PDF generates with all sections populated
- [x] PDF uploads to Cloudinary successfully
- [x] `pdf_path` saved as Cloudinary URL in database
- [x] Download button triggers file download (not browser preview)
- [x] Download works from both report page and history page
- [x] 404 returned when PDF not yet generated
- [x] Local file cleaned up after upload
