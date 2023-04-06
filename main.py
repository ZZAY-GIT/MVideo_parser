import asyncio
import logging
from random import randint

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from modules.config import API_TOKEN
from aiogram.dispatcher import FSMContext
from modules.Mvideo import parse, get_categoryId

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

pages = [
    {
        "Телевизоры": "65",
        "Ноутбуки": "118",
        "Смартфоны": "205",
        "Клавиатуры": "217",
        "Планшеты": "195",
        "Компьютерные мыши": "183",

    },
    {
        'Наушники': '3967',
        'Смарт-часы': '400',
        "Мониторы": "101",
        "Пылесосы": "2428",
        'Кондиционеры': '106',
        "Тренажёры": "8411",
    },
    {
        "Холодильники": "159",
        "Микроволновые печи": "94",
        "Электрочайники": "96",
        "Мультиварки": "180",
        "Посудомоечные машины": "160",
        'Стиральные машины': '89',
    }

]

# начальная страница
current_page = 0


# метод для обновления инлайн-клавиатуры на основе текущей страницы
def update_keyboard():
    keyboard = InlineKeyboardMarkup()
    for button_text in pages[current_page]:
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f'button_{button_text}'))
    keyboard.add(InlineKeyboardButton(f'Страница {current_page + 1} из {len(pages)}', callback_data='back'))
    if 0 < current_page < len(pages) - 1:
        keyboard.add(InlineKeyboardButton('⬅️', callback_data='prev'), InlineKeyboardButton('➡️', callback_data='next'))
    elif current_page > 0:
        keyboard.add(InlineKeyboardButton('⬅️', callback_data='prev'))
    elif current_page < len(pages) - 1:
        keyboard.add(InlineKeyboardButton('➡️', callback_data='next'))
    return keyboard


def delete_InlineKeyboard():
    keyboard = InlineKeyboardMarkup()
    return keyboard


def delete_Keyboard():
    keyboard = types.ReplyKeyboardMarkup.clean
    return keyboard


# обработка команды /start
@dp.message_handler(commands=['start'], state=None)
async def start_command(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Информация", "Категории"]
    keyboard.add(*buttons)
    await message.answer("Добро пожаловать! Выберите что хотите посмотреть ниже.", reply_markup=keyboard)
    global current_page
    current_page = 0


@dp.message_handler(lambda message: message.text == "Категории" or message.text == "Отправить новый запрос")
async def categories(message: types.Message):
    await message.answer('Выберите категорию:', reply_markup=update_keyboard())


# обработка нажатия на кнопки
@dp.callback_query_handler(lambda c: c.data in ['prev', 'next'] or c.data in pages[current_page])
async def process_callback(callback_query: CallbackQuery):
    global current_page
    if callback_query.data == 'prev' and current_page > 0:
        current_page -= 1
        await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                            callback_query.message.message_id,
                                            reply_markup=update_keyboard())
    elif callback_query.data == 'next' and current_page < len(pages) - 1:
        current_page += 1
        await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                            callback_query.message.message_id,
                                            reply_markup=update_keyboard())
    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(lambda message: message.text == "Информация")
async def cmd_help(message: types.Message):
    await message.reply(f"<b>Что делает этот бот?</b> \n"
                        f"Этот бот автоматически собирает информацию с сайта и выдаёт вам готовый файл "
                        f"с товарами исходя из той категории, которую вы выбрали.\n"
                        f"-----------------------------------------------------------------------------------------------------\n"
                        f"<b>Как пользоваться этим ботом?</b> \n"
                        f'Всё очень просто! Нажмите на кнопку "Категории", выберите нужную категорию, нажмите на неё '
                        f'и немного подождите.\n'
                        f"-----------------------------------------------------------------------------------------------------\n"
                        f"<b>Чем может быть полезна эта информация?</b> \n"
                        f"Бот может быть полезен для тех, кто хочет быстро и из нескольких категорий выявить тот "
                        f"товар который ему нужен, потому что все данные отправляются в виде Excel-таблицы.",
                        parse_mode="HTML")


@dp.callback_query_handler(lambda c: 'button_' in c.data)
async def click(callback_query: CallbackQuery):
    category = callback_query.data.split('_')[-1]
    await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=delete_InlineKeyboard())
    await bot.edit_message_text("Пожалуйста подождите, ваш запрос выполняется...", callback_query.message.chat.id,
                                callback_query.message.message_id)
    path = parse(category)
    print(path)
    await bot.send_document(callback_query.from_user.id, types.InputFile(path))
    await bot.edit_message_text("Успешно! Ваш запрос выполнен✅", callback_query.message.chat.id,
                                callback_query.message.message_id)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
