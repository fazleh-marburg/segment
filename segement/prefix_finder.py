import os

def list_pdf_filenames(folder_path):
    """
    Returns a list of PDF filenames (without .pdf extension)
    from the given folder.
    """
    return [
        os.path.splitext(filename)[0]
        for filename in os.listdir(folder_path)
        if filename.lower().endswith(".pdf")
    ]

def main():
    folder_path = "/home/melahi/code/image/segment-anything/documents/input/"
    pefixes = list_pdf_filenames(folder_path)

    print("PDF files found:")
    for prefix in pefixes:
        print(f"- {prefix}")

if __name__ == "__main__":
    main()

