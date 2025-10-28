import fitz  # PyMuPDF
import json
import os
from typing import Dict, List



def get_paragraphs_from_page(page):
    """
    Extract all paragraphs (text blocks) from a PDF page.
    Returns a list of dictionaries with 'text' and 'bbox' (bounding box).
    """
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (b[1], b[0]))  # Sort top-to-bottom, left-to-right

    paragraphs = []
    for b in blocks:
        text = b[4].strip()
        if not text:
            continue
        rect = fitz.Rect(b[:4])
        paragraphs.append({
            "text": text,
            "bbox": [rect.x0, rect.y0, rect.x1, rect.y1]
        })
    return paragraphs


def process_pdf(pdf_path, output_dir,output_pdf,output_json):
    """
    Process a single PDF:
    - Draw red borders around images (IMG1, IMG2, ...)
    - Draw blue boxes and number paragraphs [1], [2], ...
    - Keep paragraph numbers synchronized in PDF and JSON
    - Save marked PDF and JSON file
    """
    os.makedirs(output_dir, exist_ok=True)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    #output_pdf = os.path.join(output_dir, f"marked_{pdf_name}.pdf")
    #output_json = os.path.join(output_dir, f"{pdf_name}.json")

    doc = fitz.open(pdf_path)
    extracts = {"images": [], "paragraphs": []}
    global_paragraph_number = 1  # continuous numbering

    for page_index, page in enumerate(doc):
        page_number = page_index + 1
        print(f"Processing page {page_number}/{len(doc)}")

        # --- Extract and mark images ---
        img_list = page.get_images(full=True)
        for img_idx, img in enumerate(img_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]

            img_filename = f"input_{pdf_name}_page{page_number}_img{img_idx}.{img_ext}"
            img_path = os.path.join(output_dir, img_filename)
            with open(img_path, "wb") as f:
                f.write(img_bytes)

            rects = page.get_image_rects(xref)
            rect_coords = []
            for rect in rects:
                page.draw_rect(rect, color=(1, 0, 0), width=1.2)
                page.insert_text(rect.tl, f"IMG{img_idx}", fontsize=8, color=(1, 0, 0))
                rect_coords.append([rect.x0, rect.y0, rect.x1, rect.y1])

            extracts["images"].append({
                "page": page_number,
                "number": img_idx,
                "file": img_path,
                "rects": rect_coords
            })

        # --- Extract and mark paragraphs ---
        paragraphs = get_paragraphs_from_page(page)
        for para in paragraphs:
            rect = fitz.Rect(para["bbox"])
            text = para["text"]

            # Draw blue border and label
            page.draw_rect(rect, color=(0, 0, 1), width=0.7)
            page.insert_text(rect.tl, f"[{global_paragraph_number}]", fontsize=8, color=(0, 0, 1))

            extracts["paragraphs"].append({
                "page": page_number,
                "number": global_paragraph_number,
                "text": text,
                "bbox": para["bbox"]
            })

            global_paragraph_number += 1

    # --- Save marked PDF and JSON ---
    doc.save(output_pdf)
    doc.close()

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(extracts, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved marked PDF: {output_pdf}")
    print(f"✅ Saved JSON: {output_json}")


def read_paragraphs_from_json(json_path):
    """
    Reads all paragraphs from the JSON and groups them by page.
    Returns a dictionary: { page_number: [list of paragraph texts] }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    paragraphs_by_page = {}

    for para in data.get("paragraphs", []):
        page = para["page"]
        text = para["text"]
        paragraphs_by_page.setdefault(page, []).append(text)

    return paragraphs_by_page

def read_paragraphs_from_json(json_path: str) -> Dict[int, List[dict]]:
    """
    Reads all paragraphs from a JSON file created by the PDF processing script.
    Groups them by page and returns paragraph text + bbox.

    Args:
        json_path (str): Path to the JSON file generated after PDF processing.

    Returns:
        Dict[int, List[dict]]: A dictionary where each key is a page number,
                               and each value is a list of paragraph dictionaries
                               with 'text' and 'bbox'.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    paragraphs_by_page = {}

    for para in data.get("paragraphs", []):
        page = para["page"]
        text = para["text"].strip()
        bbox = para.get("bbox", [])
        paragraphs_by_page.setdefault(page, []).append({
            "text": text,
            "bbox": bbox
        })

    return paragraphs_by_page


def get_paragraphs_by_page(json_path: str, page_number: int) -> List[dict]:
    """
    Returns all paragraphs for a specific page number from the JSON file.

    Args:
        json_path (str): Path to the JSON file.
        page_number (int): Page number to extract paragraphs from.

    Returns:
        List[dict]: List of paragraph dictionaries containing 'text' and 'bbox'.
    """
    paragraphs_by_page = read_paragraphs_from_json(json_path)
    return paragraphs_by_page.get(page_number, [])


def get_total_pages(json_path: str) -> int:
    """
    Finds the total number of pages in the JSON file.

    Args:
        json_path (str): Path to the JSON file.

    Returns:
        int: Total number of pages found in the JSON.
    """
    paragraphs_by_page = read_paragraphs_from_json(json_path)
    return len(paragraphs_by_page)


def print_all_pages(json_path: str):
    """
    Iterates through all pages and prints all paragraphs page by page.
    """
    paragraphs_by_page = read_paragraphs_from_json(json_path)
    total_pages = len(paragraphs_by_page)

    print(f"\n📘 Total pages found: {total_pages}\n")

    for page_number in sorted(paragraphs_by_page.keys()):
        print(f"--- 🧾 Page {page_number} ---")
        paragraphs = paragraphs_by_page[page_number]
        for i, para in enumerate(paragraphs, start=1):
            text = para["text"].replace("\n", " ")
            preview = text[:200] + ("..." if len(text) > 200 else "")
            print(f"[{i}] {preview}")
        print()  # blank line between pages

def read_images_from_json(json_path: str) -> Dict[int, List[dict]]:
    """
    Reads all image entries (including bounding rectangles) from the JSON file.
    Groups them by page number.

    Returns:
        { page_number: [ {number, file, rects}, ... ] }
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    images_by_page = {}
    for img in data.get("images", []):
        page = img["page"]
        img_info = {
            "number": img["number"],
            "file": img["file"],
            "rects": img.get("rects", [])
        }
        images_by_page.setdefault(page, []).append(img_info)

    return images_by_page



def print_image_rects(json_path: str):
    """
    Print all image rectangles from JSON file, grouped by page.
    """
    images_by_page = read_images_from_json(json_path)
    print("\n🖼 Image Rectangles by Page\n")
    for page, images in sorted(images_by_page.items()):
        print(f"--- Page {page} ---")
        for img in images:
            print(f"IMG{img['number']}: {img['file']}")
            for rect in img["rects"]:
                print(f"  rect: {rect}")
        print()

def main():
    pdf_dir = "/documents/input/"
    output_dir = "/documents/output/"
    os.makedirs(output_dir, exist_ok=True)

    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            process_pdf(pdf_path, output_dir)

    """
        Main function:
        - Reads JSON file
        - Prints total pages
        - Iterates through all pages and prints all paragraphs
        """
    # 👇 Change this path to your JSON file
    json_path = "/documents/output/book_Bruggen_Israels_Machtelt_Piero_del.json"

    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return

    print_all_pages(json_path)


if __name__ == "__main__":
    main()
