import os
import logging
import asyncio  # Этот импорт был пропущен в предыдущих версиях
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiohttp
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Конфигурация Kinopoisk API
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
API_URL = "https://api.kinopoisk.dev/v1.4/movie"

# Проверка наличия API ключа
if not KINOPOISK_API_KEY:
    logger.error("KINOPOISK_API_KEY не найден в .env файле!")
    exit(1)

# Жанры для кнопок (используем английские названия как в API)
GENRES = {
    "комедия": "комедия",
    "фантастика": "фантастика",
    "ужасы": "ужасы",
    "боевик": "боевик",
    "драма": "драма"
}

# Клавиатура с жанрами
genres_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=genre) for genre in GENRES.keys()]],
    resize_keyboard=True,
    input_field_placeholder="Выберите жанр из списка"
)

class FilmStates(StatesGroup):
    choosing_genre = State()

async def fetch_kinopoisk_movies(genre: str):
    """Запрос к Kinopoisk API с обработкой ошибок"""
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "genres.name": GENRES[genre],
        "limit": 5,
        "sortField": "rating.kp",
        "sortType": "-1"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [
                        {
                            "title": movie.get("name", "Без названия"),
                            "year": str(movie.get("year", "N/A")),
                            "rating": str(movie.get("rating", {}).get("kp", "0.0")),
                            "poster": movie.get("poster", {}).get("url"),
                            "description": movie.get("description", "Описание отсутствует")
                        }
                        for movie in data.get("docs", [])
                    ]
                logger.error(f"Ошибка API: {resp.status}")
                return None
    except Exception as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message, state: FSMContext):
    """Обработка команды /start"""
    await message.answer(
        "🎬 <b>Кинобот с базой Kinopoisk</b>\nВыберите жанр:",
        reply_markup=genres_kb,
        parse_mode="HTML"
    )
    await state.set_state(FilmStates.choosing_genre)

@dp.message(FilmStates.choosing_genre)
async def genre_chosen(message: types.Message, state: FSMContext):
    """Обработка выбора жанра"""
    try:
        user_genre = message.text.lower()
        
        if user_genre not in GENRES:
            await message.answer("Пожалуйста, выберите жанр из предложенных кнопок!")
            return
        
        await message.answer(f"🔍 Ищу фильмы в жанре '{message.text}'...")
        
        movies = await fetch_kinopoisk_movies(user_genre)
        
        if not movies:
            await message.answer("⚠️ Не удалось получить данные. Попробуйте позже.")
            return
        
        for movie in movies:
            caption = (
                f"🎥 <b>{movie['title']}</b> ({movie['year']})\n"
                f"⭐ Рейтинг: {movie['rating']}/10\n"
                f"📝 {movie['description']}"
            )
            
            if movie.get('poster'):
                try:
                    await message.answer_photo(
                        photo=movie['poster'],
                        caption=caption,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки постера: {e}")
                    await message.answer(caption, parse_mode="HTML")
            else:
                await message.answer(caption, parse_mode="HTML")
        
        await message.answer("🎉 Готово! Для нового поиска нажмите /start")
        
    except Exception as e:
        logger.error(f"Ошибка обработки жанра: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")
    finally:
        await state.clear()

async def main():
    """Запуск бота"""
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
