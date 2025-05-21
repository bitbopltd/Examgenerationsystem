
import PyPDF2
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a given PDF file using PyPDF2.

    Args:
        pdf_path (str): The absolute path to the PDF file.

    Returns:
        str: The extracted text content from the PDF, or None if an error occurs.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()

        if not text.strip():
            print("Warning: Extracted text is empty. The PDF might be image-based.")
            return None

        return text
    except Exception as e:
        print(f"Error during PDF text extraction: {e}")
        return None

# Example usage (can be removed or commented out in production code)
if __name__ == '__main__':
    test_pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'test.pdf')
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
