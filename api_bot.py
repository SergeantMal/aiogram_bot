import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties



logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
EUROPEANA_KEY = os.getenv("EUROPEANA_API_KEY")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())



# 🟢 /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! 👋 Я могу предоставить краткую информацию о музейных экспонатах.\n\n"
        "Пожалуйста, введите название экспоната, например: <b>Van Gogh</b>"
    )



@dp.message()
async def handle_query(message: Message):
    query = message.text
    url = f"https://api.europeana.eu/record/v2/search.json?wskey=apidemo&query={query}&rows=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await message.answer("⚠️ Ошибка при обращении к API.")
                return

            data = await resp.json()
            items = data.get("items", [])
            if not items:
                await message.answer("Ничего не найдено по вашему запросу.")
                return

            item = items[0]
            title = item.get("title", ["Без названия"])[0]
            description = item.get("dcDescription", ["Нет описания"])[0]
            image_url = item.get("edmPreview", [None])[0]

            text = f"<b>{title}</b>\n\n{description}"
            if image_url:
                await message.answer_photo(photo=image_url, caption=text)
            else:
                await message.answer(text)


# 🟢 Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())