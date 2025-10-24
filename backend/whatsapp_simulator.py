from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "whatsapp-simulator"})

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json or {}
    to = data.get('to', 'unknown')
    message = data.get('message', '')
    
    print(f"📤 WhatsApp vers {to}: {message}")
    
    return jsonify({
        "status": "sent",
        "message_id": f"sim_{hash(message) % 10000}",
        "to": to
    })

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json or {}
    tenant_id = data.get('tenant_id', 1)
    phone = data.get('customer_phone', '+237600000000')
    message = data.get('message', 'Test message')
    
    print(f"🧪 Simulation: T{tenant_id} <- {phone}: {message}")
    
    try:
        response = requests.post('http://localhost:8000/api/process-message', 
            json={
                "tenant_id": tenant_id,
                "customer_phone": phone,
                "message": message
            }, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "status": "success",
                "ai_response": result.get("ai_response"),
                "conversation_id": result.get("conversation_id")
            })
        else:
            return jsonify({"status": "error", "details": response.text})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == '__main__':
    print("📱 WhatsApp Simulator - Port 3000")
    app.run(host='0.0.0.0', port=3000, debug=False)
