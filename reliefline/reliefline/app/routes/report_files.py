"""
Renders a build_report() dict (see report_data.py) into a real PDF or Excel
file. One renderer per format, shared by every report type - the report data
already carries generic columns/rows, so no per-report-type layout code is
needed here.
"""
import io
import os
from xml.sax.saxutils import escape

from flask import current_app

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether, Image

NAVY = colors.HexColor("#0f2547")
MUTED = colors.HexColor("#8a94a6")
LIGHT_GRAY = colors.HexColor("#f4f6fa")
BORDER = colors.HexColor("#e1e5eb")


def _column_widths(columns, rows, total_width):
    """Width per column proportional to its longest content (header words or
    cell text), clamped so a short column like "#" stays narrow and one long
    column can't starve the rest - instead of every column getting the same
    share and long values spilling out of narrow cells."""
    weights = []
    for i, col in enumerate(columns):
        longest_word = max((len(w) for w in str(col).split()), default=1)
        longest_cell = max((len(str(r[i])) for r in rows), default=0)
        # +2 on header words: they're bold, so a word needs a little more
        # room than its character count or it splits mid-word.
        weights.append(min(max(longest_word + 2, min(longest_cell, 28), 4), 30))
    scale = total_width / sum(weights)
    return [w * scale for w in weights]


# Box a letterhead seal is scaled into - wider than tall, so a landscape
# logo (Urdaneta's) isn't shrunk down to a round seal's width.
SEAL_W, SEAL_H = 1.3 * inch, 0.95 * inch


def _static_path(rel):
    """Absolute path of a file under app/static, or None if it's missing."""
    if not rel:
        return None
    path = os.path.join(current_app.static_folder, *rel.split("/"))
    return path if os.path.exists(path) else None


def _seal(rel):
    """A letterhead seal image scaled to fit SEAL_W x SEAL_H (keeps its aspect)."""
    path = _static_path(rel)
    if not path:
        return ""
    iw, ih = ImageReader(path).getSize()
    scale = min(SEAL_W / iw, SEAL_H / ih)
    return Image(path, width=iw * scale, height=ih * scale)


def _letterhead_block(lh, width, line_style, lgu_style, office_style):
    """[left seal | centered Republic/Province/LGU lines + office | right seal]."""
    text = [Paragraph(escape(line), lgu_style if i >= 2 else line_style) for i, line in enumerate(lh["lines"])]
    text.append(Paragraph(escape(lh["office"].upper()), office_style))
    side = SEAL_W + 6
    table = Table([[_seal(lh.get("logo_left")), text, _seal(lh.get("logo_right"))]],
                  colWidths=[side, width - 2 * side, side])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _signature_table(letterhead, width):
    sigs = letterhead["signatories"]
    gap = 24
    col = (width - gap * (len(sigs) - 1)) / len(sigs)
    label = ParagraphStyle("RLSigLabel", fontName="Helvetica", fontSize=9)
    name = ParagraphStyle("RLSigName", fontName="Helvetica-Bold", fontSize=9, alignment=TA_CENTER)
    pos = ParagraphStyle("RLSigPos", fontName="Helvetica", fontSize=8.5, leading=10.5, alignment=TA_CENTER)

    # Signer columns separated by empty gap columns, so each signature line
    # is its own segment instead of one rule running across the page.
    def with_gaps(cells):
        out = []
        for i, c in enumerate(cells):
            if i:
                out.append("")
            out.append(c)
        return out

    widths = with_gaps([col] * len(sigs))
    widths = [gap if w == "" else w for w in widths]
    table = Table([
        with_gaps([Paragraph(f"{s['label']}:", label) for s in sigs]),
        with_gaps([Paragraph(escape(s["name"].upper()) if s["name"] else "&nbsp;", name) for s in sigs]),
        with_gaps([Paragraph(escape(s["position"]), pos) for s in sigs]),
    ], colWidths=widths)
    style = [
        ("TOPPADDING", (0, 1), (-1, 1), 26),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
    ]
    for i in range(len(sigs)):
        style.append(("LINEBELOW", (i * 2, 1), (i * 2, 1), 0.8, colors.black))
    table.setStyle(TableStyle(style))
    return KeepTogether([Spacer(1, 26), table])


