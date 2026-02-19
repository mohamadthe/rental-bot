import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.config import BOT_TOKEN
from bot.database import create_pool, CREATE_TABLE
from bot.states import ListingForm

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db_pool = None
PAGE_SIZE = 5

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Post Listing", callback_data="post")],
        [InlineKeyboardButton(text="🔍 Find Rental", callback_data="find")],
        [InlineKeyboardButton(text="✏️ Edit My Listing", callback_data="edit")],
        [InlineKeyboardButton(text="❌ Delete My Listing", callback_data="delete")]
    ])

async def on_startup(app):
    global db_pool
    db_pool = await create_pool()
    async with db_pool.acquire() as conn:
        await conn.execute(CREATE_TABLE)
    webhook_url = os.getenv("WEBHOOK_URL")
    await bot.set_webhook(webhook_url)

async def on_shutdown(app):
    await bot.delete_webhook()

@dp.message(commands=["start"])
async def start(message: types.Message):
    await message.answer("Rental Bot Menu", reply_markup=main_menu())

# --- Post Listing ---

@dp.callback_query(F.data == "post")
async def post_listing(callback: types.CallbackQuery, state: FSMContext):
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM listings WHERE user_id=$1",
            callback.from_user.id
        )
        if existing:
            await callback.message.answer("You already have an active listing.")
            return
    await state.set_state(ListingForm.city)
    await callback.message.answer("Enter City:")

@dp.message(ListingForm.city)
async def city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(ListingForm.address)
    await message.answer("Enter Address:")

@dp.message(ListingForm.address)
async def address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(ListingForm.rent)
    await message.answer("Enter Monthly Rent (number):")

@dp.message(ListingForm.rent)
async def rent(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Enter valid number.")
        return
    await state.update_data(rent=int(message.text))
    await state.set_state(ListingForm.bedrooms)
    await message.answer("Enter Bedrooms (number):")

@dp.message(ListingForm.bedrooms)
async def bedrooms(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Enter valid number.")
        return
    await state.update_data(bedrooms=int(message.text))
    await state.set_state(ListingForm.bathrooms)
    await message.answer("Enter Bathrooms (number):")

@dp.message(ListingForm.bathrooms)
async def bathrooms(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Enter valid number.")
        return
    await state.update_data(bathrooms=int(message.text))
    await state.set_state(ListingForm.size)
    await message.answer("Enter Size:")

@dp.message(ListingForm.size)
async def size(message: types.Message, state: FSMContext):
    await state.update_data(size=message.text)
    await state.set_state(ListingForm.furnished)
    await message.answer("Furnished? (yes/no)")

@dp.message(ListingForm.furnished)
async def furnished(message: types.Message, state: FSMContext):
    await state.update_data(furnished=message.text.lower() == "yes")
    await state.set_state(ListingForm.pets)
    await message.answer("Pets allowed? (yes/no)")

@dp.message(ListingForm.pets)
async def pets(message: types.Message, state: FSMContext):
    await state.update_data(pets=message.text.lower() == "yes")
    await state.set_state(ListingForm.smoking)
    await message.answer("Smoking allowed? (yes/no)")

@dp.message(ListingForm.smoking)
async def smoking(message: types.Message, state: FSMContext):
    await state.update_data(smoking=message.text.lower() == "yes")
    await state.set_state(ListingForm.available_date)
    await message.answer("Available date:")

@dp.message(ListingForm.available_date)
async def available_date(message: types.Message, state: FSMContext):
    await state.update_data(available_date=message.text)
    await state.set_state(ListingForm.phone)
    await message.answer("Enter Contact Phone:")

@dp.message(ListingForm.phone)
async def phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["phone"] = message.text

    async with db_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO listings 
            (user_id, city, address, rent, bedrooms, bathrooms, size, furnished, pets, smoking, available_date, phone)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)""",
            message.from_user.id,
            data["city"],
            data["address"],
            data["rent"],
            data["bedrooms"],
            data["bathrooms"],
            data["size"],
            data["furnished"],
            data["pets"],
            data["smoking"],
            data["available_date"],
            data["phone"]
        )

    await state.clear()
    await message.answer("Listing saved successfully!", reply_markup=main_menu())

def main():
    app = web.Application()
    webhook_path = "/webhook"
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
