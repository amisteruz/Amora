import telebot
from telebot import types
import random
import time
import os
import threading
import subprocess
import datetime
from questions import QUESTIONS

# ============ SOZLAMALAR ============
BOT_TOKEN = "9293087369:AAGDSrMn0Rx9r07XLceljmRrsrH1HtUrwbs"
ADMIN_ID  = 5062136446

bot = telebot.TeleBot(BOT_TOKEN)

active_games = {}
active_arenas = {}

# ============ AVTOMATIK ZAXIRA ============
def auto_backup():
    zip_name = "amora_ideal.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)
    try:
        subprocess.run(
            ["zip", "-r", zip_name, ".", "-x", zip_name, "-x", "__pycache__/*", "-x", "*.log"],
            check=True, capture_output=True
        )
        with open(zip_name, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📦 Avtomatik zaxira nusxa")
        print("ZIP yuborildi:", ADMIN_ID)
    except Exception as e:
        print("Zaxira xatosi:", e)

# ============ AVTOMATIK GITHUB PUSH ============
def auto_github_push():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)
    time.sleep(60)

    while True:
        try:
            # Faqat kod fayllarini tekshiramiz
            status = subprocess.run(["git", "status", "--porcelain", "*.py"], capture_output=True, text=True).stdout.strip()
            if not status:
                print("ℹ️ Kodda o'zgarish yo'q")
            else:
                a = subprocess.run(["git", "add", "*.py"], capture_output=True, text=True)
                if a.returncode == 0:
                    msg = "Avtomatik: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    c = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
                    if c.returncode == 0 or "nothing to commit" not in (c.stdout + c.stderr).lower():
                        p = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
                        if p.returncode == 0:
                            print("✅ GitHub'ga yuklandi:", msg)
        except Exception as e:
            print("Git xatosi:", e)
        time.sleep(3600)

# ============ 1. QUIZ ============
@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.send_message(m.chat.id, "👋 <b>Assalomu alaykum!</b>\n\n🎮 Quiz: /startgame\n🏟️ Arena: /arena", parse_mode='HTML')

@bot.message_handler(commands=['startgame'])
def start_game(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🌍 Umumiy", callback_data="topic_umumiy"), types.InlineKeyboardButton("🎵 Musiqa", callback_data="topic_musiqa"))
    bot.send_message(m.chat.id, "🎮 <b>Mavzuni tanlang:</b>", reply_markup=kb, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith('topic_'))
def start_duel(c):
    topic = c.data.split('_')[1]
    chat = c.message.chat.id
    qs = random.sample(QUESTIONS[topic], min(3, len(QUESTIONS[topic])))
    active_games[chat] = {'questions': qs, 'current_q': 0, 'score': 0}
    bot.edit_message_text("⏳ O'yin boshlanmoqda...", chat, c.message.message_id)
    time.sleep(1)
    ask_question(chat)

def ask_question(chat):
    if chat not in active_games: return
    g = active_games[chat]
    i = g['current_q']
    if i >= len(g['questions']):
        bot.send_message(chat, f"🏆 <b>Natija: {g['score']} / {len(g['questions'])}</b> ball.\n\n/startgame", parse_mode='HTML')
        del active_games[chat]
        return
    q = g['questions'][i]
    kb = types.InlineKeyboardMarkup()
    for idx, opt in enumerate(q['options']):
        kb.add(types.InlineKeyboardButton(opt, callback_data=f"ans_{idx}"))
    bot.send_message(chat, f"❓ <b>{i+1}-savol:</b>\n\n{q['q']}", reply_markup=kb, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith('ans_'))
def handle_answer(c):
    chat = c.message.chat.id
    if chat not in active_games: return
    g = active_games[chat]
    i = g['current_q']
    if int(c.data.split('_')[1]) == g['questions'][i]['answer']:
        g['score'] += 1
        g['current_q'] += 1
        bot.answer_callback_query(c.id, "✅ To'g'ri! +1 ball")
        time.sleep(1)
        ask_question(chat)
    else:
        bot.answer_callback_query(c.id, "❌ Xato!", show_alert=True)

# ============ 2. ARENA ============
@bot.message_handler(commands=['arena'])
def start_arena(m):
    chat_id = m.chat.id
    if chat_id in active_arenas:
        bot.reply_to(m, "⚠️ Arena ketmoqda! /natija")
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("10 daqiqa", callback_data="arena_time_10"), types.InlineKeyboardButton("30 daqiqa", callback_data="arena_time_30"), types.InlineKeyboardButton("60 daqiqa", callback_data="arena_time_60"))
    bot.send_message(chat_id, "🏟️ <b>Amora Arena!</b>\n⏳ Vaqtni tanlang:", reply_markup=kb, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith('arena_time_'))
