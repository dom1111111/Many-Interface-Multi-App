from threading import Thread, Lock
from subprocess import run
from time import sleep
from pprint import pprint
from .GUI_audio_voice.GUI_tk import tkTextBoxGUI
from .input_command_processing import command_data_loader as com_loader, command_processing as com_proc, input_string_processing as input_proc
from .input_command_processing.misc_tools import flatten_generator

#------

# set this to True to print out the App's initial command-related properties and print events in `_main_loop` as they're happening
DEBUG_PRINT = True 

def debug_pprint(*args, title=None):
    if DEBUG_PRINT:
        if title:
            line = '_' * (40 - int(len(title) / 2))
            print('\n' + line + title + line + '\n')
        if args:
            pprint(*args)

#------

class App():
    def __init__(self, commands_path:str, user_func_map:dict=None):
        """
        Instatiate this class to build an instance of the app.

        Accepts 2 arguments:
        - `commands_path` (required): a str path to a JSON file containing the commands (must adhere to proper command data syntax)
        - `user_func_map` (optional): a dictionary containing string refferences to any python functions which the commands may refference

        This class also adds on to the user_func_map with exposure to methods with access to the internal parts app, such as the UI,
        as well as access to external processes (via python's subprocess module).

        Start the app with `run()` method
        """
        #-- UI --#
        self._UI = tkTextBoxGUI("Universal Controller")                                 # the main user interface object
        #-- State --#
        self._active = False                                                            # keeps track of whether or not to keep running main loop

        #-- Action Function Map --#
        self.func_map = {                                                               # an initial map of string refferences to all internal command action methods
            "SHUTDOWN":     self.shutdown,
            "SAY":          self.say,
            "IS_SPEAKING":  self._UI.is_listening,
            "DISMISS":      self.dismiss,
            "RUN":          self.proc_run
        }
        if user_func_map:
            self.func_map.update(user_func_map)                                         # if a user function map arg is provided, add it to the func_map
        #-- Commands and Command Indices --#
        self._commands = com_loader.load_commands(commands_path, self.func_map)         # load command data, ensure that they're valid, convert to internally usable command dict
        self._preq_only_commands = com_proc.get_pre_req_only_coms(self._commands)       # get all commands which have only pre requirements and no input requirements
        self._input_only_commands = com_proc.get_input_req_only_coms(self._commands)    # get all commands which have only input requirements and no pre requirements
        # Command Vocab/Token Indices #
        self._vocab_to_com = com_proc.get_input_req_vocab_index(self._commands)         # generate a vocab-to-command-name index 
        self._com_to_unique_vocab = com_proc.get_unique_input_vocab_map(self._commands) # generate an index of each command's most unique input requirement's vocabulary
        self._com_to_all_vocab = com_proc.get_full_input_vocab_map(self._commands)      # generate an index of each command's vocabulary for all input requirements
        self._unique_vocab_list = list(flatten_generator(self._com_to_unique_vocab.values()))   # generate a list of the most unique vocabulary
        #-- Internal General Vocabulary --#
        self._general_vocab = ['quote', 'unquote']                                      # a list of general words which should be used as transcription vocabulary with most commands, regardless of their input requirements

    #-------- Internal Command Action Methods --------#

    #-- Core system control methods --#

    def shutdown(self):
        """Shutdown app"""
        self.active = False
        self._UI.stop()

    #-- UI methods --#

    def say(self, *message):
        """Output any number of messages to the provided UI"""
        message = ' '.join(str(m) for m in message)
        self._UI.mainview_append(message, "left")
        self._UI.say(message)

    def dismiss(self):
        """Silence any UI components currently making sound and stop listening for voice commands"""
        self._UI.stop_listening()
        self._UI.silence()

    #-- External process method --#

    @staticmethod
    def proc_run(args:list):
        """run a program in a new sub process. Pass in a list of strings for all args, starting with the program/command name"""
        assert isinstance(args, list)
        result = run(args, capture_output=True, text=True)
        output = result.stdout
        error = result.stderr
        if output and not error:
            return output
        elif error and not output:
            return error
            # trigger error noise and message in UI - which wraps around the error
        else:
            pass
            # something else

    #-------- Testing/Debugging Output Methods --------#

    def _print_command_properties(self):
        if DEBUG_PRINT:
            debug_pprint(self._commands, title="Commands")
            debug_pprint(self._preq_only_commands, title="Pre-Requirement Only Commands")
            debug_pprint(self._input_only_commands, title="Input-Requirement Only Commands")
            debug_pprint(self._vocab_to_com, title="Vocab to Command-Name Index")
            debug_pprint(self._com_to_unique_vocab, title="Command-Name to Unique Input Requirement Vocabulary Index")
            debug_pprint(self._unique_vocab_list, title="List of Unique Vocabulary")
            debug_pprint(self._com_to_all_vocab, title="Command-Name to All Input Requirement Vocabulary Index")
            print('\n' + '-'*60 + '\n' + '-'*60 + '\n')

    #-------- Main Run Methods --------#

    def _main_loop(self):
        current_input = None
        last_preq_met_commands = {}                     # this is just for debug print

        while self.active:
            sleep(0.01)
            # (0) isolate only commands which have their initial pre requirements met
            commands = com_proc.get_preq_met_commands(self._commands)
            if commands != last_preq_met_commands:
                debug_pprint(commands, title="0) Initial Commands with *Met Pre-Reqs*")
                last_preq_met_commands = commands
            # (1) if there's any preq-only/non-input commands, check if their pre-requirements are met
            met_command_name = None
            if self._preq_only_commands and commands:
                for name, data in commands.items():
                    if name in self._preq_only_commands.keys():
            # (1a) if any are fully met, use the first one, and skip to the command action execution step. otherwise check for input instead
                        met_command_name = name
                        break
            if not met_command_name:
            # (2) get input
                user_input = self._UI.get_input()       # non-blocking
                if not user_input:
                    continue                            # if no input is available, continue to the next loop cycle
                debug_pprint("INPUT GOT", title='_')
                input_type, input_data = user_input
                input_text = input_data
            # (3) further add commands don't have any pre-requirements at all
                commands.update(self._input_only_commands)
                if not commands:                        # continue on to the next loop cycle if at any point, `commands` is empty
                    continue
                debug_pprint(commands, title="1)Commands with *Met Pre-Reqs* or *No Pre-Reqs*")
            # (2a) if the input type is voice, then update input_text with an initial transcription using the most unique vocabulary of each command.
            # this way, the smallest possible vocabulary can be used to check for all commands (smaller vocab == faster more accurate transcription!)
                if input_type == "VOICE":
                    unique_vocab = list(flatten_generator([self._com_to_unique_vocab.get(name) for name in commands.keys()]))
                    input_text = self._UI.transcribe_audio(input_data, unique_vocab + self._general_vocab)
                if not input_text:
                    continue
            # (2b) output user input text
                self._UI.mainview_append(f'"{input_text}"', 'right')
                debug_pprint(f'"{input_text}"', title='User Input Text 1')
            # (4) split input_text into inidividual tokens (words)
                input_tokens, input_quotes = input_proc.get_basic_tokens_and_quote_sections(input_text)
                debug_pprint(input_tokens, title='User Input Text Basic Tokens')
            # (5) further filter the possible commands, by including only those which their most unique vocabulary overlap with input_tokens
                possible_commands_names = list(flatten_generator([self._vocab_to_com.get(token) for token in input_tokens if token in self._unique_vocab_list]))
                commands = {name:commands.get(name) for name in possible_commands_names if commands.get(name)}  # exclude any commands which aren't in current `commands` dict
                if not commands:
                    continue
                debug_pprint(commands, title="2) Possible Commands (com's unique vocab is in input tokens)")
            # (5a) if the input type is voice, then update input_text again with a second transcription using the vocabulary of only the possible commands
                if input_type == "VOICE":
                    full_vocab = list(flatten_generator([self._com_to_all_vocab.get(name) for name in commands.keys()]))
                    input_text = self._UI.transcribe_audio(input_data, full_vocab + self._general_vocab)
                    self._UI.mainview_append(f'"{input_text}"', 'right')
                    debug_pprint(f'"{input_text}"', title='User Input Text 2')
            # (6) now check each of the possible command's input requirements, and see if any have all of them met
                met_command_name, input_req_values = com_proc.get_commands_matching_input_reqs(input_text, input_data, commands, self._UI.transcribe_audio)
            # (7) if a command is fully met, call its action function, passing in the matched input requirement values
            if met_command_name:
                debug_pprint(f'now executing "{met_command_name}"', title='COMMAND MET')
                action_func = commands.get(met_command_name)["action"]                      # get the action function
                Thread(target=action_func, args=(input_req_values,), daemon=True).start()   # run the command action in a new thread

    def run(self):
        self._print_command_properties()                        # print out initial command properties (if `DEBUG_PRINT` is True)
        self.active = True                                      # set `active` to True
        Thread(target=self._main_loop, daemon=True).start()     # start main_loop in new thread
        self._UI.run()                                          # start UI
