from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message")
    if not message:
        return jsonify({"error": "Message vide"}), 400
    return jsonify({"response": f"Tu as dit : {message}"})