import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://hacker-simulator-bot.onrender.com')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Главное меню
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
        "• С другом - поделитесь ссылкой\n"
        "• С ботом - играйте против ИИ\n"
        "• Быстрый старт - найдите случайного соперника\n\n"
        "Нажмите кнопку ниже, чтобы начать!",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    # Здесь будет логика получения статистики
    await callback.answer("Статистика в разработке", show_alert=True)

@dp.callback_query(F.data == "help")
async def show_help(callback: types.CallbackQuery):
    help_text = """
🎮 <b>Правила игры "Морской бой":</b>

• У каждого игрока поле 10x10
• Разместите корабли:
  - 1 четырехпалубный
  - 2 трехпалубных
  - 3 двухпалубных
  - 4 однопалубных

• По очереди стреляйте по клеткам
• Кто первым уничтожит все корабли - победил!

<b>Режимы игры:</b>
• <b>С другом</b> - создайте комнату и поделитесь ссылкой
• <b>С ботом</b> - игра против компьютера
• <b>Быстрый старт</b> - найдет случайного соперника
    """
    await callback.message.answer(help_text, parse_mode="HTML")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
