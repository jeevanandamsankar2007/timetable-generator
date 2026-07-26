import io
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.timetable_entry import TimetableEntry
from app.models.faculty_mapping import FacultyMapping
from app.models.class_model import Class
from app.models.subject import Subject
from app.models.faculty import Faculty

# ReportLab imports for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def _get_timetable_data(self, upload_id: int):
        """Fetch all entries for the given upload_id, structured for export."""
        entries = (
            self.db.query(TimetableEntry)
            .join(Class)
            .join(Subject)
            .filter(Class.upload_id == upload_id)
            .all()
        )
        if not entries:
            raise HTTPException(status_code=404, detail="No timetable data found for this upload.")

        data = []
        for entry in entries:
            faculties = [fm.faculty.faculty_name if hasattr(fm.faculty, 'faculty_name') else fm.faculty.name for fm in entry.faculty_mappings if fm.faculty]
            data.append({
                "Department": entry.class_ref.department if entry.class_ref and hasattr(entry.class_ref, 'department') else "",
                "Semester": entry.class_ref.semester if entry.class_ref and hasattr(entry.class_ref, 'semester') else "",
                "Class": entry.class_ref.class_name if entry.class_ref and hasattr(entry.class_ref, 'class_name') else "",
                "Day": entry.day or "",
                "Period": entry.period or "",
                "Subject Code": entry.subject.subject_code if entry.subject and hasattr(entry.subject, 'subject_code') else "",
                "Subject Name": entry.subject.subject_name if entry.subject and hasattr(entry.subject, 'subject_name') else "",
                "Faculty": ", ".join(faculties),
                "Room": entry.room or ""
            })
        return data

    def generate_excel(self, upload_id: int) -> bytes:
        data = self._get_timetable_data(upload_id)
        df = pd.DataFrame(data)

        # Reorder columns
        cols = ["Department", "Semester", "Class", "Day", "Period", "Subject Code", "Subject Name", "Faculty", "Room"]
        df = df[cols]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Timetable')
            
            # Autofit columns
            worksheet = writer.sheets['Timetable']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[worksheet.cell(1, idx).column_letter].width = max_length

        return output.getvalue()

    def generate_pdf(self, upload_id: int) -> bytes:
        """Generates a PDF using reportlab reflecting the timetable grid."""
        data = self._get_timetable_data(upload_id)
        
        # We need to pivot this into a Grid for the first Class found (assuming one class per upload for now)
        if not data:
            raise HTTPException(status_code=404, detail="No data")
        
        # Build pivot table
        class_name = data[0]["Class"]
        dept = data[0]["Department"]
        sem = data[0]["Semester"]
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        # Find all unique periods and sort them 
        periods = sorted(list(set(d["Period"] for d in data)))
        if not periods:
            periods = ["1", "2", "3", "4", "5", "6", "7"]
            
        grid = [["Day"] + periods]
        
        for day in days:
            row = [day]
            for period in periods:
                cell_entries = [d for d in data if str(d["Day"]).lower().startswith(day.lower()) and d["Period"] == period]
                if cell_entries:
                    # Just show Subject Code in the grid to save space
                    row.append(cell_entries[0]["Subject Code"])
                else:
                    row.append("")
            # Only add days that have actual classes, or just add all of them
            grid.append(row)

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4))
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleCenter', 
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            spaceAfter=14
        )
        
        elements.append(Paragraph(f"Class Timetable", title_style))
        elements.append(Paragraph(f"Dept: {dept} | Semester: {sem} | Class: {class_name}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Grid Table
        t = Table(grid)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (0,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        
        elements.append(t)
        
        elements.append(Spacer(1, 30))
        
        # Subject Master Table
        master_headers = ["Sub. Code", "Subject Name", "Faculty"]
        master_grid = [master_headers]
        
        # Unique subjects
        seen_codes = set()
        for d in data:
            code = d["Subject Code"]
            if code not in seen_codes:
                master_grid.append([code, d["Subject Name"], d["Faculty"]])
                seen_codes.add(code)
                
        mt = Table(master_grid)
        mt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        
        elements.append(Paragraph("Subject Master", styles['Heading2']))
        elements.append(mt)

        doc.build(elements)
        return output.getvalue()
