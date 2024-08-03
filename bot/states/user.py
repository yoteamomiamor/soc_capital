from aiogram.fsm.state import StatesGroup, State


class UserStates(StatesGroup):
    menu = State()

    class ingame(StatesGroup):
        requesting = State()
        
        class voiting(StatesGroup):
            person = State()
            amount = State()
            
        spectator = State()
