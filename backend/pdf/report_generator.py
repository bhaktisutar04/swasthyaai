import os
import json
from datetime import datetime
from dotenv import load_dotenv

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

load_dotenv()

# Define colors
PRIMARY = HexColor("#2D7DD2")
SUCCESS = HexColor("#3BB273")
WARNING = HexColor("#F4A261")
DANGER = HexColor("#E63946")
LIGHT_GRAY = HexColor("#F8FAFC")

def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.drawString(inch, 0.75 * inch, "SwasthyaAI | AI Health Companion for India")
    canvas.drawRightString(A4[0] - inch, 0.75 * inch, "Consult a qualified healthcare professional for medical advice.")
    canvas.restoreState()

def generate_report(patient_profile: dict) -> str:
    import os
    PDF_STORAGE_PATH = os.getenv("PDF_STORAGE_PATH", "./pdfs/")
    os.makedirs(PDF_STORAGE_PATH, exist_ok=True)
    print(f"Generating PDF to: {PDF_STORAGE_PATH}")
    try:
        # 1. Create PDF filename
        name = patient_profile.get("name", "Patient").replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"SwasthyaAI_Report_{name}_{date_str}.pdf"
        
        pdf_storage_path = os.getenv("PDF_STORAGE_PATH", "./pdfs/")
        os.makedirs(pdf_storage_path, exist_ok=True)
        pdf_path = os.path.join(pdf_storage_path, filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, textColor=PRIMARY, fontSize=24, spaceAfter=6)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, textColor=DANGER, fontSize=12, spaceAfter=12)
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], textColor=PRIMARY, spaceBefore=12, spaceAfter=6)
        normal_style = ParagraphStyle('BodyText', parent=styles['Normal'], spaceAfter=6)
        bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], leftIndent=20, spaceAfter=2)
        
        story = []
        
        # HEADER
        story.append(Paragraph("SwasthyaAI Health Report", title_style))
        story.append(Paragraph("AI-Generated Report — Not a Medical Diagnosis", subtitle_style))
        story.append(Paragraph(f"<b>Session ID:</b> {patient_profile.get('session_id', 'N/A')} | <b>Date:</b> {date_str}", ParagraphStyle('Center', alignment=TA_CENTER)))
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=10))
        
        # SECTION 1: PATIENT INFORMATION
        story.append(Paragraph("Patient Information", h2_style))
        patient_data = [
            ["Name:", patient_profile.get("name", "N/A"), "Age:", str(patient_profile.get("age", "N/A"))],
            ["Gender:", patient_profile.get("gender", "N/A"), "City:", patient_profile.get("city", "N/A")],
            ["Diet Preference:", patient_profile.get("diet_pref", "N/A"), "Session Date:", patient_profile.get("session_date", "N/A")]
        ]
        t1 = Table(patient_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_GRAY),
            ('TEXTCOLOR', (0,0), (-1,-1), black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t1)
        story.append(Spacer(1, 0.2*inch))
        
        # SECTION 2: SYMPTOMS & ASSESSMENT
        story.append(Paragraph("Symptoms & Assessment", h2_style))
        s_list = ", ".join(patient_profile.get("symptoms", []) or ["None reported"])
        story.append(Paragraph(f"<b>Reported Symptoms:</b> {s_list}", normal_style))
        
        disclaimer_table = Table([["⚠️ This is AI-powered analysis, NOT a medical diagnosis.\nAlways consult a qualified healthcare professional."]])
        disclaimer_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, DANGER),
            ('TEXTCOLOR', (0,0), (-1,-1), DANGER),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,-1), white)
        ]))
        story.append(Spacer(1, 0.1*inch))
        story.append(disclaimer_table)
        story.append(Spacer(1, 0.2*inch))
        
        # SECTION 3: DIAGNOSIS
        story.append(Paragraph("Diagnosis", h2_style))
        conditions = patient_profile.get("conditions", [])
        if conditions:
            data = [["Condition", "Confidence", "Likelihood"]]
            for c in conditions:
                l = c.get("likelihood", "possible")
                data.append([c.get("name", ""), f"{c.get('confidence', 0)}%", l])
            
            t2 = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            color_style = [
                ('BACKGROUND', (0,0), (-1,0), PRIMARY),
                ('TEXTCOLOR', (0,0), (-1,0), white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, black),
            ]
            for i, row in enumerate(data[1:], start=1):
                lk = row[2].lower()
                if lk == "most_likely": c_color = SUCCESS
                elif lk == "possible": c_color = WARNING
                else: c_color = HexColor("#808080")
                color_style.append(('TEXTCOLOR', (2,i), (2,i), c_color))
                
            t2.setStyle(TableStyle(color_style))
            story.append(t2)
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No conditions mapped.", normal_style))

        medicines = patient_profile.get("medicines", [])
        if medicines:
            story.append(Paragraph("<b>Medicines:</b>", normal_style))
            m_data = [["Medicine Name", "Used For"]]
            for m in medicines:
                m_data.append([m.get("name", ""), m.get("use", "")])
            t3 = Table(m_data, colWidths=[2.5*inch, 3.5*inch])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, black),
            ]))
            story.append(t3)
            story.append(Spacer(1, 0.1*inch))
            
        story.append(Paragraph(f"<b>Specialist Recommendation:</b> {patient_profile.get('specialist_type', 'N/A')}", normal_style))
        see_doc = "True" if patient_profile.get('see_doctor') else "False"
        if see_doc == "True":
            story.append(Paragraph(f"<b>See Doctor Strongly Advised:</b> <b>True</b>", normal_style))
        else:
            story.append(Paragraph(f"<b>See Doctor Strongly Advised:</b> False", normal_style))
        
        home_care = patient_profile.get("home_care", [])
        if home_care:
            story.append(Paragraph("<b>Home Care Tips:</b>", normal_style))
            for hc in home_care:
                story.append(Paragraph(f"• {hc}", bullet_style))
                
        red_flags = patient_profile.get("red_flags", [])
        if red_flags:
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph("<b>Red Flags:</b>", normal_style))
            for rf in red_flags:
                story.append(Paragraph(f"• {rf}", bullet_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # SECTION 4: NUTRITION PLAN
        story.append(Paragraph("Nutrition & Meal Plan", h2_style))
        meal_plan = patient_profile.get("meal_plan", [])
        deficiencies = patient_profile.get("deficiencies", [])
        nutritional_focus = patient_profile.get("nutritional_focus", "")
        nutrition_tips = patient_profile.get("nutrition_tips", [])
        if meal_plan or deficiencies or nutritional_focus:
            if nutritional_focus:
                story.append(Paragraph(
                    f"<b>Nutritional Focus:</b> {nutritional_focus}",
                    normal_style))
            if deficiencies:
                d_data = [["Nutrient", "Current", "Required"]]
                for d in deficiencies:
                    d_data.append([
                        d.get("nutrient", ""),
                        str(d.get("current_mg", "")),
                        str(d.get("required_mg", ""))
                    ])
                t4 = Table(d_data)
                t4.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
                    ('GRID', (0,0), (-1,-1), 0.5, black),
                ]))
                story.append(t4)
                story.append(Spacer(1, 0.1*inch))
            for day_info in meal_plan[:2]:
                story.append(Paragraph(
                    f"<b>Day {day_info.get('day','')} - {day_info.get('day_name','')}</b>",
                    normal_style))
                brk = ", ".join(day_info.get("breakfast",{}).get("items",[]))
                lun = ", ".join(day_info.get("lunch",{}).get("items",[]))
                din = ", ".join(day_info.get("dinner",{}).get("items",[]))
                story.append(Paragraph(f"• Breakfast: {brk}", bullet_style))
                story.append(Paragraph(f"• Lunch: {lun}", bullet_style))
                story.append(Paragraph(f"• Dinner: {din}", bullet_style))
            if nutrition_tips:
                story.append(Spacer(1, 0.05*inch))
                story.append(Paragraph("<b>Nutrition Tips:</b>", normal_style))
                for tip in nutrition_tips:
                    story.append(Paragraph(f"• {tip}", bullet_style))
        else:
            story.append(Paragraph(
                "Complete a full consultation to generate nutrition plan.",
                normal_style))
            
        story.append(Spacer(1, 0.2*inch))
        
        # SECTION 5: MEDICAL EXPENSES
        story.append(Paragraph("Medical Expenses & Finance", h2_style))
        monthly_total = patient_profile.get("monthly_total", 0)
        expense_breakdown = patient_profile.get("expense_breakdown", {})
        savings_estimate = patient_profile.get("savings_estimate", 0)
        medicines = patient_profile.get("medicines", [])
        has_expenses = expense_breakdown and any(v > 0 for v in expense_breakdown.values())
        if has_expenses:
            story.append(Paragraph(
                f"<b>Logged Expenses This Month: Rs.{monthly_total}</b>",
                ParagraphStyle('H3', parent=normal_style, fontSize=14)))
            b_data = [["Category", "Amount (Rs.)"]]
            for cat, amt in expense_breakdown.items():
                if amt > 0:
                    b_data.append([cat.capitalize(), f"Rs.{amt}"])
            t5 = Table(b_data)
            t5.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
                ('GRID', (0,0), (-1,-1), 0.5, black),
            ]))
            story.append(t5)
            story.append(Spacer(1, 0.1*inch))
        if medicines:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                "<b>Estimated Medicine Costs (Reference):</b>",
                normal_style))
            med_data = [["Medicine", "Estimated Cost (Rs.)"]]
            est_costs = {
                "Paracetamol": 30, "Ibuprofen": 25, "Azithromycin": 120,
                "Amoxicillin": 80, "Metoclopramide": 35, "Ondansetron": 90,
                "Loperamide": 40, "Domperidone": 45, "Loratadine": 50,
                "Cetirizine": 25, "Ranitidine": 30, "Pantoprazole": 55
            }
            total_est = 0
            for m in medicines:
                mname = m.get("name", "")
                cost = est_costs.get(mname, 50)
                total_est += cost
                med_data.append([mname, f"Rs.{cost}"])
            med_data.append(["TOTAL ESTIMATED", f"Rs.{total_est}"])
            t6 = Table(med_data, colWidths=[3*inch, 2*inch])
            t6.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), LIGHT_GRAY),
                ('BACKGROUND', (0,-1), (-1,-1), PRIMARY),
                ('TEXTCOLOR', (0,-1), (-1,-1), white),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, black),
            ]))
            story.append(t6)
            story.append(Paragraph(
                "<i>⚠️ Estimated costs only. Actual prices vary by pharmacy.</i>",
                ParagraphStyle('small', parent=normal_style, fontSize=9)))
        if savings_estimate > 0:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"<b>Estimated Monthly Savings with Nutrition Plan: Rs.{savings_estimate}</b>",
                normal_style))
            story.append(Paragraph(
                "<i>Estimated projection. Actual savings may vary.</i>",
                normal_style))

        doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
        return pdf_path
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None