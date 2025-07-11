from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

BOT_TOKEN = config("7854593039:AAH6BqG0YpdEuJG-BJrN4cXXZurysQqMj3o")
TMDB_API_KEY = config("c2ce62cf0ab90983716eb52966672e09")  # Получите на https://www.themoviedb.org/

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
