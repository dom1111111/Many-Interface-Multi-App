import json
from .command_processing import REQ_TYPES
from .input_string_processing import _get_number_from_string
from .misc_tools import is_numbers


#-------- Command Data Symbols --------#

# value modifier symbols:
_ESCAPE = '/'
_ALIAS = '^'
# input requirement type symbols
_OPEN = "<_>"
_NUMBER = "<#>"
_TIME = "<T>"
_DURATION = "<D>"
_ANY = '<ANY>'
_ALL = '<ALL>'
_ORDERED = '<ORD>'
# special reference symbols
_INPUT_INDEX = "^I"
_ACTION_INDEX = "^A"


#-------- Supporting Conversion Functions --------#

def _get_alias(req, aliases:dict):
    """If a requirement is an alias for another value, return the alias value. Otherwise just return the requirement back as is"""
    new_req = req
    if isinstance(req, str) and req.startswith(_ALIAS): # if the req is a string starting with the alias-prefix
        new_req = aliases.get(req.removeprefix(_ALIAS)) # try setting requirement match value to corresponding value (after the alias prefix) in aliases dict
        assert new_req != None, f'"{req}" alias does not exist'
    return new_req

def _get_input_req_val_number_range(req_value:str, og_req) -> tuple:
    """Get a tuple of any specified range of numbers (after type prefix) for certain input requirement types (number, time, duration).
    If no range is specified, then return the requirement value unaffected. Also pass in original requirement value for error reporting"""
    error_msg =  f"{og_req} is invalid. Any input requirement string which begins with the number-type, time-type, or duration-type prefix must be a string representing a number (ex: `1`) or a range of numbers (ex: `1-10`)"
    range = None
    if '-' in req_value:
        range = tuple(_get_number_from_string(n) for n in req_value.split('-'))
        assert len(range) == 2 and is_numbers(range), error_msg
    elif req_value:
        range = _get_number_from_string(req_value)
        range = (range, range)                          # even for single number, must return a tuple representing range of numbers
        assert is_numbers(range), error_msg
    return range

def _get_func_ref(ref:str|list, func_map:dict) -> tuple:
    """convert any function string reference (found in function-requirements or actions) to a tuple with the actual function reference and args"""
    if isinstance(ref, str):                            # if the function reference is just a string, 
        name = ref                                      # then the string is the name of the function, 
        args = ()                                       # and there are no arguments to pass to it
    elif isinstance(ref, list):                         # if the function reference is a list
        assert len(ref) > 1 , f"{ref} invalid. Any array/list starting with a function reference must have more than one item"
        name = ref[0]                                   # then first element is the function name
        args = tuple(ref[1:])                           # and any subsequent items are args to pass to it
    func_ref = func_map.get(name)                       # get actual internal function reference from name in func_map
    assert func_ref != None, f'no matching function found for "{name}" string reference'
    assert callable(func_ref), f'"{name}" is not callable'
    return (func_ref, args)


#-------- Primary Conversion Functions for Each of the 2 Command Requirements Properties --------#

# 1) convert single pre requirement
def _convert_pre_req(freq:list, action_func_map:dict) -> tuple:
    """convert a pre-requirement into a tuple: (func, (args), required_return_value)"""
    # the first item must always be the function name ref, and the last item must be the return value to check
    # any items inbetween (optional) are args to pass to the function
    assert len(freq) >= 2, "All function requirements need 1 function and a return value to check"    
    if len(freq) > 2:
        return (_get_func_ref(freq[:-1], action_func_map)) + (freq[-1],)
    else:
        return (_get_func_ref(freq[0], action_func_map)) + (freq[1],)

