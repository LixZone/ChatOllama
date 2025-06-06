from flask import Flask, request, jsonify, render_template_string, Response
import ollama
import json

app = Flask(__name__)

relevant_keywords = ['solaire', 'photovoltaïque', 'panneaux', 'énergie', 'autoconsommation']

def is_relevant(message):
    return any(word in message.lower() for word in relevant_keywords)

@app.route('/')
def index():
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
                flex-wrap: wrap;
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
            #temperature {
                width: 80px;
                background: #343541;
                color: #ececf1;
                border: none;
                border-radius: 6px;
                padding: 10px;
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
                <input type="number" id="temperature" min="0" max="1" step="0.1" value="0.0" title="Température">
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
    const temperature = parseFloat(document.getElementById('temperature').value || "0");

    if (!message.trim()) return false;

    history.push({role: 'user', content: message});
    renderHistory();
    document.getElementById('message').value = '';
    loader.style.display = 'block';

    let botMsg = {role: 'bot', content: ''};
    history.push(botMsg);
    renderHistory();
    let botBubble = responseDiv.lastChild;

    const response = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, history, temperature})
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
    temperature = float(data.get("temperature", 0.1))

    if not message:
        return jsonify({"error": "Message vide"}), 400

    ollama_history = [{
        "role": "system",
        "content": (
            "Tu es un assistant spécialisé en énergie solaire et photovoltaïque. "
            "Réponds de manière concise et précise. "
            "Si tu ne connais pas la réponse à une question, ou si elle n’est pas liée au domaine du solaire, "
            "réponds simplement : « Je ne sais pas. » "
            "Ne tente jamais d’inventer une réponse. Sois honnête et rigoureux."
            "Donc si tu ne sais pas, dis simplement : « Je ne sais pas. »"
            "Tu es un assistant spécialisé en énergie solaire et photovoltaïque. "
            "Tu réponds uniquement aux questions liées à ce domaine. "
            "Si une question ne concerne pas ce sujet, ou si tu n’as pas la réponse, tu dis simplement : « Je ne sais pas. » "
            "Tu ne réponds pas aux autres types de questions, même si elles semblent amusantes ou simples."
            "Sois concis. Utilise des termes techniques justes. Ne répète pas l’information inutilement."
            "Tu es un assistant expert en énergie solaire et photovoltaïque. "
            "Tu ne dois répondre qu’aux questions strictement liées à ce domaine. "
            "Si une question sort du cadre (comme la politique, la géographie, la cuisine, etc.), "
            "tu dois répondre uniquement : « Je ne sais pas. » "
            "Tu ne dois jamais inventer, supposer ou répondre de manière créative en dehors de ton domaine d’expertise."
        )
    }]

    for i, msg in enumerate(history):
        if msg['role'] == 'user' and is_relevant(msg['content']):
            ollama_history.append({'role': 'user', 'content': msg['content']})
            if i + 1 < len(history) and history[i + 1]['role'] == 'bot':
                ollama_history.append({'role': 'assistant', 'content': history[i + 1]['content']})

    if is_relevant(message):
        ollama_history.append({'role': 'user', 'content': message})
    else:
        return Response("data: " + json.dumps({'response': "Je ne sais pas."}) + "\n\n", mimetype='text/event-stream')

    options={"temperature": temperature}

    def generate():
        try:
            print("Modèle utilisé :", 'qwen2.5:7b')
            for chunk in ollama.chat(
                model='qwen2.5:7b',
                messages=ollama_history,
                stream=True,
                options=options,
            ):
                content = chunk['message']['content']
                yield f"data: {json.dumps({'response': content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)