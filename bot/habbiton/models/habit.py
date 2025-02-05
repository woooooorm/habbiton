from sqlalchemy import Column, Integer, String, Date, select, delete, ForeignKey, update, Boolean
from habbiton import Base, session
from sqlalchemy.orm import mapped_column
from datetime import datetime, timedelta

class Habit(Base):
    __tablename__ = 'habits'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False)
    created_date = mapped_column(Date, nullable=True, default = datetime.now().date)
    period = mapped_column(String, nullable=True)
    starred = mapped_column(Boolean, nullable=True, default = False)
    session = session
    
    @classmethod
    def set_session(cls, session) -> None:
        cls.session = session

    @classmethod
    async def new(cls, name: str, user_id: int) -> None:
        "Creates a temporary habit"
        async with cls.session() as ses:
            ses.add(cls(name = name, user_id = user_id))
            await ses.commit()
    
    @classmethod
    async def delete_unfinished(cls, id) -> None:
        "Deletes a temporary habit, if user decided to cancel habit creation"
        async with cls.session() as ses:
            stmt = delete(cls).where(cls.period == None, cls.user_id == id)
            await ses.execute(stmt)
            await ses.commit()
    
    @classmethod
    async def set_period(cls, value, id) -> None:
        "Finishes a temporary habit, making it a normal one"
        async with cls.session() as ses:
            stmt = update(cls).where(cls.period == None, cls.user_id == id).values(period = value)
            await ses.execute(stmt)
            await ses.commit()
    
    @classmethod
    async def get_user_habits(cls, user_id, type = None) -> list['Habit']:
        async with cls.session() as ses:
            if type:
                stmt = select(cls).where(cls.user_id == user_id, cls.period == type).order_by(cls.starred.desc())
            else:
                stmt = select(cls).where(cls.user_id == user_id).order_by(cls.starred.desc())
            return (await ses.execute(stmt)).scalars().all()
    
    @classmethod
    async def get_user_habit(cls, user_id, id) -> 'Habit':
        async with cls.session() as ses:
            stmt = select(cls).where(cls.user_id == user_id, cls.id == int(id))
            return (await ses.execute(stmt)).scalar()
        
    async def complete(self) -> None:
        async with self.session() as ses:
            ses.add(HabitCompletion(habit_id = self.id))
            await ses.commit()
    
    async def star(self) -> None:
        async with self.session() as ses:
            self.starred = not self.starred
            stmt = update(Habit).where(Habit.id == self.id).values(starred = self.starred)
            await ses.execute(stmt)
            await ses.commit()

    async def check_completion(self, today = datetime.now().date()) -> bool:
        "Checks habit completion in the current period"
        if self.period == 'Daily':
            stmt = select(HabitCompletion).where(HabitCompletion.habit_id == self.id, HabitCompletion.created_date == today)
        elif self.period == 'Weekly':
            stmt = select(HabitCompletion).where(
                HabitCompletion.habit_id == self.id,
                HabitCompletion.created_date >= (today - timedelta(today.weekday())),
                HabitCompletion.created_date < (today - timedelta(today.weekday()) + timedelta(weeks = 1))
            )
        elif self.period == 'Monthly':
            if today.month == 12:
                upper_buffer = datetime(today.year + 1, 1, 1).date()
            else:
                upper_buffer = datetime(today.year, today.month + 1, 1).date()

            stmt = select(HabitCompletion).where(
                HabitCompletion.habit_id == self.id,
                HabitCompletion.created_date >= today.replace(day=1),
                HabitCompletion.created_date < upper_buffer
            )
                
        async with self.session() as ses:
            return True if (await ses.execute(stmt)).scalar() else False
    
    async def delete(self) -> None:
        "Deletes habit and all completions of it"
        async with self.session() as ses:
            stmt = delete(HabitCompletion).where(HabitCompletion.habit_id == self.id)
            await ses.execute(stmt)
            await ses.commit()

            stmt = delete(Habit).where(Habit.id == self.id)
            await ses.execute(stmt)
            await ses.commit()
    
    async def calculate_streak(self) -> int:
        "Checks completion in the current period, and periods before it, unless a missing completion is found or habit creating date is passes"
        streak = 0
        today = datetime.now().date()
        while today >= self.created_date:
            if await self.check_completion(today):
                streak += 1
            else:
                if today != datetime.now().date():
                    break
            if self.period == 'Daily':
                today -= timedelta(1)
            elif self.period == 'Weekly':
                today -= timedelta(today.weekday()) + timedelta(weeks= 1)
            elif self.period == 'Monthly':
                if today.month == 1:
                    today = datetime(today.year - 1, 12, 1).date()
                else:
                    today = datetime(today.year, today.month - 1, 1).date()
        return streak
    
    async def calculate_longest_streak(self) -> int:
        "Checks completion in the current period, and periods before it, habit creating date is passes, tracks maximum streak seen"
        streak = 0
        max = 0
        today = datetime.now().date()
        while today >= self.created_date:
            if await self.check_completion(today):
                streak += 1
            else:
                if streak > max:
                    max = streak
                streak = 0
            if self.period == 'Daily':
                today -= timedelta(1)
            elif self.period == 'Weekly':
                today -= timedelta(today.weekday()) + timedelta(weeks= 1)
            elif self.period == 'Monthly':
                if today.month == 1:
                    today = datetime(today.year - 1, 12, 1).date()
                else:
                    today = datetime(today.year, today.month - 1, 1).date()
        if streak > max:
            max = streak
        return max
        

class HabitCompletion(Base):
    __tablename__ = 'habit_completions'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id = mapped_column(ForeignKey("habits.id"), nullable=False)
    created_date = mapped_column(Date, nullable=True, default = datetime.now().date())