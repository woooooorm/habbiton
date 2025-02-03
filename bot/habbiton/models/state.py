from sqlalchemy import Column, Integer, String, select, ForeignKey
from habbiton import Base, session
from sqlalchemy.orm import mapped_column

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

class Level(Base):
    __tablename__ = 'levels'
    name = mapped_column(String, primary_key=True)
    callback = mapped_column(String, nullable=True)

    @classmethod
    async def from_name(cls, name: str) -> 'Level':
        async with session() as ses:
            stmt = select(cls).where(cls.name == name)
            return (await ses.execute(stmt)).scalar_one()
        
    async def get_messages(self):
        async with session() as ses:
            stmt = select(Message).where(Message.level_name == self.name).order_by(Message.order)
            return (await ses.execute(stmt)).scalars().all()
        
    async def get_buttons(self):
        async with session() as ses:
            stmt = select(Button).where(Button.current_level_name == self.name).order_by(Button.order)
            buttons = (await ses.execute(stmt)).scalars().all()
            if len(buttons) == 0:
                return ReplyKeyboardRemove()
            return ReplyKeyboardMarkup(
                resize_keyboard = True,
                one_time_keyboard = False,
                keyboard = [
                    [KeyboardButton(text = button.text)]
                    for button in buttons
                ]
            )
    async def check_button(self, text: str):
        async with session() as ses:
            stmt = select(Button).where(Button.current_level_name == self.name, Button.text == text)
            return (await ses.execute(stmt)).scalar()

class Message(Base):
    __tablename__ = 'messages'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    level_name = mapped_column(ForeignKey("levels.name"))
    text = mapped_column(String, nullable=False)
    order = mapped_column(Integer, nullable=False, default = 1)

class Button(Base):
    __tablename__ = 'buttons'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    current_level_name = mapped_column(ForeignKey("levels.name"))
    target_level_name = mapped_column(ForeignKey("levels.name"))
    text = mapped_column(String, nullable=False)
    callback = mapped_column(String, nullable=True)
    order = mapped_column(Integer, nullable=True)