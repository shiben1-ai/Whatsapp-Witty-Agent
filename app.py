import os
from flask import Flask, request, render_template_string
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Twilio client
twilio_client = Client(
    os.environ.get('TWILIO_ACCOUNT_SID'),
    os.environ.get('TWILIO_AUTH_TOKEN')
)

# Initialize Claude client
claude_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Store recent messages (in production, use a database)
recent_messages = []


def add_witty_line(original_message):
    """
    Use Claude to add a witty, mood-boosting line to the message
    """
    
    prompt = f"""You are a clever, upbeat assistant who adds delightful, context-aware responses to messages.

Original message: "{original_message}"

Your task:
1. Read the message carefully and understand its tone and context
2. Create ONE short, witty response that:
   - Relates specifically to what they said (not generic!)
   - Matches their energy (playful, thoughtful, excited, etc.)
   - Makes them smile or think "that's clever!"
   - Is 1-2 sentences maximum
3. Be creative and vary your style - don't repeat the same format

Examples of good responses:
- If they say "I'm so tired" → "😴 Even coffee is giving up on Mondays. Hang in there, warrior!"
- If they say "Just finished my presentation" → "🎉 Nailed it! Your future self is already thanking you."
- If they say "What's up?" → "🌟 Just here adding sparkle to conversations. You?"

Format: Keep the original message, then add your witty response on a new line starting with an emoji.

Original message: {original_message}

Your witty response:"""

    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        enhanced_message = message.content[0].text
        return enhanced_message
        
    except Exception as e:
        print(f"Error with Claude API: {e}")
        # Better fallback messages
        import random
        fallbacks = [
            f"{original_message}\n\n✨ Couldn't reach the wit-generator, but you're still awesome!",
            f"{original_message}\n\n🌟 Message received loud and clear!",
            f"{original_message}\n\n💫 Got it! Stay brilliant!"
        ]
        return random.choice(fallbacks)


@app.route('/')
def home():
    """
    WHY THIS ROUTE?
    - Provides a simple web interface to see your system working
    - Shows recent messages that were processed
    - Helps you monitor what's happening
    """
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Witty Agent</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background-color: #25D366;
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .message-box {
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .original {
                color: #666;
                font-style: italic;
            }
            .enhanced {
                color: #25D366;
                font-weight: bold;
                margin-top: 10px;
            }
            .status {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }
        </style>
        <meta http-equiv="refresh" content="10">
    </head>
    <body>
        <div class="header">
            <h1>🎭 WhatsApp Witty Message Agent</h1>
            <p>Making conversations more fun, one message at a time!</p>
        </div>
        
        <div class="status">
            <h3>📊 System Status</h3>
            <p>✅ Agent is running and ready</p>
            <p>📱 WhatsApp webhook configured</p>
            <p>🤖 Claude AI connected</p>
            <p>💬 Messages processed: {{ message_count }}</p>
        </div>
        
        <h2>Recent Messages:</h2>
        {% if messages %}
            {% for msg in messages %}
            <div class="message-box">
                <div class="original">
                    <strong>Original:</strong> {{ msg.original }}
                </div>
                <div class="enhanced">
                    <strong>Enhanced:</strong><br>{{ msg.enhanced }}
                </div>
                <small style="color: #999;">From: {{ msg.sender }}</small>
            </div>
            {% endfor %}
        {% else %}
            <p>No messages yet. Send a WhatsApp message to get started!</p>
        {% endif %}
        
        <div style="margin-top: 30px; padding: 20px; background: #fff3cd; border-radius: 8px;">
            <h3>🚀 How to Use:</h3>
            <ol>
                <li>Send a WhatsApp message to your Twilio number</li>
                <li>The agent will read it and add a witty line</li>
                <li>You'll receive the enhanced message back</li>
                <li>Watch this page to see all processed messages</li>
            </ol>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, 
                                 messages=recent_messages[-10:], 
                                 message_count=len(recent_messages))


@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    WHY THIS ROUTE?
    - This is where Twilio sends incoming WhatsApp messages
    - It's the heart of your system
    - Receives message → Enhances it → Sends it back
    
    HOW IT WORKS:
    1. Twilio forwards WhatsApp messages here
    2. We extract the message text and sender
    3. We send it to Claude to add wit
    4. We send the enhanced message back via WhatsApp
    """
    
    # Get the incoming message details
    incoming_msg = request.values.get('Body', '')
    sender = request.values.get('From', '')
    
    print(f"Received message from {sender}: {incoming_msg}")
    
    # Use Claude to add a witty line
    enhanced_msg = add_witty_line(incoming_msg)
    
    # Store the message (for the webpage)
    recent_messages.append({
        'original': incoming_msg,
        'enhanced': enhanced_msg,
        'sender': sender
    })
    
    # Create WhatsApp response
    resp = MessagingResponse()
    resp.message(enhanced_msg)
    
    return str(resp)


@app.route('/send-message', methods=['POST'])
def send_message():
    """
    WHY THIS ROUTE?
    - Allows you to send messages FROM your system
    - Useful for testing or automation
    
    OPTIONAL: You can use this to send messages programmatically
    """
    
    to_number = request.json.get('to')
    message = request.json.get('message')
    
    # Enhance the message before sending
    enhanced = add_witty_line(message)
    
    # Send via Twilio
    twilio_message = twilio_client.messages.create(
        body=enhanced,
        from_=os.environ.get('TWILIO_WHATSAPP_NUMBER'),
        to=f'whatsapp:{to_number}'
    )
    
    return {'status': 'sent', 'sid': twilio_message.sid}


if __name__ == '__main__':
    """
    WHY THIS?
    - Starts the Flask web server
    - debug=True shows detailed errors (helpful for learning)
    - port=5000 is the default port
    """
    print("🚀 Starting WhatsApp Witty Agent...")
    print("📱 Webhook URL: http://localhost:5001/webhook")
    print("🌐 Dashboard: http://localhost:5001")
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)  


