import random
import sqlite3
from datetime import datetime, timedelta
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
BOT_TOKEN = "8744175076:AAGn4vemK0oylty9XE68EVhtvSjBJG9bxGY"
bot = telebot.TeleBot(BOT_TOKEN)
def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, description TEXT DEFAULT 'Садовод-новичок', created_at TEXT, plants_count INTEGER DEFAULT 0, points INTEGER DEFAULT 0, fertilizers INTEGER DEFAULT 0, next_grow TEXT)")
    conn.commit()
    return conn
conn = init_db()
cursor = conn.cursor()
PLANTS_BY_RARITY = {"⚪ Обычная ⚪": ["🌱 Маленькое Деревце 🌱", "🌴 Яблоня 🌴", "🌲 Ёлка 🌲"], "🟢 Редкая 🟢": ["🌳 Большое Деревце 🌳", "🔥 Огненное Дерево 🔥", "🌵 Кактус 🌵", "🎄 Праздничная Ёлка 🎄"], "🔵 Супер Редкая 🔵": ["☘️ Обычный Клевер ☘️"], "🟣 Эпическая 🟣": ["🍀 Четырёхлистный клевер 🍀", "🌴 Персиковое Дерево 🌴", "🌳 Секвойядендрон Гигантский 🌳"]}
RARITY_POINTS_CONFIG = {"⚪ Обычная ⚪": {"min": 1, "max": 5}, "🟢 Редкая 🟢": {"min": 10, "max": 20}, "🔵 Супер Редкая 🔵": {"min": 21, "max": 35}, "🟣 Эпическая 🟣": {"min": 30, "max": 50}}
def db_get_or_create_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)", (user_id, username or "Без ника", now_str))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    return user
def calculate_time_spent(created_at_str):
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - created_at
    return delta.days // 365, (delta.days % 365) // 30, ((delta.days % 365) % 30) // 7
def db_get_top(order_by, limit=10, offset=0):
    cursor.execute(f"SELECT username, {order_by} FROM users ORDER BY {order_by} DESC LIMIT ? OFFSET ?", (limit, offset))
    return cursor.fetchall()
