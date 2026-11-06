from flask import Flask, request, jsonify, render_template_string
from google import genai
from google.genai import types

app = Flask(__name__)

# Ініціалізація клієнта Gemini (автоматично шукає GEMINI_API_KEY у змінних середовища)
# Або вкажіть ключ напряму: client = genai.Client(api_key="ВАШ_КЛЮЧ")
client = genai.Client()

# Глобальний чат для прикладу (у реальному проєкті для кожного відвідувача створюється окрема сесія)
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=(
            "Ти онлайн-асистент на сайті. Будь ввічливим, коротким і допомагай клієнтам. "
            "Якщо клієнт хоче зробити запис, забронювати час або залишити свої контакти, "
            "обов'язково почни свою відповідь з тегу [BOOKING] і далі запиши деталі."
        ),
        temperature=0.7,
    )
)

# Функція надсилання сповіщення власнику (тут можна підключити Telegram Bot або Email)
def send_to_owner(data):
    print("
" + "="*50)
    print("🚨 [СПОВІЩЕННЯ ДЛЯ ВЛАСНИКА] Новий запис від клієнта!")
    print(f"Деталі: {data}")
    print("="*50 + "
")

# Головна сторінка сайту з віджетом чату
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мой Сайт з ШІ-Асистентом</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 40px; }
        .content { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        /* Стилі віджета чату */
        #chat-widget { position: fixed; bottom: 20px; right: 20px; width: 350px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); overflow: hidden; display: flex; flex-direction: column; }
        #chat-header { background: #007bff; color: white; padding: 15px; font-weight: bold; text-align: center; }
        #chat-messages { height: 300px; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { padding: 8px 12px; border-radius: 8px; max-width: 80%; word-wrap: break-word; font-size: 14px; }
        .user-msg { background: #007bff; color: white; align-self: flex-end; }
        .ai-msg { background: #e9ecef; color: black; align-self: flex-start; }
        #chat-input-area { display: flex; border-top: 1px solid #ddd; }
        #chat-input { flex: 1; border: none; padding: 12px; outline: none; }
        #send-btn { background: #007bff; color: white; border: none; padding: 12px 16px; cursor: pointer; font-weight: bold; }
        #send-btn:hover { background: #0056b3; }
    </style>
</head>
<body>

    <div class="content">
        <h1>Ласкаво просимо на наш сайт!</h1>
        <p>Це демонстраційна сторінка. Праворуч внизу розташований чат-асистент, куди відвідувачі можуть писати.</p>
    </div>

    <!-- Віджет чату -->
    <div id="chat-widget">
        <div id="chat-header">💬 Онлайн Консультант</div>
        <div id="chat-messages">
            <div class="msg ai-msg">Вітаю! Чим можу вам допомогти?</div>
        </div>
        <div id="chat-input-area">
            <input type="text" id="chat-input" placeholder="Напишіть повідомлення..." onkeypress="handleKey(event)">
            <button id="send-btn" onclick="sendMessage()">Надіслати</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;

            const messagesDiv = document.getElementById('chat-messages');
            
            // Додаємо повідомлення користувача у чат
            messagesDiv.innerHTML += `<div class="msg user-msg">${message}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            try {
                // Відправляємо запит на наш Python-сервер
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'json' },
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                // Додаємо відповідь ШІ у чат
                messagesDiv.innerHTML += `<div class="msg ai-msg">${data.reply}</div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch (err) {
                messagesDiv.innerHTML += `<div class="msg ai-msg">❌ Помилка з'єднання з сервером.</div>`;
            }
        }

        function handleKey(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'reply': 'Порожнє повідомлення.'})

    try:
        # Відправляємо повідомлення в Gemini
        response = chat.send_message(user_message)
        reply_text = response.text

        # Перевіряємо, чи є в відповіді тег запису
        if "[BOOKING]" in reply_text:
            booking_info = reply_text.replace("[BOOKING]", "").strip()
            send_to_owner(booking_info)
            reply_text = booking_info

        return jsonify({'reply': reply_text})
    except Exception as e:
        return jsonify({'reply': f"Помилка: {str(e)}"})

if __name__ == '__main__':
    print("🚀 Сервер запущено! Відкрийте http://127.0.0.1:5000 у браузері.")
    app.run(debug=True, port=5000)
