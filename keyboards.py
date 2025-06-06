from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Задание 1: Простое меню
def greeting_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Привет"), KeyboardButton(text="Пока")]
        ],
        resize_keyboard=True
    )

# Задание 2: Кнопки с URL-ссылками
def links_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📰 Новости", url="https://news.yandex.ru")],
        [InlineKeyboardButton(text="🎵 Музыка", url="https://music.yandex.ru")],
        [InlineKeyboardButton(text="🎬 Видео", url="https://www.youtube.com")]
    ])
    return keyboard

# Задание 3: Динамическая клавиатура
def show_more_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать больше", callback_data="show_more")]
    ])
    return keyboard

def options_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Опция 1", callback_data="option_1")],
        [InlineKeyboardButton(text="Опция 2", callback_data="option_2")]
    ])
    return keyboard
