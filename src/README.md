# Program Inventory Generator

This application predicts program inventories for government organizations based on department personnel data and the organization's website.

## Features

- Upload an Excel file with department, division, and position data
- Enter an organization's website URL
- Choose how many programs to generate per department
- Receive an Excel file with predicted programs for each department

## Requirements

- Python 3.8+
- OpenAI API Key
- Required Python packages (see requirements.txt)

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
5. Run the application:
   ```
   flask run
   ```
6. Open http://localhost:5000 in your browser

## Deployment on Render.com

1. Push your code to a GitHub repository
2. Sign up for [Render.com](https://render.com)
3. Create a new Web Service and select your GitHub repository
4. Use these settings:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add the following environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: A random string for Flask session security
6. Deploy your application

## Project Structure

- `app.py`: Main Flask application
- `program_inventory.py`: The ProgramInventoryAgent class and related functions
- `templates/`: HTML templates for the web interface
- `uploads/`: Temporary storage for uploaded files
- `output/`: Generated Excel files
- `requirements.txt`: Required Python packages
- `.env`: Environment variables (not included in Git)

## Notes

- This application requires an OpenAI API key with access to the GPT-4 model
- The application stores uploaded files temporarily and deletes them after processing
- Excel files must include columns for Department, Division, and Position Name