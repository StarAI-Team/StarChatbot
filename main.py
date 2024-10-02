from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os, PyPDF2
from flask import send_from_directory
from werkzeug.utils import secure_filename
import google.generativeai as genai
from waitress import serve

load_dotenv()
# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

TRANSCRIPTS_DIR = "transcripts"

# Ensure the transcripts directory exists
if not os.path.exists(TRANSCRIPTS_DIR):
    os.makedirs(TRANSCRIPTS_DIR)

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
    system_instruction=""" Capture load details from uploaded pdf. if you receive a call summary, rephrase the call summary from the AI caller called Taurai and a potential transporter, using available loads knowledge from uploaded PDF, 
    correct route names, load types, and rates. after rephrasing, you are sending the summary to the admin reporting on what Taurai's call resulted in. make the reprt short and conscise: 
    Example:
    *Admin Report:*

    Taurai successfully booked a load for a potential transporter. The load is for bagged lime, moving from Ndola to Harare at a rate of $1700. The transporter's contact information is their Whatsapp number: 0778524824.
    
    """
)
chat_session = model.start_chat(history=[])

def save_transcript(call_id, transcript):
    transcript_filename = f"{call_id}.txt"
    transcript_filepath = os.path.join(TRANSCRIPTS_DIR, transcript_filename)

    with open(transcript_filepath, "w") as transcript_file:
        transcript_file.write(transcript)

    return transcript_filename

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

# Define the CallLog model
class CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caller_name = db.Column(db.String(100))
    call_time = db.Column(db.String(100))
    summary = db.Column(db.Text)
    rate_accepted = db.Column(db.Boolean, default=False)  # New field
    notes = db.Column(db.String(255))  # New field

# Google Sheets Updater class
class GoogleSheetUpdater:
    def __init__(self, service_account_file, document_id, sheet_index=0):
        self.service_account_file = service_account_file
        self.document_id = document_id
        self.sheet_index = sheet_index
        self.gc = self._authorize_client()
        self.worksheet = self._open_worksheet()

    def _authorize_client(self):
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_file(self.service_account_file, scopes=scopes)
        return gspread.authorize(credentials)

    def _open_worksheet(self):
        spreadsheet = self.gc.open_by_key(self.document_id)
        return spreadsheet.get_worksheet(self.sheet_index)

    def get_dataframe(self):
        records = self.worksheet.get_all_records()
        return pd.DataFrame(records)

    def get_transcript_by_id(self, call_id):
        records = self.worksheet.get_all_records()
        for row in records:
            if row['Call ID'] == call_id:
                return row['Transcript']
        return None


    def update_existing_data(self, call_id, suggestion):
    # Fetch all data to find the row index based on Call ID
        sheet_data = self.worksheet.get_all_records()


    # Loop through each row to find the matching Call ID
        for i, row in enumerate(sheet_data):
            if str(row['Call ID']) == str(call_id):
                try:
                # Handle None case by providing a default empty string
                    suggestion = suggestion if suggestion is not None else ''
                    suggestion_col = self.worksheet.find('Suggestions').col
                    self.worksheet.update_cell(i + 2, suggestion_col, suggestion)  # +2 because of 0 index and header row
                    print(f"Updated row {i + 2} with suggestion: {suggestion}")
                    return {'status': 'success', 'message': 'Data updated successfully'}
                except Exception as e:
                    print(f"Failed to update row {i + 2}. Error: {e}")
                return {'status': 'error', 'message': f'Failed to update data: {str(e)}'}

        return {'status': 'error', 'message': 'Call ID not found'}


# Assuming `data` is a list of dictionaries that includes 'Call ID' and 'Transcript' fields
#data = []  # This would actually be populated with your fetched data


# Usage
SERVICE_ACCOUNT_FILE = './star-chatbot-admin-23fcc20045c7.json'
DOCUMENT_ID = '154VvsJcn7ZKE7mqPEIP1T-JIJbEzw4IyEExPZesa2Gc'

updater = GoogleSheetUpdater(SERVICE_ACCOUNT_FILE, DOCUMENT_ID)

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            call_logs = CallLog.query.all()
            return render_template('logs.html', call_logs=call_logs)
        else:
            flash('Invalid username or password')

    return render_template('index.html')

@app.route('/transcript/<call_id>')
def view_transcript(call_id):
    print(f"Requested call_id: {call_id}")  # Debugging
    transcript = updater.get_transcript_by_id(call_id)
    if transcript:
        return render_template('transcript.html', transcript=transcript)
    else:
        return f"Transcript not found for call_id: {call_id}", 404


# Route for the main dashboard (protected by login)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    call_logs = CallLog.query.all()
    return render_template('logs.html', call_logs=call_logs)

# Route for handling logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Route to fetch data from Google Sheets
@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    try:
        df = updater.get_dataframe()  # Fetch updated data from Google Sheets
        data = df.to_dict(orient="records")
        return jsonify(data)
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 500

# Route to send updates to Google Sheets
@app.route('/send_update', methods=['POST'])
def send_update():
    if request.method == 'POST':
        updates = request.json

        # Check if updates is a dictionary
        if isinstance(updates, dict):
            updated_call_ids = []
            try:
                # Loop through each updated suggestion
                for call_id, suggestion in updates.items():
                    result = updater.update_existing_data(call_id, suggestion)
                    if result['status'] == 'success':
                        updated_call_ids.append(call_id)
                    elif result['status'] != 'no_change' and result['status'] != 'success':
                        return jsonify(result), 500

                return jsonify({"status": "success", "message": "Sheet updated successfully.", "updated_call_ids": updated_call_ids}), 200

            except Exception as e:
                print(f"Error processing updates: {e}")
                return jsonify({"status": "error", "message": "Failed to update sheet.", "error": str(e)}), 500

    return jsonify({"status": "error", "message": "Invalid request method."}), 400

# Directory for uploaded PDF files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_pdf(file_path):
    """Parse the uploaded PDF and extract the text."""
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text
@app.route('/upload_loads', methods=['GET', 'POST'])
def upload_loads():
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
            
            return render_template('logs.html')
    
    # If GET request, render the upload form
    return render_template('upload_loads.html')

from twilio.rest import Client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
ADMIN_NUMBER = 'whatsapp:+79999171644'
# Function to send WhatsApp messages
def send_whatsapp_message(to, message):
    client.messages.create(
        body=message,
        from_='whatsapp:+14155238886',  # Twilio sandbox or registered WhatsApp number
        to=to
    )

# Endpoint to receive and forward the rephrased summary to admin
@app.route('/send-to-admin', methods=['POST'])
def send_initial_message():
    summary = request.values.get('Body', '').strip()
    from_number = request.form.get('From')

    if not summary:
        return "Error: No valid summary found", 400

    # Rephrase the summary using the generative AI model
    rephrased_summary = chat_session.send_message(summary)
    rephrased_summary = rephrased_summary.text if hasattr(rephrased_summary, 'text') else str(rephrased_summary)

    # Send the rephrased summary to the admin
    send_whatsapp_message(ADMIN_NUMBER, rephrased_summary)  

    return jsonify({"status": "success", "message": "Rephrased summary sent to admin"}), 200


@app.route('/update_logs', methods=['GET', 'POST'])
def update_logs():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    #app.run(debug=True, port=3000)
    serve(app,host="0.0.0.0",port=8000)
