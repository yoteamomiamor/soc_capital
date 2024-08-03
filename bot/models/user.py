from pydantic import BaseModel
from typing import Optional
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey


class TempData(BaseModel):
    money: Optional[int] = None
    voted: Optional[str] = None
    spent: Optional[int] = None
    
    def has_money(self) -> bool:
        return self.money > 0

    def spend(self, amount: int) -> None:
        self.spent = amount
        self.money -= amount


class UserData(BaseModel):
    game_id: Optional[int]
    temp: Optional[TempData] = TempData()
