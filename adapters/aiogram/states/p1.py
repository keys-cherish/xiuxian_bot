"""P1 FSM states for aiogram event-driven gameplay."""

from aiogram.fsm.state import State, StatesGroup


class HuntFSM(StatesGroup):
    selecting_monster = State()
    in_battle = State()


class BreakthroughFSM(StatesGroup):
    selecting_strategy = State()


class ShopFSM(StatesGroup):
    selecting_currency = State()
    browsing = State()


class SecretRealmFSM(StatesGroup):
    selecting_realm = State()
    selecting_path = State()
    in_event_choice = State()
    in_battle = State()

