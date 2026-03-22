import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://sea-battle-bot.onrender.com')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎮 Играть в Морской бой",
            web_app=WebAppInfo(url=f"{WEB_APP_URL}/game")
        )],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])
    
    await message.answer(
        "⚓ Добро пожаловать в Морской бой! ⚓\n\n"
        "Выберите режим игры:\n"
        "• 👥 С другом - создайте комнату и поделитесь ID\n"
        "• 🤖 С ботом - играйте против искусственного интеллекта\n"
        "• ⚡ Быстрый старт - найдите случайного соперника\n\n"
        "Нажмите кнопку ниже, чтобы начать игру!",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer("📊 Статистика игроков будет доступна в следующей версии!", show_alert=True)

@dp.callback_query(F.data == "help")
async def show_help(callback: types.CallbackQuery):
    help_text = """
🎮 <b>Правила игры "Морской бой":</b>

<b>📋 Размещение кораблей:</b>
• 1 четырехпалубный корабль
• 2 трехпалубных корабля
• 3 двухпалубных корабля
• 4 однопалубных корабля

<b>🎯 Как играть:</b>
1. Корабли расставляются автоматически
2. По очереди стреляйте по клеткам противника
3. Попадание дает право дополнительного хода
4. Кто первым уничтожит все корабли - победил!

<b>🎮 Режимы игры:</b>
• <b>👥 С другом</b> - создайте комнату и поделитесь ID
• <b>🤖 С ботом</b> - игра против компьютера
• <b>⚡ Быстрый старт</b> - автоматический поиск соперника

<i>Удачи в морском сражении! 🌊</i>
    """
    await callback.message.answer(help_text, parse_mode="HTML")
    await callback.answer()

async def main():
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
