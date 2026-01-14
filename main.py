# -*- coding: utf-8 -*-

import os
import sqlite3
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

PRIVATE_CHANNEL_ID = -1003336905435
ADMIN_CHANNEL_ID = -1003109975028

TARIFF_NAME = "PrivatForFap🍑"
PRICE = "200 ₽"

DB_FILE = "subscriptions.db"

# ================= БАЗА ДАННЫХ =================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            expire_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def set_subscription(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO subscriptions (user_id, expire_date) VALUES (?, ?)",
        (user_id, None)  # None = навсегда
    )
    conn.commit()
    conn.close()


def has_subscription(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM subscriptions WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


# ================= UI =================

def main_menu():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🛒 Тарифы"), KeyboardButton("📊 Подписка")]],
        resize_keyboard=True
    )


# ================= /start =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nВыбери действие 👇",
        reply_markup=main_menu()
    )


# ================= МЕНЮ =================

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "🛒 Тарифы":
        await update.message.reply_text(
            "📦 Доступные тарифы:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"🍑 {TARIFF_NAME} — {PRICE}",
                    callback_data="buy"
                )]
            ])
        )

    elif text == "📊 Подписка":
        if has_subscription(user_id):
            msg = (
                "📊 Информация о подписке\n\n"
                "♾ Подписка активна навсегда"
            )
        else:
            msg = (
                "📊 Информация о подписке\n\n"
                "❌ У тебя нет активной подписки."
            )

        await update.message.reply_text(msg)


# ================= CALLBACKS =================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "buy":
        await query.message.reply_text(
            f"📦 Тариф: {TARIFF_NAME}\n"
            f"💰 Цена: {PRICE}\n\n"
            "Выбери способ оплаты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 СБП (200 ₽)", callback_data="sbp")]
            ])
        )

    elif query.data == "sbp":
        await query.message.reply_text(
            "💳 Оплата по СБП\n\n"
            "Переведи 200 ₽ по реквизитам:\n"
            "👉 ТУТ ТВОИ РЕКВИЗИТЫ\n\n"
            "После оплаты нажми кнопку ниже 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏳ Я оплатил", callback_data="wait")]
            ])
        )

    elif query.data == "wait":
        time = datetime.now().strftime("%d.%m.%Y %H:%M")

        await context.bot.send_message(
            ADMIN_CHANNEL_ID,
            f"💸 Заявка на оплату\n\n"
            f"👤 @{user.username or 'без username'}\n"
            f"🆔 ID: {user.id}\n"
            f"📦 Тариф: {TARIFF_NAME} (навсегда)\n"
            f"🕒 Время: {time}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "✅ Подтвердить оплату",
                    callback_data=f"approve_{user.id}"
                )]
            ])
        )

        await query.message.reply_text(
            "⏳ Заявка отправлена.\nОжидай подтверждения администратора.",
            reply_markup=main_menu()
        )

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])

        # сохраняем подписку
        set_subscription(user_id)

        link = await context.bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1
        )

        await context.bot.send_message(
            user_id,
            "🎉 Оплата подтверждена!\n\n"
            "♾ Подписка активна навсегда\n\n"
            f"🔗 Ссылка для входа:\n{link.invite_link}"
        )

        await query.message.edit_text(
            "✅ Оплата подтверждена\n♾ Доступ выдан"
        )


# ================= ЗАПУСК =================

def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    app.run_polling()


if __name__
