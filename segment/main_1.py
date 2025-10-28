import torch
from PIL import Image
import clip
import json
import nltk
from nltk.corpus import stopwords
from typing import Dict, Tuple
import re
from typing import List
from extract_pdf import process_pdf, read_paragraphs_from_json
import spacy
from find_best_paragraphs import find_best_paragraphs,save_results,load_json,print_results
from aggregate_most_fre_para import find_most_frequent_paragraphs
from arch.highlight_para_1 import highlight_paragraphs,extract_page_and_image,highlight_image,parse_bbox
from fileUtils import find_images,find_subimages_for_images
from paragraph import is_valid_paragraph
from marge_json import  add_rects_to_image_json
import os
from object_extract import process_folder
import fitz  # PyMuPDF

nlp = spacy.load("en_core_web_sm")

# Download stopwords (only first time)
nltk.download("stopwords")
STOPWORDS = set(stopwords.words("english"))

def is_sentence(text):
    text = text.strip()
    return bool(text) and text[0].isupper() and text.endswith(('.', '!', '?')) and len(text.split()) > 1



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

def process_images_and_paragraphs(main_img, sub_imgs, segment_dir,paragraphs, model, preprocess, device, output_dir,page_num,book):
    """Compute image ↔ paragraph similarities and save all results to one JSON file."""

    # Unpack cleaned texts for CLIP
    cleaned_texts = [p[3] for p in paragraphs]
    tokenized_texts = tokenize_with_truncate(cleaned_texts, device)

    with torch.no_grad():
        text_features = model.encode_text(tokenized_texts)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    global_results = []  # 🧩 collect ALL results here
    all_results = []  # 🧩 store all image results

    # Print results
    for fileName in sub_imgs:
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

"""
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
"""



def main(segment_dir,output_dir,prefix,paragraph_json):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = load_clip_model(device)

    # read the json files
    json_path = os.path.join(output_dir, f"{prefix}.json")
    print(json_path)

    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return

    global_results = []  # 🧩 collect ALL results here
    paragraphs = []

    paragraphs_by_page = read_paragraphs_from_json(json_path)

    index=1
    for page_number, paras in paragraphs_by_page.items():
        print(f"--- Page {page_number} ---")
        for para_index, para in enumerate(paras, start=1):
            text = para["text"]  # extract string from dict
            if not (is_valid_paragraph(text)):
                continue
            cleaned = clean_text(text)  # now safe
            paragraphs.append((page_number, para_index, para, cleaned))
            print(text)
            index=index+1

    print(f"✅ Loaded {len(paragraphs)} cleaned paragraphs "+str(index))
    # Find main images
    main_images = find_images(output_dir, prefix)

    # Find subimages corresponding to each main image
    image_to_subimages = find_subimages_for_images(main_images, segment_dir)

    # Print results
    for main_img, sub_imgs in image_to_subimages.items():
        print(f"\nMain image: {os.path.basename(main_img)}")
        all_results = process_images_and_paragraphs(main_img, sub_imgs,segment_dir,paragraphs, model, preprocess, device,
                                                     output_dir, page_number, prefix)
        global_results.append({
            "main_image": main_img,
            "Images": all_results
        })
    return global_results

def find_best(all_similarities_json,best_similarities_json,final_summary_json,final_output_json,
                     global_results, paragraph_json):

    # 📝 Write everything to ONE big JSON file
    #all_similarities_json = os.path.join(output_dir, f"{prefix}_similarities.json")
    #best_similarities_json = all_similarities_json.replace("similarities", "best")
    #final_summary_json = all_similarities_json.replace("similarities", "final")
    #final_output_json = final_summary_json.replace("final", "final_image_text")



    with open(all_similarities_json, "w", encoding="utf-8") as json_file:
        json.dump(global_results, json_file, ensure_ascii=False, indent=4)


    data = load_json(all_similarities_json)
    results = find_best_paragraphs(data)
    print_results(results)

    if best_similarities_json:
        save_results(results, best_similarities_json)
        print(f"\n✅ Results saved to: {best_similarities_json}")


    data = load_json(best_similarities_json)
    results = find_most_frequent_paragraphs(data)
    save_results(results, final_summary_json)
    print(f"✅ Results saved to {final_summary_json}")


    add_rects_to_image_json(final_summary_json, paragraph_json, final_output_json)


