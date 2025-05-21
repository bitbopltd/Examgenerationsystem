# Adding detailed logging to aid in debugging the question generation process.
import google.generativeai as genai
import os
import random
from typing import Dict, List, Any, Optional
import time
import json
import re
import traceback

# Import specific exceptions for cleaner error handling
from google.api_core import exceptions 

# --- Configuration ---
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=API_KEY)

# Rate limit configuration
REQUESTS_PER_MINUTE = 14  # Keep slightly under the 15/min limit
RETRY_BASE_DELAY = 2  # Base delay in seconds for exponential backoff

# --- Model and Safety Settings ---
MODEL_NAME = 'models/gemini-1.5-flash-latest' 

DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Utility Functions ---
def log_progress(msg: str):
    """Logs a message with a timestamp and flushes the output."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

log_progress(f"Using Gemini model: {MODEL_NAME}")
model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=DEFAULT_SAFETY_SETTINGS
)

def extract_json_from_response(text_response: str) -> Any:
    """
    Extracts a JSON object or list from a string, handling markdown and heuristics.
    """
    if not text_response:
        log_progress("extract_json_from_response: Received empty text_response.")
        return None

    match = re.search(r"```json\s*([\s\S]*?)\s*```", text_response, re.IGNORECASE)
    if match:
        json_str = match.group(1)
        try: return json.loads(json_str)
        except json.JSONDecodeError as e: 
            log_progress(f"extract_json_from_response: Failed to decode JSON from markdown block: {e}")
            return None

    first_b, first_sq_b = text_response.find('{'), text_response.find('[')
    start_idx = min(first_b, first_sq_b) if first_b != -1 and first_sq_b != -1 else max(first_b, first_sq_b)
    if start_idx != -1:
        cand_str = text_response[start_idx:]; ob, osb, lci = 0,0,-1
        for i,c in enumerate(cand_str):
            if c=='{':ob+=1 
            elif c=='}':ob-=1 
            elif c=='[':osb+=1 
            elif c==']':osb-=1
            if ob==0 and osb==0 and (c=='}' or c==']'):
                if (cand_str[0] == '{' and c == '}') or (cand_str[0] == '[' and c == ']'):
                    lci = i
                    break
        if lci!=-1:
            h_str=cand_str[:lci+1]
            try: return json.loads(h_str)
            except json.JSONDecodeError as e: 
                log_progress(f"extract_json_from_response: Failed heuristic decode: {e}")
    try: return json.loads(text_response)
    except json.JSONDecodeError as e: 
        log_progress(f"extract_json_from_response: Failed full parse: {e}")
        return None

def analyze_text_for_topics(text_content: str, num_topics: int) -> List[str]:
    """Analyzes text content using Gemini to identify distinct topics."""
    log_progress(f"Analyzing text for {num_topics} distinct topics...")
    analysis_prompt = f"""Analyze the following text and identify {num_topics} distinct topics, themes, concepts, named entities (like specific people, companies, tools), or specific outcomes discussed within it.
Provide the topics as a JSON array of strings. Each string should be a concise phrase (3-8 words) summarizing a topic.
Ensure the topics are varied and cover different aspects mentioned in the text.
Focus on specific details, names, or concepts.

