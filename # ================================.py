# ============================================
# MYXA AI — FULL ULTRA GUI (ГОТОВАЯ ВЕРСИЯ)
# Автор: Мухаммад & ChatGPT
# ВСЁ РАБОТАЕТ: чаты, имя, темы, поиск, игры, счётчик, ГДЗ, БЕСПЛАТНАЯ НЕЙРОСЕТЬ
# ============================================
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import json
import os
import time
import threading
import random
import re
from datetime import datetime
import webbrowser
import urllib.parse
import requests

# ============================================
# ----------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ----------
# ============================================

APP_NAME = "MYXA AI"
DATA_FILE = "myxa_history.json"
SETTINGS_FILE = "myxa_settings.json"
PROFILE_FILE = "myxa_profile.json"

current_chat = "Главный чат"
chat_history = {}
internet_enabled = True
user_name = None
current_theme = "light"
message_count = 0

# === КОНТЕКСТ ===
last_user_action = None
last_bot_response = None
context_data = {}

# === ВЫБОР МОДЕЛИ ===
current_ai_model = "myxa"   # "myxa" или "neural"

# ============================================
# ----------------- ТЕМЫ ----------------------
# ============================================

THEMES = {
    "light": {
        "bg": "#ffffff", "fg": "#000000", "input_bg": "#f2f2f2", "input_fg": "#000000",
        "btn_bg": "#e0e0e0", "btn_fg": "#000"
    },
    "dark": {
        "bg": "#1f1f1f", "fg": "#ffffff", "input_bg": "#2a2a2a", "input_fg": "#ffffff",
        "btn_bg": "#3a3a3a", "btn_fg": "#fff"
    },
    "blue": {
        "bg": "#e6f0ff", "fg": "#003366", "input_bg": "#d4e2ff", "input_fg": "#001a33",
        "btn_bg": "#b5ccff", "btn_fg": "#001a33"
    },
    "green": {
        "bg": "#e8ffe8", "fg": "#003300", "input_bg": "#d8ffd8", "input_fg": "#002200",
        "btn_bg": "#b4ffb4", "btn_fg": "#002200"
    },
    "red": {
        "bg": "#ffe6e6", "fg": "#660000", "input_bg": "#ffd4d4", "input_fg": "#330000",
        "btn_bg": "#ffb3b3", "btn_fg": "#330000"
    }
}

# ============================================
# ----------- ЗАГРУЗКА / СОХРАНЕНИЕ ----------
# ============================================

def load_history():
    global chat_history
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                chat_history.update(json.load(f))
        except:
            chat_history.clear()
    if current_chat not in chat_history:
        chat_history[current_chat] = []

def save_history():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)

def load_profile():
    global user_name
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_name = data.get("name")
        except:
            user_name = None

def save_profile(name):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f, ensure_ascii=False, indent=2)

def load_settings():
    global current_theme
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                current_theme = settings.get("theme", "light")
        except:
            pass

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"theme": current_theme}, f, ensure_ascii=False, indent=2)

load_profile()
load_settings()

# ============================================
# ----------- СОЗДАНИЕ ОСНОВНОГО ОКНА --------
# ============================================

root = tk.Tk()
root.title(APP_NAME)
root.geometry("1250x800")
root.resizable(False, False)

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), height=28)
chat_box.pack(fill="both", padx=5, pady=5)
chat_box.config(state=tk.DISABLED)

entry_box = tk.Entry(root, font=("Arial", 14))
entry_box.pack(fill="x", padx=5, pady=3)

button_frame = tk.Frame(root)
button_frame.pack(fill="x", padx=5)

bottom_buttons = []

def make_button(text, command):
    btn = tk.Button(button_frame, text=text, width=10, command=command)
    btn.pack(side="left", padx=2, pady=3)
    bottom_buttons.append(btn)
    return btn

# ============================================
# ----------- ПРИМЕНЕНИЕ ТЕМЫ ----------------
# ============================================

