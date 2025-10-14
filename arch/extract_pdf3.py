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


def process_pdf(pdf_path, output_dir):
    """
    Process a PDF:
    - Extract and mark images and paragraphs
    - Save output JSON with their coordinates
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    output_pdf = os.path.join(output_dir, f"marked_{pdf_name}.pdf")
    output_json = os.path.join(output_dir, f"{pdf_name}.json")

    doc = fitz.open(pdf_path)
    extracts = {"images": [], "paragraphs": []}
    global_paragraph_number = 1

    for page_index, page in enumerate(doc):
        page_number = page_index + 1
        print(f"Processing page {page_number}/{len(doc)}")

        # --- Extract images ---
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

            rects = []
            for rect in page.get_image_rects(xref):
                rects.append([rect.x0, rect.y0, rect.x1, rect.y1])
                page.draw_rect(rect, color=(1, 0, 0), width=1.2)
                page.insert_text(rect.tl, f"IMG{img_idx}", fontsize=8, color=(1, 0, 0))

            extracts["images"].append({
                "page": page_number,
                "number": img_idx,
                "file": img_path,
                "rects": rects
            })

        # --- Extract paragraphs ---
        paragraphs = get_paragraphs_from_page(page)
        for para in paragraphs:
            rect = fitz.Rect(para["bbox"])
            text = para["text"]

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


def read_paragraphs_from_json(json_path: str) -> Dict[int, List[dict]]:
    """
    Reads all paragraphs from the JSON and groups them by page.
    Returns { page_number: [ {text, bbox}, ... ] }
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


def print_all_pages(json_path: str):
    """
    Print all paragraphs grouped by page.
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
        print()


def main():
    pdf_dir = "/documents/input/"
    output_dir = "/documents/output/"
    os.makedirs(output_dir, exist_ok=True)

    # Process all PDFs
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            process_pdf(pdf_path, output_dir)

    # Example JSON path
    json_path = "/documents/output/book_Bruggen_Israels_Machtelt_Piero_del.json"

    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return

    print_all_pages(json_path)
    print_image_rects(json_path)


if __name__ == "__main__":
    main()