if __name__ == "__main__":
    # Path to the input directory containing PDF files
    dir = "/documents/"
    image_dir = dir + "input/"
    segment_dir = dir + "segmented_objects/"
    output_dir = dir + "output/"

    # --- Add menu option ---
    menu = 0


    # Loop through all files in the directory
    for pdf_file in os.listdir(image_dir):
        if pdf_file.lower().endswith(".pdf"):
            print(f"\n=== Reading: {pdf_file} ===")

            prefix = pdf_file.replace(".pdf", "")
            pdf_path = os.path.join(image_dir, pdf_file)
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            marked_output_pdf = os.path.join(output_dir, f"marked_{pdf_name}.pdf")
            paragraph_json = os.path.join(output_dir, f"{pdf_name}.json")

            # --- Step 1: Extract images and paragraphs from PDF ---
            process_pdf(pdf_path, output_dir, marked_output_pdf, paragraph_json)

            # --- Step 2: Run process_folder only if menu == 1 ---
            if menu == 1:
                print("\n🧩 Running process_folder (segmenting objects)...")
                process_folder(
                    input_folder=output_dir,
                    output_dir=segment_dir,
                    checkpoint_path=dir + "models/sam_vit_h_4b8939.pth",
                    model_type="vit_h"
                )
            else:
                print("\n⏭️ Skipping process_folder.")

            # --- Step 3: Run CLIP similarity and highlight best paragraphs ---
            global_results = main(segment_dir, output_dir, prefix, paragraph_json)
            # --- Step 4: highlight the
            # 📝 Write everything to ONE big JSON file
            all_similarities_json = os.path.join(output_dir, f"{prefix}_similarities.json")
            best_similarities_json = all_similarities_json.replace("similarities", "best")
            final_summary_json = all_similarities_json.replace("similarities", "final")
            final_output_json = final_summary_json.replace("final", "final_image_text")
            output_pdf="outlined_output_" + prefix + ".pdf"
            find_best(all_similarities_json,best_similarities_json,final_summary_json,final_output_json,
                       global_results,  paragraph_json)

            #highlight_paragraphs(pdf_path=image_dir + pdf_file,json_path=final_summary_json,output_path=output_dir + output_pdf)
            with open(final_output_json, "r") as f:
                data = json.load(f)

            # --- Extract info ---
            for entry in data:
                page_num = entry.get("Most Frequent Page", 1) - 1  # PyMuPDF uses 0-based indexing
                bbox = parse_bbox(entry.get("Representative Original Text", ""))
                rect = fitz.Rect(*bbox)
                doc = fitz.open(pdf_path)
                # Define outline color (red)
                red = (1, 0, 0)
                try:
                    page = doc.load_page(page_num)

                    # Add a red rectangular outline (no fill)
                    annot = page.add_rect_annot(rect)
                    annot.set_colors(stroke=red, fill=None)
                    annot.set_border(width=1.5)  # thickness of the outline
                    annot.update()

                    print(f"✅ Outlined paragraph on Page {page_num + 1}: {entry['Representative Text'][:60]}...")
                except Exception as e:
                    print(f"⚠️ Could not outline Page {page_num + 1}: {e}")

                # Save the output PDF
                doc.save(output_pdf, deflate=True)
                doc.close()
                print(f"\n💾 Saved outlined PDF to: {output_pdf}")
                exit(1)
                main_image = entry["Main Image"]
                page_number, image_number = extract_page_and_image(main_image)
                print(f"🔹 Found: Page {page_number}, Image {image_number}")

                highlight_paragraphs(entry,page_num,rect,doc,output_pdf,red)
                highlight_image(image_dir+pdf_file, page_number, image_number, output_pdf)

