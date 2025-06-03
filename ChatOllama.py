from flask import Flask, request, jsonify, render_template_string, Response
import ollama
import json

# Crée une application Flask
app = Flask(__name__)


@app.route('/')
def index():
    # Retourne une page HTML stylée façon ChatGPT avec barre de chargement
    return render_template_string("""
        <style>
            body {
                background: #343541;
                color: #ececf1;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 0;
                min-height: 100vh;
            }
            .chat-container {
                max-width: 600px;
                margin: 40px auto;
                background: #444654;
                border-radius: 10px;
                box-shadow: 0 2px 16px #0004;
                padding: 32px 24px 24px 24px;
            }
            h2 {
                text-align: center;
                margin-bottom: 24px;
                color: #19c37d;
            }
            #chat-form {
                display: flex;
                gap: 8px;
                margin-bottom: 16px;
            }
            #message {
                flex: 1;
                padding: 10px;
                border-radius: 6px;
                border: none;
                font-size: 1em;
                background: #343541;
                color: #ececf1;
            }
            #message:focus {
                outline: 2px solid #19c37d;
            }
            button {
                background: #19c37d;
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
                font-size: 1em;
                cursor: pointer;
                transition: background 0.2s;
            }
            button:hover {
                background: #13a06f;
            }
            .bubble {
                background: #565869;
                color: #ececf1;
                padding: 12px 16px;
                border-radius: 12px;
                margin-bottom: 10px;
                max-width: 80%;
                word-break: break-word;
            }
            .bubble.user {
                background: #19c37d;
                color: #fff;
                margin-left: auto;
                text-align: right;
            }
            .bubble.bot {
                background: #444654;
                color: #ececf1;
                margin-right: auto;
                text-align: left;
            }
            /* Barre de chargement */
            #loader {
                display: none;
                margin: 0 auto 16px auto;
                border: 4px solid #444654;
                border-top: 4px solid #19c37d;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg);}
                100% { transform: rotate(360deg);}
            }
        </style>
        <div class="chat-container">
            <h2>Chat avec Ollama</h2>
            <form id="chat-form" autocomplete="off">
                <input type="text" id="message" placeholder="Votre message" required autofocus>
                <button type="submit">Envoyer</button>
            </form>
            <div id="loader"></div>
            <div id="response"></div>
        </div>
        <script>
let history = [];
const responseDiv = document.getElementById('response');
const loader = document.getElementById('loader');

function renderHistory() {
    responseDiv.innerHTML = '';
    for (const msg of history) {
        if (msg.role === 'user') {
            responseDiv.innerHTML += `<div class="bubble user">${msg.content}</div>`;
        } else {
            responseDiv.innerHTML += `<div class="bubble bot">${msg.content}</div>`;
        }
    }
    responseDiv.scrollTop = responseDiv.scrollHeight;
}

document.getElementById('chat-form').onsubmit = async function(e) {
    e.preventDefault();
    const message = document.getElementById('message').value;
    if (!message.trim()) return false;
    history.push({role: 'user', content: message});
    renderHistory();
    document.getElementById('message').value = '';
    loader.style.display = 'block';

    // Prépare la bulle pour la réponse du bot (streaming)
    let botMsg = {role: 'bot', content: ''};
    history.push(botMsg);
    renderHistory();
    let botBubble = responseDiv.lastChild;

    const response = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, history})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    loader.style.display = 'block';

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, {stream: true});
        let lines = buffer.split(/\\r?\\n\\r?\\n/);
        buffer = lines.pop();
        for (let line of lines) {
            if (line.startsWith('data: ')) {
                let data = JSON.parse(line.slice(6));
                if (data.response) {
                    botMsg.content += data.response;
                    botBubble.innerHTML = botMsg.content;
                } else if (data.error) {
                    botMsg.content = data.error;
                    botBubble.innerHTML = botMsg.content;
                }
                responseDiv.scrollTop = responseDiv.scrollHeight;
            }
        }
    }
    loader.style.display = 'none';
    return false;
};
</script>
    """)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message")
    history = data.get("history", [])
    if not message:
        return jsonify({"error": "Message vide"}), 400

    # On prépare l'historique pour Ollama
    ollama_history = []
    for msg in history:
        if msg['role'] == 'user':
            ollama_history.append({'role': 'user', 'content': msg['content']})
        elif msg['role'] == 'bot':
            ollama_history.append({'role': 'assistant', 'content': msg['content']})

    # Ajoute le message courant si pas déjà dans l'historique (sécurité)
    if not ollama_history or ollama_history[-1]['content'] != message:
        ollama_history.append({'role': 'user', 'content': message})

    def generate():
        try:
            for chunk in ollama.chat(
                model='llama3.2:1b',
                messages=ollama_history,
                stream=True
            ):
                content = chunk['message']['content']
                yield f"data: {json.dumps({'response': content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)