def apply_theme():
    theme = THEMES[current_theme]
    root.configure(bg=theme["bg"])
    try:
        chat_box.configure(bg=theme["bg"], fg=theme["fg"])
        entry_box.configure(bg=theme["input_bg"], fg=theme["input_fg"])
        for btn in bottom_buttons:
            btn.configure(bg=theme["btn_bg"], fg=theme["btn_fg"])
    except:
        pass

# ============================================
# ----------- СИСТЕМА СООБЩЕНИЙ --------------
# ============================================

def add_message(sender, text):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"{sender}: {text}\n\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)

    if current_chat not in chat_history:
        chat_history[current_chat] = []
    chat_history[current_chat].append({"sender": sender, "text": text})
    save_history()

# ============================================
# ----------- ЛОГИКА ИИ (МОЗГ) --------------
# ============================================

message_history = []
max_history = 30

def fix_text(text):
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()

def detect_emotion(text):
    sad = ["груст", "плохо", "печаль", "тяжело", "устал", "не хочу", "один", "страх"]
    happy = ["круто", "класс", "спасибо", "норм", "отлично", "хорошо", "ура"]
    low = text.lower()
    if any(w in low for w in sad): return "sad"
    if any(w in low for w in happy): return "happy"
    return "neutral"

def emotion_reply(em):
    if em == "sad": return "Бро… я с тобой. Ты сильный. Всё наладится 💪🔥"
    if em == "happy": return "Красавчик! Рад слышать такие эмоции! 😎"
    return None

def build_reply(main, extra=None):
    return main + "\n\n" + extra if extra else main

def remember(text):
    message_history.append(text)
    if len(message_history) > max_history:
        message_history.pop(0)

def save_name(name):
    global user_name
    user_name = name.capitalize()
    save_profile(user_name)
    return f"Отлично! Теперь я знаю, что тебя зовут {user_name} 🔥"

# ============================================
# ----------- ИГРЫ ---------------------------
# ============================================

secret_number = None

def game_rps(choice):
    options = ["камень", "ножницы", "бумага"]
    bot = random.choice(options)
    choice = choice.lower()
    if choice not in options:
        return "Выбери: камень / ножницы / бумага"
    if choice == bot:
        result = "Ничья!"
    elif (choice == "камень" and bot == "ножницы") or \
         (choice == "ножницы" and bot == "бумага") or \
         (choice == "бумага" and bot == "камень"):
        result = "Ты выиграл! 🔥"
    else:
        result = "Ты проиграл 😅"
    return f"Ты: {choice}\nБот: {bot}\n\n{result}"

def play_coin_gui():
    """Окно с выбором стороны монетки"""
    coin_win = tk.Toplevel(root)
    coin_win.title("🪙 Монетка")
    coin_win.geometry("300x250")
    coin_win.resizable(False, False)
    
    result_label = tk.Label(coin_win, text="Выбери сторону:", font=("Arial", 14))
    result_label.pack(pady=15)
    
    def play(choice):
        result = random.choice(["Орёл", "Решка"])
        if choice == result:
            outcome = "🎉 Ты выиграл!"
        else:
            outcome = "😅 Ты проиграл!"
        
        result_label.config(text=f"Ты выбрал: {choice}\nВыпало: {result}\n{outcome}")
        add_message("MYXA AI", f"🪙 Монетка: Ты — {choice}, Выпало — {result}. {outcome}")
    
    btn_frame = tk.Frame(coin_win)
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="🦅 Орёл", width=10, command=lambda: play("Орёл")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="🪙 Решка", width=10, command=lambda: play("Решка")).pack(side="left", padx=5)
    
    tk.Button(coin_win, text="Закрыть", command=coin_win.destroy, width=15).pack(pady=10)

def game_coin():
    return f"🪙 Монетка подброшена!\nВыпало: {random.choice(['Орёл', 'Решка'])}"

def game_guess_start():
    global secret_number
    secret_number = random.randint(1, 10)
    return "🎯 Я загадал число от 1 до 10! Попробуй угадать!"

def game_guess_check(n):
    global secret_number
    if secret_number is None:
        return "Сначала напиши: игра угадай"
    if n == secret_number:
        secret_number = None
        return "🔥 Ты угадал! Красавчик!"
    return "Больше!" if n < secret_number else "Меньше!"

