# exam_formatter.py

def format_exam_paper(exam_details, questions_data, section_config):
    """
    Formats the generated questions into a structured exam paper string.

    Args:
        exam_details (dict): Contains overall exam information like:
            "school_name": str,
            "exam_title": str,
            "class_level": str,
            "subject": str,
            "total_time": str, (e.g., "3:00 Hours")
            "total_marks": int,
            "version": str (e.g., "A")
        questions_data (dict): The output from ai_question_generator, containing:
            "mcq": list of dicts (question, options, correct_option_index, marks)
            "short_answer": list of dicts (question, answer_guideline, marks)
            "long_answer": list of dicts (question, answer_guideline, marks)
        section_config (dict): Configuration for each section, e.g.:
            {
                "A": {
                    "title": "SECTION A",
                    "instructions": "Attempt this section on the MCQ’s Answer Sheet only...",
                    "time_allowed": "20 Minutes",
                    "marks_per_question": 1, # Can be overridden by question itself
                    "total_marks_section": 15
                },
                "B": {
                    "title": "SECTION B",
                    "instructions": "Attempt any Nine (9) questions each carry equal marks.",
                    "marks_per_question": 4, # Example
                    "total_marks_section": 36
                },
                "C": {
                    "title": "SECTION C",
                    "instructions": "Attempt any Three (3) questions.",
                    "marks_per_question": 8, # Example
                    "total_marks_section": 24
                }
            }

    Returns:
        str: A string representing the formatted exam paper.
    """
    paper_content = []

    # 1. Overall Paper Header
    paper_content.append(f"{exam_details.get('school_name', 'Oriental Public School Mardan').center(80)}")
    paper_content.append(f"{exam_details.get('exam_title', 'Final Term Examination – 2025').center(80)}")
    paper_content.append(f"CLASS {exam_details.get('class_level', '6th')} PAPER {exam_details.get('subject', 'SUBJECT').upper().center(80)}")
    paper_content.append(f"Total Time : {exam_details.get('total_time', '3:00 Hours'):<40} {'Total Marks: ' + str(exam_details.get('total_marks', 75)):>39}")
    if exam_details.get('version'):
        paper_content.append(f"{'Version: ' + exam_details['version']:>79}")
    paper_content.append("\nNote: There are three sections in this paper i.e. Section A, B & C.")
    paper_content.append("-" * 80)

    current_question_number = 1

    # 2. Section A - MCQs
    if questions_data.get("mcq") and "A" in section_config:
        config_a = section_config["A"]
        paper_content.append(f"\n{config_a.get('title', 'SECTION A').center(80)}")
        section_a_marks = config_a.get('total_marks_section', sum(q.get('marks', 1) for q in questions_data["mcq"]))
        paper_content.append(f"Marks: {section_a_marks:<40} {'Time Allowed: ' + config_a.get('time_allowed', '20 Minutes'):>39}")
        
        # Define default instructions for Section A using a triple-quoted string
        default_instructions_A = """    Attempt this section on the MCQ’s Answer Sheet only
    Use black ball point or marker for shading only one circle for correct option of a question.
    No mark will be awarded for cutting, erasing, over writing and multiple circles shading."""
        # Get instructions, using the default if not provided in config_a
        instructions_A = config_a.get('instructions', default_instructions_A)
        paper_content.append(f"INSTRUCTION :\n{instructions_A}") # Use the variable in the f-string
        paper_content.append("")

        for i, q_data in enumerate(questions_data["mcq"]):
            paper_content.append(f"{current_question_number}. {q_data['question']} ({q_data.get('marks', config_a.get('marks_per_question',1))} Mark{'s' if q_data.get('marks',1) > 1 else ''})")
            options = q_data.get("options", [])
            for j, option in enumerate(options):
                paper_content.append(f"    {chr(65 + j)} {option}") # A, B, C, D
            paper_content.append("")
            current_question_number += 1
        paper_content.append("-" * 80)

    # Reset question numbering for subjective part or continue if preferred (continuing for now)
    # current_question_number = 1 # Uncomment to reset for Section B

    # 3. Section B - Short Answers
    if questions_data.get("short_answer") and "B" in section_config:
        config_b = section_config["B"]
        paper_content.append(f"\n{config_b.get('title', 'SECTION B').center(80)}")
        section_b_total_marks = config_b.get('total_marks_section', sum(q.get('marks', 3) for q in questions_data["short_answer"]))
        paper_content.append(f"{config_b.get('instructions', 'Attempt all questions. Each question carries equal marks.')} (Marks: {section_b_total_marks})")
        paper_content.append("")

        for i, q_data in enumerate(questions_data["short_answer"]):
            paper_content.append(f"{current_question_number}. {q_data['question']} ({q_data.get('marks', config_b.get('marks_per_question',3))} Mark{'s' if q_data.get('marks',3) > 1 else ''})")
            paper_content.append("") # Space for answer
            current_question_number += 1
        paper_content.append("-" * 80)

    # 4. Section C - Long Answers
    if questions_data.get("long_answer") and "C" in section_config:
        config_c = section_config["C"]
        paper_content.append(f"\n{config_c.get('title', 'SECTION C').center(80)}")
        section_c_total_marks = config_c.get('total_marks_section', sum(q.get('marks', 5) for q in questions_data["long_answer"]))
        paper_content.append(f"{config_c.get('instructions', 'Attempt all questions. Each question carries equal marks.')} (Marks: {section_c_total_marks})")
        paper_content.append("")

        for i, q_data in enumerate(questions_data["long_answer"]):
            paper_content.append(f"{current_question_number}. {q_data['question']} ({q_data.get('marks', config_c.get('marks_per_question',5))} Mark{'s' if q_data.get('marks',5) > 1 else ''})")
            paper_content.append("\n" * 3)  # More space for long answers
            current_question_number += 1
        paper_content.append("-" * 80)

    return "\n".join(paper_content)