def start_arena_timer(c):
    chat_id = c.message.chat.id
    minutes = int(c.data.split('_')[2])
    active_arenas[chat_id] = {'votes': {}, 'end_time': time.time() + (minutes * 60), 'voted_users': set()}
    bot.edit_message_text(f"🔥 <b>Raqobat boshlandi!</b>\n⏳ Vaqt: {minutes} daqiqa\n\nNomzodingizni guruhga yozing!", chat_id, c.message.message_id, parse_mode='HTML')
    threading.Thread(target=arena_timer_task, args=(chat_id, minutes), daemon=True).start()

def arena_timer_task(chat_id, minutes):
    time.sleep(minutes * 60)
    if chat_id in active_arenas:
        announce_arena_winner(chat_id)

@bot.message_handler(func=lambda m: m.chat.id in active_arenas and m.text and not m.text.startswith('/'))
def collect_arena_votes(m):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if user_id in active_arenas[chat_id]['voted_users']: return
    candidate = m.text.strip()
    if not candidate: return
    active_arenas[chat_id]['voted_users'].add(user_id)
    active_arenas[chat_id]['votes'][candidate] = active_arenas[chat_id]['votes'].get(candidate, 0) + 1
    bot.reply_to(m, f"✅ Qabul qilindi: <b>{candidate}</b>", parse_mode='HTML')

@bot.message_handler(commands=['natija'])
def show_arena_results(m):
    chat_id = m.chat.id
    if chat_id not in active_arenas:
        bot.reply_to(m, "Arena yo'q.")
        return
    votes = active_arenas[chat_id]['votes']
    remaining = int(active_arenas[chat_id]['end_time'] - time.time())
    mins, secs = divmod(max(0, remaining), 60)
    text = f"📊 <b>Natijalar:</b> ({mins} daq {secs} son)\n"
    if not votes: text += "Ovoz yo'q."
    else:
        for i, (name, count) in enumerate(sorted(votes.items(), key=lambda x: x[1], reverse=True), 1):
            text += f"{i}. {name} — {count} ovoz\n"
    bot.send_message(chat_id, text, parse_mode='HTML')

def announce_arena_winner(chat_id):
    votes = active_arenas[chat_id]['votes']
    if not votes:
        bot.send_message(chat_id, "🏁 Vaqt tugadi! Ovoz yo'q.")
    else:
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        res = "🏁 <b>Yakuniy natijalar:</b>\n"
        for i, (name, count) in enumerate(sorted_votes, 1):
            res += f"{i}. {name} — {count} ovoz\n"
        res += f"\n🎉 <b>G'olib: {sorted_votes[0][0]}!</b>"
        bot.send_message(chat_id, res, parse_mode='HTML')
    del active_arenas[chat_id]

# ============ ISHGA TUSHIRISH ============
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    # Zaxirani orqa fonda ishga tushiramiz (bot qotib qolmasligi uchun)
    threading.Thread(target=auto_backup, daemon=True).start()
    # GitHub'ga yuklashni orqa fonda ishga tushiramiz
    threading.Thread(target=auto_github_push, daemon=True).start()
    # Botni ishga tushirish
    bot.polling(none_stop=True)
