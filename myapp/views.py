from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import os
import urllib.parse
from .backend import process_answers  # Ensure this import is correct
def result_view(request):
    if request.method == 'POST':
        # Get the uploaded files
        student_file = request.FILES.get('file')
        model_answers_file = request.FILES.get('model_answers')

        # Check if both files were uploaded
        if not student_file or not model_answers_file:
            return render(request, 'form.html', {'error': 'Please upload both files.'})

        # Create a directory to store the files if it doesn't exist
        upload_dir = 'temp'
        os.makedirs(upload_dir, exist_ok=True)

        # Sanitize and save the files
        sanitized_student_name = urllib.parse.quote(student_file.name)
        sanitized_model_name = urllib.parse.quote(model_answers_file.name)

        student_file_path = os.path.join(upload_dir, sanitized_student_name)
        model_answers_file_path = os.path.join(upload_dir, sanitized_model_name)

        fs = FileSystemStorage(location=upload_dir)
        fs.save(sanitized_student_name, student_file)
        fs.save(sanitized_model_name, model_answers_file)

        # Call the process_answers function to process the PDFs
        results, total_marks = process_answers(student_file_path, model_answers_file_path)

        # Here, results should be the processed output you want to display
        return render(request, 'results.html', {
            'total_marks': total_marks,  # Pass total marks to the template
            'results': results  # Pass the processed results to the template
        })

    return render(request, 'form.html')

def home_view(req):
    return render(req, 'home.html')

# Create your views here.
def form_view(req) : 
    return render(req, 'form.html')

def feature_view(req) :
    return render(req, 'features.html')

def about_view(req) :
    return render(req, 'about.html')