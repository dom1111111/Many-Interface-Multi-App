import sys
from os import chdir, path
from os.path import dirname, join

sys.path.append(dirname(__file__))
sys.path.append(dirname(dirname(__file__)))
sys.path.append(join(dirname(dirname(__file__)), "app"))

from app.input_command_processing import command_data_loader, input_string_processing, command_processing
from app.GUI_audio_voice import speech_proc
from app.input_command_processing import input_string_processing as input_proc

chdir(path.dirname(__file__))

#------

# set this to True to have tests print out return values and other values related to the things they're testing
PRINT_OUTPUT = True

def optional_print(*args):
    if PRINT_OUTPUT:
        print(*args)

#------

COMMAND_DATA_FILEPATH = "test_com_data.json"

TEST_FUNC_MAP = {
    'SAY':          print,
    'SHUTDOWN':     exit,
    'DISMISS':      print,
    'IS_SPEAKING':  lambda: True,
    'GET_TIME':     print,
    'GET_DATE':     print,
    'START_TIMER':  print,
    'STOP_TIMER':   print,
    'GET_TIMER':    print,
    'TIMER_ACTIVE': lambda: True,
    #'set_alarm':
}


#-------- `command_data_loader` tests --------#

def test_command_data_loader():
    commands = command_data_loader.load_commands(COMMAND_DATA_FILEPATH, TEST_FUNC_MAP)

    if PRINT_OUTPUT:
        for name, data in commands.items():
            print(f"\n------{name}------")
            for key, val in data.items():
                print(' '*3, key)
                try:
                    for sub_val in val:
                        print(' '*7, sub_val)
                except:
                    print(' '*7, val)
    
    #assert commands == 


#--- Commands to use for further testing ---#
commands = command_data_loader.load_commands(COMMAND_DATA_FILEPATH, TEST_FUNC_MAP)


#-------- `input_string_processing` tests --------#

def test_basic_tokenizer():
    input_text_list = [
        (   # single pair of double quote characters
            """ Hello there! I would like to order the "cooked tree -sap d' onut", please and thank you!""", 
            ['hello', 'there', 'i', 'would', 'like', 'to', 'order', 'the', "cooked tree -sap d' onut", 'please', 'and', 'thank', 'you']
        ),
        (   # single pair of 'quote' + 'unquote' pair
            """ Hello there! I would like to order the quote, cooked tree -sap d' onut unquote, please and thank you!""", 
            ['hello', 'there', 'i', 'would', 'like', 'to', 'order', 'the', "cooked tree -sap d' onut", 'please', 'and', 'thank', 'you']
        ),
        (   # multiple pairs of double quote characters
            """Once upon a time there was a "cool dragon", who lived in a "stylish rave cave", and this is a true story.""", 
            ['once', 'upon', 'a', 'time', 'there', 'was', 'a', "cool dragon", 'who', 'lived', 'in', 'a', "stylish rave cave", 'and', 'this', 'is', 'a', 'true', 'story']
        ),
        (   # multiple pairs of 'quote' + 'unquote' pair
            """Once upon a time there was a quote cool dragon unquote, who lived in a quote stylish rave cave unquote, and this is a true story.""", 
            ['once', 'upon', 'a', 'time', 'there', 'was', 'a', "cool dragon", 'who', 'lived', 'in', 'a', "stylish rave cave", 'and', 'this', 'is', 'a', 'true', 'story']
        )
    ]
    optional_print('\n' + '-'*50)
    optional_print('__' + 'test_basic_tokenizer' + '__')
    for text, expected_value in input_text_list:
        tokens, quotes = input_proc.get_basic_tokens_and_quote_sections(text)
        optional_print('\ntokens:', tokens)
        optional_print('quotes:', quotes)
        assert tokens == expected_value

def test_word_to_number_converter():
    input_text_list = [
        (
            "I really want to eat five hundred and sixty five apples and just shy of seven point six two five bananas", 
            ['i', 'really', 'want', 'to', 'eat', 565, 'apples', 'and', 'just', 'shy', 'of', 7.625, 'bananas'],
            [['five', 'hundred', 'and', 'sixty', 'five'], ['seven', 'point', 'six', 'two', 'five']]
        ),
        (
            "I really want to eat five hundred and sixty five, and just shy of seven point six two five, apples and bananas, respectively", 
            ['i', 'really', 'want', 'to', 'eat', 565, 'and', 'just', 'shy', 'of', 7.625, 'apples', 'and', 'bananas', 'respectively'],
            [['five', 'hundred', 'and', 'sixty', 'five'], ['seven', 'point', 'six', 'two', 'five']]
        ),
        (
            "okay so my number is nine oh five, five two six, oh one two three!", 
            ['okay', 'so', 'my', 'number', 'is', 9055260123],
            [['nine', 'oh', 'five', 'five', 'two', 'six', 'oh', 'one', 'two', 'three']]
        ),
        (
            "the only number here is 11 and twelve", 
            ['the', 'only', 'number', 'here', 'is', 11, 'and', 12],
            [['11'], ['twelve']]
        ),
    ]
    optional_print('\n' + '-'*50)
    optional_print('__' + 'test_word_to_number_converter' + '__')
    for text, expected_new_tokens, expected_changed_tokens in input_text_list:
        basic_tokens, quotes = input_string_processing.get_basic_tokens_and_quote_sections(text)
        updated_tokens, original_converted_words = input_string_processing.convert_words_to_numbers(basic_tokens)
        optional_print('\norginal text:                           ', text)
        optional_print('updated tokens:                         ', updated_tokens)
        optional_print('original tokens turned into numbers:    ', original_converted_words)
        optional_print('updated text:                           ', " ".join(str(token) for token in updated_tokens))
        assert updated_tokens == expected_new_tokens
        assert original_converted_words == expected_changed_tokens

