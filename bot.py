import asyncio
import aiohttp
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from gtts import gTTS
import uuid
import sqlite3
from keyboards import greeting_keyboard, links_keyboard, show_more_keyboard, options_keyboard
from aiogram.types import CallbackQuery
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("API_WEATHER")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            grade TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def insert_student(name, age, grade):
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO students (name, age, grade) VALUES (?, ?, ?)', (name, age, grade))
    conn.commit()
    conn.close()

# 📌 Клавиатура с эмодзи
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👋 Старт")
    builder.button(text="ℹ️ Помощь")
    builder.button(text="🌦 Прогноз погоды")
    builder.button(text="🎤 Голосовое сообщение")
    builder.button(text="💬 Переведи текст")
    builder.button(text="👤 Записать данные")
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup(resize_keyboard=True)

class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()

# Задание 1: Привет / Пока
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Выберите действие:", reply_markup=greeting_keyboard())

@dp.message(F.text == "Привет")
async def say_hello(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}!")

@dp.message(F.text == "Пока")
async def say_goodbye(message: Message):
    await message.answer(f"До свидания, {message.from_user.first_name}!")

# Задание 2: URL-ссылки
@dp.message(Command("links"))
async def show_links(message: Message):
    await message.answer("Выберите ссылку:", reply_markup=links_keyboard())

# Задание 3: Динамическое меню
@dp.message(Command("dynamic"))
async def dynamic_menu(message: Message):
    await message.answer("Нажмите кнопку ниже:", reply_markup=show_more_keyboard())

@dp.callback_query(F.data == "show_more")
async def handle_show_more(callback: CallbackQuery):
    await callback.message.edit_text("Выберите опцию:", reply_markup=options_keyboard())

@dp.callback_query(F.data.startswith("option_"))
async def handle_option(callback: CallbackQuery):
    option = callback.data.split("_")[1]
    await callback.answer()
    await callback.message.answer(f"Вы выбрали опцию {option}.")


# 🟢 Обработка "Старт"
# @dp.message(F.text == "👋 Старт")
# async def start_handler(message: Message):
#     await message.answer(
#         "Привет! Я погодный бот. Я могу сохранить фото, отправить голосовое сообщение, перевести текст и записать твои данные в базу студентов. Я также могу показать тебе прогноз погоды в Москве ☁️\n\n."
#         "Выбери нужную опцию ниже 👇.",
#         reply_markup=get_main_keyboard()
#     )

@dp.message(F.text == "👤 Записать данные")
async def request_name(message: Message, state: FSMContext):
    await message.answer("Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введи возраст числом.")
    await state.update_data(age=int(message.text))
    await message.answer("В каком классе ты учишься?")
    await state.set_state(Form.grade)

@dp.message(Form.grade)
async def get_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    data = await state.get_data()

    insert_student(data['name'], data['age'], data['grade'])

    await message.answer(f"Спасибо, {data['name']}! Данные сохранены.")
    await state.clear()

# 🟡 Обработка "Помощь"
@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Я могу:\n"
        "🌦 Показать текущую погоду в Москве\n"
        "👋 Поздороваться\n"
        "ℹ️ Рассказать, что я умею\n"
        "🔤 Перевести твой текст на английский\n"
        "🎤 Преобразовать твой текст в голосовое сообщение\n\n"
        "👤 Записать твои данные в базу данных студентов\n\n"
        "Просто нажми на кнопку или напиши сообщение!"
    )

# Состояния FSM
class VoiceStates(StatesGroup):
    waiting_for_text = State()

class TranslateStates(StatesGroup):
    waiting_for_text = State()

# --- Обработка кнопки "🎤 Голосовое сообщение" ---
@dp.message(F.text == "🎤 Голосовое сообщение")
async def request_voice_text(message: Message, state: FSMContext):
    await message.answer("✍️ Введите текст, который хотите озвучить:")
    await state.set_state(VoiceStates.waiting_for_text)

@dp.message(VoiceStates.waiting_for_text)
async def generate_and_send_voice(message: Message, state: FSMContext):
    text = message.text
    try:
        tts = gTTS(text, lang='ru')
        filename = f"{uuid.uuid4()}.ogg"
        tts.save(filename)

        voice = FSInputFile(filename)
        await message.answer_voice(voice, caption="🎧 Вот ваше голосовое сообщение")

        os.remove(filename)
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
    finally:
        await state.clear()

# --- Обработка кнопки "💬 Переведи текст" ---
@dp.message(F.text == "💬 Переведи текст")
async def request_translation_text(message: Message, state: FSMContext):
    await message.answer("✍️ Введите текст на русском для перевода на английский:")
    await state.set_state(TranslateStates.waiting_for_text)

@dp.message(TranslateStates.waiting_for_text)
async def handle_translation(message: Message, state: FSMContext):
    try:
        translated = GoogleTranslator(source='ru', target='en').translate(message.text)
        await message.reply(f"🔤 Перевод:\n{translated}")
    except Exception as e:
        await message.reply(f"Произошла ошибка при переводе: {e}")
    finally:
        await state.clear()

# 🔵 Обработка "Прогноз погоды"
@dp.message(F.text == "🌦 Прогноз погоды")
async def forecast_handler(message: Message):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q=Moscow&lang=ru"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                weather = data["current"]
                text = (
                    f"🌍 Город: Москва\n"
                    f"🌡 Температура: {weather['temp_c']}°C\n"
                    f"☁️ Состояние: {weather['condition']['text']}\n"
                    f"💨 Ветер: {weather['wind_kph']} км/ч\n"
                    f"💧 Влажность: {weather['humidity']}%"
                )
                await message.answer(text)
            else:
                await message.answer("⚠️ Не удалось получить прогноз. Попробуйте позже.")


# --- Сохраняем фото в папку img ---
@dp.message(F.content_type == ContentType.PHOTO)
async def save_photo(message: Message):
    os.makedirs("img", exist_ok=True)
    photo = message.photo[-1]  # самое большое фото
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    destination = f"img/{photo.file_id}.jpg"
    await bot.download_file(file_path, destination)
    await message.reply("✅ Фото сохранено!")

# 🔹 На случай ввода текста вручную
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await start_handler(message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await help_handler(message)

# 🚀 Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
