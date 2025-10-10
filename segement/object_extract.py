import os
import cv2
import torch
import numpy as np
from glob import glob
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator


# ------------------------------
# Configuration
# ------------------------------
def load_sam_model(checkpoint_path: str, model_type: str = "vit_h", device: str = None):
    """Load the SAM model from a checkpoint."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"🔧 Loading SAM model ({model_type}) on {device}...")
    sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
    sam.to(device=device)
    return sam


def get_input_files(input_folder: str, pattern: str = "input_*"):
    """Find all input images matching a given pattern."""
    input_pattern = os.path.join(input_folder, pattern)
    input_files = glob(input_pattern)
    if not input_files:
        raise FileNotFoundError(f"❌ No files found matching pattern: {input_pattern}")
    print(f"✅ Found {len(input_files)} input images.")
    return input_files


def create_output_dir(output_dir: str):
    """Ensure the output directory exists."""
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def generate_masks(image: np.ndarray, sam_model) -> list:
    """Generate masks for an image using the SAM model."""
    mask_generator = SamAutomaticMaskGenerator(sam_model)
    masks = mask_generator.generate(image)
    return masks


def segment_and_save_objects(image_path: str, sam_model, output_dir: str):
    """Segment all objects in an image and save them as separate files."""
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    print(f"\n🔹 Processing {base_name}...")

    # Read and convert image
    image = cv2.imread(image_path)
    if image is None:
        print(f"⚠️ Skipping {image_path} (could not read)")
        return
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Generate masks
    masks = generate_masks(image, sam_model)
    print(f"   Found {len(masks)} objects")

    # Save each segmented object
    for i, mask_data in enumerate(masks):
        mask = mask_data["segmentation"]
        masked_img = np.zeros_like(image)
        masked_img[mask] = image[mask]

        y, x = np.where(mask)
        if len(x) == 0 or len(y) == 0:
            continue
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        cropped_obj = masked_img[y_min:y_max, x_min:x_max]

        # Output filename
        base_name_out = base_name.replace("input", "output")
        output_path = os.path.join(output_dir, f"{base_name_out}_object_{i + 1:03d}.png")
        cv2.imwrite(output_path, cv2.cvtColor(cropped_obj, cv2.COLOR_RGB2BGR))
        print(f"   💾 Saved {output_path}")


def process_folder(
        input_folder: str,
        output_dir: str,
        checkpoint_path: str,
        model_type: str = "vit_h"
):
    """Main function to process all input images in a folder."""
    # Load model
    sam_model = load_sam_model(checkpoint_path, model_type)

    # Get input files
    input_files = get_input_files(input_folder)

    # Ensure output directory exists
    create_output_dir(output_dir)

    # Process each file
    for image_path in input_files:
        segment_and_save_objects(image_path, sam_model, output_dir)

    print("\n✅ All images processed successfully!")


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    dir = "/home/melahi/code/image/segment-anything/documents/"
    process_folder(
        input_folder=dir+"input/",
        output_dir=dir+"segmented_objects/",
        checkpoint_path=dir+"models/sam_vit_h_4b8939.pth",
        model_type="vit_h"
    )
