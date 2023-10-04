
# gpt4_utils.py
import json
import openai
import logging

gpt4_api_key = os.environ.get('GPT4_API_KEY')
openai.api_key = gpt4_api_key

def get_gpt4_response(conversation):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation
        )
        gpt4_reply = response['choices'][0]['message']['content'].strip()
        return gpt4_reply
    except Exception as e:
        logging.error(f"An error occurred while getting GPT-4 response: {e}")
        return None
