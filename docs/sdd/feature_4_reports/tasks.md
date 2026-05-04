# Tasks: Report Generation & Export

## Module 1: Web Dashboard UI Integration
- [ ] **Task 1.1**: Update `frontend/js/report.js` `renderSymptoms` function. Map the `symptoms` array to generate styled HTML cards. Implement type-checking fallback to render simple strings if legacy data is passed.
- [ ] **Task 1.2**: Update `renderDiagnosis` function to parse the `conditions` array and render a table, applying visual badges for the `likelihood` field.
- [ ] **Task 1.3**: Update `renderNutrition` and `renderDeficiencies` functions to loop through the `nutrition_focus` and `meal_plan` arrays, dynamically building HTML accordions for each day.
- [ ] **Task 1.4**: Update `renderFinance` to display a sub-section for `Estimated Medicine Costs`, itemizing the AI-generated medicines array.

## Module 2: PDF Generator Setup
- [ ] **Task 2.1**: Create `backend/pdf/report_generator.py`. Import `reportlab.platypus` and initialize standard `ParagraphStyle` and `TableStyle` variables (e.g., matching the app's primary blue).
- [ ] **Task 2.2**: Implement the `add_footer` canvas function to append the medical disclaimer on every page of the PDF.

## Module 3: PDF Document Construction
- [ ] **Task 3.1**: Inside `generate_report()`, construct the Patient Demographics and Symptoms section. Parse the structured JSON into a `ReportLab` `Table`. Implement a fallback for string arrays.
- [ ] **Task 3.2**: Construct the Diagnosis and Recommendation section. Build tables for likelihood-ranked conditions and suggested medicines.
- [ ] **Task 3.3**: Construct the Nutrition Plan section. Iterate through the `nutrition_focus` objects and append them as bolded `Paragraph` items, followed by the meal plan lists.
- [ ] **Task 3.4**: Construct the Finance section. Display the itemized medicine costs table and the final estimated monthly savings text. Add a final visual disclaimer HR line.

## Module 4: API & File Serving
- [ ] **Task 4.1**: Create the `GET /consultation/{session_id}/pdf` endpoint in `backend/routes/consultation.py`.
- [ ] **Task 4.2**: Implement logic to verify the current user owns the consultation.
- [ ] **Task 4.3**: Check if the PDF file exists on the local filesystem. If not, invoke `generate_report()`, save the file, and update `Consultation.pdf_path` in the database.
- [ ] **Task 4.4**: Return the generated file using FastAPI's `FileResponse` with headers set for attachment download.
