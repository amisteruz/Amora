import os
import random
import subprocess
import time

import telebot
from telebot import types

from questions import QUESTIONS

# ============ SOZLAMALAR ============
BOT_TOKEN = "9293087369:AAGDSrMn0Rx9r07XLceljmRrsrH1HtUrwbs"
ADMIN_ID  = 5062136446

bot = telebot.TeleBot(BOT_TOKEN)
active_games = {}


# ============ AVTOMATIK ZAXIRA ============
def auto_backup():
    zip_name = "amora_ideal.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)
    try:
        subprocess.run(
            ["zip", "-r", zip_name, ".", "-x", zip_name, "-x", "__pycache__/*"],
            check=True, capture_output=True
        )
    except Exception as e:
        print("ZIP xato:", e)
        return
    try:
        with open(zip_name, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="Avtomatik zaxira nusxa")
        print("ZIP yuborildi:", ADMIN_ID)
    except Exception as e:
        print("Yuborish xato:", e)


# ============ HANDLERLAR ============
@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.send_message(
        m.chat.id,
        "<b>Assalomu alaykum!</b>\n\n"
        "AmoraNet — bilimingizni sinash platformasi.\n\n"
        "O'yinni boshlash: /startgame",
        parse_mode='HTML'
    )


@bot.message_handler(commands=['startgame'])
def start_game(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Umumiy bilim", callback_data="topic_umumiy"),
        types.InlineKeyboardButton("Musiqa", callback_data="topic_musiqa")
    )
    bot.send_message(m.chat.id, "<b>Mavzuni tanlang:</b>", reply_markup=kb, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data.startswith('topic_'))
def start_duel(c):
    topic = c.data.split('_')[1]
    chat = c.message.chat.id
    qs = random.sample(QUESTIONS[topic], min(3, len(QUESTIONS[topic])))
    active_games[chat] = {'questions': qs, 'current_q': 0, 'score': 0}
    bot.edit_message_text("O'yin boshlanmoqda...", chat, c.message.message_id)
    time.sleep(1)
    ask_question(chat)


def ask_question(chat):
    if chat not in active_games:
        return
    g = active_games[chat]
    i = g['current_q']
    if i >= len(g['questions']):
        bot.send_message(
            chat,
            f"<b>O'yin tugadi!</b>\n\nNatija: <b>{g['score']} / {len(g['questions'])}</b> ball.\n\n"
            f"Yana o'ynash: /startgame",
            parse_mode='HTML'
        )
        del active_games[chat]
        return
    q = g['questions'][i]
    kb = types.InlineKeyboardMarkup()
    for idx, opt in enumerate(q['options']):
        kb.add(types.InlineKeyboardButton(opt, callback_data=f"ans_{idx}"))
    bot.send_message(
        chat,
        f"<b>Savol {i+1}/{len(g['questions'])}</b>\n\n{q['q']}",
        reply_markup=kb, parse_mode='HTML'
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('ans_'))
def handle_answer(c):
    chat = c.message.chat.id
    if chat not in active_games:
        return
    g = active_games[chat]
    i = g['current_q']
    if int(c.data.split('_')[1]) == g['questions'][i]['answer']:
        g['score'] += 1
        g['current_q'] += 1
        bot.answer_callback_query(c.id, "To'g'ri! +1 ball")
        time.sleep(1)
        ask_question(chat)
    else:
        bot.answer_callback_query(c.id, "Xato!", show_alert=True)



import threading
import datetime

def _run(cmd):
    """Buyruqni bajaradi. Xato bo'lsa matnini qaytaradi, aks holda None."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return (r.stderr or r.stdout).strip()
    return None

def auto_github_push():
    """Har soatda FAQAT o'zgarish bo'lsa GitHub'ga yuklaydi."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)

    while True:
        try:
            # 1) O'zgarish bormi?
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True
            ).stdout.strip()

            if not status:
                print("ℹ️  O'zgarish yo'q, yuklash shart emas")
            else:
                # 2) Stage
                err = _run(["git", "add", "-A"])
                if err:
                    print("❌ git add xato:", err); time.sleep(3600); continue

                # 3) Commit
                msg = "Avtomatik yangilanish: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                err = _run(["git", "commit", "-m", msg])
                if err:
                    print("❌ git commit xato:", err); time.sleep(3600); continue

                # 4) Push
                err = _run(["git", "push", "origin", "main"])
                if err:
                    print("❌ git push xato:", err)
                else:
                    print("✅ GitHub'ga yuklandi:", msg)

        except Exception as e:
            print("❌ auto_github_push xato:", e)

        time.sleep(3600)

# ============ ISHGA TUSHIRISH ============
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    threading.Thread(target=auto_github_push, daemon=True).start()
    auto_backup()
    bot.polling(none_stop=True)
