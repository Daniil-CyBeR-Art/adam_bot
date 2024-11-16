# Импорт необходимых библиотек
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from structure import quiz_data
from parameters import IDENTIFIER
from database import create_table, update_quiz_index, get_quiz_index, save_results, get_user_statistics

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=IDENTIFIER)
# Диспетчер
dp = Dispatcher()

user_results = {}  # Хранение результатов в памяти

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for index, option in enumerate(answer_options):
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"{index}_{'right' if option == right_answer else 'wrong'}"
        ))
    builder.adjust(1)
    return builder.as_markup()

@dp.callback_query(lambda c: True)
async def process_answer_callback(callback: types.CallbackQuery):
    button_index, answer_status = callback.data.split('_')
    button_index = int(button_index)

    # Убираем кнопки вне зависимости от ответа
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    # Получение информации о текущем вопросе
    current_question = quiz_data[current_question_index]
    correct_option = current_question['correct_option']

    # Проверяем, правильный ли ответ
    if callback.from_user.id not in user_results:
        user_results[callback.from_user.id] = {'correct': 0, 'wrong': 0}

    if answer_status == 'right':
        user_results[callback.from_user.id]['correct'] += 1
        await callback.message.answer(f"Вы ответили: {current_question['options'][correct_option]}\n"
                                      f"И вы ответили верно 🤩")
    else:
        user_results[callback.from_user.id]['wrong'] += 1
        response_message = (
            f"Вы ответили: {current_question['options'][button_index]}\n"
            f"И вы ошиблись 😞\n\n"
            f"Правильный ответ: {current_question['options'][correct_option]}"
        )
        await callback.message.answer(response_message)

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    # Проверяем, достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer(f"Это последний вопрос на сегодня.\n"
                                      f"Заходите позже, быть может я найду чем вас порадовать.\n"
                                      f"А сейчас - пора отдыхать!")

        # Сохранение результатов в базе данных

        await save_results(callback.from_user.id, user_results[callback.from_user.id]['correct'], user_results[callback.from_user.id]['wrong'])

        correct_count = user_results[callback.from_user.id]['correct']
        wrong_count = user_results[callback.from_user.id]['wrong']
        await callback.message.answer(f"Ваш результат:\n"
                                      f"Правильные ответы - {correct_count};\n"
                                      f"Неправильные ответы - {wrong_count}.")
        del user_results[callback.from_user.id]

@dp.message(F.text=="Посмотреть результаты ближних")
@dp.message(Command("stats"))
async def show_statistics(message: types.Message):
    all_statistics = await get_user_statistics()

    if all_statistics:
        response_message = "Результаты всех путников:\n\n"
        for user_id, correct, wrong in all_statistics:
            response_message += (f"Путник {user_id}:\n"
                                 f"Правильные ответы - {correct};\n"
                                 f"Неправильные ответы - {wrong}.\n\n")
        
        await message.answer(response_message)
    else:
        await message.answer("В Эдеме пусто 😢")

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="«Поехали!»"))
    builder.add(types.KeyboardButton(text="Посмотреть результаты ближних"))
    await message.answer("Добро пожаловать!", reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await get_question(message, user_id)

# Хэндлер на команду /quiz
@dp.message(F.text=="«Поехали!»")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Итак, начнём!")
    await new_quiz(message)

# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())