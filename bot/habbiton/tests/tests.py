import pytest
import pytest_asyncio
from sqlalchemy import select, delete, update

from habbiton.models.habit import Habit, HabitCompletion
from habbiton.models.state import Level, Message, Button
from habbiton.models.user import User
from datetime import date, timedelta
pytest_plugins = ('pytest_asyncio')



@pytest.mark.asyncio
async def test_initial():
    habits = await Habit.get_user_habits(123)
    assert len(habits) == 1

@pytest.mark.asyncio
async def test_new_habbit(db_session):
    async with db_session() as ses:
        ses.add(Habit(user_id = 123, name = 'Test2'))
        await ses.commit()
    test = await Habit.get_user_habits(123)
    assert len(test) == 2

@pytest.mark.asyncio
async def test_new_habbit_with_steps(db_session):
    async with db_session() as ses:
        await Habit.new("Test2", 123)
        await Habit.set_period("Daily", 123)

        stmt = select(Habit).where(Habit.name == "Test2")
        habit: Habit = (await ses.execute(stmt)).scalar()

        assert habit.name == "Test2" and habit.user_id == 123 and habit.period == "Daily"

@pytest.mark.asyncio
async def test_delete_unfinished(db_session):
    async with db_session() as ses:
        await Habit.new("Test2", 123)
        await Habit.delete_unfinished(123)

        stmt = select(Habit).where(Habit.name == "Test2")
        habit: Habit = (await ses.execute(stmt)).scalar()

        assert habit == None

@pytest.mark.asyncio
async def test_habit_deletion(db_session):
    async with db_session() as ses:
        stmt = select(Habit).where(Habit.id == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        
        await habit.delete()
        habits = await Habit.get_user_habits(123)
        assert len(habits) == 0

@pytest.mark.asyncio
async def test_habit_completion(db_session):
    async with db_session() as ses:
        stmt = select(Habit).where(Habit.id == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        
        await habit.complete()

        assert (await habit.check_completion()) == True

@pytest.mark.asyncio
async def test_habit_starring(db_session):
    async with db_session() as ses:
        stmt = select(Habit).where(Habit.id == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        
        await habit.star()
        await ses.refresh(habit)

        assert habit.starred == True

@pytest.mark.asyncio
async def test_habit_non_completion(db_session):
    async with db_session() as ses:
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        
        assert (await habit.check_completion()) == False

@pytest.mark.asyncio
async def test_daily_zero_streak(db_session):
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 0

@pytest.mark.asyncio
async def test_daily_streak(db_session):
    today = date.today()
    async with db_session() as ses:
        for i in range(1, 29):
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(days=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 28

@pytest.mark.asyncio
async def test_daily_streak_broken(db_session):
    today = date.today()
    async with db_session() as ses:
        for i in range(1, 29):
            if i in [7, 22]:
                continue
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(days=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 6

@pytest.mark.asyncio
async def test_daily_streak_broken_max(db_session):
    today = date.today()
    async with db_session() as ses:
        for i in range(1, 29):
            if i in [7, 22]:
                continue
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(days=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_longest_streak()

    assert streak == 14


@pytest.mark.asyncio
async def test_weekly_zero_streak(db_session):
    async with db_session() as ses:   
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Weekly")
        await ses.execute(stmt)
        await ses.commit()

        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 0

@pytest.mark.asyncio
async def test_weekly_streak(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Weekly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 5):
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(weeks=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 4

@pytest.mark.asyncio
async def test_weekly_streak_broken(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Weekly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 5):
            if i in [2]:
                continue
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(weeks=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 1

@pytest.mark.asyncio
async def test_weekly_streak_broken_max(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Weekly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 6):
            if i in [2]:
                continue
            ses.add(HabitCompletion(habit_id = 1001, created_date = today - timedelta(weeks=i)))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_longest_streak()

    assert streak == 3

@pytest.mark.asyncio
async def test_monthly_zero_streak(db_session):
    async with db_session() as ses:   
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Monthly")
        await ses.execute(stmt)
        await ses.commit()

        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 0

@pytest.mark.asyncio
async def test_monthly_streak(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Monthly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 6):
            if today.month - i > 0:
                buffer = date(today.year, today.month - i, 1)
            else:
                buffer = date(today.year - 1, 12 - i + 2, 1)
            ses.add(HabitCompletion(habit_id = 1001, created_date = buffer))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 5

@pytest.mark.asyncio
async def test_monthly_streak_broken(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Monthly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 6):
            if i in [5]:
                continue

            if today.month - i > 0:
                buffer = date(today.year, today.month - i, 1)
            else:
                buffer = date(today.year - 1, 12 - i + 2, 1)
            ses.add(HabitCompletion(habit_id = 1001, created_date = buffer))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_streak()

    assert streak == 4

@pytest.mark.asyncio
async def test_monthly_streak_broken_max(db_session):
    today = date.today()
    async with db_session() as ses:
        stmt = update(Habit).where(Habit.id == 1001).values(period = "Monthly")
        await ses.execute(stmt)
        await ses.commit()

        for i in range(1, 6):
            if i in [5]:
                continue

            if today.month - i > 0:
                buffer = date(today.year, today.month - i, 1)
            else:
                buffer = date(today.year - 1, 12 - i + 2, 1)
            ses.add(HabitCompletion(habit_id = 1001, created_date = buffer))
        await ses.commit()
    
    async with db_session() as ses:   
        stmt = select(Habit).where(Habit.id  == 1001)
        habit: Habit = (await ses.execute(stmt)).scalar()
        streak = await habit.calculate_longest_streak()

    assert streak == 4
