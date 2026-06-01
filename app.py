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

# Standard baseline exchange rates for quick calculations (Can be manually tweaked)
EXCHANGE_RATES = {
    "USD": 3750.0,  # 1 USD to UGX
    "KES": 28.5,    # 1 KES to UGX
    "AED": 1020.0,  # 1 AED to UGX
    "EUR": 4050.0   # 1 EUR to UGX
}

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
        :root { --primary: #0d6efd; --success: #25D366; --dark: #0f172a; --light: #f8fafc; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: var(--light); color: var(--dark); }
        header { background: linear-gradient(135deg, #0f172a, #1e3a8a); color: white; padding: 40px 20px; text-align: center; border-bottom: 5px solid var(--primary); }
        header h1 { margin: 0; font-size: 2.5rem; letter-spacing: 2px; text-transform: uppercase; }
        header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem; }
        .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
        
        .grid { display: grid; grid-template-columns: 1fr; gap: 25px; margin-bottom: 40px; }
        @media (min-width: 992px) { .grid { grid-template-columns: 4fr 3fr 3fr; } }
        
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 22px; display: flex; flex-direction: column; justify-content: space-between; }
        .card h2 { margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; font-size: 1.4rem; }
        .card p { font-size: 0.95rem; color: #475569; line-height: 1.5; margin-bottom: 15px; }
        
        textarea, input { width: 100%; padding: 10px; margin: 8px 0; border-radius: 6px; border: 1px solid #cbd5e1; box-sizing: border-box; font-size: 0.95rem; }
        button, .btn-wa { width: 100%; padding: 12px; border: none; border-radius: 6px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: all 0.2s; text-align: center; box-sizing: border-box; }
        
        .btn-ai { background-color: var(--primary); color: white; }
        .btn-ai:hover { background-color: #0b5ed7; }
        .btn-wa { background-color: var(--success); color: white; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }
        .btn-wa:hover { background-color: #20ba5a; }
        
        #result { background: #f1f5f9; padding: 15px; border-radius: 6px; margin-top: 15px; border-left: 4px solid var(--primary); white-space: pre-wrap; display: none; font-size: 0.95rem; }
        
        .catalog-title { text-align: center; margin: 40px 0 20px 0; font-size: 2rem; color: #0f172a; }
        .catalog-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; }
        .product-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }
        .product-image { width: 100%; height: 200px; object-fit: cover; background-color: #cbd5e1; }
        .product-info { padding: 20px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .product-name { font-size: 1.15rem; font-weight: bold; margin: 0 0 8px 0; color: #0f172a; }
        .product-desc { font-size: 0.9rem; color: #64748b; margin-bottom: 15px; min-height: 40px; }
        .product-price { font-size: 1.25rem; font-weight: bold; color: #b91c1c; margin-bottom: 15px; }
    </style>
</head>
<body>
    <header>
        <h1>BROOKSAUTOPLUG</h1>
        <p>Premium Genuine Auto Parts & Smart AI Car Diagnostics</p>
    </header>
    <div class="container">
        <div class="grid">
            <!-- AI DIAGNOSTICS ENGINE -->
            <div class="card">
                <div>
                    <h2>AI Vehicle Diagnostic Engine</h2>
                    <p>Describe the strange sound, mechanical issue, or dashboard warning lights. Our AI mechanic will analyze the problem instantly.</p>
                    <textarea id="issue" rows="4" placeholder="Example: My Toyota Premio makes a grinding noise from the front wheels whenever I apply brakes..."></textarea>
                </div>
                <div>
                    <button class="btn-ai" onclick="runDiagnostic()">Analyze Vehicle Issue</button>
                    <div id="result"></div>
                </div>
            </div>

            <!-- DIRECT SPARE PARTS ORDER FORM -->
            <div class="card">
                <form action="/order-parts" method="POST" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h2>Order Spare Parts</h2>
                        <p>Know the specific part your vehicle requires? Submit details directly to our automated dispatch desk via WhatsApp.</p>
                        <input type="text" name="part_name" placeholder="Part Needed (e.g. Front Shock Absorbers)" required>
                        <input type="text" name="car_model" placeholder="Car Model & Year (e.g. Harrier 2015)" required>
                    </div>
                    <button type="submit" class="btn-wa">Order Parts via WhatsApp</button>
                </form>
            </div>

            <!-- CLIENT MOBILE REPAIR REQUEST FORM -->
            <div class="card">
                <form action="/request-mobile-repair" method="POST" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <h2>On-Site Mobile Repair</h2>
                        <p>Stranded or need a mechanic sent directly to you? Request mobile tracking service anywhere around town.</p>
                        <input type="text" name="client_name" placeholder="Your Name / Contact Info" required>
                        <input type="text" name="car_model" placeholder="Car Model (e.g. Toyota Wish)" required>
                        <input type="text" name="location" placeholder="Current Location (e.g. Kololo, Kampala)" required>
                        <input type="text" name="problem" placeholder="What needs fixing? (e.g. Car won't start)" required>
                    </div>
                    <button type="submit" class="btn-wa" style="background-color: #1d4ed8;">Request Mobile Repair</button>
                </form>
            </div>
        </div>

        <!-- PRODUCT CATALOG SECTION -->
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
                        <form action="/order-parts" method="POST">
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
        .container { max-width: 1300px; margin: 30px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr; gap: 30px; }
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
        .calc-box { background: #f0fdf4; border: 2px dashed #22c55e; padding: 15px; border-radius: 6px; margin-top: 15px; font-weight: bold; color: #166534; }
    </style>
</head>
<body>
    <nav>
        <h1>BROOKSAUTOPLUG Command Center</h1>
        <a href="/logout" class="logout-btn">Secure Log Out</a>
    </nav>
    <div class="container">
        
        <!-- SIDE PANEL FOR ADDS & CALCULATORS -->
        <div>
            <!-- ADD PRODUCT FORM -->
            <div class="card">
                <h2>Add New Stock Item</h2>
                <form action="/admin/add-product" method="POST">
                    <label>Product Name</label>
                    <input type="text" name="name" required>
                    <label>Price Description</label>
                    <input type="text" name="price" placeholder="e.g. 180,000 UGX" id="form_calculated_price" required>
                    <label>Image Link (URL)</label>
                    <input type="url" name="image" required>
                    <label>Short Description</label>
                    <textarea name="description" rows="2" required></textarea>
                    <button type="submit" class="btn-submit">Publish to Catalog</button>
                </form>
            </div>

            <!-- WHOLESALE PRICE CONVERTER TOOL -->
            <div class="card" style="background-color: #f8fafc; border: 1px solid #e2e8f0;">
                <h2>Price Converter (Markup Tool)</h2>
                <p>Convert international distributor quotes to final consumer UGX retail pricing.</p>
                <form action="/admin/convert-price" method="POST">
                    <label>Wholesale Cost</label>
                    <input type="number" step="0.01" name="cost" value="{{ last_calc.cost if last_calc else '' }}" placeholder="e.g. 50" required>
                    
                    <label>Source Currency</label>
                    <select name="currency" required>
                        <option value="USD" {% if last_calc and last_calc.currency == 'USD' %}selected{% endif %}>USD ($)</option>
                        <option value="AED" {% if last_calc and last_calc.currency == 'AED' %}selected{% endif %}>AED (Dirham)</option>
                        <option value="KES" {% if last_calc and last_calc.currency == 'KES' %}selected{% endif %}>KES (Shilling)</option>
                        <option value="EUR" {% if last_calc and last_calc.currency == 'EUR' %}selected{% endif %}>EUR (€)</option>
                    </select>
                    
                    <label>Profit Margin Markup (%)</label>
                    <input type="number" name="markup" value="{{ last_calc.markup if last_calc else '25' }}" placeholder="e.g. 25" required>
                    
                    <button type="submit" class="btn-submit" style="background-color: #475569;">Calculate UGX Rate</button>
                </form>
                
                {% if last_calc %}
                <div class="calc-box">
                    Suggested UGX Price:<br>
                    <span style="font-size: 1.4rem; color: #15803d;">{{ last_calc.result }} UGX</span>
                    <br><span style="font-size: 0.8rem; font-weight: normal; color: #65a30d;">Base Conversion: {{ last_calc.base }} UGX</span>
                </div>
                {% endif %}
            </div>

            <!-- LOG CONFIRMED REPAIR JOB MANUALLY -->
            <div class="card">
                <h2>Log Internal Booking</h2>
                <form action="/admin/add-job" method="POST">
                    <label>Customer Details</label>
                    <input type="text" name="customer" placeholder="Name or Phone" required>
                    <label>Car Model</label>
                    <input type="text" name="car_model" required>
                    <label>Location</label>
                    <input type="text" name="location" required>
                    <label>Issue</label>
                    <textarea name="issue" rows="2" required></textarea>
                    <button type="submit" class="btn-submit" style="background-color: var(--success);">Save to Monitoring Log</button>
                </form>
            </div>
        </div>

        <!-- MAIN MONITORING BOARDS -->
        <div>
            <!-- MOBILE SERVICES TRACKING ARCHIVE -->
            <div class="card">
                <h2>Mobile Services Monitoring Log</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Car & Customer</th>
                            <th>Location</th>
                            <th>Issue</th>
                            <th>Status Control</th>
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

# Active session store for quick calculations without a database hit
current_calculation = None

# --- PUBLIC ROUTING SYSTEM & WHATSAPP REDIRECTS ---

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT, catalog=load_catalog())

@app.route('/diagnose', methods=['POST'])
def diagnose_car():
    if not client:
        return jsonify({"error": "Gemini API key is missing. Please configure environment variables."}), 500
        
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
                time.sleep(delay)
                delay *= 2
                continue
            return jsonify({"error": f"Heavy traffic. Details: {e.message}"}), 503
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/order-parts', methods=['POST'])
def order_parts():
    part_name = request.form.get('part_name')
    car_model = request.form.get('car_model')
    message = f"Hello BROOKSAUTOPLUG, I would like to order: {part_name} for vehicle: {car_model}."
    encoded_message = urllib.parse.quote(message)
    return redirect(f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={encoded_message}")

@app.route('/request-mobile-repair', methods=['POST'])
def request_mobile_repair():
    client_name = request.form.get('client_name')
    car_model = request.form.get('car_model')
    location = request.form.get('location')
    problem = request.form.get('problem')
    
    message = (
        f"🚨 *BROOKSAUTOPLUG MOBILE REPAIR REQUEST*\n\n"
        f"👤 *Client Name:* {client_name}\n"
        f"🚗 *Vehicle Model:* {car_model}\n"
        f"📍 *Location:* {location}\n"
        f"🔧 *Issue Reported:* {problem}"
    )
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
    global current_calculation
    calc = current_calculation
    # Flush tool window cache upon rendering view to avoid stale values later
    current_calculation = None
    return render_template_string(HTML_ADMIN, catalog=load_catalog(), jobs=load_jobs(), last_calc=calc)

@app.route('/admin/add-product', methods=['POST'])
@login_required
def add_product():
    catalog = load_catalog()
    new_item = {
        "id": int(time.time()),
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

@app.route('/admin/convert-price', methods=['POST'])
@login_required
def convert_price():
    global current_calculation
    cost = float(request.form.get('cost', 0))
    currency = request.form.get('currency', 'USD')
    markup = float(request.form.get('markup', 0))
    
    # Mathematical execution logic
    rate = EXCHANGE_RATES.get(currency, 1.0)
    base_ugx = cost * rate
    final_ugx = base_ugx * (1 + (markup / 100))
    
    # Standard format with commas for cleaner presentation (e.g. 150,000)
    current_calculation = {
        "cost": cost,
        "currency": currency,
        "markup": markup,
        "base": f"{int(base_ugx):,}",
        "result": f"{int(final_ugx):,}"
    }
    return redirect(url_for('admin_panel'))

@app.route('/admin/add-job', methods=['POST'])
@login_required
def add_job():
    jobs = load_jobs()
    new_job = {
        "id": int(time.time()),
        "customer": request.form.get('customer'),
        "car_model": request.form.get('car_model'),
        "location": request.form.get('location'),
        "issue": request.form.get('issue'),
        "status": "pending"
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