# ============================================
# ----------- ПОИСК И ИНТЕРНЕТ ---------------
# ============================================

def toggle_inet():
    global internet_enabled
    internet_enabled = not internet_enabled
    add_message("MYXA AI", f"Интернет {'включен 🌐' if internet_enabled else 'выключен 📴'}")

def search_duckduckgo(query):
    if not query or not query.strip():
        return "❌ Введи запрос для поиска!"
    url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"🔍 Ищу в DuckDuckGo: {query}\nОткрываю браузер..."

def search_handler(user_text):
    if not internet_enabled:
        text = user_text.lower()
        is_search = (
            text.startswith("/search ") or text.startswith("/искать ") or
            any(text.startswith(t) for t in ["найди ", "поищи ", "загугли ", "найти ", "поиск "])
        )
        if is_search:
            return "📴 Интернет выключен! Нажми кнопку 'Инет' чтобы включить."
        else:
            return None
    text = user_text.lower()
    if text.startswith("/search ") or text.startswith("/искать "):
        query = user_text.replace("/search ", "").replace("/искать ", "").strip()
        return search_duckduckgo(query)
    for trigger in ["найди ", "поищи ", "загугли ", "найти ", "поиск "]:
        if text.startswith(trigger):
            return search_duckduckgo(user_text[len(trigger):].strip())
    return None

# ============================================
# ----------- ОБРАБОТКА КОМАНД ---------------
# ============================================

def handle_commands(text):
    t = text.lower()
    if t.startswith("/name "):
        return save_name(text[6:].strip())
    if t == "/clear":
        message_history.clear()
        return "История очищена 🧹"
    if t == "/about":
        return "MYXA AI — оффлайн интеллектуальная система. Версия ULTRA+."
    if t == "/myname":
        return f"Тебя зовут {user_name}!" if user_name else "Ты ещё не сказал своё имя."
    if t == "/help":
        return "📘 /name, /myname, /clear, /about, /search, игры: камень/ножницы/бумага, монетка, угадай"
    if t == "/forget":
        message_history.clear()
        return "🧠 Контекст очищен."
    if t == "/context":
        ctx = f"📝 Последнее действие: {last_user_action or 'нет'}\n"
        ctx += f"💬 Мой последний ответ: {last_bot_response or 'нет'}"
        return ctx
    return None

# ============================================
# ----------- БЕСПЛАТНАЯ НЕЙРОСЕТЬ (SAIGA) ----
# ============================================

def ask_free_ai(prompt):
    """Бесплатная русская нейросеть Saiga (Hugging Face)"""
    try:
        url = "https://api-inference.huggingface.co/models/IlyaGusev/saiga_llama3_8b"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
        response = requests.post(url, json=payload, timeout=45)
        if response.status_code == 200:
            return response.json()[0]['generated_text']
        else:
            return f"❌ Ошибка API: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)[:50]}"

# ============================================
# ----------- ГЛАВНЫЙ МОЗГ -------------------
# ============================================

