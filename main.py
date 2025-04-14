import logging
import os
import sqlite3

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.message import ContentType
from aiogram.utils import executor

API_TOKEN = "YOUR_BOT_TOKEN_HERE"
DB_NAME = "data.db"
UPLOAD_DIR = "uploads"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

os.makedirs(UPLOAD_DIR, exist_ok=True)

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT,
    xpath TEXT
)"""
)
conn.commit()
conn.close()

upload_btn = KeyboardButton("Загрузить файл")
keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(upload_btn)


@dp.message_handler(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Загрузите файл Excel:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Загрузить файл")
async def prompt_file_upload(message: types.Message):
    await message.answer(
        "Пожалуйста, прикрепите Excel-файл (.xls или .xlsx) сообщением"
    )


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def handle_file(message: types.Message):
    document = message.document

    if not document.file_name.endswith((".xls", ".xlsx")):
        await message.answer("Пожалуйста, загрузите Excel файл (.xls или .xlsx)")
        return

    file_path = os.path.join(UPLOAD_DIR, document.file_name)
    await document.download(destination_file=file_path)

    try:
        df = pd.read_excel(file_path)

        text = df.to_string(index=False)
        await message.answer(f"Содержимое файла:\n<pre>{text}</pre>", parse_mode="HTML")

        conn = sqlite3.connect(DB_NAME)
        df.to_sql("links", conn, if_exists="append", index=False)
        conn.close()

    except Exception as e:
        logging.exception("Ошибка при обработке файла")
        await message.answer(f"Произошла ошибка при обработке файла: {e}")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