def generate_pdf(report):
    buffer = io.BytesIO()
    # Wide reports go landscape, same threshold as the on-screen print view.
    # Letter (short bond - the usual office paper here) with 0.75" margins.
    # An A4 page printed at actual size on Letter paper lost ~0.7" off its
    # right edge; a Letter page with these margins fits on either paper.
    pagesize = landscape(letter) if len(report["columns"]) > 7 else letter
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        title=report["title"],
    )
    lh = report["letterhead"]
    lh_line = ParagraphStyle("RLLh", fontName="Helvetica", fontSize=10, leading=13, alignment=TA_CENTER)
    lh_lgu = ParagraphStyle("RLLhLgu", parent=lh_line, fontName="Helvetica-Bold")
    lh_office = ParagraphStyle("RLLhOffice", parent=lh_line, fontName="Helvetica-Bold", fontSize=11.5, spaceBefore=4)
    title_style = ParagraphStyle("RLTitle", fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=8)
    meta_style = ParagraphStyle("RLMeta", fontName="Helvetica", fontSize=9, leading=12)
    body_style = ParagraphStyle("RLBody", fontName="Helvetica", fontSize=8.5, leading=10.5)
    head_style = ParagraphStyle("RLHead", parent=body_style, fontName="Helvetica-Bold")
    note_style = ParagraphStyle("RLNote", parent=body_style, fontSize=9, leftIndent=10, spaceAfter=3)

    story = [_letterhead_block(lh, doc.width, lh_line, lh_lgu, lh_office)]
    story += [Spacer(1, 6), HRFlowable(width="100%", thickness=1.5, color=colors.black), Spacer(1, 10)]
    story.append(Paragraph(escape(report["title"].upper()), title_style))

    area_label = "Barangay" if lh["office"] == "Office of the Punong Barangay" else "Municipality"
    meta = [
        ("Coverage", report["coverage"]),
        ("Typhoon Event", report["event_name"]),
        (area_label, report["municipality_label"]),
        ("Date Generated", report["date_generated"].strftime("%B %d, %Y")),
        ("No. of Records", report["record_count"]),
    ]
    cells = [Paragraph(f"<b>{k}:</b> {escape(str(v))}", meta_style) for k, v in meta]
    cells.append(Paragraph("", meta_style))
    meta_table = Table([cells[0:3], cells[3:6]], colWidths=[doc.width / 3] * 3)
    meta_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [meta_table, Spacer(1, 10)]

    if report["rows"]:
        widths = _column_widths(report["columns"], report["rows"], doc.width)
        header_cells = [Paragraph(escape(str(c)), head_style) for c in report["columns"]]
        wrapped_rows = [[Paragraph(escape(str(cell)), body_style) for cell in row] for row in report["rows"]]
        table = Table([header_cells] + wrapped_rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No records match the selected filters.", body_style))

    if report.get("notes"):
        story.append(Spacer(1, 14))
        story.append(Paragraph("NOTES", ParagraphStyle("RLNotesHead", parent=body_style, fontName="Helvetica-Bold", fontSize=9)))
        for note in report["notes"]:
            story.append(Paragraph(f"&bull; {escape(str(note))}", note_style))

    story.append(_signature_table(lh, doc.width))


    doc.build(story)
    page_count = max(doc.page, 1)
    buffer.seek(0)
    return buffer.getvalue(), page_count


def generate_excel(report):
    wb = Workbook()
    ws = wb.active
    ws.title = report["title"][:31]

    title_font = Font(bold=True, size=14, color="0F2547")
    meta_font = Font(size=9, color="555555")
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="0F2547")

    lh = report["letterhead"]
    last_col = max(len(report["columns"]), 2)
    center = Alignment(horizontal="center")

    def centered(row, value, font):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
        cell = ws.cell(row=row, column=1, value=value)
        cell.font = font
        cell.alignment = center

    # Letterhead - same lines as the PDF/printed report.
    row = 1
    for i, line in enumerate(lh["lines"]):
        centered(row, line, Font(size=10, bold=i >= 2))
        row += 1
    centered(row, lh["office"].upper(), Font(size=11, bold=True))
    row += 2

    # Seals over the letterhead rows' left and right ends.
    for rel, col in ((lh.get("logo_left"), 1), (lh.get("logo_right"), last_col)):
        path = _static_path(rel)
        if not path:
            continue
        img = XLImage(path)
        scale = 70 / max(img.width, img.height)
        img.width, img.height = img.width * scale, img.height * scale
        ws.add_image(img, f"{get_column_letter(col)}1")
    centered(row, report["title"].upper(), title_font)
    row += 1

    area_label = "Barangay" if lh["office"] == "Office of the Punong Barangay" else "Municipality"
    meta_lines = [
        f"Coverage: {report['coverage']}",
        f"Typhoon Event: {report['event_name']}",
        f"{area_label}: {report['municipality_label']}",
        f"Date Generated: {report['date_generated'].strftime('%B %d, %Y')}",
        f"No. of Records: {report['record_count']}",
    ]
    for line in meta_lines:
        ws.cell(row=row, column=1, value=line).font = meta_font
        row += 1

    row += 1
    header_row = row
    for col_idx, col_name in enumerate(report["columns"], start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for r_offset, data_row in enumerate(report["rows"], start=1):
        for c_idx, value in enumerate(data_row, start=1):
            ws.cell(row=header_row + r_offset, column=c_idx, value=value)

    for col_idx, col_name in enumerate(report["columns"], start=1):
        col_letter = get_column_letter(col_idx)
        cell_lens = [len(str(col_name))] + [len(str(r[col_idx - 1])) for r in report["rows"]]
        ws.column_dimensions[col_letter].width = min(max(max(cell_lens) + 2, 10), 40)

    next_row = header_row + len(report["rows"]) + 2
    if report.get("notes"):
        ws.cell(row=next_row, column=1, value="Notes").font = Font(bold=True, color="0F2547")
        for i, note in enumerate(report["notes"], start=1):
            ws.cell(row=next_row + i, column=1, value=f"• {note}")
        next_row += len(report["notes"]) + 2

    # Signatories, one per column block: label, name (on the line), position.
    sig_row = next_row + 1
    for i, s in enumerate(lh["signatories"]):
        col = 1 + i * 3
        ws.cell(row=sig_row, column=col, value=f"{s['label']}:")
        ws.cell(row=sig_row + 2, column=col, value=(s["name"] or "").upper() or "______________________").font = Font(bold=True)
        ws.cell(row=sig_row + 3, column=col, value=s["position"]).font = meta_font

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    page_count = max(1, -(-len(report["rows"]) // 40))
    return buffer.getvalue(), page_count


def generate_file(report, fmt):
    if fmt == "pdf":
        return generate_pdf(report)
    if fmt == "excel":
        return generate_excel(report)
    raise ValueError(f"Unknown export format: {fmt}")
