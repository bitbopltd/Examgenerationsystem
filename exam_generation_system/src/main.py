# main.py
import sys
import os
# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(__file__)) # Add src to path for module imports

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename
import datetime

# Import custom modules
from pdf_parser import extract_text_from_pdf
from ai_question_generator import generate_questions_from_text # Placeholder
from exam_formatter import format_exam_paper

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads') # /home/ubuntu/exam_generation_system/uploads
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {"pdf"}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_available_books():
    if not os.path.exists(UPLOAD_FOLDER):
        return []
    return [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and f.endswith(".pdf")]

@app.route("/", methods=["GET", "POST"])
def index():
    available_books = get_available_books()
    generated_paper_content = None
    error_message = None
    paper_filename_to_download = None
    selected_book_on_post = None
    exam_details_on_post = {}
    question_config_on_post = {}

    if request.method == "POST":
        selected_book_on_post = request.form.get("existing_book")
        exam_details_on_post = {
            "school_name": request.form.get("school_name"),
            "exam_title": request.form.get("exam_title"),
            "class_level": request.form.get("class_level"),
            "subject": request.form.get("subject"),
            "total_time": request.form.get("total_time"),
            "version": request.form.get("version")
        }
        question_config_on_post = {
            "num_mcq": int(request.form.get("num_mcq", 0)),
            "num_short_answer": int(request.form.get("num_short_answer", 0)),
            "num_long_answer": int(request.form.get("num_long_answer", 0))
        }

        book_path = None
        book_filename = None

        # Handle file upload
        if "book_file" in request.files:
            file = request.files["book_file"]
            if file.filename != "":
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    book_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(book_path)
                    book_filename = filename
                    available_books = get_available_books() # Refresh list
                    selected_book_on_post = filename # Select the newly uploaded book
                else:
                    error_message = "Invalid file type. Only PDF files are allowed."
                    return render_template("index.html", available_books=available_books, error_message=error_message, selected_book=selected_book_on_post, exam_details=exam_details_on_post, question_config=question_config_on_post)
            elif request.form.get("existing_book"):
                book_filename = request.form.get("existing_book")
                book_path = os.path.join(app.config["UPLOAD_FOLDER"], book_filename)
            else:
                error_message = "Please upload a new book or select an existing one."
                return render_template("index.html", available_books=available_books, error_message=error_message, selected_book=selected_book_on_post, exam_details=exam_details_on_post, question_config=question_config_on_post)
        elif request.form.get("existing_book"):
            book_filename = request.form.get("existing_book")
            book_path = os.path.join(app.config["UPLOAD_FOLDER"], book_filename)
        else:
            error_message = "No book selected or uploaded."
            return render_template("index.html", available_books=available_books, error_message=error_message, selected_book=selected_book_on_post, exam_details=exam_details_on_post, question_config=question_config_on_post)

        if not book_path or not os.path.exists(book_path):
            error_message = f"Selected book '{book_filename}' not found."
            return render_template("index.html", available_books=available_books, error_message=error_message, selected_book=selected_book_on_post, exam_details=exam_details_on_post, question_config=question_config_on_post)

        # 1. Extract text from PDF
        extracted_text = extract_text_from_pdf(book_path)
        if extracted_text is None:
            error_message = f"Failed to extract text from {book_filename}. The PDF might be image-based or corrupted."
            return render_template("index.html", available_books=available_books, error_message=error_message, selected_book=selected_book_on_post, exam_details=exam_details_on_post, question_config=question_config_on_post)
        
        if not extracted_text.strip():
             error_message = f"Extracted text from {book_filename} is empty. The PDF might be image-based or scanned. Please use a text-based PDF."
             # Still proceed to show the template with the error

        # 2. Generate Questions (using placeholder)
        questions_data = generate_questions_from_text(
            text_content=extracted_text,
            num_mcq=question_config_on_post["num_mcq"],
            num_short_answer=question_config_on_post["num_short_answer"],
            num_long_answer=question_config_on_post["num_long_answer"],
            subject=exam_details_on_post.get("subject", "N/A"),
            grade_level=exam_details_on_post.get("class_level", "N/A")
        )

        # 3. Format Exam Paper
        # Define section configurations (can be made more dynamic later)
        total_mcq_marks = question_config_on_post["num_mcq"] * 1 # Assuming 1 mark per MCQ
        total_short_marks = question_config_on_post["num_short_answer"] * 4 # Assuming 4 marks per short q
        total_long_marks = question_config_on_post["num_long_answer"] * 8 # Assuming 8 marks per long q
        total_exam_marks = total_mcq_marks + total_short_marks + total_long_marks
        exam_details_on_post["total_marks"] = total_exam_marks
        
        section_config = {
            "A": {
                "title": "SECTION A",
                "instructions": "Attempt this section on the MCQ’s Answer Sheet only. Use black ball point or marker for shading only one circle for correct option of a question. No mark will be awarded for cutting, erasing, over writing and multiple circles shading.",
                "time_allowed": "20 Minutes", # Placeholder, can be dynamic
                "marks_per_question": 1,
                "total_marks_section": total_mcq_marks
            },
            "B": {
                "title": "SECTION B",
                "instructions": f"Attempt any {question_config_on_post['num_short_answer']} questions. Each question carries equal marks.",
                "marks_per_question": 4, 
                "total_marks_section": total_short_marks
            },
            "C": {
                "title": "SECTION C",
                "instructions": f"Attempt any {question_config_on_post['num_long_answer']} questions. Each question carries equal marks.",
                "marks_per_question": 8,
                "total_marks_section": total_long_marks
            }
        }

        generated_paper_content = format_exam_paper(exam_details_on_post, questions_data, section_config)
        
        # Prepare filename for download
        subject_sanitized = exam_details_on_post.get("subject", "exam").replace(" ", "_")
        class_sanitized = exam_details_on_post.get("class_level", "paper").replace(" ", "_")
        paper_filename_to_download = f"{subject_sanitized}_{class_sanitized}_paper_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"

    return render_template(
        "index.html", 
        available_books=available_books, 
        generated_paper=generated_paper_content, 
        error_message=error_message,
        paper_filename=paper_filename_to_download,
        selected_book=selected_book_on_post,
        exam_details=exam_details_on_post,
        question_config=question_config_on_post
    )

@app.route("/download_exam", methods=["POST"])
def download_exam():
    paper_content = request.form.get("paper_content")
    paper_filename = request.form.get("paper_filename", "exam_paper.txt")
    if paper_content:
        response = make_response(paper_content)
        response.headers["Content-Disposition"] = f"attachment; filename={secure_filename(paper_filename)}"
        response.headers["Content-Type"] = "text/plain"
        return response
    return redirect(url_for("index"))

if __name__ == "__main__":
    # The Flask template uses `app.run(host='0.0.0.0', port=5000)`
    # We'll stick to that for consistency with the template's run command.
    app.run(host="0.0.0.0", port=5000, debug=True)

