import fitz  # PyMuPDF
import os
import json

def extract_paragraphs_with_bbox(pdf_dir):
    """
    For each PDF in pdf_dir:
    - Extracts all paragraphs per page with their bounding boxes
    - Saves JSON with format:
      [
        {"page": 1, "paragraphs": [{"text": "...", "bbox": [...]}, ...]},
        ...
      ]
    """
    os.makedirs(pdf_dir, exist_ok=True)

    for pdf_file in os.listdir(pdf_dir):
        if not pdf_file.lower().endswith(".pdf"):
            continue

        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_json = os.path.join(pdf_dir, f"{pdf_name}_paragraphs_with_bbox.json")

        print(f"\n📘 Processing: {pdf_file}")

        doc = fitz.open(pdf_path)
        result = []

        for page_number, page in enumerate(doc, start=1):
            blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type, ...)
            paragraphs = []

            for b in blocks:
                text = b[4].strip()
                if not text:
                    continue
                rect = list(b[:4])  # x0, y0, x1, y1
                paragraphs.append({
                    "text": text,
                    "bbox": rect
                })

            if paragraphs:
                result.append({
                    "page": page_number,
                    "paragraphs": paragraphs
                })

        doc.close()

        # Save output JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"✅ Extracted paragraphs with bbox JSON saved as: {output_json}")


def main():
    pdf_dir = "/documents/input/"
    extract_paragraphs_with_bbox(pdf_dir)


if __name__ == "__main__":
    main()
