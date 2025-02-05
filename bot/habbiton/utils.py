from habbiton.models.state import Level, Message, Button
from habbiton.models.user import User
from habbiton.models.habit import Habit, HabitCompletion
from habbiton import Base, engine, session
from datetime import date, timedelta
from sqlalchemy import select
async def fill_new_db():
    """
    Checks tables, creates if those are absent, also fills them with bot's levels structure
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with session() as ses:
        stmt = select(Level)
        levels = (await ses.execute(stmt)).scalars().all()
        if len(levels) == 0:
            await create_basic_state()
    

async def create_test_fixture(user_id):
    """
    Generates 5 predefined habits for user testing in-app, also generates track record for 4+ weeks
    """
    today = date.today()
    async with session() as ses:
        h1 = Habit(name="Drink enough water", user_id=user_id, period = "Daily", created_date = date.today().replace(year=today.year - 1))
        h2 = Habit(name="Work out", user_id=user_id, period = "Daily", created_date = date.today().replace(year=today.year - 1))
        h3 = Habit(name="Wash clothes", user_id=user_id, period = "Weekly", created_date = date.today().replace(year=today.year - 1))
        h4 = Habit(name="Tidy the house", user_id=user_id, period = "Weekly", created_date = date.today().replace(year=today.year - 1))
        h5 = Habit(name="Visit parents", user_id=user_id, period = "Monthly", created_date = date.today().replace(year=today.year - 1), starred = True)
        habits_list = [h1, h2, h3, h4, h5]
        ses.add_all(habits_list)
        await ses.commit()
        for h in habits_list:
            await ses.refresh(h)

        for i in range(1, 29):
            ses.add(HabitCompletion(habit_id = h1.id, created_date = today - timedelta(days=i)))

        for i in range(1, 29):
            if i in [7, 22]:
                continue
            ses.add(HabitCompletion(habit_id = h2.id, created_date = today - timedelta(days=i)))
        
        for i in range(1, 5):
            ses.add(HabitCompletion(habit_id = h3.id, created_date = today - timedelta(weeks=i)))
        
        for i in range(1, 5):
            if i in [2]:
                continue
            ses.add(HabitCompletion(habit_id = h4.id, created_date = today - timedelta(weeks=i)))
        
        for i in range(1, 6):
            if i in [5]:
                continue

            if today.month - i > 0:
                buffer = date(today.year, today.month - i, 1)
            else:
                buffer = date(today.year - 1, 12 - i + 2, 1)

            ses.add(HabitCompletion(habit_id = h5.id, created_date = buffer))

        await ses.commit()

async def create_basic_state():
    async with session() as ses:
        ses.add(Level(name="start"))
        ses.add(Level(name="main"))
        ses.add(Level(name="new_habit", callback="get_habit_name"))
        ses.add(Level(name="my_habits"))
        ses.add(Level(name="new_habit_period"))
        ses.add(Level(name="habit_created"))
        ses.add(Level(name="my_stats"))
        await ses.commit()

        ses.add(Message(level_name="start", text="Welcome to Habbiton, a habit tracking app!"))
        ses.add(Message(level_name="main", text="Main menu"))
        ses.add(Message(level_name="new_habit", text="Enter new habit's description"))
        ses.add(Message(level_name="my_habits", text="List of your habits:"))
        ses.add(Message(level_name="new_habit_period", text="Chose habit period"))
        ses.add(Message(level_name="habit_created", text="New habit created successfully"))
        ses.add(Message(level_name="my_stats", text="Here's you stats:"))
        await ses.commit()

        ses.add(Button(current_level_name="main", target_level_name= "my_habits", text="My habits", callback ="show_habits", order = 2))
        ses.add(Button(current_level_name="main", target_level_name= "my_stats", text="My stats", callback ="show_stats", order = 3))
        ses.add(Button(current_level_name="main", target_level_name= "new_habit", text="New habit", callback ="delete_unfinished_habit", order = 1))
        ses.add(Button(current_level_name="my_habits", target_level_name= "main", text="Back", callback ="purge_msg", order = 1))
        ses.add(Button(current_level_name="my_stats", target_level_name= "main", text="Back", order = 1))
        ses.add(Button(current_level_name="new_habit", target_level_name= "main", text="Back", order = 1))
        ses.add(Button(current_level_name="new_habit_period", target_level_name= "habit_created", text="Monthly", callback="set_habit_period", order = 3))
        ses.add(Button(current_level_name="new_habit_period", target_level_name= "habit_created", text="Weekly", callback="set_habit_period", order = 2))
        ses.add(Button(current_level_name="new_habit_period", target_level_name= "habit_created", text="Daily", callback="set_habit_period", order = 1))
        ses.add(Button(current_level_name="new_habit_period", target_level_name= "new_habit", text="Back", callback="delete_unfinished_habit", order = 4))
        
        await ses.commit()
