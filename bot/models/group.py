from pydantic import BaseModel, Field
from bot.config_reader import Config
from typing import Optional
from aiogram_i18n import I18nContext
from aiogram import html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
import logging


logger = logging.getLogger(__name__)


class Request(BaseModel):
    request: Optional[int] = None
    response: Optional[int] = None


class Voiting(BaseModel):
    who: Optional[int] = None
    amount: Optional[int] = None
    

class Player(BaseModel):
    """Data for each player"""
    name: str = 'default'
    money: int = 0
    request: Request = Request()
    voiting: list[Voiting] = Field(default_factory=list)
    
    has_voted: bool = False
    
    def new_vote(self, who: Optional[int] = None, 
                 amount: Optional[int] = None) -> None:
        self.voiting.append(Voiting(who=who, amount=amount))


class Round(BaseModel):
    """Data for one game round"""
    bank: int
    shrinked: Optional[int] = None
    alive: dict[int, Player] = Field(default_factory=dict)
    lost: dict[int, str] = Field(default_factory=dict)
    
    def all_requested(self) -> bool:
        """Returns whether all players requested or not"""
        return all([p.request.request for p in self.alive.values()])
    
    def all_voted(self) -> bool:
        """Returns whether all players voted or not"""
        return all([p.has_voted for p in self.alive.values()])

    def get_total(self) -> int:
        """Returns the sum of the player requests"""
        return sum([p.request.request for p in self.alive.values()])
    
    def format(self, round_number: int, i18n: I18nContext) -> str:
        ### FIXME | STUB
        return (str(round_number + 1) + 
                '\n'+ 
                html.pre(self.model_dump_json(indent=2, exclude_none=True)))


class Settings(BaseModel):
    """Settings of a group game"""
    # bank per one
    bank: int
    extent: float
    

class GroupData(BaseModel):
    game_id: int
    settings: Settings
    players: dict[int, str] = Field(default_factory=dict)
    rounds: list[Round] = Field(default_factory=list)
    round_number: int = -1
    lost: dict[int, str] = Field(default_factory=dict)
    bank: Optional[int] = None
    
    def menu(self, bank: int) -> None:
        """Sets the default data for the menu state"""
        self.settings = Config(bank=bank)
        self.players = {}
        self.rounds = []
        self.round_number = -1
        self.lost = {}
        self.bank = None
    
    def get_alive_players(self) -> dict[int, Player]:
        """Returns a dict of alive players"""
        
        alive = {}
        for player in self.players:
            if player in self.lost:
                continue
            alive[player] = Player(name=self.players[player])
        
        return alive

    def new_round(self, round: Optional[Round]=None) -> None:
        """Creates a new default round of the game"""
        if round is None:
            round = Round(bank=self.bank)
        
        self.round_number += 1
        
        if not round.alive:
            round.alive = self.get_alive_players()
        round.bank = self.bank or self.settings.bank
        self.rounds.append(round)
       
    def get_extents(self) -> int:
        """Calculates the sum of the request"""
        extent = self.settings.extent
        return sum([p.request.request ** extent for p in self.current_round.alive.values()])
    
    def set_requests(self) -> None:
        """Sets the final requests"""
        extents_sum = self.get_extents()
        
        for id, player in self.current_round.alive.items():
            request = player.request.request
            powered = request ** self.settings.extent
            
            income = min(request, powered * self.current_round.shrinked / extents_sum)
            self.current_round.alive[id].request.response = round(income)
    
    def shrink_bank(self) -> None:
        """Sets the shrinked bank of the current round"""
        total_requests = self.current_round.get_total()
        shrinked = min(self.current_round.bank * 2 - total_requests, self.current_round.bank)
        
        self.bank = shrinked
        self.current_round.shrinked = shrinked
    
    def set_lost_players(self) -> None:
        """Sets the lost players of the current round"""
        players = self.current_round.alive
        players_votes = {}
        
        for player in players.values():
            for vote in player.voiting:
                amount = vote.amount
                if vote.who in players_votes:
                    players_votes[vote.who] += amount
                else:
                    players_votes[vote.who] = amount
        
        maximum = max(players_votes.values())
        lost = {}
        for id in players_votes:
            if players_votes[id] == maximum:
                lost[id] = players[id].name
        
        self.lost.update(lost)
        self.current_round.lost.update(lost)

    @property
    def current_round(self) -> Round | None:
        if self.round_number > -1:
            return self.rounds[self.round_number]

    @current_round.setter
    def current_round(self, round: Round) -> None:
        self.rounds[self.round_number] = round
