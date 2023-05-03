from sqlalchemy import Column, String, Integer, Numeric, Boolean
from db_utils.database import base, session


class Task(base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    futures = Column(String)
    price = Column(Numeric)
    done = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.user_id} - {self.futures} - {self.price}"


class PairToWatch(base):
    __tablename__ = "pairs_to_watch"

    pair_id = Column(Integer, primary_key=True)
    pair = Column(String)

    def __repr__(self):
        return f'{self.pair.split("@")[0]}'
