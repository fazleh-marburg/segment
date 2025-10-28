import fitz  # PyMuPDF
import os
from PIL import Image
from io import BytesIO
import json

def extract_images_and_text(pdf_dir):
    """
    Extract images and text from all PDFs in pdf_dir.
    Saves images and JSON files in output_folder.
    """
    os.makedirs(pdf_dir, exist_ok=True)

    # Loop through all PDF files in the folder
    for pdf_file in os.listdir(pdf_dir):
        if not pdf_file.lower().endswith(".pdf"):
            continue  # Skip non-PDF files

        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_json = os.path.join(pdf_dir, f"{pdf_name}.json")

        print(f"\n📘 Processing: {pdf_file}")

        # Open PDF safely
        with fitz.open(pdf_path) as doc:
            pages_data = []  # List of text paragraphs per page
            image_count = 0

            # Loop through pages
            for page_number, page in enumerate(doc, start=1):

                # --- Extract images ---
                for img_index, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    ext = base_image["ext"]

                    # Filename with book prefix
                    filename = f"input_{pdf_name}_page{page_number}_img{img_index}.{ext}"
                    filepath = os.path.join(pdf_dir, filename)

                    # Save image to disk
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)

                    image_count += 1

                # --- Extract text ---
                blocks = page.get_text("blocks")
                text_blocks = [b for b in blocks if b[6] == 0]  # Only text
                text_blocks.sort(key=lambda b: (round(b[0] / 50), b[1]))  # Column-wise reading

                paragraphs = [b[4].strip() for b in text_blocks if b[4].strip()]
                pages_data.append({
                    "page": page_number,
                    "paragraphs": paragraphs
                })

        # Save paragraphs to JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Extracted {image_count} images and saved text to {output_json}")


def main():
    # Configure your input and output folders here
    pdf_dir = "/home/melahi/code/image/segment-anything/documents/input/"
    output_folder = pdf_dir

    extract_images_and_text(pdf_dir, output_folder)


if __name__ == "__main__":
    main()
