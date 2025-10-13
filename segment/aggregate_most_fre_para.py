import json
from collections import Counter
from typing import List, Dict, Any


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_most_frequent_paragraphs(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find the most frequent (Best Paragraph Page, Best Paragraph Number)
    for each Main Image.
    """
    results = []

    # Group all entries by Main Image
    grouped = {}
    for entry in data:
        main_img = entry["Main Image"]
        key = (entry["Best Paragraph Page"], entry["Best Paragraph Number"])
        if main_img not in grouped:
            grouped[main_img] = []
        grouped[main_img].append({
            "PageParagraph": key,
            "Text": entry["Best Paragraph Text"],
            "Original": entry["Best Paragraph Original Text"],
            "Similarity": entry["Similarity"]
        })

    # For each main image, find the most frequent (Page, Paragraph)
    for main_img, entries in grouped.items():
        # Count frequency of (Page, Paragraph) pairs
        counts = Counter(e["PageParagraph"] for e in entries)
        most_common_pair, frequency = counts.most_common(1)[0]
        page, paragraph = most_common_pair

        # Find a representative paragraph text for this pair
        representative = next(
            (e for e in entries if e["PageParagraph"] == most_common_pair),
            None
        )

        results.append({
            "Main Image": main_img,
            "Most Frequent Page": page,
            "Most Frequent Paragraph": paragraph,
            "Frequency": frequency,
            "Representative Text": representative["Text"] if representative else "",
            "Representative Original Text": representative["Original"] if representative else ""
        })

    return results


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the results to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


def main(input_path: str, output_path: str = "most_frequent_page_paragraph.json") -> None:
    """Main function: load data, find most frequent paragraphs, and save results."""
    data = load_json(input_path)
    results = find_most_frequent_paragraphs(data)
    save_results(results, output_path)
    print(f"✅ Results saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    main("best_paragraphs.json", "most_frequent_page_paragraph.json")
