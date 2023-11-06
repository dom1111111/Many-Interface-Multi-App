from .misc_tools import is_numbers

#-------- Word Maps --------#

_SINGLE_NUMBER_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
_TENS_NUMBER_WORDS = ['twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
_GRAND_NUMBER_WORDS = ['hundred', 'thousand', 'million', 'billion', 'trillion']

_SINGLE_ORDINAL_WORDS = ['zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth', 'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth', 'eighteenth', 'nineteenth']
_TENS_ORDINAL_WORDS = ['twentieth', 'thirtieth', 'fortieth', 'fiftieth', 'sixtieth', 'seventieth', 'eightieth', 'ninetieth']
_GRAND_ORDINAL_WORDS = ['hundredth', 'thousandth', 'millionth', 'billionth', 'trillionth']

# --- number word maps --- #

NUMBER_WORD_MAP = {word:i for i, word in enumerate(_SINGLE_NUMBER_WORDS)}
NUMBER_WORD_MAP.update({word:(i+2)*10 for i, word in enumerate(_TENS_NUMBER_WORDS)})
NUMBER_WORD_MAP.update({word:10**i for word, i in zip(_GRAND_NUMBER_WORDS, (2, 3, 6, 9, 12))})

ORDINAL_NUMBER_WORD_MAP = {word:i for i, word in enumerate(_SINGLE_ORDINAL_WORDS)}
ORDINAL_NUMBER_WORD_MAP.update({word:(i+2)*10 for i, word in enumerate(_TENS_ORDINAL_WORDS)})
ORDINAL_NUMBER_WORD_MAP.update({word:10**i for word, i in zip(_GRAND_ORDINAL_WORDS, (2, 3, 6, 9, 12))})

#ALL_NUMBER_WORD_MAP = {**NUMBER_WORD_MAP, **ORDINAL_NUMBER_WORD_MAP}
ALL_NUMBER_WORD_MAP = {**NUMBER_WORD_MAP}

FULL_NUMBER_VOCAB = list(ALL_NUMBER_WORD_MAP.keys()) + ['and', 'oh', 'point']

COLLOQUIAL_QUANTITY_WORD_MAP = {
    'quarter':  0.25, 
    'half':     0.5,
    'halves':   0.5,
    'couple':   2,
    'few':      3,
}

# FRACTIONAL_WORD_MAP = {**ORDINAL_NUMBER_WORD_MAP, **COLLOQUIAL_QUANTITY_WORD_MAP}
# for word in ('zeroth', 'first', 'second'):
#     FRACTIONAL_WORD_MAP.pop(word)

#--- math operator word maps ---#

MATH_OPERATOR_WORD_MAP = {
    'plus':             '+',
    'minus':            '-',
    'times':            'x',
    'divided by':       '/',
    'to the power of':  '**',
    'modulo':           '%'
}

#--- duration word maps ---#

DURATION_WORD_MAP = {    # ammount of seconds each a durational unit of time
    "second":   1, 
    "minute":   60, 
    "hour":     3600, 
    "day":      86400, 
    "week":     604800, 
    "fortnight":1209600,    # a fortnight is 14 days
    "month":    2629800,    # based on a month which is exactly 1/12th of a year (no actual calendar month works like this, but this for the sake of consistentcy)
    "year":     31557600,   # based on average of 365.25 days in a year
}

#--- time word maps ---#
CLOCK_WORDS =       ["am", "pm", "o'clock"]
WEEKDAY =           ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
MONTH =             ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"],        
DAY_WORD_MAP = {
    'dawn':     00, 
    'sunrise':  00, 
    'morning':  00, 
    'noon':     00,
    'afternoon':00, 
    'evening':  00,
    'sunset':   00,
    'dusk':     00,
    'night':    00, 
    'midnight': 00
}
    # 'hours' is needed for recognizing 24 hour time speach
#TIME_WORDS = WEEK_WORDS + MONTH_WORDS + _MISC_TIME_WORDS
#TIME_WORDS_NUMBERS = TIME_WORDS + NUMBER_WORDS + ORDINAL_NUMBER_WORDS


#-------- Special Token Type Symbols --------#

DURATION_SYMBOL = 'DUR'


#-------- Supporting Functions --------#

def remove_start_end_punctuation(word:str) -> str:
    """remove all non-alpha-numeric characters from the beginning and end of a word"""
    while True:
        if word:                                            # break if word is empty! (will happen if a word has no alpha numeric chars)
            if not word[0].isalnum():
                word = word[1:]                             # remove first character and restart loop
                continue
            elif not word[-1].isalnum():
                word = word[:-1]                            # remove last character and restart loop
                continue
        break
    return word

def _get_number_from_string(num_str:str) -> int|float:
    """try converting string into int or float, otherwise return None"""
    try:
        try:
            return int(num_str)
        except ValueError:
            return float(num_str)
    except:
        return None

def _get_number_str_from_words(num_words:list) -> str:
    """convert a list of number words to a matching string of digits"""

    # make a new list from num_words, converting each word to a string of the 
    # corresponding number in ALL_NUMBER_WORD_MAP, excluding any words which aren't in ALL_NUMBER_WORD_MAP.
    num_list = [str(ALL_NUMBER_WORD_MAP.get(word)) for word in num_words if word in ALL_NUMBER_WORD_MAP]

    final_number = last_num = num_list.pop()                        # set last number in list to be the current final_number and last_num, and remove it from list

    for num in reversed(num_list):                                  # iterate through list in reverse
        if len(num) > len(final_number):                            # if this number is longer in digits than final_number
            if int(final_number) == 0:                              ## and if final_number equal to zero
                final_number = num + final_number                   ### then prepend it to final_number
            else:                                                   ## and if final_number is not equal to zero
                final_number = str(int(final_number) + int(num))    ### then add both together as ints
        
        elif len(num) <= len(final_number):                         # if this number has the same number or less digits than final_number
            if len(last_num) >= 3:                                  ## and if last number is a grand
                final_number = num + final_number[1:]               ### then replace leading digit of final_number with this current number
            else:                                                   ## and if last_num is single or double digit number
                if int(num) >= 20 and len(num) > len(last_num):     ### and if current number is a tens or grand and has more digits than last number
                    final_number = num[:-len(last_num)] + final_number  #### then remove 'length-of-last_num' number of digits from the right of the current number, and prepend that to final_number
                else:                                               ### otherwise
                    final_number = num + final_number               #### prepend it to final_number
        
        last_num = num          # set current number to be last_num for next loop cycle
    
    return final_number


#-------- Tokenization Functions (main accesible functions) --------#

def get_basic_tokens_and_quote_sections(text:str) -> tuple[list[str], list[str]]:
    """Returns a list containing only the individual words/tokens within a string of text, 
    along with a list of strings which were surrounded by quotes. Meant to be used with a sentence or phrase."""
    tokens = []
    quotes = []
    current_word = ''
    current_sentence = ''

    def add_current_word():
        stripped_word = remove_start_end_punctuation(current_word).lower()
        if stripped_word:
            tokens.append(stripped_word)
    
    # first check for all instances of the words "quote" and "unquote" in order in the string, and replace any of these pairs with double quote characters, surrounding the text between them
    while True:
        if "quote" in text.lower() and "unquote" in text.lower():
            text_split = text.split()
            text_stripped_words = [remove_start_end_punctuation(word).lower() for word in text_split]
            try:
                q1 = text_stripped_words.index("quote")
                q2 = text_stripped_words.index("unquote")
                if q2 > q1:
                    text_split[q1+1] = '"' + text_split[q1+1]   # add first quote char to the left of the word after 'quote'
                    text_split[q2-1] = text_split[q2-1] + '"'   # add second quote char to the right of the word after 'unquote'
                    text_split.pop(q2)
                    text_split.pop(q1)
                text = ' '.join(text_split)
            except:
                pass
        else:
            break
    # now go through the text one character at a time
    for char in text:
        if char == ' ' and current_word:                    # if the character is a whitespace and `current_word` is not empty, append a cleaned up version of it to tokens
            add_current_word()
            current_word= ''
        elif char == '"':                                   # if the character is a double quote, either treat it as the start of the sentence, or the end of it. Append any complete sentence to tokens and quotes
            if current_sentence:
                tokens.append(current_sentence[1:])         # index from 1 to remove the initial quote (") character
                quotes.append(current_sentence[1:])
                current_sentence = ''
            else:
                current_sentence += char
        else:                                               # otherwise, append the character to current_string if it's not empty, and current_word if it is
            if current_sentence:
                current_sentence += char
            else:
                current_word += char
    if current_word:                                        # append any remaining current_word to tokens
        add_current_word()
    if current_sentence:                                    # if a sentence was started but never completed, then treat it as individual words
        new_tokens, quotes = get_basic_tokens_and_quote_sections(current_sentence)
        tokens.extend(new_tokens)

    return tokens, quotes


def convert_words_to_numbers(words:list[str]) -> tuple[list, list]:
    """Convert all of the number words in a list into actual numbers. Also return a list of each group of words what was converted."""
    new_tokens = []                                         # holds the words and numbers
    converted_words = []                                    # holds lists of each group of converted words (original number words)
    
    current_number_words = []                               # temporary number words to be processed into numbers
    last_word = None                                        # the previous word in the list cycle

    def convert_current_num_words():
        if current_number_words:                            # if current_number_words has any items
            converted_words.append(current_number_words.copy())     # first append a copy of the number words list to converted_words
            if "oh" in current_number_words:                # convert any "oh" to "zero"
                for i, word in enumerate(current_number_words):
                    if word == "oh":
                        current_number_words[i] = "zero"
            try:
                i = current_number_words.index("point")     # if "point" is in the words, treat this as a float number
                whole = _get_number_str_from_words(current_number_words[:i])        # first half (whole) of float
                decimal = _get_number_str_from_words(current_number_words[i+1:])    # second half of (decimal) of float
                number = float(whole + '.' + decimal)       # combine both ints with '.' in middle, and convert all to float
            except:                                         # otherwise treat as int
                number = int(_get_number_str_from_words(current_number_words))
            new_tokens.append(number)                       # add number to tokens
            current_number_words.clear()                    # reset current_number_words

    # main loop
    for i, word in enumerate(words):
        try:
            next_word = words[i+1]                          # get next word in list
        except:
            next_word = None
        
        # if the word is 'and' and it's in between 2 number words, the previous being anything higher than a tens
        if word == 'and' and ((current_number_words and ALL_NUMBER_WORD_MAP.get(last_word) >= 100) and next_word in ALL_NUMBER_WORD_MAP):
            current_number_words.append(word)               # then treat it as part of the current number
        # if the word is 'point' and it's in between 2 number words,
        elif word == 'point' and (current_number_words and (next_word in ALL_NUMBER_WORD_MAP or next_word == "oh")):  
            current_number_words.append(word)               # then treat it as part of the current number (will become a float)
        # if the word is "oh" and it's next to at least 1 number word, 
        elif word == 'oh' and (current_number_words or (next_word in ALL_NUMBER_WORD_MAP or next_word in ("point", "oh"))):
            current_number_words.append(word)               # then treat it as part of the current number (will be converted to "zero") -> isn't converted now, so that "oh" can be placed in converted words
        # if the word is a number word
        elif word in ALL_NUMBER_WORD_MAP:
            current_number_words.append(word)               # then add it to current_number_words
        # otherwise if the word is not any sort of number word
        else:
            convert_current_num_words()                     # first convert any previous number words
            number = _get_number_from_string(word)          # try converting into int or float (in case it's typed out number digit character, but not number words!)
            if number:
                converted_words.append([word])              # append a list with only original digit string to converted_words
                word = number
            new_tokens.append(word)                         # then append it to tokens

        last_word = word                                    # set last_word to be word

    convert_current_num_words()                             # convert any remianing number words 

    return new_tokens, converted_words


def convert_words_numbers_to_times(words_numbers:list):
    """Convert all of the words and numbers in a list into Unix (epoch seconds) time objects"""
    pass


def convert_words_to_durations(words:list) -> tuple[list, list]:
    """Convert all of the words in a list into intergers representing duration in seconds"""
    # all spoken/writen durations will roughly follow the formula of: 'quanity' (which is a word or number) + durational unit (a word)
    # and if these 'quanitity + unit' pairs are next to each other (or separated by 'and'), they belong to the same duration
    tokens, converted = convert_words_to_numbers(words)     # first convert number words and colloqial quantity words to numbers
    new_tokens = []                                         # holds the words, numbers, and newly created times
    last_token = None                                       # the previous token in the list cycle
    # 1) First cycle -> pair up quantities (numbers) and durational units ('minute', 'hour', etc.)
    for token in tokens:
        if isinstance(token, str):
            singular_last_token = last_token.removesuffix('s') if isinstance(last_token, str) else None
            singular_token = token.removesuffix('s')        # create a singular copy of the word (if 's' not there, doesn't change anything)
            # if the previous token (singular) was in duration_word_map, and this token is a string, regardless of its value, append it to new_tokens:
            if singular_last_token in DURATION_WORD_MAP:
                new_tokens.append(token)
            # else if the current token (singular) is in duration_word_map:
            elif singular_token in DURATION_WORD_MAP:
                # and if the last number is a number, then pair the current token and last token together in a tuple, and put it in new_tokens:
                if is_numbers(last_token):
                    new_tokens[-1] = (last_token, token)    # replace the last_token number with this
                # or if 'a' or 'an' is before it, pair both:
                elif last_token in ('a', 'an'):
                    new_tokens[-1] = (last_token, token)    # replace the last_token number with this
                # otherwise, do the same but don't pair current token:
                else:
                    new_tokens.append((token,))
        # otherwse just append token to new_tokens
            else:
                new_tokens.append(token)
        else:
            new_tokens.append(token)
        
        last_token = token

    tokens = new_tokens                                     # move new_tokens into tokens, and reset new_tokens
    new_tokens = []
    converted_words = []                                    # holds lists of each group of converted original words
    current_duration = []                                   # temporary duration tokens to be processed into duration

    def process_current_duration():
        if current_duration:
            duration = 0
            og_words = []
            for dur in current_duration:
                if isinstance(dur, tuple):
                    if len(dur) == 2:
                        quantity, unit = dur                # use first item in tuple as quantity (if number), and second string as unit
                        if is_numbers(quantity):
                            og_words.extend(converted.pop(0))   # add the number's original words to og_words
                        else:
                            og_words.append(quantity)       # if quantity is not a number, append it to og_words and set it to `1`
                            quantity = 1
                    else:
                        quantity = 1
                        unit = dur[0]                       # otherwise use `1` as quantity and the single string item as unit
                    og_words.append(unit)
                    # calculate durational seconds by getting the corresponding seconds int value of the unit str (singular) multiplied by the quantity int, and add that to `duration`
                    duration += quantity * DURATION_WORD_MAP[unit.removesuffix('s')]
                else:
                    og_words.append(dur)                    # if not tuple, must be "and" - just add this to og_words
            new_tokens.append((DURATION_SYMBOL, duration))  # append the full duration to new_tokens
            converted_words.append(og_words)                # and the og_words to converted words (will be combined with the original converted words of any converted number used in the duration)
            current_duration.clear()                        # then reset current durration

    # 2) Second cycle -> process any durational pairs (tuples of quanitity and unit), and process them together as a single duration if they're next to each other (or has 'and' between them)
    for i, token in enumerate(tokens):
        # see what the next token is (unless this is the last element in list):
        try:
            next_token = tokens[i+1]
        except:
            next_token = None
        # if the token is 'and' and it's inbetween two durations, add to current_duration:
        if token == 'and' and current_duration and isinstance(next_token, tuple):
            current_duration.append(token)
        # if token is a duration (tuple), add to current_diration
        elif isinstance(token, tuple):
            current_duration.append(token)
        # otherwise, process any current_duration, and add token to new_tokens
        else:
            if is_numbers(token):
                converted_words.append(converted.pop(0))    # move the *first* converted word group out of `converted` and append into `converted_words`
            process_current_duration()
            new_tokens.append(token)

    process_current_duration()                              # process any remaining durations
    return new_tokens, converted_words
