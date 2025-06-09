import logging
import os

import aiohttp
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def format_eq(eq):
    t = datetime.fromtimestamp(eq["time"] / 1000, tz=timezone.utc)
    place = eq["place"]
    mag = eq["mag"]
    return f"<b>{t.strftime('%Y-%m-%d %H:%M')} UTC</b>\n{place}\nМагнитуда: {mag}"

async def fetch_latest():
    params = {
        "format": "geojson",
        "limit": 5,
        "orderby": "time",
    }
    async with aiohttp.ClientSession() as sess:
        async with sess.get(USGS_API, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data["features"]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать последние 5 землетрясений", callback_data="show_latest")]
    ])
    await message.answer("Привет! Я покажу информацию о 5 последних землетрясениях в мире.", reply_markup=kb)

@dp.message(Command("latest"))
async def cmd_latest(message: Message):
    await message.answer("Получаю данные...")
    eqs = await fetch_latest()
    if not eqs:
        await message.answer("❌ Не удалось загрузить данные.")
        return
    for feat in eqs:
        props = feat["properties"]
        await message.answer(format_eq(props))

@dp.callback_query(lambda c: c.data == "show_latest")
async def cb_show_latest(callback: CallbackQuery):
    await callback.answer()  # Убираем "часик" у кнопки
    eqs = await fetch_latest()
    if not eqs:
        await callback.message.answer("❌ Не удалось загрузить данные.")
        return
    for feat in eqs:
        props = feat["properties"]
        await callback.message.answer(format_eq(props))

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())