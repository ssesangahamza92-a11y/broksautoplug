import os
from flask import Flask, request, jsonify, redirect, render_template_string
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

WHATSAPP_NUMBER = "256700000000"  # Your WhatsApp Number

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Your complete HTML embedded directly into the python file as a string
HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>BROOKSAUTOPLUG - AI Diagnostics</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }
        .box { border: 1px solid #ccc; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        input, textarea, button { width: 100%; padding: 10px; margin: 10px 0; }
        button { background-color: #25D366; color: white; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <h1>BROOKSAUTOPLUG</h1>
    
    <div class="box">
        <h3>AI Vehicle Diagnostic Engine</h3>
        <textarea id="issue" placeholder="Describe the car noise or problem..."></textarea>
        <button onclick="runDiagnostic()">Analyze Issue</button>
        <div id="result" style="margin-top: 15px; white-space: pre-wrap;"></div>
    </div>

    <div class="box">
        <h3>Order Parts via WhatsApp</h3>
        <form action="/order" method="POST">
            <input type="text" name="part_name" placeholder="Part Name" required>
            <input type="text" name="car_model" placeholder="Car Model" required>
            <button type="submit">Send Order to WhatsApp</button>
        </form>
    </div>

    <script>
        async function runDiagnostic() {
            const desc = document.getElementById('issue').value;
            const resultDiv = document.getElementById('result');
            if(!desc) return alert('Please enter a description');
            resultDiv.innerText = "Analyzing...";
            const response = await fetch('/diagnose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: desc })
            });
            const data = await response.json();
            resultDiv.innerText = data.diagnostic || data.error;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # This renders the string directly without looking for an index.html file!
    return render_template_string(HTML_LAYOUT)

@app.route('/diagnose', methods=['POST'])
def diagnose_car():
    if not client:
        return jsonify({"error": "Gemini API key missing."}), 500
    data = request.json
    user_description = data.get('description', '')
    
    prompt = f"You are the AI mechanic for BROOKSAUTOPLUG Uganda. Diagnose this issue: {user_description}. Provide causes, solutions, and estimated parts prices in UGX."
    
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return jsonify({"diagnostic": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/order', methods=['POST'])
def place_order():
    part_name = request.form.get('part_name')
    car_model = request.form.get('car_model')
    message = f"Hello BROOKSAUTOPLUG, I would like to order a {part_name} for a {car_model}."
    return redirect(f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={request.utils.quote(message)}")

@app.route('/admin-panel-secure-xyz')
def admin_panel():
    return "<h1>BROOKSAUTOPLUG Private Admin Panel</h1>"

if __name__ == '__main__':
    app.run(debug=True)