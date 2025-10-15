import json
import ast
import fitz  # PyMuPDF

def highlight_image_and_text(pdf_path, output_pdf, data):
    """
    Highlights the image rect and text bbox in a PDF using red rectangles.
    """
    doc = fitz.open(pdf_path)

    # Extract needed info
    page_num = data.get("Most Frequent Page", 1) - 1  # fitz is 0-indexed
    rects = data.get("rects", [])
    rep_text = data.get("Representative Original Text", "")

    # Parse the bbox from the Representative Original Text
    try:
        rep_dict = ast.literal_eval(rep_text)
        text_bbox = rep_dict.get("bbox", [])
    except Exception as e:
        print("Error parsing Representative Original Text:", e)
        text_bbox = []

    # Open the page
    page = doc.load_page(page_num)

    # Highlight image rectangle(s)
    for rect in rects:
        r = fitz.Rect(rect)
        page.add_rect_annot(r).set_colors(stroke=(1, 0, 0))  # Red border
        page.draw_rect(r, color=(1, 0, 0), width=2)

    # Highlight text bbox
    if text_bbox:
        r_text = fitz.Rect(text_bbox)
        page.add_rect_annot(r_text).set_colors(stroke=(1, 0, 0))
        page.draw_rect(r_text, color=(1, 0, 0), width=2)

    # Save the result
    doc.save(output_pdf)
    doc.close()

    print(f"✅ Saved highlighted PDF to: {output_pdf}")


# === Example Usage ===
if __name__ == "__main__":
    # Example data
    data = {
        "Main Image": "/home/melahi/code/image/segment/documents/output/input_etardisArticle_SemanticsConference2023_page10_img2.jpeg",
        "Most Frequent Page": 8,
        "Most Frequent Paragraph": 2,
        "Frequency": 13,
        "Representative Text": "spatial distance spatial distance dists two fragments defined shortest distances corresponding locations since locations represented pairs longitudes latitudes distance dists two locations calculated via great circle distance rearth earth radius",
        "Representative Original Text": "{'text': 'Spatial distance:\\nThe spatial distance dists between two fragments is defined as the\\nshortest distances of the corresponding locations. Since locations are represented in pairs\\nof longitudes and latitudes (φ,θ), the distance dists between two locations (φi,θi) and\\n(φj,θj) can be calculated via the great circle distance with rearth ≈6371,009 km being\\nthe earth’s radius:', 'bbox': [121.88998413085938, 153.16360473632812, 472.5758361816406, 211.32913208007812]}",
        "rects": [
            [176.76400756835938, 333.4654235839844, 417.68560791015625, 475.1830139160156]
        ]
    }

    input_pdf = "/home/melahi/code/image/segment/documents/input/etardisArticle_SemanticsConference2023.pdf"
    output_pdf = "/home/melahi/code/image/segment/documents/output/highlighted_page10_img2.pdf"

    highlight_image_and_text(input_pdf, output_pdf, data)
