import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import LabeledPrice, PreCheckoutQuery

BOT_TOKEN = 8690718330:AAE8xbjTYeDeL4Eogzv0tTYvGxDIJLe8nC4
CHANNEL_ID = -1004382269176     #
PRICE_STARS = 50         
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Доступ в приватный канал",
        description="Подписка на 30 дней в закрытый канал.",
        payload="channel_access_payload",
        currency="XTR",
        prices=[LabeledPrice(label="Доступ в ТГК", amount=PRICE_STARS)],
        provider_token=""
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            name=f"Invite for {message.from_user.id}"
        )
        await message.answer(
            f"✅ **Оплата прошла успешно!**\n\n"
            f"Твоя персональная ссылка для входа:\n{invite_link.invite_link}\n\n"
            f"_Ссылка одноразовая._",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer("Произошла ошибка при создании ссылки. Напиши администратору.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.dp_shut = True
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
