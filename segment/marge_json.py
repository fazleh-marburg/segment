import json
import os

def add_rects_to_image_json(summary_json_path, details_json_path, output_path):
    """
    Merge image rectangles (rects) from the detailed JSON into the main image summary JSON.

    Args:
        summary_json_path (str): Path to JSON containing "Main Image" entries.
        details_json_path (str): Path to JSON containing "images" with "rects".
        output_path (str): Where to save the merged JSON.
    """
    # --- Load both JSON files ---
    with open(summary_json_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    with open(details_json_path, "r", encoding="utf-8") as f:
        details_data = json.load(f)

    # --- Build quick lookup for image rects ---
    rect_lookup = {
        img["file"]: img.get("rects", [])
        for img in details_data.get("images", [])
    }

    # --- Merge rects into summary entries ---
    for entry in summary_data:
        main_img = entry.get("Main Image")
        if main_img in rect_lookup:
            entry["rects"] = rect_lookup[main_img]
        else:
            entry["rects"] = []  # fallback if image not found

    # --- Save merged output ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Merged JSON saved to: {output_path}")


# ----------------- Example usage -----------------
if __name__ == "__main__":
    summary_json = "/home/melahi/code/image/segment/documents/output/book_Bruggen_Israels_Machtelt_Piero_del_all_image_objects_similarities_final.json"
    details_json = "/home/melahi/code/image/segment/documents/output/book_Bruggen_Israels_Machtelt_Piero_del.json"
    output_json = "/home/melahi/code/image/segment/documents/output/merged_image_rects.json"

    add_rects_to_image_json(summary_json, details_json, output_json)
