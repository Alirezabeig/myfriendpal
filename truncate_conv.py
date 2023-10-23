
# truncate_conv.py

from itertools import chain

def truncate_to_last_n_words(conversation, max_words=500, essential_roles=['system']):
    word_count = 0
    truncated_conversation = []
    
    # Reverse the conversation to start from the most recent messages.
    reversed_conversation = list(reversed(conversation))

    for item in reversed_conversation:
        # Calculate the length of 'content' for each dict in words.
        length_in_words = len(item['content'].split())
        
        if word_count + length_in_words <= max_words or item['role'] in essential_roles:
            truncated_conversation.append(item)
            word_count += length_in_words
        else:
            # If we've reached the max word count, stop adding more items.
            break
    
    return list(reversed(truncated_conversation))
