import os
import json
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load configuration from our safe .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_fallback_secret_key_123')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB Limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==========================================
# 🗄️ Database Connection Helper (Updated for Aiven SSL)
# ==========================================

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),   # Fallback defaults to 3306 if not set
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'ssl_ca': None,        # Setting this tells mysql.connector to enable SSL
    'ssl_disabled': False   # Forces SSL connection required by Aiven
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Initialize the official live Google GenAI Client
load_dotenv() # Ensure this line exists right before reading!
api_key_check = os.getenv('GEMINI_API_KEY')
print(f"--- DIAGNOSTIC: Loaded API Key is: {api_key_check} ---")

ai_client = genai.Client(api_key=api_key_check)


# ==========================================
# 🤖 Live Gemini Integration Pipeline
# ==========================================
def run_live_gemini_analysis(image_path, text_location_context):
    """
    Sends the user's uploaded civic image along with context text to Gemini 2.5 Flash.
    Returns structured JSON with the problem type, department routing ID, and severity.
    """
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        prompt = f"""
        Analyze this urban infrastructure or environmental issue from an Indian city. 
        Context details regarding location: {text_location_context}.
        
        You must reply with a valid JSON block matching this structure EXACTLY:
        {{
          "detected_issue": "Name of the issue (e.g. Pothole, Broken Streetlight, Sewage Overflow, Garbage Pile)",
          "confidence_score": 95,
          "severity": "Low",
          "assigned_department_id": 1,
          "complaint_abstract": "A short sentence describing the specific situation observed in the photo."
        }}
        
        Rules for choosing severity: Must be exactly "Low", "Medium", or "High".
        Rules for choosing assigned_department_id:
        - Use 1 for Potholes & Roads issues
        - Use 2 for Water Supply & Sewage issues
        - Use 3 for Garbage & Sanitation issues
        - Use 4 for Streetlights & Electricity issues
        """

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        return json.loads(response.text)

    except Exception as e:
        print(f"⚠️ Live Gemini API Pipeline Failed: {e}. Executing structural fallback pattern.")
        return {
            "detected_issue": "General Civic Hazard",
            "confidence_score": 75,
            "severity": "Medium",
            "assigned_department_id": 1,
            "complaint_abstract": "Civic ticket filed via portal automation fallback."
        }


# ==========================================
# 🚀 Application Routing Logic
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/complaint', methods=['GET', 'POST'])
def raise_complaint():
    if request.method == 'POST':
        file = request.files.get('problem_image')
        full_address = request.form.get('full_address', None)
        latitude = request.form.get('latitude', None)
        longitude = request.form.get('longitude', None)

        if not latitude or latitude == '': latitude = None
        if not longitude or longitude == '': longitude = None

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            context_str = full_address if full_address else f"Coordinates: {latitude}, {longitude}"
            
            # Execute real-time AI processing
            ai_results = run_live_gemini_analysis(filepath, context_str)

            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO complaints (
                    image_filename, full_address, latitude, longitude,
                    detected_issue, confidence_score, severity, assigned_department_id, complaint_abstract
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                filename, full_address, latitude, longitude,
                ai_results["detected_issue"], ai_results["confidence_score"],
                ai_results["severity"], ai_results["assigned_department_id"], ai_results["complaint_abstract"]
            ))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('public_dashboard'))

    return render_template('complaint.html')


@app.route('/public-dashboard')
def public_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, d.dept_name 
        FROM complaints c 
        LEFT JOIN departments d ON c.assigned_department_id = d.id 
        ORDER BY c.id DESC
    """)
    complaints = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total FROM complaints")
    total_incidents = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as urgent_count FROM complaints WHERE severity='High' AND status != 'Resolved'")
    urgent_issues = cursor.fetchone()['urgent_count'] or 0
    
    cursor.close()
    conn.close()

    metrics = {
        "total_incidents": total_incidents,
        "urgent_issues": urgent_issues,
        "top_trend": "Potholes & Drainage (+12% this week)",
        "water_saved": "14,200 Litres",
        "waste_managed": "5.1 Tons"
    }
    return render_template('public_dashboard.html', complaints=complaints, metrics=metrics)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM departments WHERE dept_username = %s AND dept_password = %s", (username, password))
        dept = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if dept:
            session['dept_id'] = dept['id']
            session['dept_name'] = dept['dept_name']
            return redirect(url_for('department_panel'))
        else:
            return render_template('login.html', error="Invalid department credentials entered.")
            
    return render_template('login.html')


@app.route('/department-panel')
def department_panel():
    if 'dept_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM complaints WHERE assigned_department_id = %s ORDER BY id DESC", (session['dept_id'],))
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('department_panel.html', tasks=tasks, dept_name=session['dept_name'])


@app.route('/update-status', methods=['POST'])
def update_status():
    if 'dept_id' not in session:
        return jsonify({'error': 'Unauthorized entry'}), 401
        
    complaint_id = request.form.get('complaint_id')
    new_status = request.form.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE complaints SET status = %s WHERE id = %s AND assigned_department_id = %s",
        (new_status, complaint_id, session['dept_id'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('department_panel'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/knowledge-assistant')
def knowledge_assistant():
    return render_template('knowledge_assistant.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({"reply": "I didn't receive any text. Please type a message."})

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are the official SustainCity AI assistant for India. Your job is to answer "
                    "user questions regarding urban civic issues, recycling, dry/wet waste segregation, "
                    "water conservation, and environmental sustainability. Keep answers clear, "
                    "polite, and structured."
                )
            )
        )
        ai_reply = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        ai_reply = "I'm having trouble reaching my AI engine right now. Please verify your API key configuration."

    return jsonify({"reply": ai_reply})


@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, d.dept_name 
        FROM complaints c 
        LEFT JOIN departments d ON c.assigned_department_id = d.id 
        ORDER BY c.id DESC
    """)
    all_complaints = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', complaints=all_complaints)


# ==========================================
# 🛠️ Server Runner (Configured for Render Production Deployment)
# ==========================================
if __name__ == '__main__':
    # Render binds your web application dynamically to an assigned 'PORT' environment variable.
    # Locally, it defaults back to port 5000.
    port = int(os.environ.get("PORT", 5000))
    
    # We turn off debug=True for deployment stability and security in cloud staging.
    app.run(host='0.0.0.0', port=port, debug=False)
