import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from crud_functions import initiate_db, get_all_products

api = "6716646027:AAFOK2SN_sasZ0i_IZUTgxtyK7WAp-q4gL4"
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

IMAGE_FOLDER = 'files'

print("Текущий рабочий каталог:", os.getcwd())

initiate_db()


class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()


keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(types.KeyboardButton('Рассчитать'), types.KeyboardButton('Информация'))
keyboard.add(types.KeyboardButton('Купить'))

product_inline_kb = InlineKeyboardMarkup(row_width=2)
product_inline_kb.add(
    InlineKeyboardButton("Продукт1", callback_data="product_buying"),
    InlineKeyboardButton("Продукт2", callback_data="product_buying"),
    InlineKeyboardButton("Продукт3", callback_data="product_buying"),
    InlineKeyboardButton("Продукт4", callback_data="product_buying")
)


@dp.message_handler(commands='start')
async def start_cmd(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=keyboard)


@dp.message_handler(text='Рассчитать')
async def set_age(message: types.Message):
    await message.answer("Введите свой возраст:")
    await UserState.age.set()


@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число).")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Введите свой рост (в см):")
    await UserState.growth.set()


@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный рост (число в см).")
        return
    await state.update_data(growth=int(message.text))
    await message.answer("Введите свой вес (в кг):")
    await UserState.weight.set()


@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный вес (число в кг).")
        return
    await state.update_data(weight=int(message.text))

    data = await state.get_data()
    age = data['age']
    growth = data['growth']
    weight = data['weight']

    calories = 10 * weight + 6.25 * growth - 5 * age + 5

    await message.answer(f"Норма калорий для вашего возраста, роста и веса: {calories:.2f} калорий в день.")

    await state.finish()


@dp.message_handler(text='Информация')
async def info_cmd(message: types.Message):
    await message.answer(
        "Этот бот помогает рассчитать вашу норму калорий по формуле Миффлина-Сан Жеора. Нажмите 'Рассчитать', чтобы начать.")


# Хендлер для кнопки "Купить"
@dp.message_handler(text='Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()

    if not products:
        await message.answer("Продукты не найдены.")
        return

    for product in products:
        product_id, title, description, price = product

        image_path = os.path.join(IMAGE_FOLDER, f"{product_id}.jpg")

        if not os.path.isfile(image_path):
            await message.answer(f"Ошибка: файл {image_path} не найден.")
            continue

        with open(image_path, 'rb') as image:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=image,
                caption=f"Название: {title} | Описание: {description} | Цена: {price}"
            )

    await message.answer("Выберите продукт для покупки:", reply_markup=product_inline_kb)


@dp.callback_query_handler(text="product_buying")
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
