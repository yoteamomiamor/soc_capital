from aiogram import html


def format_players(players: list[str]) -> str:
    """Formats a list of nicknames to the readable list"""
    return '\n'.join([f' - {html.bold(p)}' for p in players])
