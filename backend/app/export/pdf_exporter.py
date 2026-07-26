"""
PDF Exporter - generates a downloadable PDF timetable.
"""
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.schemas.faculty import FacultyTimetableResponse


class PDFExporter:
    """Generates a styled PDF matching the dark template."""

    @staticmethod
    def _build_elements(timetable: FacultyTimetableResponse) -> list:
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Normal'], fontName='Times-Bold', 
            fontSize=14, textColor=colors.black, alignment=TA_CENTER, spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle', parent=styles['Normal'], fontName='Times-Bold', 
            fontSize=12, textColor=colors.black, alignment=TA_CENTER, spaceAfter=20
        )
        info_style = ParagraphStyle(
            'InfoStyle', parent=styles['Normal'], fontName='Times-Bold', 
            fontSize=11, textColor=colors.black, alignment=TA_LEFT
        )

        # Header
        elements.append(Paragraph("P.S.N.A. COLLEGE OF ENGINEERING & TECHNOLOGY, DINDIGUL - 624 622", title_style))
        elements.append(Paragraph("FACULTY TIME TABLE", subtitle_style))
        
        # Aggregate Subjects
        subject_set = set()
        for day_row in timetable.schedule:
            for cell in day_row:
                if cell.type == "class" and cell.subject_code:
                    name = cell.subject or ""
                    subject_set.add(f"{cell.subject_code} - {name}" if name else cell.subject_code)
        subject_str = ", ".join(sorted(subject_set)) if subject_set else "N/A"

        # Info Section
        info_data = [
            [Paragraph("<b>Name</b>", info_style), Paragraph(f"<b>: {timetable.faculty_name}</b>", info_style), 
             Paragraph("<b>Department</b>", info_style), Paragraph("<b>: </b>", info_style)],
            [Paragraph("<b>Subject</b>", info_style), Paragraph(f"<b>: {subject_str}</b>", info_style), 
             Paragraph("<b>Academic Year</b>", info_style), Paragraph("<b>: </b>", info_style)],
            ["", "", Paragraph("<b>Semester</b>", info_style), Paragraph("<b>: </b>", info_style)]
        ]
        
        info_table = Table(info_data, colWidths=[60, 350, 100, 200])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Build Grid
        grid_data = []
        
        # Header Row
        header_row = ["DAY/\nHOUR"]
        break_cols = []
        
        for idx, header in enumerate(timetable.headers):
            # Check if this column is a break by checking the header text
            is_break_header = "break" in str(header).lower() or "lunch" in str(header).lower()
            if is_break_header:
                break_cols.append(idx + 1) # +1 because of DAY column
                header_row.append("") # Break headers are spanned vertically from row 1
            else:
                parts = str(header).split()
                if len(parts) >= 4:
                    # Format as '08.45 AM\n09.40 AM'
                    h_text = f"{parts[0]} {parts[1]}\n{parts[2]} {parts[3]}"
                else:
                    h_text = str(header)
                header_row.append(h_text)
        grid_data.append(header_row)

        # Body Rows
        for day_idx, day in enumerate(timetable.days):
            row = [str(day)]
            for col_idx, cell in enumerate(timetable.schedule[day_idx]):
                if cell.type == "class":
                    text = f"{cell.subject_code}"
                    if cell.class_name and cell.class_name.strip():
                        text += f"\n({cell.class_name})"
                    row.append(text)
                elif cell.type == "break":
                    # We will span these, so only the first row needs the vertical text
                    if day_idx == 0:
                        lbl = str(cell.label or "BREAK").upper()
                        vert = "\n".join(list(lbl.replace(" ", "\n \n")))
                        row.append(vert)
                    else:
                        row.append("")
                else:
                    row.append("")
            grid_data.append(row)
            
        # Column Widths
        num_cols = len(timetable.headers) + 1
        base_w = (780 - 60) / (num_cols - len(break_cols))
        col_widths = [60]
        for i in range(1, num_cols):
            if i in break_cols:
                col_widths.append(30)
            else:
                col_widths.append(base_w)
                
        row_heights = [50] + [35] * len(timetable.days)
        
        grid_style_cmds = [
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]
        # Spans for breaks (span from row 0 down to the end so it looks like one massive column)
        for bc in break_cols:
            grid_style_cmds.append(('SPAN', (bc, 0), (bc, -1)))
        
        table = Table(grid_data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle(grid_style_cmds))
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 40))
        footer_data = [
            [Paragraph("<b>DEPT TT I/C</b>", title_style), Paragraph("<b>HOD</b>", title_style), Paragraph("<b>PRINCIPAL</b>", title_style)]
        ]
        footer_table = Table(footer_data, colWidths=[260, 260, 260])
        elements.append(footer_table)
        
        return elements

    @staticmethod
    def export(timetable: FacultyTimetableResponse) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )
        elements = PDFExporter._build_elements(timetable)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def export_all(timetables: list[FacultyTimetableResponse]) -> io.BytesIO:
        from reportlab.platypus import PageBreak
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )
        elements = []
        for i, timetable in enumerate(timetables):
            if i > 0:
                elements.append(PageBreak())
            elements.extend(PDFExporter._build_elements(timetable))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
