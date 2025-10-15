import json
import ast
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import re



def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data containing paragraph information."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_bbox(original_text: str) -> Tuple[float, float, float, float] | None:
    """Extract bbox coordinates from the 'Representative Original Text' field."""
    try:
        parsed = ast.literal_eval(original_text)
        return tuple(parsed["bbox"])
    except Exception as e:
        print(f"⚠️ Could not parse bbox from: {original_text[:50]}... Error: {e}")
        return None


def highlight_paragraphs(entry,page_num,rect,doc,output_pdf,red):
    try:
        page = doc.load_page(page_num)

        # Add a red rectangular outline (no fill)
        annot = page.add_rect_annot(rect)
        annot.set_colors(stroke=red, fill=None)
        annot.set_border(width=1.5)  # thickness of the outline
        annot.update()

        print(f"✅ Outlined paragraph on Page {page_num + 1}: {entry['Representative Text'][:60]}...")
    except Exception as e:
        print(f"⚠️ Could not outline Page {page_num + 1}: {e}")

    # Save the output PDF
    doc.save(output_pdf, deflate=True)
    doc.close()
    print(f"\n💾 Saved outlined PDF to: {output_pdf}")

"""
def highlight_paragraphs(pdf_path: str, json_path: str, output_path: str):
    # Load JSON data
    data = load_json(json_path)

    # Open the PDF
    doc = fitz.open(pdf_path)

    # Define outline color (red)
    red = (1, 0, 0)

    for entry in data:
        page_num = entry.get("Most Frequent Page", 1) - 1  # PyMuPDF uses 0-based indexing
        bbox = parse_bbox(entry.get("Representative Original Text", ""))
        if bbox is None:
            continue

        rect = fitz.Rect(*bbox)

        try:
            page = doc.load_page(page_num)

            # Add a red rectangular outline (no fill)
            annot = page.add_rect_annot(rect)
            annot.set_colors(stroke=red, fill=None)
            annot.set_border(width=1.5)  # thickness of the outline
            annot.update()

            print(f"✅ Outlined paragraph on Page {page_num + 1}: {entry['Representative Text'][:60]}...")
        except Exception as e:
            print(f"⚠️ Could not outline Page {page_num + 1}: {e}")

    # Save the output PDF
    doc.save(output_path, deflate=True)
    doc.close()
    print(f"\n💾 Saved outlined PDF to: {output_path}")

"""

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


if __name__ == "__main__":
    # Example usage
    pdf_file = "book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    prefix = pdf_file.replace(".pdf", "")
    base_dir = "/documents/"
    input_dir = base_dir + "input/"
    output_dir = base_dir + "output/"

    highlight_paragraphs(
        pdf_path=input_dir + pdf_file,
        json_path=output_dir + "etardisArticle_SemanticsConference2023_final_image_text.json",
        output_path=output_dir + f"outlined_output_{prefix}.pdf"
    )
