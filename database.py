# Импорт необходимых библиотек
import aiosqlite
from parameters import QUIZ

# Асинхронная функция create_table для создания таблиц quiz_state в базе данных QUIZ
async def create_table():
    # Соединение с базой данных QUIZ (если база данных не существует, она будет создана)
    async with aiosqlite.connect(QUIZ) as db:
        # Создание таблицы quiz_state, если она ещё не создана (IF NOT EXISTS)
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    question_index INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
    user_id INTEGER PRIMARY KEY,
    username TEXT, 
    correct INTEGER NOT NULL,
    wrong INTEGER NOT NULL)''')
        # Сохранение изменений в базе данных
        await db.commit()

# Асинхронная функция update_quiz_index для добавления в таблицу quiz_state нового пользователя user_id и обновления состояния question_index, если пользователь уже существует
async def update_quiz_index(user_id, question_index, username=None):
    # Создаем соединение с базой данных QUIZ (если она не существует, она будет создана)
    async with aiosqlite.connect(QUIZ) as db:
        # Вставляем новую запись или заменяем ее (INSERT OR REPLACE), если пользователь user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, username) VALUES (?, ?, ?)', (user_id, question_index, username))
        # Сохраняем изменения в базе данных
        await db.commit()

async def save_results(user_id, correct, wrong, username=None):
    async with aiosqlite.connect(QUIZ) as db:
        await db.execute('INSERT OR REPLACE INTO quiz_results (user_id, correct, wrong, username) VALUES (?, ?, ?, ?)', (user_id, correct, wrong, username))
        await db.commit()

# Асинхронная функция для получиения текущего значения question_index в таблице quiz_state для заданного пользователя user_id
async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(QUIZ) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            
async def get_user_statistics():
    async with aiosqlite.connect(QUIZ) as db:
        async with db.execute('SELECT user_id, correct, wrong FROM quiz_results') as cursor:
            results = await cursor.fetchall()
            return results