# Example Usage (can be removed or commented out in production code)
if __name__ == '__main__':
    # Import the placeholder generator for testing
    from ai_question_generator import generate_questions_from_text

    sample_exam_details = {
        "school_name": "My Awesome School",
        "exam_title": "Mid-Term Examination - 2024",
        "class_level": "10th",
        "subject": "Physics",
        "total_time": "2:30 Hours",
        "total_marks": 100,
        "version": "B"
    }

    # Generate some placeholder questions
    sample_questions = generate_questions_from_text(
        text_content="This is some physics related text about Newton's laws and thermodynamics.",
        num_mcq=3,
        num_short_answer=2,
        num_long_answer=1,
        subject="Physics",
        grade_level="10th"
    )

    sample_section_config = {
        "A": {
            "title": "SECTION A - Multiple Choice",
            "instructions": "Choose the best answer for each question. Each question carries 2 marks.",
            "time_allowed": "30 Minutes",
            "marks_per_question": 2,
            "total_marks_section": sum(q.get('marks', 2) for q in sample_questions["mcq"]) # Dynamically calculate
        },
        "B": {
            "title": "SECTION B - Short Answer Questions",
            "instructions": "Answer any two questions. Each question carries 10 marks.",
            "marks_per_question": 10,
            "total_marks_section": sum(q.get('marks', 10) for q in sample_questions["short_answer"]) # Dynamically calculate
        },
        "C": {
            "title": "SECTION C - Essay Questions",
            "instructions": "Answer any one question. This question carries 30 marks.",
            "marks_per_question": 30,
            "total_marks_section": sum(q.get('marks', 30) for q in sample_questions["long_answer"]) # Dynamically calculate
        }
    }
    # Update total marks based on generated questions for the example
    sample_exam_details["total_marks"] = (
        sample_section_config["A"]["total_marks_section"] + 
        sample_section_config["B"]["total_marks_section"] + 
        sample_section_config["C"]["total_marks_section"]
    )


    formatted_paper = format_exam_paper(sample_exam_details, sample_questions, sample_section_config)
    print("\n--- Formatted Exam Paper ---")
    print(formatted_paper)

    # Test with one of the original sample structures
    print("\n\n--- Testing with Math Sample Structure ---")
    math_exam_details = {
        "school_name": "Oriental Public School Mardan",
        "exam_title": "Final Term Examination – 2025",
        "class_level": "6th",
        "subject": "MATH",
        "total_time": "3:00 Hours",
        "total_marks": 75,
        "version": "A"
    }
    math_questions = generate_questions_from_text(
        text_content="Math concepts for 6th grade.",
        num_mcq=2, # Reduced for brevity in example
        num_short_answer=2, # Reduced
        num_long_answer=1, # Reduced
        subject="Math",
        grade_level="6th"
    )
    # Update marks in generated questions to match sample structure
    for q in math_questions["mcq"]: q["marks"] = 1
    for q in math_questions["short_answer"]: q["marks"] = 4 # (36 marks / 9 questions in sample)
    for q in math_questions["long_answer"]: q["marks"] = 8 # (24 marks / 3 questions in sample)

    math_section_config = {
        "A": {
            "title": "SECTION A",
            "instructions": "Attempt this section on the MCQ’s Answer Sheet only... (details omitted for brevity)",
            "time_allowed": "20 Minutes",
            "marks_per_question": 1,
            "total_marks_section": 15 # As per sample, actual questions might differ
        },
        "B": {
            "title": "SECTION B",
            "instructions": "Attempt any Nine (9) questions each carry equal marks.",
            "marks_per_question": 4, 
            "total_marks_section": 36
        },
        "C": {
            "title": "SECTION C",
            "instructions": "Attempt any Three (3) questions.",
            "marks_per_question": 8,
            "total_marks_section": 24
        }
    }
    # Recalculate total marks for this specific test case based on config
    math_exam_details["total_marks"] = (
        math_section_config["A"]["total_marks_section"] + 
        math_section_config["B"]["total_marks_section"] + 
        math_section_config["C"]["total_marks_section"]
    )

    formatted_math_paper = format_exam_paper(math_exam_details, math_questions, math_section_config)
    print(formatted_math_paper)


