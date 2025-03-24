import os
import logging
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
api = "AIzaSyCIoL10wZjF_02Edc71Z5ndnVYM6nrp6aU"
genai.configure(api_key=api)

# ------------------- Pdf to Images Conversion ---------------------------
def generate_images(pdf_path: str) -> list:
    """Converts a PDF file to a list of images."""
    try:
        images = convert_from_path(pdf_path, poppler_path=r'C:\Users\sanke\OneDrive\Desktop\Programming\Handwriting-recognition\Release-24.07.0-0\poppler-24.07.0\Library\bin')  # Update path
        return images
    except Exception as e:
        logging.error(f"Error generating images from PDF: {e}")
        raise

# --------------------- Text Recognition ----------------------------------
def generate_text(img: Image) -> str:
    """Extracts text from a given image using Tesseract OCR."""
    try:
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logging.error(f"Error extracting text from image: {e}")
        raise

# ------------------ AI Model for Keyword Extraction ----------------------
model = genai.GenerativeModel('gemini-1.5-flash')

def get_keywords(model_answer: str) -> str:
    """Extracts important keywords from the model answer using AI."""
    try:
        prompt = f"Extract the important keywords for evaluating the student's answer based on the following model answer: {model_answer}. Provide keywords in a single line, separated by commas."
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()  # Ensure no extra spaces
        else:
            raise Exception("No keywords returned from AI model.")
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        raise

# ------------------ Answer Segmentation and Comparison -------------------
def segment_answer(answer: str) -> list:
    """Segments the answer into sentences or key phrases."""
    return re.split(r'[.?!]', answer)

def check_missing_keywords(student_answer_segments: list, keywords_lower: list) -> list:
    """Checks for missing keywords in the student's answer."""
    missing_keywords = []
    for keyword in keywords_lower:
        found = any(keyword in segment for segment in student_answer_segments)
        if not found:
            missing_keywords.append(keyword)
    return missing_keywords

# ------------------ Feedback Generation -----------------------
def get_feedback(studentAnswer, modelAnswer, predictedMarks):
    try:
        prompt = f"The student's answer is: {studentAnswer}. The model answer is: {modelAnswer} and the predicted marks out of 10 is: {predictedMarks}. Give me the feedback of the student's answer in short."
        res = model.generate_content(prompt)
        feedback = res.text  # Corrected from res.text() to res.text (remove parentheses)
        if res and feedback:
            return feedback.strip()  # Ensure no extra spaces
        else:
            raise Exception("No feedback returned from AI model.")
    except Exception as e:
        raise Exception(f"Error generating feedback: {e}")

# ------------------ Scoring Mechanism ------------------------------------
from difflib import SequenceMatcher

def marks(student_answer: str, model_answer: str, max_marks: float, keywords: str) -> float:
    """Calculates marks based on the student's answer compared to the model answer.
       If answers are 95% similar, full marks are awarded."""
    
    if not student_answer.strip():
        return 0  # No answer, no marks
    
    # Check similarity between the student's answer and model answer
    similarity = SequenceMatcher(None, student_answer.lower(), model_answer.lower()).ratio()
    
    # If similarity is >= 95%, award full marks
    if similarity >= 0.95:
        return max_marks
    
    # Convert to lowercase for case-insensitive comparison
    student_answer_lower = student_answer.lower()
    keywords_lower = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()]
    
    # Segment the student answer for better comparison
    student_answer_segments = segment_answer(student_answer_lower)

    # Find missing keywords
    missing_keywords = check_missing_keywords(student_answer_segments, keywords_lower)

    # Deduct marks for each missing keyword (even distribution)
    missing_count = len(missing_keywords)
    deduction_per_keyword = max_marks / len(keywords_lower) if keywords_lower else 0
    total_deduction = missing_count * deduction_per_keyword

    # Ensure marks do not drop below 0
    marks_obtained = max(0, max_marks - total_deduction)
    return marks_obtained

# --------------- Improved Segregation of Questions and Answers -----------------------
def segregate_questions_and_answers(text: str) -> list:
    """Segregates questions and answers from the provided text."""
    segments = re.split(r'(?i)\bAnswer\s*\d+[a-z]?\]', text)  # Matches case-insensitive "Answer X" or "Answer X{letter}]"
    
    # Ignore the first segment as it is typically the content before "Answer 1a]" or the title
    answers = [segment.strip() for segment in segments if segment.strip()]

    return answers

# --------------- Main Function to Process PDFs ---------------------------
def process_answers(student_pdf: str, actual_answers_pdf: str, max_marks: float = 10) -> tuple:
    """Processes the student and model answer PDFs and returns scoring results."""
    # Generate images and extract text from model and student PDFs
    model_images = generate_images(actual_answers_pdf)
    model_text = " ".join([generate_text(img) for img in model_images])
    
    student_images = generate_images(student_pdf)
    student_text = " ".join([generate_text(img) for img in student_images])

    # Log the extracted text
    logging.info(f"Model Text: {model_text}")
    logging.info(f"Student Text: {student_text}")

    # Segregate answers for both the model and student texts
    model_answers = segregate_questions_and_answers(model_text)
    student_answers = segregate_questions_and_answers(student_text)

    # Log the segregated answers
    logging.info(f"Model Answers: {model_answers}")
    logging.info(f"Student Answers: {student_answers}")

    # Ensure both lists have the same length
    if len(model_answers) != len(student_answers):
        raise ValueError("Mismatch in number of answers between the student and model PDFs.")
    
    results = []
    total_marks = 0

    # Iterate over answers to compare and score
    for i, (student_answer, model_answer) in enumerate(zip(student_answers, model_answers), start=1):
        # Get keywords for the current model answer
        keywords = get_keywords(model_answer)
        
        # Calculate the score for the current answer
        score = int(marks(student_answer, model_answer, max_marks=max_marks, keywords=keywords))
        feedback = get_feedback(student_answer, model_answer, score)
        # Store result for current question
        results.append({
            'question_number': i,
            'student_answer': student_answer,
            'model_answer': model_answer,
            'score': score,
            'feedback' : feedback
        })
        
        # Update total marks
        total_marks += int(score)

    logging.info(f"Results: {results}")
    return results, total_marks
