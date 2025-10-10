import os
import torch
import csv
from PIL import Image
import clip
import json
import nltk
from nltk.corpus import stopwords
from typing import Dict, List, Tuple
import os
import re
from typing import List
from find_result import find_best_similarities,find_most_frequent_page_paragraph
from object_extract import process_folder
from extract_pdf import extract_images_and_text




# Download stopwords (only first time)
nltk.download("stopwords")
STOPWORDS = set(stopwords.words("english"))

def clean_text(text):
    """
    Remove stopwords, punctuation, digits, and short words from a string.
    """
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)   # keep only letters & spaces
    tokens = text.split()
    filtered = [w for w in tokens if w not in STOPWORDS and len(w) > 2]
    return " ".join(filtered)

def load_clip_model(device="cuda"):
    """Load CLIP model + preprocess function"""
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess

def get_image_files(image_directory, valid_extensions):
    """Get valid image file paths"""
    image_files = []
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(valid_extensions):
            filepath = os.path.join(image_directory, filename)
            try:
                with Image.open(filepath) as _:
                    image_files.append(filepath)
            except Exception as e:
                print(f"⚠️ Failed to open {filename}: {e}")
    return image_files

def tokenize_with_truncate(texts, device):
    """Tokenize texts safely (truncate if >77 tokens)."""
    return clip.tokenize(texts, truncate=True).to(device)



def list_book_images_by_page(folder_path: str, book_id: str) -> Dict[int, List[Tuple[int, int, str]]]:
    """
    Find and group all segmented images for a given book, organized by page number.

    Args:
        folder_path (str): Path to the folder containing the segmented image files.
        book_id (str): Unique identifier string for the book (e.g. 'book_Bruggen_Israels_Machtelt_Piero_del').

    Returns:
        Dict[int, List[Tuple[int, int, str]]]:
            Dictionary where keys are page numbers and values are lists of (img_num, obj_num, filename) tuples.
    """
    # Regex pattern dynamically based on the given book_id
    pattern = re.compile(
        rf"output_{re.escape(book_id)}_page(\d+)_img(\d+)_object_(\d+)\.png"
    )

    pages: Dict[int, List[Tuple[int, int, str]]] = {}

    # Iterate over files in the folder
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            page_num = int(match.group(1))
            img_num = int(match.group(2))
            obj_num = int(match.group(3))
            pages.setdefault(page_num, []).append((img_num, obj_num, filename))

    return pages



def find_images_for_book_page(folder_path: str, book_id: str, page_number: int) -> List[str]:
    """
    Return all image filenames for a given book and page number.

    Args:
        folder_path (str): Path to the folder containing images.
        book_id (str): Book identifier string, e.g., "book_Bruggen_Israels_Machtelt_Piero_del".
        page_number (int): Page number to find images for.

    Returns:
        List[str]: List of matching image filenames.
    """
    # Regex pattern: match book, page number, and any image/object number
    pattern = re.compile(
        rf"output_{re.escape(book_id)}_page{page_number}_img\d+_object_\d+\.png"
    )

    # List all matching files
    matching_files = [f for f in os.listdir(folder_path) if pattern.fullmatch(f)]

    # Sort results for consistency
    matching_files.sort()

    return matching_files

def process_images_and_paragraphs(segment_dir, image_files, paragraphs, model, preprocess, device, output_dir,page_num,book):
    """Compute image ↔ paragraph similarities and save all results to one JSON file."""

    # Unpack cleaned texts for CLIP
    cleaned_texts = [p[3] for p in paragraphs]
    tokenized_texts = tokenize_with_truncate(cleaned_texts, device)

    with torch.no_grad():
        text_features = model.encode_text(tokenized_texts)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    all_results = []  # 🧩 store all image results

    for fileName in image_files:
        print(f"\n📷 Processing Image: {fileName}")
        file_path = os.path.join(segment_dir, fileName)

        image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            sims = (image_features @ text_features.T).squeeze(0).cpu().numpy()

        # Attach metadata: (page, para_index, original_text, cleaned_text, similarity)
        ranked = sorted(
            [(para[0], para[1], para[2], para[3], float(sims[i])) for i, para in enumerate(paragraphs)],
            key=lambda x: x[4],
            reverse=True
        )

        # Print top-5
        for page, para_index, orig_text, cleaned_text, score in ranked[:5]:
            print(f"\n--- Page {page}, Paragraph {para_index} ---")
            print(f"Similarity: {score:.4f}")
            print(f"Paragraph: {orig_text}\n")

        # Store all results
        all_results.append({
            "Image": fileName,
            "Ranked Paragraphs": [
                {
                    "Page": int(page),
                    "Paragraph": int(para_index),
                    "Original Text": str(orig_text),
                    "Cleaned Text": str(cleaned_text),
                    "Similarity": float(score)
                }
                for page, para_index, orig_text, cleaned_text, score in ranked
            ]
        })

    return all_results
    # 📝 Save all image results in one JSON file
    #outputfile_json = os.path.join(output_dir, str(book)+"_"+"page"+str(page_num)+"_"+"all_images"+".json")
    #with open(outputfile_json, "w", encoding="utf-8") as json_file:
    #    json.dump(all_results, json_file, ensure_ascii=False, indent=4)

    #print(f"\n✅ All results saved to: {outputfile_json}")

# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    folder = "/home/melahi/code/image/marburg/documents/segmented_objects/"
    book = "book_Bruggen_Israels_Machtelt_Piero_del"
    page = 2  # Page number to find

    images = find_images_for_book_page(folder, book, page)
    print(f"Images for {book} page {page}:")
    for img in images:
        print(" ", img)


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = load_clip_model(device)


    pdf_file = "book_Bruggen_Israels_Machtelt_Piero_del.pdf"
    prefix = pdf_file.replace(".pdf", "")
    dir = "/home/melahi/code/image/marburg/documents/"
    image_dir =  dir+"input/"
    segment_dir=dir + "segmented_objects/"
    output_dir = dir+ "output/"
    os.makedirs(output_dir, exist_ok=True)

    # form a pdf file extract text and images.
    extract_images_and_text(image_dir)

    # find all objects present in the images
    process_folder(input_folder=image_dir,output_dir=segment_dir,checkpoint_path=dir + "models/sam_vit_h_4b8939.pth",model_type="vit_h")

    # read the json files
    json_path = os.path.join(image_dir, f"{prefix}.json")
    print(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)


    book = "book_Bruggen_Israels_Machtelt_Piero_del"
    global_results = []  # 🧩 collect ALL results here


    paragraphs = []

    for page_data in data:  # page_data is the dict containing 'page' and 'paragraphs'
        page_num = page_data.get("page")

        # Use page_num to find image files
        image_files = find_images_for_book_page(segment_dir, book, page_num)
        print(f"Images for {book} page {page_num}:")

        # If no images are found, skip this page
        if not image_files:
            print(f"⚠️ No images found for {book} page {page_num}, skipping...")
            continue

        for img in image_files:
            print(" ", img)

        # Iterate over paragraphs
        for para_index, para in enumerate(page_data.get("paragraphs", []), start=1):
            cleaned = clean_text(para)
            if cleaned.strip():
                # Store (page, paragraph_index, original_text, cleaned_text)
                paragraphs.append((page_num, para_index, para, cleaned))
                print(str(page_num) + " " + str(para_index) + " ")

        print(f"✅ Loaded {len(paragraphs)} cleaned paragraphs")
        page_results=process_images_and_paragraphs(segment_dir,image_files, paragraphs, model, preprocess, device, output_dir,page_num,book)
        global_results.append({
            "main_image": f"{book}_page{page_num}",
            "Images": page_results
        })

    # 📝 Write everything to ONE big JSON file
    all_similarities_json = os.path.join(output_dir, f"{book}_all_image_objects_similarities.json")
    with open(all_similarities_json, "w", encoding="utf-8") as json_file:
        json.dump(global_results, json_file, ensure_ascii=False, indent=4)

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

    print(f"\n✅ All results saved to: {all_similarities_json}")

    best_similarities_json= all_similarities_json.replace("similarities","similarities_best")
    best_matches = find_best_similarities(all_similarities_json, best_similarities_json)

    # Print summary
    for r in best_matches:
        print(f"Main Image: {r['main_image']}")
        print(f"  Image: {r['image']}")
        print(f"  Best Match: Page {r['best_page']}, Paragraph {r['best_paragraph']}")
        print(f"  Similarity: {r['best_similarity']:.3f}")
        print(f"  Text: {r['original_text']}\n")


if __name__ == "__main__":
    main()
