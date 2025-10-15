import json
import ast
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple


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


def highlight_paragraphs(pdf_path: str, json_path: str, output_path: str):
    """Draw yellow rectangles around paragraphs defined in the JSON file within a PDF."""
    # Load JSON data
    data = load_json(json_path)

    # Open the PDF
    doc = fitz.open(pdf_path)

    # Define outline color (bright yellow)
    red = (1, 0, 0)

    for entry in data:
        page_num = entry.get("Most Frequent Page", 1) - 1  # PyMuPDF uses 0-based indexing
        bbox = parse_bbox(entry.get("Representative Original Text", ""))
        if bbox is None:
            continue

        rect = fitz.Rect(*bbox)

        try:
            page = doc.load_page(page_num)

            # Add a yellow rectangular outline (no fill)
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


if __name__ == "__main__":
    # Example usage
    pdf_file = "book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    prefix = pdf_file.replace(".pdf", "")
    base_dir = "/documents/"
    input_dir=base_dir+"input/"
    output_dir = base_dir + "output/"

    highlight_paragraphs(
        pdf_path=input_dir+"book_Bruggen_Israels_Machtelt_Piero_del.pdf",
        json_path=output_dir + "book_Bruggen_Israels_Machtelt_Piero_del_all_image_objects_similarities_final.json",
        output_path=output_dir + "outlined_output_" + prefix + ".pdf"
    )
