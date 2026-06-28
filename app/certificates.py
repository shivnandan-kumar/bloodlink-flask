from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _draw_centered(pdf, text, y_position, font_name, font_size, color):
    page_width, _ = landscape(A4)
    pdf.setFillColor(color)
    pdf.setFont(font_name, font_size)
    pdf.drawCentredString(page_width / 2, y_position, text)


def generate_donation_certificate(donation_record):
    """Create a polished PDF certificate for a completed donation."""
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))

    blood = colors.HexColor("#c81d3a")
    blood_dark = colors.HexColor("#8f1529")
    charcoal = colors.HexColor("#182126")
    muted = colors.HexColor("#627176")
    soft_bg = colors.HexColor("#fff8f9")
    teal = colors.HexColor("#167b73")
    gold = colors.HexColor("#c9962c")

    pdf.setFillColor(soft_bg)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    pdf.setStrokeColor(blood)
    pdf.setLineWidth(2.4)
    pdf.roundRect(18 * mm, 16 * mm, page_width - 36 * mm, page_height - 32 * mm, 10, stroke=1, fill=0)

    pdf.setStrokeColor(colors.HexColor("#e6a7b2"))
    pdf.setLineWidth(0.8)
    pdf.roundRect(24 * mm, 22 * mm, page_width - 48 * mm, page_height - 44 * mm, 8, stroke=1, fill=0)

    pdf.setFillColor(blood)
    pdf.circle(38 * mm, page_height - 35 * mm, 10 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(38 * mm, page_height - 39 * mm, "B")

    pdf.setFillColor(charcoal)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(52 * mm, page_height - 34 * mm, "BloodLink")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(52 * mm, page_height - 40 * mm, "Verified Blood Donor Network")

    certificate_id = f"BL-DON-{donation_record.id:05d}"
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawRightString(page_width - 32 * mm, page_height - 34 * mm, "CERTIFICATE ID")
    pdf.setFillColor(blood_dark)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(page_width - 32 * mm, page_height - 40 * mm, certificate_id)

    _draw_centered(pdf, "CERTIFICATE OF APPRECIATION", page_height - 62 * mm, "Helvetica-Bold", 22, blood_dark)
    _draw_centered(pdf, "This certificate is proudly presented to", page_height - 77 * mm, "Helvetica", 13, muted)

    donor_name = donation_record.donor_profile.user.name.upper()
    _draw_centered(pdf, donor_name, page_height - 96 * mm, "Helvetica-Bold", 34, charcoal)

    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.2)
    pdf.line(70 * mm, page_height - 102 * mm, page_width - 70 * mm, page_height - 102 * mm)

    thank_you = (
        "For completing a verified blood donation through BloodLink and helping "
        "support a patient in need."
    )
    _draw_centered(pdf, thank_you, page_height - 118 * mm, "Helvetica", 13, muted)

    request = donation_record.blood_request
    completed_date = donation_record.completed_at.strftime("%d %B %Y")
    detail_y = page_height - 140 * mm
    detail_box_x = 46 * mm
    detail_box_width = page_width - 92 * mm
    detail_box_height = 32 * mm

    pdf.setFillColor(colors.white)
    pdf.roundRect(detail_box_x, detail_y - detail_box_height + 8, detail_box_width, detail_box_height, 8, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#f0ccd3"))
    pdf.roundRect(detail_box_x, detail_y - detail_box_height + 8, detail_box_width, detail_box_height, 8, fill=0, stroke=1)

    columns = [
        ("Blood Group", request.blood_group),
        ("Donation Date", completed_date),
        ("Hospital", request.hospital_name),
        ("Location", f"{request.city}{' - ' + request.pincode if request.pincode else ''}"),
    ]
    column_width = detail_box_width / len(columns)
    for index, (label, value) in enumerate(columns):
        x_position = detail_box_x + (index * column_width) + 8 * mm
        pdf.setFillColor(blood)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(x_position, detail_y - 5 * mm, label.upper())
        pdf.setFillColor(charcoal)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x_position, detail_y - 14 * mm, str(value)[:28])

    pdf.setFillColor(teal)
    pdf.circle(page_width / 2, 45 * mm, 13 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(page_width / 2, 47 * mm, "VERIFIED")
    pdf.drawCentredString(page_width / 2, 42 * mm, "DONATION")

    pdf.setStrokeColor(colors.HexColor("#d8dee0"))
    pdf.line(44 * mm, 38 * mm, 105 * mm, 38 * mm)
    pdf.line(page_width - 105 * mm, 38 * mm, page_width - 44 * mm, 38 * mm)
    pdf.setFillColor(charcoal)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(74.5 * mm, 31 * mm, "BloodLink Verification")
    pdf.drawCentredString(page_width - 74.5 * mm, 31 * mm, "Digital Certificate")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(page_width / 2, 21 * mm, "Final medical eligibility and blood safety are always confirmed by authorized healthcare professionals.")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
