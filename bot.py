import asyncio
import json
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8465475383:AAEyVW2cIH-rEmwJbXFZyULNTy4iMV1tC4U"
ADMIN_ID = 897721072

dp = Dispatcher(storage=MemoryStorage())

class GameState(StatesGroup):
    waiting_for_answer = State()

class SupportState(StatesGroup):
    waiting_for_message = State()

def load_teachers():
    try:
        with open('teachers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"teachers": []}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Игра 'Счастливый билет'")],
            [KeyboardButton(text="💬 Поддержка"),]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        "Привет! Добро пожаловать в бота\n\n"
        "💬 Поддержка - свяжись с администратором\n\n"
        "🎲 Игра Счастливый билет - угадай преподавателя",
        reply_markup=keyboard,
        resize_keyboard=True,
    )

@dp.message(F.text == "🎲 Игра 'Счастливый билет'")
async def game_start(message: types.Message, state: FSMContext):
    data = load_teachers()
    teachers = data.get("teachers", [])

    selected_teacher = random.choice(teachers)
    await state.update_data(correct_teacher=selected_teacher)

    wrong_teachers = [t for t in teachers if t != selected_teacher]
    options = random.sample(wrong_teachers, min(3, len(wrong_teachers))) + [selected_teacher]
    random.shuffle(options)

    keyboard = []
    for i in range(0, len(options), 2):
        row = []
        for j in range(2):
            if i + j < len(options):
                teacher = options[i + j]
                row.append(KeyboardButton(text=f"{teacher['name']}"))
        keyboard.append(row)

    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(GameState.waiting_for_answer)
    await message.answer(
        f"❔Угадай преподавателя\n\n"
        f"Предмет: {selected_teacher['subject']}\n"
        f"Группа: <i>{selected_teacher['group']}</i>\n\n"
        f"Кто ведет этот предмет?",
        reply_markup=reply_keyboard,
        parse_mode="HTML",
        resize_keyboard=True,
    )


@dp.message(GameState.waiting_for_answer)
async def process_game_answer(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    correct_teacher = user_data.get("correct_teacher")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Игра 'Счастливый билет'")],
            [KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )

    if message.text == correct_teacher['name']:
        await message.answer(
            f"✅Верно\n\n"
            f"Правильный ответ: <b>{correct_teacher['name']}</b>\n"
            f"Предмет: {correct_teacher['subject']}\n"
            f"Группа: <i>{correct_teacher['group']}</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
            resize_keyboard=True,
        )
    else:
        await message.answer(
            f"❌ Неправильно\n\n"
            f"Правильный ответ: <b>{correct_teacher['name']}</b>\n"
            f"Предмет: {correct_teacher['subject']}\n"
            f"Группа: <i>{correct_teacher['group']}</i>",
            reply_markup=keyboard,
            parse_mode="HTML",
            resize_keyboard=True,
        )

    await state.clear()


@dp.message(F.text == "💬 Поддержка")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportState.waiting_for_message)

    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Напишите ваше сообщение для администратора:",
        reply_markup=cancel_keyboard,
        resize_keyboard=True,
    )

@dp.message(SupportState.waiting_for_message)
async def process_support_message(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎲 Игра 'Счастливый билет'")],
                [KeyboardButton(text="💬 Поддержка")]
            ],
            resize_keyboard=True
        )
        await message.answer("Отменено", reply_markup=keyboard, resize_keyboard=True)
        await state.clear()
        return

    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{message.from_user.id}")]
            ]
        )

        await message.bot.send_message(
            ADMIN_ID,
            f"📨 Новое сообщение в поддержку!\n\n"
            f"👤 От: {message.from_user.full_name} (@{message.from_user.username or 'без username'})\n"
            f"🆔 ID: {message.from_user.id}\n\n"
            f"💬 Сообщение:\n{message.text}",
            reply_markup=keyboard,
        )

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎲 Игра 'Счастливый билет'")],
                [KeyboardButton(text="💬 Поддержка")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "Ваше сообщение отправлено администратору!\n"
            "Ожидайте ответа.",
            reply_markup=keyboard,
            resize_keyboard=True,
        )

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при отправке сообщения.\n"
            "Попробуйте позже."
        )
    await state.clear()


@dp.callback_query(F.data.startswith("reply_"))
async def admin_reply_button(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав для этого действия!")
        return

    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_to_user=user_id)

    await callback.message.answer(
        f"Напишите ответ пользователю {user_id}:\n"
        "(Отправьте сообщение, и оно будет переслано пользователю)"
    )
    await callback.answer()


@dp.message(F.from_user.id == ADMIN_ID)
async def admin_reply_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    reply_to_user = user_data.get("reply_to_user")

    if reply_to_user:
        try:
            await message.bot.send_message(
                reply_to_user,
                f"📩 Ответ от администратора:\n\n{message.text}"
            )
            await message.answer("Ответ отправлен пользователю!")
            await state.clear()
        except Exception as e:
            await message.answer(f"Ошибка при отправке ответа: {str(e)}")


@dp.message()
async def handle_other_messages(message: types.Message):
    await message.answer(
        "Используйте кнопки меню для навигации по боту:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎲 Игра 'Счастливый билет'")],
                [KeyboardButton(text="💬 Поддержка")]
            ],
            resize_keyboard=True
        )
    )


async def main():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print('start bot')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())