from os.path import dirname, join
from app.main import App
from sub_apps.time_tools import get_current_local_time_str, get_current_local_date_str
from sub_apps.timer import timer_alarm as t
from sub_apps import number_chooser

COMMAND_FUNC_MAP = {
    'TIMER_ACTIVE': t.is_any_timers,
    'GET_TIME':     get_current_local_time_str,
    'GET_DATE':     get_current_local_date_str,
    'START_TIMER':  t.start_new_timer,
    'STOP_TIMER':   t.stop_timer,
    'GET_TIMER':    t.get_remaining_time,
    'COIN_FLIP':    number_chooser.flip_a_coin
}

commands_path = join(dirname(__file__), "example_1_com_data.json")

if __name__ == "__main__":
    app = App(commands_path, COMMAND_FUNC_MAP)
    app.run()