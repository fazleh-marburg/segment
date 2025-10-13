import json
from collections import Counter, defaultdict
import os

def find_best_similarities(input_path: str, output_path: str = None):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for entry in data:
        main_image = entry["main_image"]
        for img in entry["Images"]:
            ranked_paragraphs = img.get("Ranked Paragraphs", [])
            if not ranked_paragraphs:
                # Skip images with no paragraphs
                print(f"⚠️ No ranked paragraphs for image: {img.get('Image')}")
                continue

            best_paragraph = max(ranked_paragraphs, key=lambda p: p["Similarity"])
            results.append({
                "main_image": main_image,
                "image": img.get("Image"),
                "best_page": best_paragraph["Page"],
                "best_paragraph": best_paragraph["Paragraph"],
                "best_similarity": best_paragraph["Similarity"],
                "original_text": best_paragraph["Original Text"]
            })

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Best similarities saved to '{output_path}'")

    return results



def find_most_frequent_page_paragraph(input_path: str, output_path: str = None):
    """
    Reads summarized similarity results and finds the most frequent (page, paragraph)
    pair for each main_image. Optionally saves to a JSON file including paragraph text.
    """
    # Step 1: Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Step 2: Count occurrences of (page, paragraph) per main_image
    freq_dict = defaultdict(list)
    text_lookup = defaultdict(dict)

    for item in data:
        key = (item["best_page"], item["best_paragraph"])
        freq_dict[item["main_image"]].append(key)
        # Store text for this (page, paragraph)
        text_lookup[item["main_image"]][key] = item["original_text"]

    # Step 3: Compute most frequent (page, paragraph)
    results = []
    for main_img, pairs in freq_dict.items():
        counter = Counter(pairs)
        most_common_pair, count = counter.most_common(1)[0]
        page, paragraph = most_common_pair
        text = text_lookup[main_img].get(most_common_pair, "")
        results.append({
            "main_image": main_img,
            "most_frequent_page": page,
            "most_frequent_paragraph": paragraph,
            "frequency": count,
            "paragraph_text": text
        })

    # Step 4: Optionally save to a file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Most frequent page/paragraph results saved to '{output_path}'")

    return results


# Example usage:
if __name__ == "__main__":
    dir = "/home/melahi/code/image/segment-anything/documents/"
    output_dir = os.path.join(dir, "output/")
    book = "book_Bruggen_Israels_Machtelt_Piero_del"

    all_similarities_json = os.path.join(output_dir, f"{book}_all_image_objects_similarities.json")
    best_similarities_json = all_similarities_json.replace("similarities", "similarities_best")
    final_summary_json = all_similarities_json.replace("similarities", "similarities_final")

    # Step 1: Find best matches per image
    best_matches = find_best_similarities(all_similarities_json, best_similarities_json)

    # Step 2: Print summary of best matches
    for r in best_matches:
        print(f"Main Image: {r['main_image']}")
        print(f"  Image: {r['image']}")
        print(f"  Best Match: Page {r['best_page']}, Paragraph {r['best_paragraph']}")
        print(f"  Similarity: {r['best_similarity']:.3f}")
        print(f"  Text: {r['original_text']}\n")

    # Step 3: Find most frequent page/paragraph and save results (with paragraph text)
    results = find_most_frequent_page_paragraph(best_similarities_json, final_summary_json)

    # Step 4: Print results
    for r in results:
        print(f"Main Image: {r['main_image']}")
        print(f"  Most Frequent Page: {r['most_frequent_page']}")
        print(f"  Most Frequent Paragraph: {r['most_frequent_paragraph']}")
        print(f"  Occurrences: {r['frequency']}")
        print(f"  Paragraph Text: {r['paragraph_text']}\n")
