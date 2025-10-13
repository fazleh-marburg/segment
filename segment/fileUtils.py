import os
import glob
from collections import defaultdict

def find_images(folder_path, base_name):
    """
    Find all main image files in the given folder that contain the base name.

    Parameters:
        folder_path (str): Path to the folder containing images.
        base_name (str): Substring to search for in file names.

    Returns:
        list[str]: List of matching image file paths.
    """
    pattern = os.path.join(folder_path, f"*{base_name}*.jpeg")
    image_files = glob.glob(pattern)
    return sorted(image_files)


def find_subimages_for_images(main_images, subimage_folder):
    """
    For each main image, find all subimages in the subimage folder that match its page/img pattern.

    Parameters:
        main_images (list[str]): List of paths to main images.
        subimage_folder (str): Path to folder containing subimages.

    Returns:
        dict[str, list[str]]: Mapping from main image → list of matching subimages.
    """
    mapping = defaultdict(list)
    subimage_files = glob.glob(os.path.join(subimage_folder, "*.png"))

    for main_img in main_images:
        main_filename = os.path.basename(main_img)
        parts = main_filename.split(".")
        page_pattern = parts[0]
        page_pattern=page_pattern.replace("input_","")
        print(page_pattern)
        # Find subimages that match the page/img pattern
        for sub_img in subimage_files:
            if page_pattern in os.path.basename(sub_img):
                mapping[main_img].append(sub_img)
                print(main_img+" "+ sub_img)

    return dict(mapping)


# Example usage:
if __name__ == "__main__":
    main_folder = "/home/melahi/code/image/segment/documents/output/"
    sub_folder = "/home/melahi/code/image/segment/documents/segmented_objects/"
    base_name = "book_Bruggen_Israels_Machtelt_Piero_del"

    # Find main images
    main_images = find_images(main_folder, base_name)

    # Find subimages corresponding to each main image
    image_to_subimages = find_subimages_for_images(main_images, sub_folder)

    # Print results
    for main_img, sub_imgs in image_to_subimages.items():
        print(f"\nMain image: {os.path.basename(main_img)}")
        for sub in sub_imgs:
            print(f"  ↳ {os.path.basename(sub)}")
