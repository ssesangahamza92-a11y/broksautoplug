import os
from flask import Flask, request, jsonify, redirect, render_template_string
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Connected to your exact WhatsApp number
WHATSAPP_NUMBER = "256794959101"

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

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

@app.route('/')
def home():
    # Pass the image product catalog into the layout dynamically
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
    return redirect(f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={request.utils.quote(message)}")

@app.route('/admin-panel-secure-xyz')
def admin_panel():
    return "<h1>BROOKSAUTOPLUG Secure Control Panel</h1>"

if __name__ == '__main__':
    app.run(debug=True)