@bot.message_handler(func=lambda msg: True)
def handle_messages(message):
    text = message.text.lower() if message.text else ""
    user_id = message.from_user.id
    username = message.from_user.first_name
    user = db_get_or_create_user(user_id, username)
    if text in ["растун", "/rastun"]:
        if user[7] and datetime.now() < datetime.strptime(user[7], "%Y-%m-%d %H:%M:%S"):
            time_left = datetime.strptime(user[7], "%Y-%m-%d %H:%M:%S") - datetime.now()
            bot.send_message(message.chat.id, f"⏳ Ваше растение еще растет! Через {int(time_left.total_seconds() // 60)} мин.")
            return
        chosen_rarity = random.choices(list(PLANTS_BY_RARITY.keys()), weights=[0.55, 0.25, 0.15, 0.05], k=1)[0]
        chosen_plant = random.choice(PLANTS_BY_RARITY[chosen_rarity])
        points = random.randint(RARITY_POINTS_CONFIG[chosen_rarity]["min"], RARITY_POINTS_CONFIG[chosen_rarity]["max"])
        new_next_grow = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET plants_count = plants_count + 1, points = points + ?, next_grow = ? WHERE user_id = ?", (points, new_next_grow, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"🌱 **Вы вырастили Растение Досика** 🌱\n\n🪴 **Вы вырастили:** {chosen_plant}\n💥 **Редкость:** {chosen_rarity}\n🌀 **Очки:** +{points}\n\n🌳 Следующий раз через час", parse_mode="Markdown")
    elif text in ["удобрить", "/fertilize"]:
        if not user[7] or datetime.now() >= datetime.strptime(user[7], "%Y-%m-%d %H:%M:%S"):
            bot.send_message(message.chat.id, "❌ Грядка пуста, запустите Растун!")
            return
        if user[6] <= 0:
            bot.send_message(message.chat.id, "❌ У вас нет удобрений! Купите в ДМагазин")
            return
        next_grow = datetime.strptime(user[7], "%Y-%m-%d %H:%M:%S")
        if (next_grow - datetime.now()).total_seconds() <= 1800:
            bot.send_message(message.chat.id, "❌ Удобрение уже было применено на это растение!")
            return
        acc_grow = (next_grow - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET fertilizers = fertilizers - 1, next_grow = ? WHERE user_id = ?", (acc_grow, user_id))
        conn.commit()
        rem = int((datetime.strptime(acc_grow, "%Y-%m-%d %H:%M:%S") - datetime.now()).total_seconds() // 60)
        bot.send_message(message.chat.id, f"🍁 **Удобрено!** Время сокращено на 50%.\n⏳ Осталось: {rem} мин.", parse_mode="Markdown")
    elif text in ["дпрофиль", "/dpro"]:
        y, m, w = calculate_time_spent(user[3])
        bot.send_message(message.chat.id, f"👨‍🌾 **САДОВОД** {user[1]} 👨‍🌾\n\n📃 Описание: {user[2]}\nВремя: Год {y}, Месяц {m}, Недели {w}\n\n🌿 Растений: {user[4]}\n🪙 Очков: {user[5]}\n🍂 Удобрений: {user[6]}", parse_mode="Markdown")
    elif text.startswith("+минфа") or text.startswith("/pinfo"):
        new_desc = message.text[7 if text.startswith("+минфа") else 6:].strip()
        if not new_desc or len(new_desc) > 40: bot.send_message(message.chat.id, "❌ Текст от 1 до 40 символов!"); return
        cursor.execute("UPDATE users SET description = ? WHERE user_id = ?", (new_desc, user_id)); conn.commit()
        bot.send_message(message.chat.id, f"✅ Описание установлено:\n{new_desc}")
    elif text in ["дмагазин", "/dshop"]:
        kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("5 Удобрений — 25 очков", callback_data="buy_5_25"), InlineKeyboardButton("10 Удобрений — 30 очков", callback_data="buy_10_30"), InlineKeyboardButton("25 Удобрений — 60 очков", callback_data="buy_25_60"))
        bot.send_message(message.chat.id, "🛍 **Магазин Gardener Dosik** 🛍\n\n🍂 5 Удобрений — 25 очков\n🍂 10 Удобрений — 30 очков\n🍂 25 Удобрений — 60 очков", reply_markup=kb, parse_mode="Markdown")
    elif text in ["отоп", "/otom"] or text in ["ртоп", "/rtop"]:
        col = "points" if text in ["отоп", "/otom"] else "plants_count"
        sfx = "очков" if col == "points" else "шт."
        u = db_get_top(col, 10, 0)
        res = "\\n".join(f"{idx}. **{r[0]}** — {r[1]} {sfx}" for idx, r in enumerate(u, 1))
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Показать еще 10", callback_data=f"top_{col}_10"))
        bot.send_message(message.chat.id, f"🏆 **Топ 10** 🏆\n\n{res}", reply_markup=kb, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = db_get_or_create_user(user_id, call.from_user.first_name)
    if call.data.startswith("buy_"):
        cost, items = (25, 5) if call.data == "buy_5_25" else (30, 10) if call.data == "buy_10_30" else (60, 25)
        if user[5] < cost: bot.answer_callback_query(call.id, "❌ Недостаточно очков!", show_alert=True); return
        cursor.execute("UPDATE users SET points = points - ?, fertilizers = fertilizers + ? WHERE user_id = ?", (cost, items, user_id)); conn.commit()
        bot.answer_callback_query(call.id, "✅ Успешно куплено!", show_alert=True)
    elif call.data.startswith("top_"):
        _, col, off = call.data.split("_"); off = int(off); u = db_get_top(col, 10, off)
        if not u: bot.answer_callback_query(call.id, "Больше нет игроков!", show_alert=True); return
        all_u = db_get_top(col, off + 10, 0)
        res = "\\n".join(f"{idx}. **{r[0]}** — {r[1]}" for idx, r in enumerate(all_u, 1))
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Показать еще 10", callback_data=f"top_{col}_{off+10}"))
        bot.edit_message_text(f"🏆 **Топ** 🏆\n\n{res}", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
print("⚡ БОТ-САДОВОД ОБНОВЛЕН С КОМАНДОЙ УДОБРИТЬ!")
bot.infinity_polling()
