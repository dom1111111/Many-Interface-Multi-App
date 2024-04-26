from typing import Callable
from . import input_string_processing as input_proc
from .misc_tools import flatten_generator, is_numbers


# input requirement type internal values:
REQ_TYPES = ("STRING", "OPEN", "NUMBER", "TIME", "DURATION", "ANY", "ALL", "ORDERED")
_OPEN_PLACEHOLDER = "~?OPEN?~"


#-------- Functions for Generating Command Input Requirement Indices --------#

def _get_input_req_vocab(input_req:tuple) -> list:
    """Get all of the vocabulary / tokens for a given single input requirement"""
    req_type, req_val, repl_val = input_req
    if req_type == "STRING" and req_val:
        return req_val.split()
    elif req_type == "NUMBER":
        return input_proc.FULL_NUMBER_VOCAB
    elif req_type == "TIME":
        return []
    elif req_type == "DURATION":
        return input_proc.FULL_NUMBER_VOCAB + list(input_proc.DURATION_WORD_MAP.keys())
    elif req_type in ("ANY", "ALL", "ORDERED"):
        return [vocab for vocab in flatten_generator(_get_input_req_vocab(sub_req) for sub_req in req_val)]

def _get_input_req_string_counts_and_vocab(input_req:tuple, vocab_counts:dict) -> int:
    """Pass in an input requirement, and a dictionary containing each STRING-type word and the amount of 
    times it appears across commands, and get the total count of that input requirement's STRING-type 
    vocabulary along with the vocabulary itself. This means: 

    - the count of the value/word if a STRING type
    - the total count of value/words of nested STRING-types if an ANY type containing only string types
    - the total count of value/words of only nested STRING-types if an ALL/ORDERED.
    
    Otherwise, if the requirement type doesn't correspond to the above, return 0"""
    req_type, req_val, replacement = input_req
    vocab = []
    count = 0
    if req_type == "STRING":
        str_count = vocab_counts.get(req_val)
        if str_count:                       # if req type is STRING, add it is within `vocab_counts`, append its value and add count 
            vocab.append(req_val)
            count += str_count
    elif req_type == "ANY":
        for sub_req in req_val:
            sub_vocab, sub_count = _get_input_req_string_counts_and_vocab(sub_req, vocab_counts)
            if not sub_count:
                return [], 0                # if any of the `sub_counts` are 0 (meaning not STRING or not present in vocab_counts), then immediately return an empty list and 0 for the entire thing
            else:
                vocab.append(sub_vocab)
                count += sub_count
    elif req_type in ("ALL", "ORDERED"):
        for sub_req in req_val:
            sub_vocab, sub_count = _get_input_req_string_counts_and_vocab(sub_req, vocab_counts)
            if not sub_count:               # skip this sub req if it has no count
                continue
            # if count hasn't been started yet (is 0) or the current sub_count is less than the overall count, 
            # then change the count to be this sub_count, and replace the vocab with this sub_vocab 
            if not count or sub_count < count:
                vocab = [sub_vocab]
                count = sub_count
            else:
                vocab.append(sub_vocab)
        # among all sub_reqs with the smallest count, use the one with the shortest vocabulary (if there are multiple with shortest, will take the first one)
        i, shortest_vocab = min([(i, list(flatten_generator(sub_vocab))) for i, sub_vocab in enumerate(vocab)], key=lambda x: len(x[1]))
        vocab = [vocab[i]]
    return list(flatten_generator(vocab)), count

def get_input_req_vocab_index(commands:dict) -> dict:
    """Generate an index of command input requirement words/tokens/vocabulary to command names."""
    index = {}
    for name, data in commands.items():
        func_reqs, input_reqs, actns = data.values()
        # collect all of the command's input requirement tokens, excluding any empty entries:
        req_tokens = [word for word in flatten_generator(_get_input_req_vocab(req) for req in input_reqs) if word]
        for token in req_tokens:
            try:
                index[token].append(name)                   # if the req token already exists as a key in index, then update value list with the command name
            except:
                index.update({token: [name]})               # otherwise create a new entry, with req token as key, and list with command name as value
    return index

def get_unique_input_vocab_map(commands:dict) -> dict:
    """Generate a dict containing the name and vocabulary (word tokens) of each command's most unique 
    input requirement (least used among other commands). Only considers string-type requirements 
    or string requirements nested in any/all/ordered-types."""
    com_to_vocab = {}
    # (1) Create a dict of commands' input requirement words/tokens/vocabulary to command names
    vocab_counts = {word:len(com_names) for word, com_names in get_input_req_vocab_index(commands).items()}
    # (2) Now determine the input requirement withe the most unique vocabulary in each command
        # - STRING type requirements are simple, and their one value is their entire vocabulary, 
        # and how ever many times that value shows up, is the total count for this req.
        # - ANY type requirements must have all of their STRING type sub reqs included, and so the count is summed across them. This
        # is because any of the sub reqs could be used in the input to get to the command, so *all* sub-reqs must be considered.
        # - the opposite is true for ALL/ORDERED types because all of the sub-reqs must be used in input, and therefore the use of *any*
        # one of them ensures that this req is reached. Only one STRING type's vocab within the all/ord needs to be used (and so the most unique one / longest is used).
    for name, data in commands.items():
        func_reqs, input_reqs, actns = data.values()
        req_counts = [_get_input_req_string_counts_and_vocab(req, vocab_counts) for req in input_reqs]
        req_counts = [x for x in req_counts if x[1]]
        smallest_req_count = min(req_counts, key=lambda x: x[1])
        com_to_vocab.update({name: smallest_req_count[0]})

    return com_to_vocab

