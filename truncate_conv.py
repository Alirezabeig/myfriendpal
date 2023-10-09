
# truncate_conv.py
from itertools import chain
import json
import logging
import openai

def truncate_to_last_n_words(conversation, max_words=500):
    # Convert the list of dicts to a list of strings, considering only 'content'.
    text_list = [item['content'] for item in conversation]
    
    # Join all strings into one and split it into a list of words.
    all_words = list(chain.from_iterable([text.split() for text in text_list]))
    
    # Take the last 'max_words' from the list.
    last_n_words = all_words[-max_words:]
    
    # Convert the list of last 'max_words' back to a string.
    truncated_text = ' '.join(last_n_words)
    
    # Initialize an empty list to store truncated conversation.
    truncated_conversation = []
    
    # Use a pointer to keep track of where we are in the truncated_text.
    pointer = 0
    
    for item in reversed(conversation):
        # Calculate the length of 'content' for each dict in words.
        length_in_words = len(item['content'].split())
        
        # Find the end index for each piece in the truncated_text.
        end_index = pointer + length_in_words
        
        # Extract the substring.
        part = ' '.join(last_n_words[pointer:end_index])
        
        # Create a new dict and append it to the truncated conversation.
        truncated_conversation.append({
            "role": item['role'],
            "content": part
        })
        
        # Update the pointer.
        pointer = end_index
    
    return list(reversed(truncated_conversation))

