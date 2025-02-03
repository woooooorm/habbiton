from habbiton.models.state import Level
from habbiton.models.habit import Habit
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from habbiton import utils

class Handler:
    def __init__(self, user, message):
        self.user = user
        self.message = message
    
    async def handle(self) -> None:
        self.level = await Level.from_name(self.user.current_level)
        
        button = await self.level.check_button(self.message.text)
        if button:
            await self.move_user(button.target_level_name)
            if button.callback:
                await getattr(self, button.callback)()
            return
        
        if self.level.callback:
            await getattr(self, self.level.callback)()

    async def handle_start(self) -> None:
        await self.move_user('start')
        await self.move_user('main')

    async def move_user(self, level_name: str) -> None:
        await self.user.update(current_level=level_name)

        buttons = await Level(name = level_name).get_buttons()
        for message in await Level(name = level_name).get_messages():
            await self.message.answer(message.text, reply_markup=buttons)

    async def show_habits(self, update = 'n') -> None:
        habits = await Habit.get_user_habits(self.user.id)
        if len(habits) == 0:    
            text = "Seems that you don't have any habits yet"
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard = [[InlineKeyboardButton(text = "Create text fixture", callback_data = "fixture")]])
        else:
            text = f"Total: {len(habits)}"
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard = [
                    [InlineKeyboardButton(
                        text = ("⭐ " if habit.starred else "") +  habit.name + (" ✔️" if await habit.check_completion() else " ❌"), callback_data = f"info|{habit.id}"
                        )
                    ]
                    for habit in habits
                ]
            )
        if update == 'y':
            await self.message.message.edit_text(text, reply_markup = reply_markup)
        else: 
            msg = await self.message.answer(text, reply_markup = reply_markup)
            await self.user.update(latest_msg_id=msg.message_id)

    async def purge_msg(self) -> None:
        if self.user.latest_msg_id:
            await self.message.bot.delete_message(self.user.id, self.user.latest_msg_id)
            await self.user.update(latest_msg_id=None)
   
    async def get_habit_name(self) -> None:
        await Habit.new(self.message.text, self.user.id)
        await self.move_user('new_habit_period')
    
    async def delete_unfinished_habit(self) -> None:
        await Habit.delete_unfinished(self.user.id)        
    
    async def set_habit_period(self) -> None:
        await Habit.set_period(self.message.text, self.user.id)
        await self.move_user('main')
    
    async def info(self, id: str) -> None:
        habit = await Habit.get_user_habit(self.user.id, id)
        info_msg = f"Name: {habit.name}\n\n"
        info_msg += f"Start date: {habit.created_date}\n"
        info_msg += f"Period: {habit.period}\n"
        info_msg += f"Current streak: {await habit.calculate_streak()}\n"
        info_msg += f"Max streak: {await habit.calculate_longest_streak()}"
        buttons = []
        if not await habit.check_completion():
            buttons.append([InlineKeyboardButton(text = "Complete", callback_data = f"complete|{habit.id}")])
        
        if habit.starred:
            msg = "Unstar"
        else:
            msg = "Star"
        buttons.append(
            [
                InlineKeyboardButton(text = msg, callback_data = f"star|{habit.id}"), 
                InlineKeyboardButton(text = "Delete", callback_data = f"delete|{habit.id}")
            ]
        )
        buttons.append([InlineKeyboardButton(text = "Back", callback_data = "show_habits|y")])

        reply_markup = InlineKeyboardMarkup(
            inline_keyboard = buttons
        )
        await self.message.message.edit_text(info_msg, reply_markup = reply_markup)

    async def complete(self, id: str) -> None:
        habit = await Habit.get_user_habit(self.user.id, id)
        await habit.complete()
        await self.show_habits('y')
    
    async def star(self, id: str) -> None:
        habit = await Habit.get_user_habit(self.user.id, id)
        await habit.star()
        await self.info(id)
    
    async def delete(self, id: str) -> None:
        habit = await Habit.get_user_habit(self.user.id, id)
        await habit.delete()
        await self.show_habits('y')
    
    async def show_stats(self) -> None:
        habits = await Habit.get_user_habits(self.user.id)
        if len(habits) == 0:
            await self.message.answer("You don't have any habits yet")
            return
        text = f"Total habits num: {len(habits)}\n\n"

        d_habits = [habit for habit in habits if habit.period == 'Daily']
        max, habit = await self.calculate_longest_streak(d_habits)
        if habit:
            text += f"Longest streak for daily: {habit.name}, {max}\n d"

        w_habits = [habit for habit in habits if habit.period == 'Weekly']
        max, habit = await self.calculate_longest_streak(w_habits)
        if habit:
            text += f"Longest streak for weekly: {habit.name}, {max}\n w"

        m_habits = [habit for habit in habits if habit.period == 'Monthly']
        max, habit = await self.calculate_longest_streak(m_habits)
        if habit:
            text += f"Longest streak for monthly: {habit.name}, {max}\n m"
        
        await self.message.answer(text)

    async def fixture(self) -> None:
        await utils.create_test_fixture(self.user.id)
        await self.show_habits('y')

    @staticmethod
    async def calculate_longest_streak(habits: list[Habit]) -> None:
        max = 0
        max_habit = None
        for habit in habits:
            d_max = await habit.calculate_longest_streak()
            if d_max > max:
                max = d_max
                max_habit = habit
        return max, max_habit