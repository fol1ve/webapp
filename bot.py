import asyncio
import os
import logging
import time

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    FSInputFile
)

from dotenv import load_dotenv
from pathlib import Path
from parser import TelegramChannelParser


# =========================
# НАСТРОЙКИ
# =========================
AUTO_DELETE_MINUTES = 10
FLOOD_DELAY = 15


# =========================
# АНТИФЛУД
# =========================
user_last_action = {}

def antiflood(user_id: int) -> bool:
    now = time.time()
    last = user_last_action.get(user_id, 0)

    if now - last < FLOOD_DELAY:
        return False

    user_last_action[user_id] = now
    return True


# =========================
# ENV
# =========================
load_dotenv()
load_dotenv("pz.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# PARSER
# =========================
parser = TelegramChannelParser(
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE
)


# =========================
# WEBAPP BUTTON
# =========================
webapp_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🌐 Открыть WebApp",
                web_app=WebAppInfo(
                    url="https://fol1ve.github.io/webapp/"
                )
            )
        ]
    ],
    resize_keyboard=True
)


# =========================
# /start
# =========================
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "👋 Привет!\n\n"
        "Открой WebApp и вставь ссылку на канал 👇",
        reply_markup=webapp_kb
    )


# =========================
# ПОЛУЧЕНИЕ ДАННЫХ ИЗ WEBAPP
# =========================
@dp.message(F.web_app_data)
async def webapp_handler(msg: types.Message):
    link = msg.web_app_data.data
    await process_link(msg, link)


# =========================
# ОСНОВНАЯ ЛОГИКА
# =========================
async def process_link(msg: types.Message, link: str):
    user_id = msg.from_user.id

    if not antiflood(user_id):
        await msg.answer("⏳ Подожди немного.")
        return

    if "t.me/" not in link:
        await msg.answer("❌ Некорректная ссылка.")
        return

    await msg.answer("🔌 Подключаюсь к Telegram...")
    await parser.connect()

    await msg.answer("📊 Получаю информацию...")
    info = await parser.get_channel_info(link)

    if not info:
        await msg.answer("❌ Не удалось получить данные.")
        return

    await msg.answer(
        f"📢 {info['title']}\n"
        f"👥 Участников: {info.get('participants_count', '—')}\n\n"
        f"⏳ Сбор участников..."
    )

    participants = await parser.collect_all_participants_comprehensive(link)

    await msg.answer(f"✅ Собрано: {len(participants)}")

    os.makedirs("parsed_data", exist_ok=True)
    prefix = f"parsed_data/{info['raw_username'] or 'channel'}"

    csv_file, txt_file = await parser.save_participants_with_progress(
        participants, prefix
    )

    await bot.send_document(msg.chat.id, FSInputFile(csv_file))
    await bot.send_document(msg.chat.id, FSInputFile(txt_file))

    await parser.close()


# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
