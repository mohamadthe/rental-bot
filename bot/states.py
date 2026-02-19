from aiogram.fsm.state import StatesGroup, State

class ListingForm(StatesGroup):
    city = State()
    address = State()
    rent = State()
    bedrooms = State()
    bathrooms = State()
    size = State()
    furnished = State()
    pets = State()
    smoking = State()
    available_date = State()
    phone = State()