def process_ai(text):
    global user_name, message_count, secret_number, current_ai_model

    # === ЕСЛИ ВЫБРАНА НЕЙРОСЕТЬ ===
    if current_ai_model == "neural":
        return ask_free_ai(text)

    # === СТАНДАРТНЫЙ MYXA ===
    message_count += 1
    clean = fix_text(text)
    remember(clean)
    global last_user_action, context_data
    if any(w in clean for w in ["камень", "ножницы", "бумага"]):
        last_user_action = "играли в КНБ"
    elif "таблица" in clean:
        last_user_action = "считали таблицу умножения"
        nums = re.findall(r"\d+", clean)
        if nums:
            context_data["last_table"] = int(nums[0])
    elif any(w in clean for w in ["погода", "дождь", "солнце"]):
        last_user_action = "говорили о погоде"
    elif any(w in clean for w in ["как дела", "настроение"]):
        last_user_action = "обсуждали настроение"
    elif "игра угадай" in clean:
        last_user_action = "угадывали число"
    elif "анекдот" in clean:
        last_user_action = "рассказывали анекдот"

    search_result = search_handler(clean)
    if search_result:
        return search_result

    cmd = handle_commands(clean)
    if cmd:
        return cmd

    if any(w in clean for w in ["меня зовут", "зови меня", "моё имя", "мое имя"]):
        name = clean.replace("меня зовут", "").replace("зови меня", "").replace("моё имя", "").replace("мое имя", "").strip()
        if len(name) > 0:
            return save_name(name)

    emotion = detect_emotion(clean)
    emo_reply = emotion_reply(emotion)

    if clean == "привет":
        answers = ["Привет!", "Здравствуй!", "Рад тебя видеть!", "Привет! Чем могу помочь?"]
        return build_reply(random.choice(answers), emo_reply)
    elif "ку" in clean:
        return build_reply("Ку! С чем помочь?", emo_reply)
    elif clean == "хай":
        return build_reply("Хай! С чем помочь?", emo_reply)
    elif clean == "здравствуй":
        return build_reply("Здравствуй! С чем помочь?", emo_reply)
    elif clean == "здарова":
        return build_reply("Здарова! С чем помочь?", emo_reply)

    if any(w in clean for w in ["что я говорил", "что я сказал", "помнишь", "напомни"]):
        if message_history:
            last_user_msg = ""
            for msg in reversed(message_history):
                if not msg.startswith("MYXA AI:"):
                    last_user_msg = msg
                    break
            if last_user_msg:
                return build_reply(f"Ты говорил: «{last_user_msg}»", emo_reply)
        return build_reply("Я пока ничего не помню из нашего разговора.", emo_reply)

    if clean in ["повтори", "ещё", "еще"]:
        if last_bot_response:
            return build_reply(last_bot_response, emo_reply)
        else:
            return build_reply("А что повторить? Мы пока мало общались.", emo_reply)

    if clean == "что мы делали":
        if last_user_action:
            return build_reply(f"Мы с тобой {last_user_action}. Продолжим?", emo_reply)
        else:
            return build_reply("Пока ничего особенного не делали. Может, поиграем?", emo_reply)

    elif any(w in clean for w in ["сколько времени", "который час", "время"]):
        now = datetime.now()
        return f"Сейчас времени: {now.strftime('%H:%M')}"
    elif "какие ты знаешь команду" in clean or clean in ["помощь", "помогите"]:
        return "Привет, Как дела, Сколько времени, Кто ты, ты бот, Сколько сообщений, пока, все норм, настроение"
    elif "сколько сообщений" in clean:
        return f"Мы написали {message_count} сообщений"
    elif "как дела" in clean or "как ты" in clean or "как жизнь" in clean:
        return "У меня все хорошо! А как у тебя дела?"
    elif any(w in clean for w in ["все норм", "все нормально", "у меня все хорошо"]):
        return "Рад что у тебя тоже все хорошо! А как у тебя настроение?"
    elif any(w in clean for w in ["хорошее настроение", "настроение хорошее", "настроение норм"]):
        return "Хорошо что ты сегодня на позитиве! Что будем делать?"
    elif any(w in clean for w in ["кто ты", "что ты", "ты бот"]):
        return "Я твой ИИ MYXA AI. Могу болтать и с чем-нибудь помочь"
    elif "что ты можешь" in clean:
        return "Я могу определить время, сколько сообщений, таблицу умножения, и могу поболтать"
    elif "таблица" in clean:
        nums = re.findall(r"\d+", clean)
        if nums:
            n = int(nums[0])
            out = [f"Таблица умножения на {n}:"]
            for i in range(1, 11):
                out.append(f"{n} × {i} = {n*i}")
            return "\n".join(out)
        else:
            return "Напиши число, например: Таблица 5"
    elif clean in ["пока", "бай", "до свидания", "увидимся"]:
        answers = ["До свидания!", "Бай! Заходи ещё!", "Увидимся!", "Пока!"]
        return random.choice(answers)
    elif "не работает" in clean:
        return "Пиши точные команды. Напиши 'помощь' чтобы увидеть список!"
    elif any(w in clean for w in ["а теперь понял", "а теперь поняла"]):
        return "Рад что ты все понял! С чего начнем?"
    elif clean == "что нового":
        return "Больше функционала, дальше лучше :)"

    if clean in ["камень", "ножницы", "бумага"]:
        return game_rps(clean)
    if "игра монетка" in clean or "подбрось монетку" in clean:
        play_coin_gui()
        return "🪙 Открываю монетку..."
    if "игра угадай" in clean or "угадай число" in clean:
        return game_guess_start()
    if secret_number is not None:
        nums = re.findall(r"\d+", clean)
        if nums:
            return game_guess_check(int(nums[0]))

    if "сброс счётчика" in clean:
        message_count = 0
        return "🧹 Счётчик обнулён!"

    if not user_name:
        return build_reply("Бро, а как тебя зовут? 😊", emo_reply)

    if clean == "спасибо":
        return f"Всегда пожалуйста, {user_name}! 😊"
    if "анекдот" in clean:
        jokes = ["Колобок повесился.", "Идёт медведь по лесу, видит — машина горит. Сел в неё и сгорел."]
        return random.choice(jokes)

    if any(char.isdigit() for char in clean):
        return "Напиши число с командой, например: Таблица 5"

    return build_reply(f"{user_name}, я тебя услышал. Напиши понятнее или спроси 'помощь' 😊", emo_reply)