def test_word_to_duration_converter():
    input_text_list = [
        (
            "Can you please set a timer for two hours and twenty two minutes. Thank you.", 
            ['can', 'you', 'please', 'set', 'a', 'timer', 'for', ('DUR', 8520), 'thank', 'you'],
            [['two', 'hours', 'and', 'twenty', 'two', 'minutes']]
        ),
        (
            "Can you please set a timer for an hour and twenty two minutes. Thank you.",
            ['can', 'you', 'please', 'set', 'a', 'timer', 'for', ('DUR', 4920), 'thank', 'you'],
            [['an', 'hour', 'and', 'twenty', 'two', 'minutes']]
        ),
        (
            "I think it'll take you about minute and 40 seconds, if you move fast. But no less than 3 minutes if not!",
            ['i', 'think', "it'll", 'take', 'you', 'about', ('DUR', 100), 'if', 'you', 'move', 'fast', 'but', 'no', 'less', 'than', ('DUR', 180), 'if', 'not'],
            [['minute', 'and', '40', 'seconds'], ['3', 'minutes']]
        ),
        (
            "Set a timer 10 second",
            ['set', 'a', "timer", ('DUR', 10)],
            [['10', 'second']]
        ),
    ]
    optional_print('\n' + '-'*50)
    optional_print('__' + 'test_word_to_number_duration' + '__')
    for text, expected_new_tokens, expected_changed_tokens in input_text_list:
        basic_tokens, quotes = input_string_processing.get_basic_tokens_and_quote_sections(text)
        updated_tokens, original_converted_words = input_string_processing.convert_words_to_durations(basic_tokens)
        optional_print('\norginal text:                                   ', text)
        optional_print('updated tokens:                                 ', updated_tokens)
        optional_print('original tokens turned into duration seconds:   ', original_converted_words)
        assert updated_tokens == expected_new_tokens
        assert original_converted_words == expected_changed_tokens


#-------- `command_processing` tests --------#

def test_unique_vocab_generator():
    # this was used to test nested mutli-reqs:
    # `        "remaining":    ["<ANY>", "remaining", "left", ["<ALL>", ["<ANY>", "yes", "affirmative", ["<ANY>", "okey", "okay"]], ["<ANY>", "no", "nope", "negative"]]],`
    unique_vocab_map = command_processing.get_unique_input_vocab_map(commands)
    for name, vocab in unique_vocab_map.items():
        optional_print('\n', name, '\n', vocab)

def test_command_checker():
    speech_processor = speech_proc.SpeechProcessor()
    input_text_list = [
        (
            """Hi there, can you please give me the time?""", 
            ('Get Time', ['give', 'time'])
        ),
        (
            """Create a new note with the content, I like to eat ... hot! spicy! cheese!""" , 
            ('Create Quick Note', ['create', 'note', 'content', 'I like to eat ... hot! spicy! cheese!'])
        ),
        (
            """Please set a timer for 1 hour and 10 minutes.""" , 
            ('Start Timer', ['timer', 'set', 4200])
        ),
        (
            """Make a note with content "Are birds even real? I say: '-`-11``23452345%@#$%WE'. Okay?".""" , 
            ('Create Quick Note', ['make', 'note', 'content', "Are birds even real? I say: '-`-11``23452345%@#$%WE'. Okay?"])
        )
    ]
    optional_print('\n' + '-'*50)
    optional_print('__' + 'test_command_checker' + '__')
    for text, expected_value in input_text_list:
        return_value = command_processing.get_commands_matching_input_reqs(text, text, commands, speech_processor.transcribe)
        optional_print(f'\ninput: "{text}"')
        optional_print("matching command:", return_value)
        assert return_value == expected_value


#----------------------#
#----------------------#

# test_command_data_loader()

# test_basic_tokenizer()
# test_word_to_number_converter()
# test_word_to_duration_converter()

# test_unique_vocab_generator()
# test_command_checker()

# optional_print()