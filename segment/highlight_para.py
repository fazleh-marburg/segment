import json
import ast
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data containing paragraph info."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_bbox(original_text: str) -> Tuple[float, float, float, float] | None:
    """Extract paragraph bbox coordinates from the 'Representative Original Text' field."""
    try:
        parsed = ast.literal_eval(original_text)
        return tuple(parsed["bbox"])
    except Exception as e:
        print(f"⚠️ Could not parse bbox from: {original_text[:60]}... Error: {e}")
        return None


def highlight_paragraphs(pdf_path: str, json_path: str, output_path: str):
    """
    Draw yellow rectangles around paragraphs and write associated image names inside.
    """
    data = load_json(json_path)
    doc = fitz.open(pdf_path)

    yellow = (1, 1, 0)  # paragraph color

    for entry in data:
        page_index = entry.get("Most Frequent Page", 1) - 1  # 0-based
        page = doc.load_page(page_index)

        # --- Paragraph ---
        bbox = parse_bbox(entry.get("Representative Original Text", ""))
        if bbox:
            try:
                rect = fitz.Rect(*bbox)
                annot = page.add_rect_annot(rect)
                annot.set_colors(stroke=yellow, fill=None)
                annot.set_border(width=1.5)
                annot.update()

                # Add image names at top-left of paragraph
                image_names = entry.get("Image Names", [])
                if image_names:
                    text_str = ", ".join(image_names)
                    page.insert_text(
                        rect.tl,
                        text_str,
                        fontsize=8,
                        color=(1, 0, 1)  # magenta for visibility
                    )

                print(f"🟨 Paragraph outlined on Page {page_index + 1}")
            except Exception as e:
                print(f"⚠️ Could not outline paragraph on Page {page_index + 1}: {e}")

    # Save PDF
    doc.save(output_path, deflate=True)
    doc.close()
    print(f"\n💾 Saved annotated PDF to: {output_path}")


if __name__ == "__main__":
    pdf_file = "book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    prefix = pdf_file.replace(".pdf", "")
    base_dir = "/documents/"
    input_dir = base_dir + "input/"
    output_dir = base_dir + "output/"

    highlight_paragraphs(
        pdf_path="/documents/output/marked_book_Bruggen_Israels_Machtelt_Piero_del.pdf",
        json_path=output_dir + "book_Bruggen_Israels_Machtelt_Piero_del_all_image_objects_similarities_image_final.json",
        output_path=output_dir + "outlined_output_" + prefix + ".pdf"
    )