# ============================================
# ----------- ОТПРАВКА СООБЩЕНИЙ -------------
# ============================================

def send_message():
    user_text = entry_box.get().strip()
    if not user_text:
        return
    entry_box.delete(0, tk.END)
    add_message("Ты", user_text)
    threading.Thread(target=ai_answer_thread, args=(user_text,)).start()

def ai_answer_thread(text):
    time.sleep(0.2)
    response = process_ai(text)
    global last_bot_response
    last_bot_response = response
    add_message(APP_NAME, response)

# ============================================
# ----------- ФУНКЦИИ КНОПОК -----------------
# ============================================

def next_theme():
    global current_theme
    themes_list = list(THEMES.keys())
    idx = themes_list.index(current_theme)
    current_theme = themes_list[(idx + 1) % len(themes_list)]
    save_settings()
    apply_theme()
    add_message("MYXA AI", f"🎨 Тема: {current_theme}")

def clear_current_chat():
    global chat_history
    if current_chat in chat_history:
        chat_history[current_chat] = []
    save_history()
    chat_box.config(state=tk.NORMAL)
    chat_box.delete("1.0", tk.END)
    chat_box.config(state=tk.DISABLED)
    entry_box.delete(0, tk.END)
    add_message("MYXA AI", "🧹 Чат очищен")

