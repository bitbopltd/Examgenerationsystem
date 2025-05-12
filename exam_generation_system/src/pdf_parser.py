import subprocess
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a given PDF file using pdftotext.

    Args:
        pdf_path (str): The absolute path to the PDF file.

    Returns:
        str: The extracted text content from the PDF, or None if an error occurs.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    try:
        # Use pdftotext to extract text. The '-' outputs to stdout.
        # -layout: maintain original physical layout
        # -nopgbrk: don't insert page breaks
        # -enc UTF-8: specify UTF-8 encoding
        result = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", "-enc", "UTF-8", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error during PDF text extraction: {e}")
        print(f"pdftotext stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: pdftotext command not found. Ensure poppler-utils is installed.")
        return None

# Example usage (can be removed or commented out in production code)
if __name__ == '__main__':
    # Create a dummy PDF for testing if it doesn't exist
    # In a real scenario, this test PDF would be one of the uploaded books.
    # For now, we'll assume a test PDF exists or this part is for illustration.
    test_pdf_path = "/home/ubuntu/upload/Bio 9th Unit 9.pdf" # Using the provided sample book
    if os.path.exists(test_pdf_path):
        print(f"Attempting to extract text from: {test_pdf_path}")
        extracted_text = extract_text_from_pdf(test_pdf_path)
        if extracted_text:
            print("\n--- Extracted Text (First 500 chars) ---")
            print(extracted_text[:500])
            print("\n--- End of Preview ---")
        else:
            print("Failed to extract text.")
    else:
        print(f"Test PDF not found at {test_pdf_path}. Skipping example usage.")

