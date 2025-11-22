import json
import time
import threading
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from tiktok_checker import is_live

TOKEN = "ahahah FUCK you SHITI MOM your Nigga scammer"
DATA_FILE = "data.json"
CHECK_INTERVAL = 1


# -------------------- DATEN HANDLING --------------------

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_data():
    # Falls Datei fehlt → neu erzeugen
    if not os.path.exists(DATA_FILE):
        default = {"chat_id": None, "users": []}
        save_data(default)
        return default

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        # Falls Datei eine Liste oder etwas anderes ist → reparieren
        if not isinstance(data, dict):
            default = {"chat_id": None, "users": []}
            save_data(default)
            return default

        # Falls Keys fehlen → hinzufügen
        if "chat_id" not in data:
            data["chat_id"] = None
        if "users" not in data:
            data["users"] = []

        return data

    except:
        # Falls JSON kaputt → neu erstellen
        default = {"chat_id": None, "users": []}
        save_data(default)
        return default


# -------------------- MENÜ --------------------

def menu_keyboard():
    kb = [
        [InlineKeyboardButton("➕ User hinzufügen", callback_data="add")],
        [InlineKeyboardButton("📋 Userliste anzeigen", callback_data="list")],
        [InlineKeyboardButton("🗑 User löschen", callback_data="delmenu")]
    ]
    return InlineKeyboardMarkup(kb)


def start(update: Update, context: CallbackContext):
    data = load_data()
    data["chat_id"] = update.message.chat_id
    save_data(data)

    update.message.reply_text("📌 Hauptmenü:", reply_markup=menu_keyboard())


# -------------------- BUTTON HANDLER --------------------

waiting_for_username = False


def button_handler(update: Update, context: CallbackContext):
    global waiting_for_username

    query = update.callback_query

    try:
        query.answer()
    except:
        pass

    data = load_data()
    users = data["users"]

    if query.data == "add":
        waiting_for_username = True
        query.edit_message_text("Bitte TikTok Username senden (ohne @):", reply_markup=menu_keyboard())

    elif query.data == "list":
        if not users:
            query.edit_message_text("❗ Keine User gespeichert.", reply_markup=menu_keyboard())
            return

        text = "📋 Überwachte User:\n\n"
        for u in users:
            text += f"• {u}\n"

        query.edit_message_text(text, reply_markup=menu_keyboard())

    elif query.data == "delmenu":
        if not users:
            query.edit_message_text("❗ Keine User zum Löschen.", reply_markup=menu_keyboard())
            return

        kb = [[InlineKeyboardButton(f"🗑 {u}", callback_data=f"del:{u}")] for u in users]
        kb.append([InlineKeyboardButton("🔙 Zurück", callback_data="back")])

        query.edit_message_text("Welchen User möchtest du löschen?", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("del:"):
        username = query.data.split(":")[1]

        if username in users:
            users.remove(username)
            save_data(data)
            query.edit_message_text(f"🗑 {username} gelöscht.", reply_markup=menu_keyboard())

    elif query.data == "back":
        query.edit_message_text("📌 Hauptmenü:", reply_markup=menu_keyboard())


# -------------------- TEXT HANDLER --------------------

def text_handler(update: Update, context: CallbackContext):
    global waiting_for_username

    if not waiting_for_username:
        update.message.reply_text("Bitte benutze das Menü unten.", reply_markup=menu_keyboard())
        return

    username = update.message.text.strip().lower()

    data = load_data()

    if username in data["users"]:
        update.message.reply_text("❗ User bereits vorhanden.", reply_markup=menu_keyboard())
        waiting_for_username = False
        return

    data["users"].append(username)
    save_data(data)

    update.message.reply_text(f"✔ {username} wurde hinzugefügt.", reply_markup=menu_keyboard())
    waiting_for_username = False


# -------------------- LIVE CHECKER --------------------

live_state = {}


def live_checker(bot):
    while True:
        data = load_data()
        chat_id = data["chat_id"]

        if not chat_id:
            time.sleep(CHECK_INTERVAL)
            continue

        for user in data["users"]:
            islive, _ = is_live(user)

            if islive and not live_state.get(user, False):
                bot.send_message(chat_id, f"🔴 {user} ist jetzt LIVE!\nhttps://www.tiktok.com/@{user}/live")
                live_state[user] = True

            if not islive:
                live_state[user] = False

        time.sleep(CHECK_INTERVAL)


# -------------------- MAIN --------------------

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    updater.start_polling()

    bot = updater.bot
    t = threading.Thread(target=live_checker, args=(bot,), daemon=True)
    t.start()

    updater.idle()


if __name__ == "__main__":
    main()