def load_current_chat():
    chat_box.config(state=tk.NORMAL)
    chat_box.delete("1.0", tk.END)
    if current_chat in chat_history:
        for msg in chat_history[current_chat]:
            chat_box.insert(tk.END, f"{msg['sender']}: {msg['text']}\n\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)

def open_help():
    help_window = tk.Toplevel(root)
    help_window.title("Помощь MYXA AI")
    help_window.geometry("400x500")
    help_text = (
        "📘 MYXA AI — СПРАВКА\n\n"
        "💬 КОМАНДЫ:\n/name <имя>, /myname, /clear, /help\n\n"
        "🔍 ПОИСК:\n/search <запрос>, найди <запрос>\n\n"
        "🎮 ИГРЫ:\nкамень/ножницы/бумага, монетка, угадай число\n\n"
        "📊 СЧЁТЧИК: сколько сообщений, сброс счётчика\n\n"
        "📚 ШКОЛА: таблица 5\n\n"
        "🤖 Нейросеть: кнопка «🧠 Нейро» — бесплатная Saiga"
    )
    tk.Label(help_window, text=help_text, justify="left", padx=15, pady=15, font=("Arial", 11)).pack(expand=True, fill="both")

def search_dialog():
    query = simpledialog.askstring("🔍 Поиск в DuckDuckGo", "Введите запрос:")
    if query and query.strip():
        url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        add_message("MYXA AI", f"🔍 Ищу: {query}\nОткрываю браузер...")
    else:
        add_message("MYXA AI", "❌ Поиск отменён (пустой запрос)")

def show_games_help():
    games_win = tk.Toplevel(root)
    games_win.title("🎮 Игры")
    games_win.geometry("350x300")
    text = (
        "🎮 ДОСТУПНЫЕ ИГРЫ:\n\n"
        "1️⃣ Монетка\n   Напиши: игра монетка\n\n"
        "2️⃣ Угадай число\n   Напиши: игра угадай\n\n"
        "3️⃣ Камень-ножницы-бумага\n   Напиши: камень / ножницы / бумага"
    )
    tk.Label(games_win, text=text, font=("Arial", 12), justify="left", padx=20, pady=20).pack()

def play_rps_gui():
    rps_win = tk.Toplevel(root)
    rps_win.title("🎮 Камень-ножницы-бумага")
    rps_win.geometry("350x250")
    rps_win.resizable(False, False)
    result_label = tk.Label(rps_win, text="Выбери вариант:", font=("Arial", 14))
    result_label.pack(pady=15)
    def play(choice):
        options = ["камень", "ножницы", "бумага"]
        bot = random.choice(options)
        if choice == bot:
            result = "Ничья!"
        elif (choice == "камень" and bot == "ножницы") or \
             (choice == "ножницы" and bot == "бумага") or \
             (choice == "бумага" and bot == "камень"):
            result = "Ты выиграл! 🔥"
        else:
            result = "Ты проиграл 😅"
        result_label.config(text=f"Ты: {choice} | Бот: {bot}\n{result}")
        add_message("MYXA AI", f"🎮 КНБ: Ты — {choice}, Бот — {bot}. {result}")
    btn_frame = tk.Frame(rps_win)
    btn_frame.pack(pady=20)
    tk.Button(btn_frame, text="🪨 Камень", width=10, command=lambda: play("камень")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✂️ Ножницы", width=10, command=lambda: play("ножницы")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="📄 Бумага", width=10, command=lambda: play("бумага")).pack(side="left", padx=5)
    tk.Button(rps_win, text="Закрыть", command=rps_win.destroy, width=15).pack(pady=10)

def open_chats_window():
    CHATS_FILE = "myxa_chats.json"
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            chats = json.load(f)
    else:
        chats = {"Главный чат": []}
    def save_chats():
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
    win = tk.Toplevel(root)
    win.title("📁 Чаты")
    win.geometry("300x400")
    listbox = tk.Listbox(win, font=("Arial", 12))
    listbox.pack(fill="both", expand=True, padx=10, pady=10)
    for chat in chats:
        listbox.insert(tk.END, chat)
    def new_chat():
        name = simpledialog.askstring("Новый чат", "Название:")
        if name and name.strip():
            name = name.strip()
            if name in chats:
                messagebox.showwarning("Ошибка", "Такой чат уже есть!")
            else:
                chats[name] = []
                save_chats()
                listbox.insert(tk.END, name)
                add_message("MYXA AI", f"✅ Чат '{name}' создан")
    def open_chat():
        sel = listbox.curselection()
        if sel:
            name = listbox.get(sel[0])
            global current_chat, chat_history
            current_chat = name
            chat_history = chats
            load_current_chat()
            add_message("MYXA AI", f"📂 Переключено: {name}")
            win.destroy()
    def delete_chat():
        sel = listbox.curselection()
        if sel:
            name = listbox.get(sel[0])
            if len(chats) <= 1:
                messagebox.showwarning("Ошибка", "Нельзя удалить единственный чат!")
                return
            if messagebox.askyesno("Удалить", f"Удалить чат '{name}'?"):
                del chats[name]
                save_chats()
                listbox.delete(sel[0])
                add_message("MYXA AI", f"🗑 Чат '{name}' удалён")
                global current_chat
                if current_chat == name:
                    current_chat = list(chats.keys())[0]
                    chat_history = chats
                    load_current_chat()
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="➕ Новый", command=new_chat, width=10).pack(side="left", padx=3)
    tk.Button(btn_frame, text="📂 Открыть", command=open_chat, width=10).pack(side="left", padx=3)
    tk.Button(btn_frame, text="🗑 Удалить", command=delete_chat, width=10).pack(side="left", padx=3)
    tk.Button(win, text="Закрыть", command=win.destroy, width=20).pack(pady=5)

def open_gdz():
    webbrowser.open("https://gdz-raketa.ru")
    add_message("MYXA AI", "📚 Открываю Гдз-Ракета в браузере. Рекомендую этот!")

def show_stats():
    stats_win = tk.Toplevel(root)
    stats_win.title("📊 Статистика")
    stats_win.geometry("300x200")
    stats_win.resizable(False, False)
    tk.Label(stats_win, text="📊 СТАТИСТИКА", font=("Arial", 14, "bold")).pack(pady=15)
    tk.Label(stats_win, text=f"Всего сообщений: {message_count}", font=("Arial", 12)).pack(pady=10)
    if user_name:
        tk.Label(stats_win, text=f"Пользователь: {user_name}", font=("Arial", 12)).pack(pady=5)
    else:
        tk.Label(stats_win, text="Пользователь: не указан", font=("Arial", 12)).pack(pady=5)
    tk.Label(stats_win, text=f"Текущий чат: {current_chat}", font=("Arial", 12)).pack(pady=5)
    tk.Label(stats_win, text=f"Тема: {current_theme}", font=("Arial", 12)).pack(pady=5)
    tk.Button(stats_win, text="Закрыть", command=stats_win.destroy, width=15).pack(pady=15)

def show_time_window():
    """Окно с текущим временем и датой (живые часы)"""
    time_win = tk.Toplevel(root)
    time_win.title("⏰ Время и дата")
    time_win.geometry("350x200")
    time_win.resizable(False, False)
    
    now = datetime.now()
    
    tk.Label(time_win, text="📅 СЕГОДНЯ", font=("Arial", 12, "bold")).pack(pady=10)
    date_label = tk.Label(time_win, text=now.strftime("%d.%m.%Y"), font=("Arial", 14))
    date_label.pack()
    weekday_label = tk.Label(time_win, text=now.strftime("%A"), font=("Arial", 11))
    weekday_label.pack()
    
    tk.Label(time_win, text="⏰ ТЕКУЩЕЕ ВРЕМЯ", font=("Arial", 12, "bold")).pack(pady=10)
    time_label = tk.Label(time_win, text=now.strftime("%H:%M:%S"), font=("Arial", 18, "bold"), fg="blue")
    time_label.pack()
    
    def update_time():
        new_now = datetime.now()
        time_label.config(text=new_now.strftime("%H:%M:%S"))
        date_label.config(text=new_now.strftime("%d.%m.%Y"))
        weekday_label.config(text=new_now.strftime("%A"))
        time_win.after(1000, update_time)
    
    update_time()
    tk.Button(time_win, text="Закрыть", command=time_win.destroy, width=15).pack(pady=15)

def switch_to_neural():
    global current_ai_model
    current_ai_model = "neural"
    add_message("MYXA AI", "🧠 Режим нейросети (Saiga) активирован. Все сообщения будут обрабатываться ИИ.")

def switch_to_myxa():
    global current_ai_model
    current_ai_model = "myxa"
    add_message("MYXA AI", "🤖 Режим MYXA активирован. Стандартная логика.")

# ============================================
# ----------- КНОПКИ -------------------------
# ============================================

send_btn = tk.Button(button_frame, text="➤ Отправить", width=12, command=send_message)
send_btn.pack(side="right", padx=2, pady=3)
bottom_buttons.append(send_btn)

make_button("Help", open_help)
make_button("Поиск", search_dialog)
make_button("Темы", next_theme)
make_button("ГДЗ", open_gdz)
make_button("Стат", show_stats)
make_button("Время", show_time_window)
make_button("Очистить", clear_current_chat)
make_button("Чаты", open_chats_window)
make_button("Игры", show_games_help)
make_button("КНБ", play_rps_gui)
make_button("Монетка", play_coin_gui)
make_button("🧠 Нейро", switch_to_neural)
make_button("🤖 MYXA", switch_to_myxa)

# ============================================
# ----------- ПРИВЯЗКИ И ЗАПУСК ---------------
# ============================================

entry_box.bind("<Return>", lambda event: send_message())

load_history()
apply_theme()
load_current_chat()

root.mainloop()