def get_full_input_vocab_map(commands:dict) -> dict:
    """Generate a dict containing each command's name and the collective vocabulary (word tokens) of all its input requirements"""
    # for each command, get the vocabulary of each input requirement (data.values()[1]), combine them together in a single list with the flatten_generator, 
    # remove duplicates by converting to a set, then convert back to a list and use that as the value and command name as key in the dictionary comprehension
    return {name: list({v for v in flatten_generator(_get_input_req_vocab(req) for req in tuple(data.values())[1]) if v}) for name, data in commands.items()}


#-------- Command Name Filtering Functions --------#

def get_pre_req_only_coms(commands:dict) -> dict:
    """return all commands which have no input requirements, and only pre requirements"""
    return {name:data for name, data in commands.items() if data["preqs"] and not data["input"]}

def get_input_req_only_coms(commands:dict):
    """return all commands which have no pre requirements, and only input requirements"""
    return {name:data for name, data in commands.items() if data["input"] and not data["preqs"]}


#-------- Matching Support Functions --------#

def _check_input_req_get_values(req:tuple, input_tokens:list) -> tuple:
    """Get the matched value and final value of any input requirement.
    - 'matched value' is the part of user_input that met the requirement.
    - 'final value' is the value to be used should the requirement be met."""
    matched_value = None
    req_type, req_val, rpl_val = req                        # all input requirements will have a type, value to match, and possibly a replacement value

    # STRING - requirement is considered matched if its value is in the input_tokens
    if req_type == "STRING":
        matched_value = req_val if req_val in input_tokens else None
    # OPEN - will be handled later (if all other requirements are met), so just set matched value to be a placeholder
    elif req_type == "OPEN":
        matched_value = _OPEN_PLACEHOLDER
    elif req_type in ("NUMBER", "TIME", "DURATION"):
    # NUMBER - requirement considered matched if a number can be generated within the input text and if the number is within any specified value range
        if req_type == "NUMBER":
            new_input_tokens, converted_original_tokens = input_proc.convert_words_to_numbers(input_tokens)
            token_condition = lambda tok: is_numbers(tok)
    # INCOMPLETE
        elif req_type == "TIME":
            pass    ### same code as number, but check for time and then convert unix epoch second int
    # DURATION - requirement considered matched if a duration can be generated within the input text and if the duration seconds value is within any specified value range
        elif req_type == "DURATION":
            new_input_tokens, converted_original_tokens = input_proc.convert_words_to_durations(input_tokens)
            token_condition = lambda tok: isinstance(tok, tuple) and tok[0] == input_proc.DURATION_SYMBOL
        # go through each token and check of token_condition is met:
        for token in new_input_tokens:
            if token_condition(token):
                token = token[1] if isinstance(token, tuple) else token             # use second value of token if tuple
                if req_val and not (token >= req_val[0] and token <= req_val[1]):   # values (`req_val`) for these types will always be a tuple with a minimum and maximum accepted number
                    continue
                rpl_val = token if not rpl_val else rpl_val     # use the generated token as the replacement value if none is specified, otherwise just keep the specified repl value
                matched_value = converted_original_tokens[0]    # use only the *first* list of converted_original_tokens as the overall match value
                break                                           # and use only the first token found (break immediately after one is found)                                              
    # ANY - requirement isn't a requirement on its own, but is considered met if *any* of the requirements within it are met
    elif req_type == "ANY":
        for sub_req in req_val:
            sub_matched, sub_final = _check_input_req_get_values(sub_req, input_tokens)
            if sub_final:           # the final value will not be None if the requirement was met
                matched_value = sub_matched
                rpl_val = sub_final
                break               # only the first met sub req will be used for values (even if multiple may have been met)
    # ALL - is the same as the any-type requirement, except *all* of the contained requirements must be met
    elif req_type in ("ALL", "ORDERED"):
        sub_matches, sub_finals = zip(*(_check_input_req_get_values(sub_req, input_tokens) for sub_req in req_val))     # create 2 tuples for each return value 
        if all(sub_finals):                                 # assign sub_matches to matched_value if all are matches
            if isinstance(sub_matches, list) or isinstance(sub_matches, tuple):
                matched_value = list(flatten_generator(sub_matches))        # if sub_match_vals is list/tuple, make sure there are no sub lists/tuples (flatten)
            else:
                matched_value = list(sub_matches)
    # ORDERED - same as all-type, but must also be in order, and right next to each other
            if req_type == "ORDERED":
                last_i = None
                for sub_matches in matched_value:
                    if isinstance(sub_matches, list):
                        i = input_tokens.index(sub_matches[0])              # get index of the last element in sub-match in input_tokens
                    else:
                        i = input_tokens.index(sub_matches)                 # or get index of the sub-match in input_tokens
                    if not last_i:
                        last_i = i - 1                                      # if last index not set yet, set it to this current index - 1
                    if i - 1 != last_i:
                        matched_value = None                                # if any sub-match's index is not right after the last value's index, then it is not in order
                        break
                    if isinstance(sub_matches, list):
                        last_i = input_tokens.index(sub_matches[-1])        # set last index to be current index of last element in sub_matches before next loop
                    else:
                        last_i = i                                          # or set last index to be current index before next loop

    final_value = rpl_val if matched_value and rpl_val else matched_value   # use a replacement value if specified (and if a match was found), otherwise use matched_value
    return matched_value, final_value

