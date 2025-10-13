import fitz  # PyMuPDF
import io, os, json
from PIL import Image


# ---------- Helpers ----------
def save_image(img_bytes, filename):
    """Save extracted image bytes to a file."""
    with open(filename, "wb") as f:
        f.write(img_bytes)


# ---------- Main ----------
def process_pdf(input_pdf):
    base_dir = os.path.dirname(input_pdf)
    output_pdf = os.path.join(base_dir, "output_marked_" + os.path.basename(input_pdf))
    json_path = os.path.join(base_dir, "extracted.json")

    doc = fitz.open(input_pdf)
    extracts = {"images": [], "paragraphs": []}
    para_counter = 1
    img_counter = 1

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"🔹 Processing page {page_num + 1}/{len(doc)}")

        # --- Process images ---
        image_list = page.get_images(full=True)
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]

            # Save extracted image (optional)
            img_path = os.path.join(base_dir, f"page{page_num+1}_img{img_counter}.{img_ext}")
            save_image(img_bytes, img_path)

            # Get image rectangle(s)
            img_rects = page.get_image_rects(xref)
            for rect in img_rects:
                # 🔴 Draw red border and label
                page.draw_rect(rect, color=(1, 0, 0), width=1.2)  # red border
                page.insert_text(rect.tl, f"IMG{img_counter}", fontsize=8, color=(1, 0, 0))  # red label

            extracts["images"].append({
                "page": page_num + 1,
                "number": img_counter,
                "file": img_path,
                "rects": [list(r) for r in img_rects]
            })

            img_counter += 1

        # --- Process paragraphs ---
        blocks = page.get_text("blocks")
        for b in blocks:
            rect = fitz.Rect(b[:4])
            text = b[4].strip()
            if not text:
                continue

            label = f"[{para_counter}]"
            # Mark paragraph number and border
            page.insert_text(rect.tl, label, fontsize=8, color=(1, 0, 0))
            page.draw_rect(rect, color=(0, 0, 1), width=0.4)  # blue border for paragraphs

            extracts["paragraphs"].append({
                "page": page_num + 1,
                "number": para_counter,
                "text": text,
                "bbox": list(rect)
            })

            para_counter += 1

    # Save marked PDF
    doc.save(output_pdf)
    doc.close()

    # Save JSON metadata
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extracts, f, indent=2, ensure_ascii=False)

    print("\n✅ DONE!")
    print(f"✅ Marked PDF saved as: {output_pdf}")
    print(f"✅ Extracted images & paragraphs info saved in: {json_path}")


# ---------- Run ----------
if __name__ == "__main__":
    INPUT_PDF = "/home/melahi/code/image/segment/documents/input/book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    process_pdf(INPUT_PDF)