Text: {text_content[:8000]}"""

    generation_config = genai.types.GenerationConfig(
        temperature=0.8,
        max_output_tokens=512
    )

    for attempt in range(3):
        try:
            log_progress(f"Sending topic analysis prompt (Attempt {attempt + 1}/3)...")
            response = model.generate_content(analysis_prompt, generation_config=generation_config)

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                log_progress(f"Topic analysis prompt blocked. Reason: {response.prompt_feedback.block_reason}.")
                return []

            if not response.parts:
                log_progress(f"Topic analysis response has no parts.")
                if attempt < 2: time.sleep(2 ** attempt); continue
                return []

            parsed_data = extract_json_from_response(response.text)

            if parsed_data and isinstance(parsed_data, list):
                cleaned_topics = [topic.strip() for topic in parsed_data]
                unique_topics = list(dict.fromkeys(cleaned_topics))
                log_progress(f"Successfully extracted {len(unique_topics)} unique topics")
                return unique_topics
            else:
                if attempt < 2: time.sleep(2 ** attempt); continue
                return []

        except exceptions.ResourceExhausted as r_exc:
            log_progress(f"RATE LIMIT HIT during topic analysis: {str(r_exc)[:500]}")
            if attempt < 2:
                delay_match = re.search(r"retry_delay {\s*seconds: (\d+)\s*}", str(r_exc))
                sleep_for = int(delay_match.group(1)) + 1 if delay_match else (2 ** attempt) * 2
                time.sleep(sleep_for)
            else: return []
        except Exception as e:
            log_progress(f"ERROR during topic analysis: {type(e).__name__} - {str(e)}")
            if attempt < 2: time.sleep(2 ** attempt); continue
            return []
    return []

def generate_single_question_for_topic_with_retry(
    base_prompt: str,
    question_type: str,
    topic: str,
    generation_index: int,
    max_api_calls: int = 3
) -> Optional[Dict[str, Any]]:

    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=1024
    )

    topic_instruction_prompt = (
        f"Generate a {question_type} question based on the provided text. "
        f"The question MUST focus specifically on this topic: '{topic}'. "
        "Ensure the question relates directly to this topic.\n\n"
        "--- Original Format and Content Instructions ---\n"
    )

    modified_prompt = topic_instruction_prompt + base_prompt 

    log_progress(f"Prompting for {question_type} (Gen {generation_index}) about topic: '{topic}'...")

    for api_call_attempt in range(max_api_calls):
        try:
            log_progress(f"Sending prompt for {question_type} (Gen {generation_index}, API call {api_call_attempt + 1}/{max_api_calls})")

            response = model.generate_content(modified_prompt, generation_config=generation_config)

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                log_progress(f"Prompt blocked for topic '{topic}'. Reason: {response.prompt_feedback.block_reason}")
                return None

            if not response.parts:
                if api_call_attempt < max_api_calls - 1: 
                    time.sleep(1 * (api_call_attempt + 1))
                    continue
                return None

            parsed_question_data = extract_json_from_response(response.text)

            if parsed_question_data and isinstance(parsed_question_data, dict):
                if question_type == "mcq":
                    if not all(key in parsed_question_data for key in ["question", "options", "correct_option_index"]):
                        if api_call_attempt < max_api_calls - 1: 
                            time.sleep(1.5 * (api_call_attempt + 1))
                            continue
                        return None
                elif question_type in ["short_answer", "long_answer"]:
                    if not all(key in parsed_question_data for key in ["question", "guideline"]):
                        if api_call_attempt < max_api_calls - 1: 
                            time.sleep(1.5 * (api_call_attempt + 1))
                            continue
                        return None

                if parsed_question_data.get("question") == "":
                    return None

                log_progress(f"Successfully generated {question_type} for topic: '{topic}'")
                return parsed_question_data

            else:
                if api_call_attempt < max_api_calls - 1: 
                    time.sleep(1.5 * (api_call_attempt + 1))
                    continue
                return None

        except exceptions.ResourceExhausted as r_exc:
            log_progress(f"RATE LIMIT HIT: {str(r_exc)[:500]}")
            if api_call_attempt < max_api_calls - 1:
                delay_match = re.search(r"retry_delay {\s*seconds: (\d+)\s*}", str(r_exc))
                sleep_for = int(delay_match.group(1)) + 1 if delay_match else (2 ** api_call_attempt) * 2
                time.sleep(sleep_for)
            else: return None
        except Exception as e:
            log_progress(f"ERROR: {type(e).__name__} - {str(e)}")
            if api_call_attempt < max_api_calls - 1: 
                time.sleep(2 ** api_call_attempt)
            else: return None

    return None

def generate_questions_from_text(text_content: str, num_mcq: int = 0, num_short_answer: int = 0, num_long_answer: int = 0, subject: str = "General", grade_level: str = "N/A") -> Dict[str, List[Any]]:
    generated_questions = {"mcq": [], "short_answer": [], "long_answer": []}
    if not text_content: 
        log_progress("Input text_content is empty.")
        return generated_questions

    total_questions_needed = num_mcq + num_short_answer + num_long_answer
    if total_questions_needed <= 0:
        return generated_questions

    num_topics_to_analyze = max(total_questions_needed * 2, 10)
    available_topics = analyze_text_for_topics(text_content, num_topics=num_topics_to_analyze)

    if not available_topics:
        log_progress("Failed to extract topics from the text.")
        return generated_questions

    random.shuffle(available_topics)

    mcq_base_prompt = f"""Generate exactly ONE multiple choice question with 4 unique options based on the provided text.
The response MUST be a JSON object in this format:
{{
  "question": "Your question here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_option_index": 0
}}

Text: {text_content[:5000]}"""

    saq_base_prompt_text = f"""Generate ONE short answer question based on the provided text.
The response MUST be a JSON object in this format:
{{ "question": "Your question here?", "guideline": "Guideline for answering here." }}

Text content: {text_content[:5500]}"""

    laq_base_prompt_text = f"""Generate ONE detailed essay question based on the provided text.
The response MUST be a JSON object in this format:
{{ "question": "Your essay question here?", "guideline": "Comprehensive answer guideline here." }}

Text content: {text_content[:7000]}"""

    # Generate MCQs
    mcq_count = 0
    while mcq_count < num_mcq and available_topics:
        chosen_topic = available_topics.pop(0)
        mcq_data = generate_single_question_for_topic_with_retry(
            mcq_base_prompt, "mcq", chosen_topic, mcq_count + 1
        )

        if mcq_data:
            try:
                correct_answer_text_val = mcq_data['options'][mcq_data['correct_option_index']]
                shuffled_options = list(mcq_data['options'])
                random.shuffle(shuffled_options)
                new_correct_index = shuffled_options.index(correct_answer_text_val)

                generated_questions["mcq"].append({
                    "type": "mcq",
                    "question": mcq_data["question"],
                    "options": shuffled_options,
                    "correct_option_index": new_correct_index,
                    "marks": 1
                })
                mcq_count += 1
            except (IndexError, ValueError) as e:
                log_progress(f"Error processing MCQ: {str(e)}")
                continue

    # Generate Short Answer Questions
    if num_short_answer > 0:
        saq_count = 0
        while saq_count < num_short_answer and available_topics:
            chosen_topic = available_topics.pop(0)
            saq_data = generate_single_question_for_topic_with_retry(
                saq_base_prompt_text, "short_answer", chosen_topic, saq_count + 1
            )

            if saq_data:
                generated_questions["short_answer"].append({
                    "type": "short_answer",
                    "question": saq_data["question"],
                    "answer_guideline": saq_data.get('guideline', ''),
                    "marks": 4
                })
                saq_count += 1

    # Generate Long Answer Questions
    if num_long_answer > 0:
        laq_count = 0
        while laq_count < num_long_answer and available_topics:
            chosen_topic = available_topics.pop(0)
            laq_data = generate_single_question_for_topic_with_retry(
                laq_base_prompt_text, "long_answer", chosen_topic, laq_count + 1
            )

            if laq_data:
                generated_questions["long_answer"].append({
                    "type": "long_answer",
                    "question": laq_data["question"],
                    "answer_guideline": laq_data.get('guideline', ''),
                    "marks": 8
                })
                laq_count += 1

    return generated_questions