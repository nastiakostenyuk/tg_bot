from aiogram.dispatcher.filters.state import StatesGroup, State


class Cryptocurrency(StatesGroup):
    cryptocurrency = State()


class Task(StatesGroup):
    futures = State()
    price = State()
