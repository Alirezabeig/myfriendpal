
# truncate_conv.py
from itertools import chain

def truncate_to_last_n_letters(conversation, max_letters=500):
    # Convert the list of dicts to a list of strings, considering only 'content'.
    text_list = [item['content'] for item in conversation]
    
    # Join all strings into one string.
    all_letters = ''.join(text_list)
    
    # Take the last 'max_letters' from the string.
    last_n_letters = all_letters[-max_letters:]
    
    # Initialize an empty list to store truncated conversation.
    truncated_conversation = []
    
    # Use a pointer to keep track of where we are in the truncated_text.
    pointer = 0
    
    for item in reversed(conversation):
        # Calculate the length of 'content' for each dict in letters.
        length_in_letters = len(item['content'])
        
        # Find the end index for each piece in the truncated_text.
        end_index = pointer + length_in_letters
        
        # Extract the substring.
        part = last_n_letters[pointer:end_index]
        
        # Create a new dict and append it to the truncated conversation.
        truncated_conversation.append({
            "role": item['role'],
            "content": part
        })
        
        # Update the pointer.
        pointer = end_index
    
    return list(reversed(truncated_conversation))

