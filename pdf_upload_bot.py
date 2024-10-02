import os
import re
import PyPDF2
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai

# Flask application
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

load_dotenv()
api_key = os.getenv('AI_API_KEY')

# Configure the Generative AI model (Google PaLM API)
genai.configure(api_key=api_key)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=""" Capture load details from uploaded pdf. 
    
    """
)
chat_session = model.start_chat(history=[])

def allowed_file(filename):
    """Check if the uploaded file is a PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def parse_pdf(file_path):
    """Parse the uploaded PDF and extract the text."""
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

@app.route('/upload-pdf', methods=['GET', 'POST'])
def upload_pdf():
    """Route to upload and process a PDF file."""
    if request.method == 'POST':
        # Check if a file is part of the POST request
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        
        # Check if a valid file is selected
        if file.filename == '':
            return "No selected file", 400
        
        if file and allowed_file(file.filename):
            # Secure the filename and save it
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Parse the PDF to extract the text
            pdf_content = parse_pdf(file_path)
            
            # Send the extracted text to the bot as a prompt
            try:
                # Sending PDF content to the bot as a prompt
                bot_prompt = f"Taurai, here is the load list for today:\n\n{pdf_content}"
                bot_reply = chat_session.send_message(bot_prompt)
                bot_response_text = bot_reply.text if hasattr(bot_reply, 'text') else str(bot_reply)
            except Exception as e:
                return f"Error sending prompt to bot: {e}", 500
            
            return f"Bot response: {bot_response_text}", 200
    
    # If GET request, render the upload form
    return render_template('pdfupload.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
