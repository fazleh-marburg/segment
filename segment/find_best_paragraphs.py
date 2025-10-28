import json
from typing import List, Dict, Any


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the best paragraph results to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

def find_best_paragraphs(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find the best paragraph (highest similarity) for each image, considering only paragraphs with >3 words."""
    results = []

    for entry in data:
        main_img = entry["main_image"]

        for img in entry["Images"]:
            image_name = img["Image"]

            # Filter paragraphs with more than 3 words in 'Cleaned Text'
            valid_paragraphs = [
                p for p in img["Ranked Paragraphs"]
                if len(p["Cleaned Text"].split()) > 3
            ]

            if not valid_paragraphs:
                # If no valid paragraphs, skip this image
                continue

            # Find the paragraph with the highest similarity among valid ones
            best_paragraph = max(valid_paragraphs, key=lambda x: x["Similarity"])

            results.append({
                "Main Image": main_img,
                "Image": image_name,
                "Best Paragraph Page": best_paragraph["Page"],
                "Best Paragraph Number": best_paragraph["Paragraph"],
                "Best Paragraph Text": best_paragraph["Cleaned Text"],
                "Best Paragraph Original Text": best_paragraph["Original Text"],
                "Similarity": best_paragraph["Similarity"]
            })

    return results


def print_results(results: List[Dict[str, Any]]) -> None:
    """Print best paragraph results in a readable format."""
    if not results:
        print("No valid paragraphs found (more than 3 words).")
        return

    for r in results:
        print(f"Image: {r['Image']}")
        print(f" → Best Paragraph (Page {r['Best Paragraph Page']}, #{r['Best Paragraph Number']}):")
        print(f"   {r['Best Paragraph Text']}")
        print(f"   Similarity: {r['Similarity']:.3f}\n")


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save the best paragraph results to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


def main(input_path: str, output_path: str = None) -> None:
    """Main function to load data, find best paragraphs, and output results."""
    data = load_json(input_path)
    results = find_best_paragraphs(data)
    print_results(results)

    if output_path:
        save_results(results, output_path)
        print(f"\n✅ Results saved to: {output_path}")


if __name__ == "__main__":
    # Example usage
    dir = "/documents/"
    image_dir = dir + "input/"
    segment_dir = dir + "segmented_objects/"
    output_dir = dir + "output/"
    main(output_dir+"input.json", "best_paragraphs.json")
