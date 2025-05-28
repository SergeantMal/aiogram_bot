import asyncio
import aiohttp
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("API_WEATHER")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

# 📌 Клавиатура с эмодзи
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👋 Старт")
    builder.button(text="ℹ️ Помощь")
    builder.button(text="🌦 Прогноз погоды")
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup(resize_keyboard=True)

# 🟢 Обработка "Старт"
@dp.message(F.text == "👋 Старт")
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я погодный бот. Я могу показать тебе прогноз погоды в Москве ☁️\n\n"
        "Выбери нужную опцию ниже 👇",
        reply_markup=get_main_keyboard()
    )

# 🟡 Обработка "Помощь"
@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Я могу:\n"
        "🌦 Показать текущую погоду в Москве\n"
        "👋 Поздороваться\n"
        "ℹ️ Рассказать, что я умею\n\n"
        "Просто нажми на кнопку!"
    )

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
