import json
import re
import fitz  # PyMuPDF

def extract_page_and_image(main_image_path):
    """
    Extract page and image number from the Main Image filename.
    Example:
    '..._page10_img2.jpeg' → (10, 2)
    """
    match = re.search(r'_page(\d+)_img(\d+)', main_image_path)
    if match:
        page_num = int(match.group(1))
        image_num = int(match.group(2))
        return page_num, image_num
    else:
        raise ValueError(f"❌ Could not extract page/image from path: {main_image_path}")


def highlight_image(pdf_path, page_number, image_number, output_pdf):
    """
    Highlight the specified image on a given page in red.
    """
    doc = fitz.open(pdf_path)
    page_index = page_number - 1  # PyMuPDF is 0-based
    page = doc.load_page(page_index)
    images = page.get_images(full=True)

    if not images:
        print(f"⚠️ No images found on page {page_number}")
        return

    if image_number > len(images):
        print(f"⚠️ Page {page_number} has only {len(images)} image(s).")
        return

    # Get XREF of the image and its location
    xref = images[image_number - 1][0]
    rects = page.get_image_rects(xref)

    if not rects:
        print(f"⚠️ Could not locate image {image_number} on page {page_number}.")
        return

    rect = rects[0]
    page.draw_rect(rect, color=(1, 0, 0), width=2)
    annot = page.add_rect_annot(rect)
    annot.set_colors(stroke=(1, 0, 0))
    annot.update()

    doc.save(output_pdf)
    doc.close()

    print(f"✅ Highlighted image {image_number} on page {page_number} → {output_pdf}")


def main():
    # --- Input paths ---
    json_path = "/home/melahi/code/image/segment/documents/output/etardisArticle_SemanticsConference2023_final_image_text.json"
    input_pdf = "/home/melahi/code/image/segment/documents/input/etardisArticle_SemanticsConference2023.pdf"
    output_pdf = "/home/melahi/code/image/segment/documents/output/highlighted_from_json.pdf"

    # --- Read JSON ---
    with open(json_path, "r") as f:
        data = json.load(f)

    # --- Extract info ---
    for entry in data:
        main_image = entry["Main Image"]
        page_number, image_number = extract_page_and_image(main_image)
        print(f"🔹 Found: Page {page_number}, Image {image_number}")
        highlight_image(input_pdf, page_number, image_number, output_pdf)


if __name__ == "__main__":
    main()
