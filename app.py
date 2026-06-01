import os
from flask import Flask, request, jsonify, redirect, render_template_string, flash, url_for
from google import genai
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
# Required key for securing admin sessions
app.secret_key = os.getenv("SECRET_KEY", "brookautoplug_secret_key_2026")

# Connected to your exact WhatsApp number
WHATSAPP_NUMBER = "256794959101"

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# --- FLASK-LOGIN & SECURITY CONFIGURATION ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ADMIN_USERNAME = "admin"
# This hashes your admin password securely
ADMIN_PASSWORD_HASH = generate_password_hash("AdminPass2026!")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(ADMIN_USERNAME)
    return None

# Hardcoded product catalog with image URLs for your brand display
PRODUCT_CATALOG = [
    {
        "id": 1,
        "name": "Heavy Duty Brake Pads",
        "price": "180,000 UGX",
        "image": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?q=80&w=400&auto=format&fit=crop",
        "description": "Premium stopping power for Toyota, Nissan, and Subaru."
    },
    {
        "id": 2,
        "name": "High-Performance Spark Plugs (Set of 4)",
        "price": "120,000 UGX",
        "image": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?q=80&w=400&auto=format&fit=crop",
        "description": "Improves fuel efficiency and smooths out engine idling."
    },
    {
        "id": 3,
        "name": "Full Synthetic Engine Oil 5W-30 (5L)",
        "price": "250,000 UGX",
        "image": "https://images.unsplash.com/photo-1622595202812-70b1a0397746?q=80&w=400&auto=format&fit=crop",
        "description": "Advanced engine wear protection for hot Ugandan climates."
    }
]

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
        
        /* Catalog Styling */
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
                    resultDiv.innerText = "⚠️ Setup Status: " + (data.error || "Could not fetch diagnosis.");
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
        :root { --primary: #0d6efd; --dark: #1e293b; --light: #f8fafc; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: var(--light); }
        nav { background: #0f172a; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        nav h1 { margin: 0; font-size: 1.5rem; }
        .logout-btn { color: #f8fafc; background: #b91c1c; padding: 8px 15px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background-color: #f1f5f9; color: #1e293b; }
    </style>
</head>
<body>
    <nav>
        <h1>BROOKSAUTOPLUG Command Center</h1>
        <a href="/logout" class="logout-btn">Secure Log Out</a>
    </nav>
    <div class="container">
        <div class="card">
            <h2>Welcome Back, Boss!</h2>
            <p>This control grid handles active item deployments completely offline from search spiders.</p>
            <h3>Live Connected Catalog ({{ catalog|length }} Items)</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Product Tracked</th>
                        <th>Market Price</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in catalog %}
                    <tr>
                        <td>{{ product.id }}</td>
                        <td><strong>{{ product.name }}</strong></td>
                        <td>{{ product.price }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT, catalog=PRODUCT_CATALOG)

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
    
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return jsonify({"diagnostic": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/order', methods=['POST'])
def place_order():
    part_name = request.form.get('part_name')
    car_model = request.form.get('car_model')
    message = f"Hello BROOKSAUTOPLUG, I would like to order: {part_name} for vehicle: {car_model}."
    
    # Safe import inside route execution block
    import urllib.parse
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
    return render_template_string(HTML_ADMIN, catalog=PRODUCT_CATALOG)

if __name__ == '__main__':
    app.run(debug=True)