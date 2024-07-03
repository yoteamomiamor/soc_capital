from aiogram.fsm.state import StatesGroup, State


class UserMain(StatesGroup):
    menu = State()


class UserIngame(StatesGroup):
    requesting = State()
    class voiting(StatesGroup):
        person = State()
        amount = State()
        
    spectator = State()


class GroupMain(StatesGroup):
    menu = State()
    starting = State()
    settings = State()


class GroupIngame(StatesGroup):
    requesting = State()
    voting = State()
