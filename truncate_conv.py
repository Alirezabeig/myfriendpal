
# truncate_conv.py
from itertools import chain



def truncate_to_last_n_letters(text, max = 1000 ):
    if len(text) > max:
        return text[-max:]
    else:
        return text