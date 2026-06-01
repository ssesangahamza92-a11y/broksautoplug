import os
import time
import json
import urllib.parse
from flask import Flask, request, jsonify, redirect, render_template_string, flash, url_for
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "brookautoplug_secret_key_2026")

WHATSAPP_NUMBER = "256794959101"

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# --- FLASK-LOGIN & SECURITY CONFIGURATION ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("AdminPass2026!")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(ADMIN_USERNAME)
    return None

# --- JSON DATABASE HELPERS ---
DB_FILE = "database.json"
JOBS_FILE = "jobs_database.json"

def load_catalog():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_catalog(catalog):
    with open(DB_FILE, "w") as f:
        json.dump(catalog, f, indent=4)

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=4)

# --- HTML TEMPLATES ---

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BROOKSAUTOPLUG | Premium Auto Parts & AI Diagnostics</title>
    <style>
        :root { --primary: #0d6efd; --success: #25D366; --dark: #1e293b; --light: #f8fafc; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: var(--light); color: var(--dark); }
        header { background: linear-gradient(135deg, #0f172a, #1e3a8a); color: white; padding: 40px 20px; text-align: center; border-bottom: 5px solid var(--primary); }
        header h1 { margin: 0; font-size: 2.5rem; letter-spacing: 2px; text-transform: uppercase; }
        header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem; }
        .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
        .grid { display: grid; grid-template-columns: 1fr; gap: 30px; }
        @media (min-width: 768px) { .grid { grid-template-columns: 2fr 1fr; } }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 25px; margin-bottom: 25px; }
        .card h2 { margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        textarea, input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #cbd5e1; box-sizing: border-box; font-size: 1rem; }
        button { width: 100%; padding: 14px; border: none; border-radius: 6px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
        .btn-ai { background-color: var(--primary); color: white; }
        .btn-ai:hover { background-color: #0b5ed7; }
        .btn-wa { background-color: var(--success); color: white; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
        .btn-wa:hover { background-color: #20ba5a; }
        #result { background: #f1f5f9; padding: 15px; border-radius: 6px; margin-top: 15px; border-left: 4px solid var(--primary); white-space: pre-wrap; display: none; }
        
        .catalog-title { text-align: center; margin: 40px 0 20px 0; font-size: 2rem; color: #0f172a; }
        .catalog-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; }
        .product-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
        .product-image { width: 100%; height: 200px; object-fit: cover; background-color: #cbd5e1; }
        .product-info { padding: 20px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .product-name { font-size: 1.2rem; font-weight: bold; margin: 0 0 10px 0; color: #0f172a; }
        .product-desc { font-size: 0.9rem; color: #64748b; margin-bottom: 15px; }
        .product-price { font-size: 1.3rem; font-weight: bold; color: #b91c1c; margin-bottom: 15px; }
    </style>
</head>
<body>
    <header>
        <h1>BROOKSAUTOPLUG</h1>
        <p>Premium Genuine Auto Parts & Smart AI Car Diagnostics</p>
    </header>
    <div class="container">
        <div class="grid">
            <div class="card">
                <h2>AI Vehicle Diagnostic Engine</h2>
                <p>Describe the strange sound, mechanical issue, or dashboard lights your vehicle is experiencing. Our adaptive AI mechanic will identify potential causes and suggest solutions.</p>
                <textarea id="issue" rows="4" placeholder="Example: My Toyota Premio makes a grinding noise from the front wheels whenever I apply brakes..."></textarea>
                <button class="btn-ai" onclick="runDiagnostic()">Analyze Vehicle Issue</button>
                <div id="result"></div>
            </div>
            <div class="card">
                <h2>Direct WhatsApp Order</h2>
                <p>Know exactly what you need? Order directly through our dispatch desk.</p>
                <form action="/order" method="POST">
                    <input type="text" name="part_name" placeholder="Part Needed (e.g. Shock Absorbers)" required>
                    <input type="text" name="car_model" placeholder="Car Model / Year (e.g. Harrier 2015)" required>
                    <button type="submit" class="btn-wa">Order via WhatsApp</button>
                </form>
            </div>
        </div>
        <h2 class="catalog-title">Our Stock Catalog</h2>
        <div class="catalog-grid">
            {% for product in catalog %}
            <div class="product-card">
                <img class="product-image" src="{{ product.image }}" alt="{{ product.name }}">
                <div class="product-info">
                    <div>
                        <div class="product-name">{{ product.name }}</div>
                        <div class="product-desc">{{ product.description }}</div>
                    </div>
                    <div>
                        <div class="product-price">{{ product.price }}</div>
                        <form action="/order" method="POST">
                            <input type="hidden" name="part_name" value="{{ product.name }}">
                            <input type="hidden" name="car_model" value="Stock Catalog Item">
                            <button type="submit" class="btn-wa">Buy via WhatsApp</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>
        async function runDiagnostic() {
            const desc = document.getElementById('issue').value;
            const resultDiv = document.getElementById('result');
            if(!desc) return alert('Please tell us what your car is doing.');
            resultDiv.style.display = "block";
            resultDiv.innerText = "BROOKSAUTOPLUG Brain analyzing your car diagnostics...";
            resultDiv.style.borderLeftColor = "#0d6efd";
            try {
                const response = await fetch('/diagnose', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: desc })
                });
                const data = await response.json();
                if(data.diagnostic) {
                    resultDiv.innerText = data.diagnostic;
                    resultDiv.style.borderLeftColor = "#25D366";
                } else {
                    resultDiv.innerText = "⚠️ " + (data.error || "Could not fetch diagnosis.");
                    resultDiv.style.borderLeftColor = "#b91c1c";
                }
            } catch (err) {
                resultDiv.innerText = "Error connecting to backend services.";
            }
        }
    </script>
</body>
</html>
"""

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BROOKSAUTOPLUG | Admin Gateway</title>
    <style>
        :root { --primary: #0d6efd; --dark: #1e293b; --light: #f8fafc; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: var(--light); color: var(--dark); display: flex; flex-direction: column; min-height: 100vh; }
        header { background: linear-gradient(135deg, #0f172a, #1e3a8a); color: white; padding: 25px; text-align: center; border-bottom: 5px solid var(--primary); }
        .login-container { max-width: 400px; margin: auto; width: 90%; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 12px; margin: 10px 0 20px 0; border-radius: 6px; border: 1px solid #cbd5e1; box-sizing: border-box; }
        button { width: 100%; padding: 14px; border: none; border-radius: 6px; font-weight: bold; background-color: var(--primary); color: white; cursor: pointer; }
        .msg { color: #b91c1c; text-align: center; margin-bottom: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <header><h1>BROOKSAUTOPLUG Portal</h1></header>
    <div class="login-container">
        <h2>Private Access Login</h2>
        {% if error %}<div class="msg">{{ error }}</div>{% endif %}
        <form method="POST">
            <label>Admin Username</label>
            <input type="text" name="username" required>
            <label>Secure Password</label>
            <input type="password" name="password" required>
            <button type="submit">Verify Identity</button>
        </form>
    </div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BROOKSAUTOPLUG | Control Panel</title>
    <style>
        :root { --primary: #0d6efd; --dark: #1e293b; --light: #f8fafc; --danger: #b91c1c; --success: #25D366; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: var(--light); }
        nav { background: #0f172a; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        nav h1 { margin: 0; font-size: 1.5rem; }
        .logout-btn { color: #f8fafc; background: var(--danger); padding: 8px 15px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr; gap: 30px; }
        @media (min-width: 992px) { .container { grid-template-columns: 1fr 2fr; } }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: fit-content; margin-bottom: 20px; }
        .card h2 { margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        input, textarea, select { width: 100%; padding: 10px; margin: 8px 0 15px 0; border-radius: 6px; border: 1px solid #cbd5e1; box-sizing: border-box; font-size: 0.95rem; }
        .btn-submit { background-color: var(--primary); color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background-color: #f1f5f9; color: #1e293b; }
        .btn-delete { background-color: var(--danger); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; text-decoration: none; font-size: 0.8rem; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
        .status-pending { background-color: #fef3c7; color: #d97706; }
        .status-active { background-color: #dbeafe; color: #2563eb; }
        .status-done { background-color: #dcfce7; color: #15803d; }
        .inline-form { display: inline; }
        .status-select { width: auto; padding: 4px; margin: 0; font-size: 0.8rem; }
    </style>
</head>
<body>
    <nav>
        <h1>BROOKSAUTOPLUG Command Center</h1>
        <a href="/logout" class="logout-btn">Secure Log Out</a>
    </nav>
    <div class="container">
        
        <!-- SIDE PANEL FOR FORMS -->
        <div>
            <!-- ADD PRODUCT FORM -->
            <div class="card">
                <h2>Add New Stock Item</h2>
                <form action="/admin/add-product" method="POST">
                    <label>Product Name</label>
                    <input type="text" name="name" required>
                    <label>Price Description</label>
                    <input type="text" name="price" placeholder="e.g. 180,000 UGX" required>
                    <label>Image Link (URL)</label>
                    <input type="url" name="image" required>
                    <label>Short Description</label>
                    <textarea name="description" rows="2" required></textarea>
                    <button type="submit" class="btn-submit">Publish to Catalog</button>
                </form>
            </div>

            <!-- LOG MOBILE REPAIR JOB FORM -->
            <div class="card">
                <h2>Log Mobile Repair Job</h2>
                <form action="/admin/add-job" method="POST">
                    <label>Customer Name / Contact</label>
                    <input type="text" name="customer" placeholder="e.g. John +256..." required>
                    <label>Car Model</label>
                    <input type="text" name="car_model" placeholder="e.g. Toyota Wish 2012" required>
                    <label>Location Around Town</label>
                    <input type="text" name="location" placeholder="e.g. Kololo, Kampala" required>
                    <label>Issue Description</label>
                    <textarea name="issue" rows="2" placeholder="e.g. Alternator replacement" required></textarea>
                    <button type="submit" class="btn-submit" style="background-color: var(--success);">Dispatch / Log Job</button>
                </form>
            </div>
        </div>

        <!-- MAIN MANAGEMENT BOARDS -->
        <div>
            <!-- MOBILE SERVICES DISPATCH LOG -->
            <div class="card">
                <h2>Mobile Services Dispatch Log</h2>
                <p>Tracks on-site mechanic assignments and location repairs around town.</p>
                <table>
                    <thead>
                        <tr>
                            <th>Car & Customer</th>
                            <th>Location</th>
                            <th>Issue</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for job in jobs %}
                        <tr>
                            <td><strong>{{ job.car_model }}</strong><br><small style="color: #64748b;">{{ job.customer }}</small></td>
                            <td>{{ job.location }}</td>
                            <td>{{ job.issue }}</td>
                            <td>
                                <span class="status-badge {% if job.status == 'pending' %}status-pending{% elif job.status == 'in-progress' %}status-active{% else %}status-done{% endif %}">
                                    {{ job.status }}
                                </span>
                                <form action="/admin/update-job/{{ job.id }}" method="POST" class="inline-form">
                                    <select name="status" class="status-select" onchange="this.form.submit()">
                                        <option value="">-- Change --</option>
                                        <option value="pending">Pending</option>
                                        <option value="in-progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                    </select>
                                </form>
                            </td>
                            <td>
                                <a href="/admin/delete-job/{{ job.id }}" class="btn-delete" onclick="return confirm('Remove this job record entirely?')">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- CATALOG MANAGEMENT GRID -->
            <div class="card">
                <h2>Live Connected Catalog</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Product Tracked</th>
                            <th>Market Price</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for product in catalog %}
                        <tr>
                            <td><strong>{{ product.name }}</strong></td>
                            <td><span style="color: var(--danger); font-weight: bold;">{{ product.price }}</span></td>
                            <td>
                                <a href="/admin/delete-product/{{ product.id }}" class="btn-delete" onclick="return confirm('Remove this part from public display?')">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</body>
</html>
"""

# --- PUBLIC CONTROLLERS ---

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT, catalog=load_catalog())

@app.route('/diagnose', methods=['POST'])
def diagnose_car():
    if not client:
        return jsonify({"error": "Gemini API key is missing on Render. Please configure your environment variables."}), 500
        
    data = request.json
    user_description = data.get('description', '')
    
    prompt = f"""
    You are the expert diagnostic master mechanic for BROOKSAUTOPLUG Uganda. 
    A customer is describing this auto issue: "{user_description}".
    Provide a professional breakdown pinpointing the exact parts likely failing, 
    the safety severity, step-by-step repair strategy, and estimated prices for 
    the replacement elements in Ugandan Shillings (UGX). Keep it bold and easy to scan.
    """
    
    max_retries = 3
    delay = 2
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return jsonify({"diagnostic": response.text})
        except APIError as e:
            if e.code == 503 and attempt < max_retries - 1:
                print(f"Google 503 Traffic Spike. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
                continue
            return jsonify({"error": f"Our diagnostic assistant is experiencing heavy traffic. Please try again shortly. Details: {e.message}"}), 503
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/order', methods=['POST'])
def place_order():
    part_name = request.form.get('part_name')
    car_model = request.form.get('car_model')
    message = f"Hello BROOKSAUTOPLUG, I would like to order: {part_name} for vehicle: {car_model}."
    encoded_message = urllib.parse.quote(message)
    return redirect(f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={encoded_message}")

# --- SECURED PRIVATE ADMIN CONTROLLERS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            user = User(ADMIN_USERNAME)
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            error = "Invalid credential authorization signature."
            
    return render_template_string(HTML_LOGIN, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin-panel-secure-xyz')
@login_required
def admin_panel():
    return render_template_string(HTML_ADMIN, catalog=load_catalog(), jobs=load_jobs())

@app.route('/admin/add-product', methods=['POST'])
@login_required
def add_product():
    catalog = load_catalog()
    new_id = int(time.time())
    new_item = {
        "id": new_id,
        "name": request.form.get('name'),
        "price": request.form.get('price'),
        "image": request.form.get('image'),
        "description": request.form.get('description')
    }
    catalog.append(new_item)
    save_catalog(catalog)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-product/<int:product_id>')
@login_required
def delete_product(product_id):
    catalog = load_catalog()
    updated_catalog = [item for item in catalog if item['id'] != product_id]
    save_catalog(updated_catalog)
    return redirect(url_for('admin_panel'))

# --- MOBILE DISPATCH CONTROLLERS ---

@app.route('/admin/add-job', methods=['POST'])
@login_required
def add_job():
    jobs = load_jobs()
    new_id = int(time.time())
    new_job = {
        "id": new_id,
        "customer": request.form.get('customer'),
        "car_model": request.form.get('car_model'),
        "location": request.form.get('location'),
        "issue": request.form.get('issue'),
        "status": "pending"  # Jobs default to pending when first opened
    }
    jobs.append(new_job)
    save_jobs(jobs)
    return redirect(url_for('admin_panel'))

@app.route('/admin/update-job/<int:job_id>', methods=['POST'])
@login_required
def update_job(job_id):
    jobs = load_jobs()
    new_status = request.form.get('status')
    if new_status:
        for job in jobs:
            if job['id'] == job_id:
                job['status'] = new_status
                break
        save_jobs(jobs)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-job/<int:job_id>')
@login_required
def delete_job(job_id):
    jobs = load_jobs()
    updated_jobs = [job for job in jobs if job['id'] != job_id]
    save_jobs(updated_jobs)
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)