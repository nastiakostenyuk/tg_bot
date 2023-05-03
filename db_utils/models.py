from sqlalchemy import Column, String, Integer, Numeric, VARCHAR, ForeignKey, ARRAY, Boolean
from db_utils.database import base, session


class Task(base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    futures = Column(String)
    price = Column(Numeric)
    done = Column(Boolean, default=False)

    def __repr__(self):
        return f'{self.user_id} - {self.futures} - {self.price}'
