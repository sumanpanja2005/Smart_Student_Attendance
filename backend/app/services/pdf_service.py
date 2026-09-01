import os
import logging
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

logger = logging.getLogger("uvicorn.error")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to compute and render 'Page X of Y' footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 36, 576, 36)

        footer_text = f"Smart Attendance System • Confidential Report • Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 22, footer_text)
        self.restoreState()


class PDFService:
    @classmethod
    def generate_pdf_report(
        cls,
        report_title: str,
        subtitle: str,
        metadata: Dict[str, str],
        summary_stats: Dict[str, Any],
        table_headers: List[str],
        table_rows: List[List[str]],
        output_filepath: Optional[str] = None,
    ) -> bytes:
        """
        Generates a professional PDF report using ReportLab.
        If output_filepath is provided, writes file to disk; returns raw PDF bytes.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            output_filepath if output_filepath else buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12,
        )

        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )

        meta_val_style = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
        )

        th_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.white,
        )

        td_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
        )

        story = []

        # 1. Document Header
        story.append(Paragraph(report_title, title_style))
        story.append(Paragraph(subtitle, subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4F46E5"), spaceAfter=12))

        # 2. Metadata Grid Table
        if metadata:
            meta_data = []
            keys = list(metadata.keys())
            for i in range(0, len(keys), 2):
                k1 = keys[i]
                v1 = str(metadata[k1])
                row = [
                    Paragraph(f"{k1}:", meta_label_style),
                    Paragraph(v1, meta_val_style),
                ]
                if i + 1 < len(keys):
                    k2 = keys[i + 1]
                    v2 = str(metadata[k2])
                    row.extend([Paragraph(f"{k2}:", meta_label_style), Paragraph(v2, meta_val_style)])
                else:
                    row.extend(["", ""])
                meta_data.append(row)

            meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
            meta_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(meta_table)
            story.append(Spacer(1, 12))

        # 3. Summary Statistics Table
        if summary_stats:
            stat_data = []
            stat_headers = [Paragraph(k, th_style) for k in summary_stats.keys()]
            stat_values = [Paragraph(str(v), td_style) for v in summary_stats.values()]
            stat_data.append(stat_headers)
            stat_data.append(stat_values)

            col_w = 540 / len(summary_stats) if len(summary_stats) > 0 else 540
            stat_table = Table(stat_data, colWidths=[col_w] * len(summary_stats))
            stat_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1F5F9")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(stat_table)
            story.append(Spacer(1, 14))

        # 4. Main Data Table
        if table_headers and table_rows is not None:
            t_data = []
            header_row = [Paragraph(h, th_style) for h in table_headers]
            t_data.append(header_row)

            for r in table_rows:
                t_data.append([Paragraph(str(c), td_style) for c in r])

            num_cols = len(table_headers)
            c_width = 540 / num_cols if num_cols > 0 else 540

            data_table = Table(t_data, colWidths=[c_width] * num_cols, repeatRows=1)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]

            # Alternating row colors
            for idx in range(1, len(t_data)):
                if idx % 2 == 0:
                    t_style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F8FAFC")))

            data_table.setStyle(TableStyle(t_style))
            story.append(data_table)

        doc.build(story, canvasmaker=NumberedCanvas)

        if output_filepath:
            with open(output_filepath, "rb") as f:
                return f.read()
        return buffer.getvalue()
