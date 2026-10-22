import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8690718330:AAGfd4wBtBA_81ZnEYH9b7MSD5dtEX0XqX8"
CHANNEL_ID = -1004382269176

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            chat_id INTEGER,
            expire_date TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    """)
    conn.commit()
    conn.close()

def add_subscription(user_id: int, chat_id: int, days: int = 30):
    expire_date = datetime.now() + timedelta(days=days)
    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO subscriptions (user_id, chat_id, expire_date)
        VALUES (?, ?, ?)
    """, (user_id, chat_id, expire_date.isoformat()))
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    prices = [LabeledPrice(label="Месячная подписка", amount=50)]
    await message.answer_invoice(
        title="Подписка на закрытый канал",
        description="Доступ на 30 дней с автоматической проверкой",
        payload="monthly_sub",
        currency="XTR",
        prices=prices
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    expire_time = int((datetime.now() + timedelta(days=1)).timestamp())
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=expire_time
        )
        add_subscription(message.from_user.id, CHANNEL_ID, days=30)
        await message.answer(
            "✅ Оплата прошла успешно!\n\n"
            "Вот твоя персональная ссылка на вход в канал (действует 1 раз):\n"
            f"{invite_link.invite_link}\n\n"
            "Подписка активна в течение 30 дней."
        )
    except Exception as e:
        await message.answer(f"⚠️ Оплата прошла, но произошла ошибка при создании ссылки: {e}")

async def check_subscriptions():
    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, chat_id, expire_date FROM subscriptions")
    rows = cursor.fetchall()
    now = datetime.now()
    for user_id, chat_id, expire_date_str in rows:
        expire_date = datetime.fromisoformat(expire_date_str)
        if now >= expire_date:
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status in ["administrator", "creator"]:
                    add_subscription(user_id, chat_id, days=1)
                    continue
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                cursor.execute("DELETE FROM subscriptions WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
                conn.commit()
                try:
                    await bot.send_message(
                        user_id, 
                        "⌛️ Твоя подписка на закрытый канал истекла, и ты был исключен.\n"
                        "Чтобы продлить доступ, отправь боту /start."
                    )
                except Exception:
                    pass
            except Exception as e:
                logging.error(f"Не удалось проверить пользователя {user_id}: {e}")
    conn.close()

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
