# -*- coding: utf-8 -*-

import os
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

# 🔐 Токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

PRIVATE_CHANNEL_ID = -1003336905435
ADMIN_CHANNEL_ID = -1003109975028

TARIFF_NAME = "PrivatForFap🍑"
PRICE = "200 ₽"

# временное хранилище заявок
PENDING_PAYMENTS = {}


# ====== REPLY-МЕНЮ (плашки снизу) ======
def get_main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛒 Тарифы"), KeyboardButton("📊 Подписка")]
        ],
        resize_keyboard=True
    )


# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выбери пункт меню 👇",
        reply_markup=get_main_menu()
    )


# ====== обработка плашек снизу ======
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛒 Тарифы":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"🍑 {TARIFF_NAME} — {PRICE}",
                callback_data="buy"
            )]
        ])

        await update.message.reply_text(
            "📦 Доступные тарифы:",
            reply_markup=keyboard
        )

    elif text == "📊 Подписка":
        await update.message.reply_text(
            "📊 *Информация о подписке*\n\n"
            "У тебя пока нет активной подписки.",
            parse_mode="Markdown"
        )


# ====== INLINE-КНОПКИ (покупка) ======
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "buy":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 СБП (200 ₽)", callback_data="sbp")]
        ])

        await query.message.reply_text(
            f"📦 Тариф: {TARIFF_NAME}\n"
            f"💰 Цена: {PRICE}\n\n"
            "Выбери способ оплаты:",
            reply_markup=keyboard
        )

    elif query.data == "sbp":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Я оплатил", callback_data="wait")]
        ])

        await query.message.reply_text(
            "💳 *Оплата по СБП*\n\n"
            "Переведи *200 ₽* по реквизитам:\n"
            "👉 ТУТ ТВОИ РЕКВИЗИТЫ\n\n"
            "После оплаты нажми кнопку ниже 👇",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif query.data == "wait":
        time = datetime.now().strftime("%d.%m.%Y %H:%M")
        PENDING_PAYMENTS[user.id] = True

        admin_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ Подтвердить оплату",
                callback_data=f"approve_{user.id}"
            )]
        ])

        await context.bot.send_message(
            ADMIN_CHANNEL_ID,
            (
                "💸 *Заявка на оплату*\n\n"
                f"👤 @{user.username or 'без username'}\n"
                f"🆔 ID: {user.id}\n"
                f"📦 Тариф: {TARIFF_NAME}\n"
                f"💳 Способ: СБП\n"
                f"🕒 Время: {time}"
            ),
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )

        await query.message.reply_text(
            "⏳ *Заявка отправлена*\n"
            "Ожидай подтверждения администратора.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])

        if user_id not in PENDING_PAYMENTS:
            await query.message.reply_text("❌ Заявка уже обработана")
            return

        link = await context.bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1
        )

        await context.bot.send_message(
            user_id,
            "🎉 *Оплата подтверждена!*\n\n"
            "Вот ссылка для входа 👇\n\n"
            f"{link.invite_link}",
            parse_mode="Markdown"
        )

        del PENDING_PAYMENTS[user_id]

        await query.message.edit_text("✅ Оплата подтверждена\nДоступ выдан")


# ====== ЗАПУСК ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
