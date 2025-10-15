from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import json
import os

from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, Color
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from io import BytesIO

def highlight_pdf_region(input_pdf, output_pdf, rects_by_page):
    """
    Highlight rectangles on specific pages of a PDF.

    rects_by_page: dict of {page_number (int): [ [x1,y1,x2,y2], ... ]}
    """
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page_number in range(len(reader.pages)):
        page = reader.pages[page_number]
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        if page_number + 1 in rects_by_page:
            for rect in rects_by_page[page_number + 1]:
                x1, y1, x2, y2 = rect
                width = x2 - x1
                height = y2 - y1
                can.setStrokeColor(red)
                can.setLineWidth(2)
                can.rect(x1, y1, width, height, stroke=1, fill=0)

        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    print(f"✅ Highlighted PDF saved to {output_pdf}")


def main():
    # --- Paths ---
    output_dir = "/home/melahi/code/image/segment/documents/output/"
    json_path = os.path.join(output_dir, "etardisArticle_SemanticsConference2023_all_image_objects_similarities_image_final.json")
    input_pdf = os.path.join(output_dir, "marked_etardisArticle_SemanticsConference2023.pdf")
    output_pdf = os.path.join(output_dir, "highlighted_page10_img2.pdf")

    # --- Load JSON ---
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- Extract target entry ---
    target_image = "/home/melahi/code/image/segment/documents/output/input_etardisArticle_SemanticsConference2023_page10_img2.jpeg"
    rects_by_page = {}

    for item in data:
        if item.get("Main Image") == target_image:
            # Page number comes from JSON
            page_num = int(item.get("Most Frequent Page", 1))
            rects_by_page[page_num] = item.get("rects", [])

    if not rects_by_page:
        print("⚠️ No matching image found in JSON.")
        return

    # --- Highlight ---
    highlight_pdf_region(input_pdf, output_pdf, rects_by_page)


if __name__ == "__main__":
    main()
