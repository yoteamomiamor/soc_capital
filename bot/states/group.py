from aiogram.fsm.state import StatesGroup, State


class GroupStates(StatesGroup):
    menu = State()
    starting = State()
    settings = State()

    class ingame(StatesGroup):
        requesting = State()
        voting = State()
