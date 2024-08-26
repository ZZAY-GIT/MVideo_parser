import asyncio
import sqlite3
import datetime
import logging
import sys

from modules.config import pages, API_TOKEN
from modules.Mvideo import parse

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    FSInputFile
)

dp = Dispatcher()
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
con = sqlite3.connect('database\\database.db')
cur = con.cursor()
dates = cur.execute('SELECT date FROM active').fetchall()
dates = list(map(lambda x: str(x[0]), dates))
if datetime.datetime.now().strftime('%d.%m') not in dates:
    cur.execute(f'INSERT INTO active(messages, date) VALUES(0, {datetime.datetime.now().strftime("%d.%m")})')
    con.commit()

current_page = 0


def update_keyboard():
    buttons = []
    for button_text in pages[current_page]:
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f'button_{button_text}')])
    buttons.append([InlineKeyboardButton(text=f'Страница {current_page + 1} из {len(pages)}', callback_data='back')])
    if 0 < current_page < len(pages) - 1:
        buttons.append([InlineKeyboardButton(text='⬅️', callback_data='prev'),
                        InlineKeyboardButton(text='➡️', callback_data='next')])
    elif current_page > 0:
        buttons.append([InlineKeyboardButton(text='⬅️', callback_data='prev')])
    elif current_page < len(pages) - 1:
        buttons.append([InlineKeyboardButton(text='➡️', callback_data='next')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def message_count():
    messages = \
        cur.execute(
            f'SELECT messages FROM active WHERE date == {datetime.datetime.now().strftime("%d.%m")}').fetchall()[0]
    messages = messages[0]
    messages += 1

    cur.execute(f'UPDATE active \n'
                f"SET (messages) = ({messages}) \n"
                f'WHERE date = {datetime.datetime.now().strftime("%d.%m")}')
    con.commit()


# обработка команды /start
@dp.message(CommandStart())
async def start_command(message: Message) -> None:
    buttons = [
        [KeyboardButton(text="Информация")],
        [KeyboardButton(text="Категории")],
        [KeyboardButton(text="Статистика")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True,
                                   input_field_placeholder="Выберите то, что вас интересует")
    await message.answer("Добро пожаловать! Выберите что хотите посмотреть ниже.", reply_markup=keyboard)
    global cur
    global current_page
    response = cur.execute('SELECT user_id FROM users').fetchall()[0]

    message_count()

    if message.from_user.id not in response:
        cur.execute(f'INSERT INTO users(user_id) VALUES({message.from_user.id})')
        con.commit()
    current_page = 0


@dp.message(lambda message: message.text == "Категории" or message.text == "Отправить новый запрос")
async def categories(message: Message):
    message_count()

    await message.answer('Выберите категорию:', reply_markup=update_keyboard())


@dp.message(lambda message: message.text == "Информация")
async def cmd_help(message: Message):
    message_count()

    await message.reply(f"<b>Что делает этот бот?</b> \n"
                        f"Этот бот автоматически собирает информацию с сайта и выдаёт вам готовый файл "
                        f"с товарами исходя из той категории, которую вы выбрали.\n"
                        f"\n"
                        f"<b>Как пользоваться этим ботом?</b> \n"
                        f'Всё очень просто! Нажмите на кнопку <b>"Категории"</b>, выберите нужную категорию, нажмите '
                        f'на неё и немного подождите.\n'
                        f"\n"
                        f"<b>Чем может быть полезна эта информация?</b> \n"
                        f"Бот может быть полезен для компаний и каких-либо стартапов, также для обычных пользователей "
                        f"так как для каждого товара есть цена, цена со скидкой и ссылки на товары, любой "
                        f"программист может использовать данную информацию в своих целях.",
                        parse_mode="HTML")


@dp.message(lambda message: message.text == "Статистика")
async def cmd_stat(message: Message):
    users = cur.execute('SELECT user_id FROM users').fetchall()
    messages_today = \
        cur.execute(
            f'SELECT messages FROM active WHERE date == {datetime.datetime.now().strftime("%d.%m")}').fetchall()[0]
    messages_today = messages_today[0]
    messages_today += 1
    all_messages = cur.execute('SELECT messages FROM active').fetchall()
    all_messages = list(map(lambda x: int(x[0]), all_messages))
    await message.reply(f"<b> ---------------Статистика--------------- </b> \n \n"
                        f"Общее количество людей: {len(users)} \n"
                        f"Отправлено сообщений сегодня: {messages_today} \n"
                        f"Отправлено сообщений всего: {sum(all_messages) + 1}"
                        f""
                        f"",
                        parse_mode="HTML")
    cur.execute(f'UPDATE active \n'
                f"SET (messages) = ({messages_today}) \n"
                f'WHERE date = {datetime.datetime.now().strftime("%d.%m")}')
    con.commit()


@dp.callback_query(F.data == 'next')
async def next_page(callback_query: CallbackQuery):
    global current_page
    if callback_query.data == 'next' and current_page < len(pages) - 1:
        current_page += 1
        await callback_query.message.edit_text(text='Выберите категорию:', reply_markup=update_keyboard())
    await callback_query.answer()


@dp.callback_query(F.data == 'prev')
async def next_page(callback_query: CallbackQuery):
    global current_page
    if callback_query.data == 'prev' and current_page > 0:
        current_page -= 1
        await callback_query.message.edit_text(text='Выберите категорию:', reply_markup=update_keyboard())
    await callback_query.answer()


@dp.callback_query(F.data.startswith('button_'))
async def click_on_category(callback_query: CallbackQuery):
    category = callback_query.data.split('_')[-1]
    await callback_query.message.edit_text(text="Пожалуйста подождите, ваш запрос выполняется...", reply_markup=None)
    document_path = parse(category)
    print(document_path)
    await bot.send_document(chat_id=callback_query.message.chat.id, document=FSInputFile(document_path))
    await callback_query.message.edit_text(text="Успешно! Ваш запрос выполнен✅", reply_markup=None)
    await callback_query.answer()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())