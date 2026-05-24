import os
import time
from flask import Flask, request, jsonify, render_template_string
import psycopg2

app = Flask(__name__)

# Шаблон интерфейса (HTML)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | SimpleAuthApp</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #333;
        }
        /* Шапка сайта */
        header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        .logo {
            font-size: 20px;
            font-weight: 700;
            color: #fff;
            text-decoration: none;
            letter-spacing: 0.5px;
        }
        .nav-links a {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            margin-left: 20px;
            font-size: 14px;
            font-weight: 500;
            transition: color 0.3s;
        }
        .nav-links a:hover {
            color: #fff;
        }
        /* Главный контейнер с формой */
        .main-container {
            flex-grow: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .card {
            background: #ffffff;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            width: 100%;
            max-width: 400px;
            transform: translateY(0);
            transition: all 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }
        .card h2 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2d3748;
            text-align: center;
        }
        .subtitle {
            font-size: 14px;
            color: #718096;
            text-align: center;
            margin-bottom: 28px;
        }
        /* Стили полей ввода */
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 6px;
            color: #4a5568;
        }
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #cbd5e0;
            border-radius: 8px;
            font-size: 14px;
            background-color: #f7fafc;
            transition: all 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            background-color: #fff;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
        }
        /* Кнопка отправки */
        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .btn:hover {
            opacity: 0.95;
            transform: translateY(-1px);
            box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4);
        }
        .btn:active {
            transform: translateY(1px);
        }
        /* Системные уведомления */
        .message-box {
            margin-top: 20px;
            padding: 10px;
            border-radius: 6px;
            font-size: 13px;
            text-align: center;
            font-weight: 500;
            background-color: #edf2f7;
            color: #2b6cb0;
        }
        /* Подвал */
        footer {
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        footer a {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
        }
    </style>
</head>
<body>

    <header>
        <a href="/" class="logo">SimpleAuthApp</a>
        <nav class="nav-links">
            <a href="/login">Вход</a>
            <a href="/register">Регистрация</a>
        </nav>
    </header>

    <div class="main-container">
        <div class="card">
            <h2>{{ title }}</h2>
            <p class="subtitle">Пожалуйста, заполните форму ниже</p>
            
            <form action="{{ action }}" method="POST">
                <div class="form-group">
                    <label>Электронная почта / Логин</label>
                    <input type="text" name="username" placeholder="name@example.com" required autocomplete="off">
                </div>
                <div class="form-group">
                    <label>Пароль</label>
                    <input type="password" name="password" placeholder="••••••••" required>
                </div>
                <button type="submit" class="btn">Продолжить</button>
            </form>

            {% if message %}
            <div class="message-box">
                {{ message }}
            </div>
            {% endif %}
        </div>
    </div>

    <footer>
        &copy; 2026 - SimpleAuthApp - <a href="#">Конфиденциальность</a>
    </footer>

</body>
</html>
"""


def get_db_connection():
    # Параметры берутся из переменных окружения (важно для Cloud Native)
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'authdb'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'secret')
    )

# Инициализация БД: создаем таблицу, если её нет
def init_db():
    for i in range(5): # 5 попыток дождаться старта БД
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(50) NOT NULL
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("БД успешно инициализирована")
            break
        except Exception as e:
            print(f"Ожидание БД... Ошибка: {e}")
            time.sleep(3)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, title="Добро пожаловать в SimpleAuthApp", action="/login", message="Выберите Регистрацию или Вход.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            cur.close()
            conn.close()
            return render_template_string(HTML_TEMPLATE, title="Регистрация", action="/register", message="Пользователь успешно зарегистрирован! Теперь войдите.")
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, title="Регистрация", action="/register", message=f"Ошибка: Пользователь уже существует или БД недоступна.")
    return render_template_string(HTML_TEMPLATE, title="Регистрация нового пользователя", action="/register", message="")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return render_template_string(HTML_TEMPLATE, title="Личный кабинет", action="/login", message=f"Успешный вход! Привет, {username}!")
        else:
            return render_template_string(HTML_TEMPLATE, title="Вход в систему", action="/login", message="Неверное имя пользователя или пароль.")
    return render_template_string(HTML_TEMPLATE, title="Вход в систему", action="/login", message="")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
