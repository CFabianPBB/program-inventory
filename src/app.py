import os
import sys
import pandas as pd
import time
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import threading

# Add current directory to path to find program_inventory.py in the same folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from program_inventory import ProgramInventoryAgent

# Create Flask app with custom template folder path pointing to templates inside src
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Configure upload folder
UPLOAD_FOLDER = '../input'
OUTPUT_FOLDER = '../output'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory storage for background tasks
processing_tasks = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health')
def health():
    return "OK", 200

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        website_url = request.form.get('website_url', '').strip()
        programs_per_department = int(request.form.get('programs_per_department', 5))
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if not website_url:
            flash('Please enter a website URL')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Start processing in background
                task_id = str(int(time.time()))
                processing_tasks[task_id] = {
                    'status': 'processing',
                    'filename': filename,
                    'output_filename': None,
                    'error': None
                }
                
                # Start background task
                thread = threading.Thread(
                    target=process_file_background,
                    args=(task_id, filepath, website_url, programs_per_department)
                )
                thread.daemon = True
                thread.start()
                
                # Redirect to status page
                return redirect(url_for('task_status', task_id=task_id))
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)
    
    return render_template('index.html')

def process_file_background(task_id, filepath, website_url, programs_per_department):
    """Process file in background thread"""
    try:
        # Process file
        agent = ProgramInventoryAgent()
        
        # Read input file
        input_df = agent.read_excel_data(filepath)
        
        # Get unique departments
        departments = input_df['Department'].unique()
        
        # Process each department
        all_programs = []
        for dept in departments:
            programs = agent.process_department(
                input_df, 
                dept, 
                website_url, 
                programs_per_department
            )
            all_programs.append(programs)
        
        # Combine results
        final_df = pd.concat(all_programs, ignore_index=True)
        
        # Generate a unique output filename based on the input filename
        output_filename = f"programs_{os.path.basename(filepath)}"
        output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Save to Excel
        final_df.to_excel(output_filepath, index=False)
        
        # Update task status
        processing_tasks[task_id]['status'] = 'completed'
        processing_tasks[task_id]['output_filename'] = output_filename
        
    except Exception as e:
        # Update task status with error
        processing_tasks[task_id]['status'] = 'error'
        processing_tasks[task_id]['error'] = str(e)

@app.route('/task/<task_id>')
def task_status(task_id):
    """Check status of a background task"""
    if task_id not in processing_tasks:
        flash('Task not found')
        return redirect(url_for('index'))
    
    task = processing_tasks[task_id]
    
    if task['status'] == 'completed':
        return redirect(url_for('download_file', filename=task['output_filename']))
    elif task['status'] == 'error':
        flash(f"Error processing file: {task['error']}")
        return redirect(url_for('index'))
    else:
        # Still processing
        return render_template('processing.html', task_id=task_id)

@app.route('/status/<task_id>')
def check_status(task_id):
    """AJAX endpoint to check task status"""
    if task_id not in processing_tasks:
        return jsonify({'status': 'not_found'})
    
    task = processing_tasks[task_id]
    return jsonify({
        'status': task['status'],
        'error': task['error'] if 'error' in task else None
    })

@app.route('/download/<filename>')
def download_file(filename):
    return render_template('download.html', filename=filename)

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)