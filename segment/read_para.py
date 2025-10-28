import json
import os
from typing import Dict, List


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


def main():
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
