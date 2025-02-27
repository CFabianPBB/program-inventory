import os
import pandas as pd
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
import io
from src.program_inventory import ProgramInventoryAgent

# Create Flask app with custom template folder path
app = Flask(__name__, template_folder='src/templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Configure upload folder - using your existing input/output folders
UPLOAD_FOLDER = 'input'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create folders if they don't exist (though you already have them)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                output_filename = f"programs_{filename}"
                output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                # Save to Excel
                final_df.to_excel(output_filepath, index=False)
                
                # Redirect to download page
                return redirect(url_for('download_file', filename=output_filename))
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return render_template('download.html', filename=filename)

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)