def _get_open_req_value(input_text:str, input_quotes:list, match_values:list):
    """Determine OPEN-type-input-requirement value"""
    # If there was quotes in input, use those as the OPEN req value
    if input_quotes:                            
        open_req_val = input_quotes[-1]                     # always use the last quote if there are multiple
    # Otherwise, remove the matched values from the input text, and use the last remainder as the OPEN req value:
    else:
        SEPARATOR = "___"
        input_split = input_text.split()                    # start by splitting the input_text by whitespace, and then removing punctuation, but NOT doing full tokenization
        input_split_stripped = [input_proc.remove_start_end_punctuation(t).lower() for t in input_split]
        for i, word in enumerate(input_split_stripped):
            if word in match_values:
                match_values.remove(word)                   # if the word is a match value, then remove it from match_values,
                input_split[i] = SEPARATOR                  # and set the match value word in input_split to the separator value
        open_req_val = ' '.join(input_split).strip()        # join the words back into a single string
        i = open_req_val.rindex(SEPARATOR) + len(SEPARATOR)
        open_req_val = open_req_val[i:].strip()             # find the index of last occurrence of the separator, and isolate everything after that index in the string (and remove trailing whitespace)

    return open_req_val


#-------- Main Matching Functions --------#

def get_preq_met_commands(commands:dict) -> dict:
    """Get back all commands which have all of their pre requirements met"""
    preq_met_commands = {}
    for name, data in commands.items():
        preqs, input_reqs, actns = data.values()
        if not preqs:
            continue                                        # if a command has no pre requirements, skip it
        else:
            for func, args, val in preqs:                   # otherwise, check each pre requirement
                if not func(*args) == val:                  # if any of their return values do not match their specified required value, then skip the command
                    break
            else:
                preq_met_commands.update({name: data})      # if all pre reqs are met, add it to the new commands dict
    return preq_met_commands

def get_commands_matching_input_reqs(input_text:str, input_data:str|bytes, commands:dict, transcription_function:Callable) -> tuple:
    """Pass in input text and the list of commands, and return the name and input requirement values
    of the first command which has all of its input requirements met."""
    input_tokens, input_quotes = input_proc.get_basic_tokens_and_quote_sections(input_text)     # split input_text into words/tokens (and extract any quote sections)
    #all_command_req_values = {}
    for name, data in commands.items():
        temp_input_tokens = input_tokens.copy()
        func_reqs, input_reqs, actns = data.values()
        match_values = []
        req_values = []
        # 1) check each individual input requirement in each command
        for req in input_reqs:
            matched_val, final_val = _check_input_req_get_values(req, input_tokens)
            if matched_val:                                 # if the req was matched,
                if matched_val == _OPEN_PLACEHOLDER:        # if match value is the OPEN-requirement placeholder, then do nothing for now (will be handled later)
                    pass
                elif isinstance(matched_val, list):
                    for sub_val in matched_val:
                        match_values.append(sub_val)        # add them to match_values (will be needed later if there's an OPEN type req),
                        i = temp_input_tokens.index(sub_val)
                        temp_input_tokens[i] = None         # and replace the match value(s) in temp_input_tokens with None (this way a value(s) can only be used once)
                else:
                    match_values.append(matched_val)
                    i = temp_input_tokens.index(matched_val)
                    temp_input_tokens[i] = None
            req_values.append(final_val)                    # append the final value to the req_values list
        
        # 2) if all input requirements have been met, get any remaining req values and return the command and the values
        if all(req_values):
            if _OPEN_PLACEHOLDER in req_values:             # check if there was an OPEN requirement, and determine its value
                i = req_values.index(_OPEN_PLACEHOLDER)
                if isinstance(input_data, bytes):           # if input came from voice, first re-transcribe the original input voice audio with full vocabulary, and use that as input_text:
                    input_text = transcription_function(input_data)
                req_values[i] = _get_open_req_value(input_text, input_quotes, match_values) # replace open-placeholder with OPEN req value
            return name, req_values                         # return the command name and its req values
    
    return None, []                                         # if no command is fully met, return None and empty list