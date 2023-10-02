
# gpt4_utils.py
import logging
import openai
import os

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key
conversations = {}

def generate_response(user_input, phone_number):
    global conversations
    if phone_number not in conversations:
        conversations[phone_number] = [
            {"role": "system", "content": "1. You are like a friend. Your name is Pal . 2. You have no other name. Your language is like a friend. 3. You are built by love and prespration. 4. if someone asks you how you are built , always respond a funny and spirtual answer. Also make sure you know the name of the person you are chatting with and make sure to alway listen to their daily success and challenges and respond accordingly. 5. never answer cheesy and useles stuff 6. keep it concise to maximum 30 words. 7. no need to explain yourself.7. Don't explain what your job is or what you are asked to do"},
        ]
    conversations[phone_number].append({"role": "user", "content": user_input})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversations[phone_number]
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        conversations[phone_number].append({"role": "assistant", "content": gpt4_reply})
        return gpt4_reply
    except Exception as e:
        logging.error(f"Failed to generate message with GPT-4: {e}")
        return "Sorry, I couldn't understand that."
     
