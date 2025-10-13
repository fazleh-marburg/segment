import fitz  # PyMuPDF
import io, os, json
from PIL import Image

YELLOW_ALPHA = 120  # transparency for image tint


# ---------- Helpers ----------
def tint_image_bytes(img_bytes, alpha=YELLOW_ALPHA):
    """Apply a semi-transparent yellow overlay to an image (bytes)."""
    with Image.open(io.BytesIO(img_bytes)).convert("RGBA") as pil_img:
        overlay = Image.new("RGBA", pil_img.size, (255, 255, 0, alpha))
        result = Image.alpha_composite(pil_img, overlay)
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue()


def save_image(img_bytes, filename):
    with open(filename, "wb") as f:
        f.write(img_bytes)


# ---------- Main ----------
def process_pdf(input_pdf):
    # Save everything in same directory as input PDF
    base_dir = os.path.dirname(input_pdf)
    output_pdf = os.path.join(base_dir, "output_marked_" + os.path.basename(input_pdf))
    json_path = os.path.join(base_dir, "extracted.json")

    doc = fitz.open(input_pdf)
    extracts = {"images": [], "paragraphs": []}
    para_counter = 1

    for page_num in range(len(doc)):
        page = doc[page_num]

        # --- Process images ---
        image_list = page.get_images(full=True)
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]

            # Save original image
            img_path = os.path.join(base_dir, f"page{page_num+1}_img{img_idx+1}.png")
            save_image(img_bytes, img_path)

            # Tint and replace image in PDF
            new_bytes = tint_image_bytes(img_bytes)
            doc.update_stream(xref, new_bytes)

            extracts["images"].append({
                "page": page_num + 1,
                "index": img_idx + 1,
                "file": img_path
            })

        # --- Process paragraphs ---
        blocks = page.get_text("blocks")
        for b in blocks:
            rect = fitz.Rect(b[:4])
            text = b[4].strip()
            if not text:
                continue

            label = f"[{para_counter}]"
            page.insert_text(rect.tl, label, fontsize=8, color=(1, 0, 0))  # red label

            extracts["paragraphs"].append({
                "page": page_num + 1,
                "number": para_counter,
                "text": text
            })

            para_counter += 1

    # Save marked PDF
    doc.save(output_pdf)
    doc.close()

    # Save JSON output
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extracts, f, indent=2, ensure_ascii=False)

    print(f"✅ Marked PDF saved as {output_pdf}")
    print(f"✅ Extracted images & paragraphs saved in {json_path}")


# ---------- Run ----------
if __name__ == "__main__":
    INPUT_PDF = "/home/melahi/code/image/segment/documents/input/book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    process_pdf(INPUT_PDF)
