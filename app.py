import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# --- CONFIGURATION ---
# The Google GenAI SDK automatically reads the GEMINI_API_KEY environment variable.
try:
    ai_client = genai.Client()
except Exception as e:
    print(f"AI Initialization Warning: {e}")
    ai_client = None

# Your private WhatsApp number for receiving customer orders
MY_WHATSAPP_NUMBER = "256700000000"  # Replace with your actual Uganda number format


# --- ROUTES ---

# 1. Home / Customer Interface
@app.route('/')
def home():
    return render_template('index.html')


# 2. AI Diagnostic Endpoint
@app.route('/diagnose', methods=['POST'])
def diagnose_car():
    if not ai_client:
        return jsonify({"error": "AI service is currently unavailable. Check Render environment keys."}), 500
        
    data = request.json
    customer_input = data.get("issue", "")
    
    if not customer_input:
        return jsonify({"error": "Please describe the problem or noise your car is making."}), 400
        
    # Expert mechanic prompt guiding the engine to provide clear diagnostic breakdowns and Ugandan prices
    prompt = f"Act as an expert car mechanic. A customer says: '{customer_input}'. Diagnose the issue, suggest solutions, and list common part replacements with estimated costs in Ugandan Shillings (UGX)."
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return jsonify({"diagnosis": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. Private Admin Panel (Secure baseline)
@app.route('/admin-panel-secret')
def admin_panel():
    # We will secure this route so only you can see store metrics and manage parts
    return "<h1>BROOKSAUTOPLUG - Private Admin Dashboard</h1>"


if __name__ == '__main__':
    app.run(debug=True)