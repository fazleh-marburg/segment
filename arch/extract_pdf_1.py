import fitz  # PyMuPDF
import os
import json

def extract_images_and_text(pdf_dir):
    """
    For each PDF in pdf_dir:
    - Draws red borders around images (IMG1, IMG2, …)
    - Draws blue borders around paragraphs ([1], [2], …)
    - Saves marked PDF and extracted JSON data
    """
    os.makedirs(pdf_dir, exist_ok=True)

    # Loop through all PDF files in the folder
    for pdf_file in os.listdir(pdf_dir):
        if not pdf_file.lower().endswith(".pdf"):
            continue  # Skip non-PDF files

        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_pdf = os.path.join(pdf_dir, f"output_marked_{pdf_file}")
        output_json = os.path.join(pdf_dir, f"{pdf_name}.json")

        print(f"\n📘 Processing: {pdf_file}")

        doc = fitz.open(pdf_path)
        extracts = {"images": [], "paragraphs": []}
        img_counter = 1
        para_counter = 1

        for page_number, page in enumerate(doc, start=1):
            print(f"🔹 Processing page {page_number}/{len(doc)}")

            # --- Process Images ---
            image_list = page.get_images(full=True)
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image["ext"]

                # Save image
                img_filename = "input_"+f"{pdf_name}_page{page_number}_img{img_counter}.{img_ext}"
                img_path = os.path.join(pdf_dir, img_filename)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                # Get all rectangles where the image appears
                img_rects = page.get_image_rects(xref)
                for rect in img_rects:
                    # 🔴 Draw red border and label
                    page.draw_rect(rect, color=(1, 0, 0), width=1.2)
                    page.insert_text(rect.tl, f"IMG{img_counter}", fontsize=8, color=(1, 0, 0))

                extracts["images"].append({
                    "page": page_number,
                    "number": img_counter,
                    "file": img_path,
                    "rects": [list(r) for r in img_rects]
                })

                img_counter += 1

            # --- Process Paragraphs ---
            blocks = page.get_text("blocks")  # returns list of (x0, y0, x1, y1, text, block_no, block_type, ...)
            for b in blocks:
                rect = fitz.Rect(b[:4])
                text = b[4].strip()
                if not text:
                    continue

                # Draw blue box and label
                label = f"[{para_counter}]"
                page.draw_rect(rect, color=(0, 0, 1), width=0.5)
                page.insert_text(rect.tl, label, fontsize=8, color=(1, 0, 0))

                extracts["paragraphs"].append({
                    "page": page_number,
                    "number": para_counter,
                    "text": text,
                    "bbox": list(rect)  # Save bounding box for paragraph
                })

                para_counter += 1

        # --- Save the marked PDF ---
        doc.save(output_pdf)
        doc.close()

        # --- Save JSON metadata ---
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(extracts, f, indent=2, ensure_ascii=False)

        print(f"✅ Marked PDF saved as: {output_pdf}")
        print(f"✅ Extracted data (with bbox) saved in: {output_json}")


def main():
    pdf_dir = "/documents/input/"
    mark_pdf(pdf_dir)


if __name__ == "__main__":
    main()