# 2) convert single input requirement
def _convert_input_req(req, aliases:dict) -> tuple:
    """convert an input requirement into a tuple: (type, match_value, replace)"""
    r_type, value, replacement = None, None, None
    og_req = req
    # 1. check and convert requirement if it's an alias:
    req = _get_alias(req, aliases)
    # 2. get any replacement return values:
    if isinstance(req, dict):
        assert len(req) == 1, "Command requirements which are objects must have only one key:value pair"
        req = list(req.items())                         # convert items to list of tuple
        req = req[0][0]                                 # the key is the actual initial requirement value to convert
        replacement = req[2]                            # the value is the replacement value
    # 3. determine requirement type and/or match value:
    if isinstance(req, str):
        if req == _OPEN:                                # OPEN
            r_type = "OPEN"
        elif req.startswith(_NUMBER):                   # NUMBER
            r_type = "NUMBER"
            value = req.removeprefix(_NUMBER)
            value = _get_input_req_val_number_range(value, og_req)
        elif req.startswith(_TIME):                     # TIME
            r_type = "TIME"
        elif req.startswith(_DURATION):                 # DURATION
            r_type = "DURATION"
            value = req.removeprefix(_DURATION)
            value = _get_input_req_val_number_range(value, og_req)
        else:
            if req.startswith(_ESCAPE):
                req = req[1:]                           # if the string starts with the escape character, then set match value to be everything after it
            else:
                req_split = req.split()
                if len(req_split) > 1:                  # if the string has mutliple words in it (whitespace in between) then treat it as an ordered-type req
                    r_type = "ORDERED"                  # ORDERED
                    value = [('STRING', word, None) for word in req_split]
                else:                                   # STRING
                    r_type = "STRING"
                    value = req
    elif isinstance(req, list):
        type_symbol = req[0]
        if type_symbol ==  _ANY:                        # ANY
            r_type = "ANY"
        elif type_symbol == _ALL:                       # ALL
            r_type = "ALL"
        elif type_symbol == _ORDERED:                   # ORDERED
            r_type = "ORDERED"
        else:
            raise Exception(f'"{req}" is invalid. All requirement values which are arrays must have their first item be a string: "ANY", "ALL", or "ORD"')
        value = [_convert_input_req(sub_req, aliases) for sub_req in req[1:]] # run each nested item (after the first) through the same function
    # 4. ensure that match value was generated and that it's in the list of REQ_TYPES
    if not r_type in REQ_TYPES:
        raise Exception(f'"{og_req}" is an invalid requirement')

    return (r_type, value, replacement)


#-------- Action Function Generation Function --------#

# 3) convert all actions
def _generate_actions_func(actions:list):
    """Generates and returns a function which executes all of the actions from the provided command action list"""

    def command_actions(input_req_values:list):
        return_values = []
        for func, args in actions:
            new_args = []
            # update any args which are references to input requirements or previous function return values:
            for arg in args:
                if isinstance(arg, str):
                    if arg.startswith(_INPUT_INDEX):            # if the string arg starts with the input-index symbol
                        i = int(arg.removeprefix(_INPUT_INDEX)) # then extract the following number to use as an index,
                        arg = input_req_values[i]               # and use input_req_values's value at index as the arg   
                    elif arg.startswith(_ACTION_INDEX):         # if the string arg starts with the action-index symbol, 
                        i = int(arg.removeprefix(_ACTION_INDEX))# then extract the following number to use as an index,
                        arg = return_values[i]                  # and use return_values's value at index as the arg 
                new_args.append(arg)
            return_values.append(func(*new_args))               # call the function with the args and append the result to return values

    return command_actions


#-------- Main Accessible Command Loader Function --------#

def load_commands(commands_path:str, func_map:dict) -> dict:
    """Load json containing commands from `command_path`, check that their code is valid, 
    and convert command data into internally usable list of commands."""
    # 1) load JSON file:
    with open(commands_path, 'r') as coms:
        data = json.load(coms)
    
    # 2) check that the loaded data is an dict with both "aliases" and "commands" sub dicts:
    aliases = data.get("aliases")
    commands = data.get("commands")
    assert isinstance(aliases, dict) and isinstance(commands, dict), f"""the JSON file at '{commands_path}' has incorrect base structure. File must contain a JSON object, which itself contains 2 other objects called "aliases" and "commands"."""
    
    # 3) convert the command data:
    converted_commands = {}
    for com_name, com_data in commands.items():
        # check that each command dict has the correct structure and valid values:
        assert isinstance(com_data, dict) and tuple(com_data) == ('preqs', 'input', 'actns'), f"'{com_name}' command is invalid. All commands must be an object with the keys 'preqs', 'input', and 'actns'"
        assert all(isinstance(val, list) for val in com_data.values()), f"'{com_name}' command is invalid. Each command object's values must be arrays"
        assert len(com_data["preqs"]) > 0 or len(com_data["input"]) > 0, f"'{com_name}' command is invalid. Each command must have at least one pre-requirement or one input requirement. Can have multiple of both, but can't have neither"
        assert len(com_data["actns"]) > 0, f"'{com_name}' command is invalid. Each command must have at least one action"
        # convert command requirements into tuples with any references replaced with their corresponding values:
        preqs = [_convert_pre_req(preq, func_map) for preq in com_data.get("preqs")]
        input_reqs = [_convert_input_req(inp_req, aliases) for inp_req in com_data.get("input")]
        # convert and combine all actions into a single function with any references replaced with their corresponding values:
        action_func = _generate_actions_func([_get_func_ref(action, func_map) for action in com_data.get("actns")])
        # add fully converted command to converted_commands:
        converted_commands.update({
            com_name: {
                'preqs': preqs, 
                'input': input_reqs,
                'action': action_func
            }
        })

    return converted_commands
