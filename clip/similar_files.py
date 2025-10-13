import os
from collections import defaultdict

def strip_extensions(filename):
    """
    Strips all extensions from a filename (e.g., 'file.jpeg.csv' -> 'file')
    """
    while '.' in filename:
        filename = filename.rsplit('.', 1)[0]
    return filename

def find_similar_named_files(directory):
    """
    Groups files that have the same base name (excluding all extensions).
    """
    file_groups = defaultdict(list)

    for file_name in os.listdir(directory):
        full_path = os.path.join(directory, file_name)
        if os.path.isfile(full_path):
            base_name = strip_extensions(file_name)
            file_groups[base_name].append(file_name)

    print("=== Files with same base name (partial match) ===")
    for base_name, files in file_groups.items():
        if len(files) > 1:
            print(f"\nGroup: {base_name}")
            for f in files:
                print(" -", f)

def main():
    directory = "/home/melahi/code/marburg/images/Gipsy/"  # 🔁 Replace with your folder path
    if not os.path.isdir(directory):
        print(f"Error: directory not found: {directory}")
        return

    find_similar_named_files(directory)

if __name__ == "__main__":
    main()
